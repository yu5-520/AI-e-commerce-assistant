"""V16.2 real task mapping Agent + RAG.

V16.2 completes the MVP-real chain after V16.1: product judgments come from a
real product judgment Agent, and 70%+ product_judgment_package rows are mapped
into tasks by a real task mapping Agent using RAG / permission / SOP context.

Failure is transparent: missing API key, provider failure, invalid JSON, or no
valid task output creates no fake task and no local SOP-template fallback.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from typing import Any, Dict, Iterable, List, Tuple

import src.services.dual_agent_product_task_service as base
import src.services.real_product_judgment_agent_v161_service as product_agent
from src.services.agent_budget_ledger_service import get_or_create_agent_budget_ledger, read_agent_budget_summary, register_agent_event
from src.services.signal_pool_service import list_signals, update_signal_status
from src.services.task_generation_run_service import record_task_generation_run

REAL_TASK_MAPPING_VERSION = "16.2"
TASK_AGENT_STAGE = "task_mapping_agent"
TASK_AGENT_MODE = "real_rag_permission_task_mapping_strict_json"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com/chat/completions"
MAX_PACKAGES_PER_CALL = int(os.getenv("TASK_MAPPING_AGENT_BATCH_SIZE", "8"))
MAX_TASK_AGENT_CALLS_PER_RUN = int(os.getenv("TASK_MAPPING_AGENT_MAX_CALLS", "2"))
TIMEOUT_SECONDS = int(os.getenv("TASK_MAPPING_AGENT_TIMEOUT", "120"))
ALLOWED_DECISIONS = {"create_task_snapshot", "manager_review_required", "no_task"}
ALLOWED_PRIORITIES = {"高", "中", "低"}


def _provider_api_key() -> str | None:
    return os.getenv("TASK_MAPPING_AGENT_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")


def _provider_base_url() -> str:
    return os.getenv("TASK_MAPPING_AGENT_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL


def _provider_model() -> str:
    return os.getenv("TASK_MAPPING_AGENT_MODEL") or os.getenv("DEEPSEEK_MODEL") or DEFAULT_MODEL


def _provider_enabled() -> bool:
    flag = os.getenv("TASK_MAPPING_AGENT_ENABLED", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def _chunks(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    size = max(1, size)
    for index in range(0, len(items), size):
        yield items[index:index + size]


def _compact_rag_context(rag_context: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(rag_context, dict):
        return {}
    items = rag_context.get("items") or rag_context.get("matchedContexts") or rag_context.get("contexts") or []
    if isinstance(items, list):
        items = items[:16]
    return {
        "ragContextRef": rag_context.get("ragContextRef") or rag_context.get("outputRef"),
        "matchedContextCount": rag_context.get("matchedContextCount"),
        "items": items,
        "rule": "Use these contexts as permission/SOP/baseline references. Do not invent permissions not present in the context.",
    }


def _compact_package(package: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "packageId": package.get("packageId"),
        "dataVersion": package.get("dataVersion"),
        "storeId": package.get("storeId"),
        "productId": package.get("productId"),
        "primaryRisk": package.get("primaryRisk"),
        "secondaryRisks": package.get("secondaryRisks"),
        "maxSeverity": package.get("maxSeverity"),
        "packageConfidence": package.get("packageConfidence") or package.get("confidence"),
        "judgmentCount": package.get("judgmentCount"),
        "riskCandidateCount": package.get("riskCandidateCount"),
        "summary": package.get("summary"),
        "evidencePack": package.get("evidencePack") or [],
    }


def _build_messages(data_version: str | None, packages: List[Dict[str, Any]], rag_context: Dict[str, Any]) -> List[Dict[str, str]]:
    payload = {"dataVersion": data_version, "packages": [_compact_package(item) for item in packages], "ragContext": _compact_rag_context(rag_context)}
    system_prompt = (
        "你是电商经营任务映射Agent。你不重新判断商品风险，只把70%+商品判断包映射成真实组织任务。"
        "你必须结合RAG中的公司权限、账号权限、审批规则、SOP、证据要求和复盘规则；没有权限依据时输出no_task或manager_review_required。"
        "你必须只返回严格JSON，不要Markdown。不要编造输入中没有的数字。"
        "输出格式：{\"tasks\":[{\"packageId\":str,\"productId\":str,\"storeId\":str,\"decision\":\"create_task_snapshot|manager_review_required|no_task\",\"taskTitle\":str,\"priority\":\"高|中|低\",\"deadline\":str,\"assigneeRole\":str,\"approvalRequired\":bool,\"forbiddenActions\":[str],\"sopSteps\":[str],\"evidenceRequirements\":[str],\"reviewMetrics\":[str],\"reason\":str}]}。"
        "每个正式任务必须可执行：至少3个sopSteps，至少2个evidenceRequirements，必须说明禁止动作或权限边界。"
    )
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]


def _extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError("task_mapping_response_has_no_json_object")
        return json.loads(match.group(0))


def _call_provider(messages: List[Dict[str, str]]) -> Tuple[Dict[str, Any], Dict[str, int]]:
    api_key = _provider_api_key()
    if not _provider_enabled():
        raise RuntimeError("task_mapping_agent_disabled")
    if not api_key:
        raise RuntimeError("missing_TASK_MAPPING_AGENT_API_KEY_or_DEEPSEEK_API_KEY")
    body = json.dumps({"model": _provider_model(), "messages": messages, "temperature": 0.1, "response_format": {"type": "json_object"}}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(_provider_base_url(), data=body, method="POST", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:500]
        raise RuntimeError(f"task_mapping_provider_http_{exc.code}:{detail}") from exc
    data = json.loads(raw)
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise ValueError("task_mapping_response_empty_content")
    return _extract_json_object(content), {"input": int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0), "output": int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)}


def _package_map(packages: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(item.get("packageId")): item for item in packages if item.get("packageId")}


def _safe_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()][:12]
    if value:
        return [str(value)]
    return []


def _normalize_decision(item: Dict[str, Any], package_by_id: Dict[str, Dict[str, Any]], data_version: str | None) -> Dict[str, Any] | None:
    package_id = str(item.get("packageId") or "").strip()
    package = package_by_id.get(package_id)
    if not package:
        return None
    product_id = str(item.get("productId") or package.get("productId") or "").strip()
    store_id = str(item.get("storeId") or package.get("storeId") or "GLOBAL").strip()
    if product_id != str(package.get("productId")):
        return None
    decision = str(item.get("decision") or "no_task").strip()
    if decision not in ALLOWED_DECISIONS:
        decision = "no_task"
    priority = str(item.get("priority") or "中").strip()
    if priority not in ALLOWED_PRIORITIES:
        priority = "中"
    sop_steps = _safe_list(item.get("sopSteps"))
    evidence = _safe_list(item.get("evidenceRequirements"))
    forbidden = _safe_list(item.get("forbiddenActions"))
    if decision != "no_task" and (len(sop_steps) < 3 or len(evidence) < 2):
        return None
    approval_required = bool(item.get("approvalRequired")) or decision == "manager_review_required"
    reason = str(item.get("reason") or f"商品判断包 {package_id} 经真实任务映射Agent处理。")
    title = str(item.get("taskTitle") or f"商品经营复核｜{product_id}｜{package.get('primaryRisk')}")
    deadline = str(item.get("deadline") or ("6小时内" if priority == "高" else "24小时内"))
    if decision == "no_task":
        task_plan = {"title": title, "taskType": "observe_only", "priority": "低", "deadline": "后台观察", "reason": reason, "sopSteps": [], "evidenceRequirements": []}
    else:
        task_plan = {
            "title": title,
            "subtitle": "真实RAG权限任务映射",
            "entityType": "product",
            "entityId": product_id,
            "productId": product_id,
            "storeId": store_id,
            "taskType": "product_operation_review",
            "actionType": "real_rag_permission_task_mapping",
            "priority": priority,
            "riskLevel": "high" if priority == "高" else "medium",
            "deadline": deadline,
            "riskDomain": package.get("primaryRisk"),
            "assigneeRole": str(item.get("assigneeRole") or "operator"),
            "approvalRequired": approval_required,
            "forbiddenActions": forbidden,
            "operationBudget": {"taskType": "product_operation_review", "riskLevel": "high" if priority == "高" else "medium", "budgetUpperBound": 0, "operatorBudgetApplies": False, "requiresApproval": approval_required, "forbiddenActions": forbidden},
            "sopSteps": sop_steps,
            "evidenceRequirements": evidence,
            "reviewMetrics": _safe_list(item.get("reviewMetrics")) or [package.get("primaryRisk") or "经营指标"],
            "needManagerReview": approval_required,
            "reason": reason,
        }
    return {
        "version": REAL_TASK_MAPPING_VERSION,
        "decisionId": base.make_id("TGD"),
        "packageId": package_id,
        "dataVersion": data_version or package.get("dataVersion"),
        "storeId": store_id,
        "productId": product_id,
        "decision": decision,
        "taskTitle": task_plan.get("title"),
        "priority": task_plan.get("priority"),
        "reason": reason,
        "taskPlan": task_plan,
        "productJudgmentPackage": package,
        "taskMappingAgentEvidence": {"providerModel": _provider_model(), "source": "real_task_mapping_agent", "forbiddenActions": forbidden},
        "rule": "V16.2 real task mapping Agent output; no permission SOP template fallback.",
    }


def _real_task_mapping_decisions(packages: List[Dict[str, Any]], data_version: str | None, rag_context: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    candidate_packages = [item for item in packages if item.get("taskCandidateAllowed")]
    package_by_id = _package_map(candidate_packages)
    if not candidate_packages:
        return [], {"providerStatus": "no_candidate_packages", "actualCalls": 0, "attemptedBatches": 0, "errors": []}
    decisions: List[Dict[str, Any]] = []
    errors: List[str] = []
    actual_calls = 0
    input_tokens = 0
    output_tokens = 0
    attempted_batches = 0
    for batch_index, batch in enumerate(_chunks(candidate_packages, MAX_PACKAGES_PER_CALL)):
        if batch_index >= MAX_TASK_AGENT_CALLS_PER_RUN:
            errors.append("task_mapping_call_budget_reached_remaining_packages_skipped")
            break
        attempted_batches += 1
        try:
            payload, usage = _call_provider(_build_messages(data_version, batch, rag_context))
            actual_calls += 1
            input_tokens += usage.get("input", 0)
            output_tokens += usage.get("output", 0)
            raw_tasks = payload.get("tasks") if isinstance(payload, dict) else []
            if not isinstance(raw_tasks, list):
                raise ValueError("task_mapping_json_missing_tasks_array")
            for raw in raw_tasks:
                if isinstance(raw, dict):
                    decision = _normalize_decision(raw, package_by_id, data_version)
                    if decision:
                        decisions.append(decision)
        except Exception as exc:
            errors.append(str(exc)[:500])
            break
    status = "ok" if decisions and not errors else "partial" if decisions else "failed"
    return decisions, {"providerStatus": status, "actualCalls": actual_calls, "attemptedBatches": attempted_batches, "errors": errors, "inputTokens": input_tokens, "outputTokens": output_tokens, "model": _provider_model(), "baseUrl": _provider_base_url(), "maxPackagesPerCall": MAX_PACKAGES_PER_CALL, "maxCallsPerRun": MAX_TASK_AGENT_CALLS_PER_RUN, "candidatePackageCount": len(candidate_packages)}


def run_dual_agent_product_task_pipeline(data_version: str | None = None, *, rag_context_ref: str | None = None, max_signals: int = 160, created_by: str | None = None) -> Dict[str, Any]:
    base.ensure_dual_agent_tables()
    ledger = get_or_create_agent_budget_ledger(data_version=data_version, source="v16_2_real_task_mapping_agent")
    base._clear_version_rows(data_version)
    rag_context, rag_retrieval_count = product_agent._latest_or_build_rag_context(data_version)
    signals = (list_signals(data_version=data_version, status="pending_rag_agent", limit=max_signals).get("signals") or [])[:max_signals]

    raw_judgments, product_provider = product_agent._real_agent_judgments(signals, data_version, rag_context)
    register_agent_event(
        ledger_id=ledger["ledgerId"], data_version=data_version, stage="product_judgment_agent", call_type="real_llm_batch_product_judgment",
        requested_calls=min(product_agent.MAX_PRODUCT_AGENT_CALLS_PER_RUN, max(1, (len([s for s in signals if product_agent._strict_product_id(s)]) + product_agent.MAX_PRODUCTS_PER_CALL - 1) // product_agent.MAX_PRODUCTS_PER_CALL)) if signals else 0,
        actual_calls=int(product_provider.get("actualCalls") or 0), fallback_used=False, rag_retrievals=rag_retrieval_count,
        actual_input_tokens=int(product_provider.get("inputTokens") or 0), actual_output_tokens=int(product_provider.get("outputTokens") or 0),
        reason="V16.2沿用V16.1真实商品判断Agent批量分析fullProductBundle；失败不回退假判断。",
        payload={"provider": product_provider, "signalCount": len(signals), "mode": product_agent.PRODUCT_AGENT_MODE},
    )
    base._save_raw_judgments(raw_judgments)
    next_status = "real_product_agent_judged" if raw_judgments else "real_product_agent_failed"
    for signal in signals:
        update_signal_status(signal.get("signalId"), next_status, {"version": REAL_TASK_MAPPING_VERSION, "productProviderStatus": product_provider.get("providerStatus")})

    packages, identity_gaps = base._package_product_judgments(data_version)
    sorted_packages = sorted(packages, key=lambda item: (1 if item.get("taskCandidateAllowed") else 0, float(item.get("packageConfidence") or item.get("confidence") or 0), base.SEVERITY_RANK.get(str(item.get("maxSeverity") or "normal"), 0)), reverse=True)

    if raw_judgments:
        decisions, task_provider = _real_task_mapping_decisions(sorted_packages, data_version, rag_context)
    else:
        decisions, task_provider = [], {"providerStatus": "skipped_no_product_judgments", "actualCalls": 0, "attemptedBatches": 0, "errors": ["no_real_product_judgments"]}
    register_agent_event(
        ledger_id=ledger["ledgerId"], data_version=data_version, stage=TASK_AGENT_STAGE, call_type="real_rag_permission_task_mapping",
        requested_calls=min(MAX_TASK_AGENT_CALLS_PER_RUN, max(1, (len([p for p in sorted_packages if p.get("taskCandidateAllowed")]) + MAX_PACKAGES_PER_CALL - 1) // MAX_PACKAGES_PER_CALL)) if raw_judgments and sorted_packages else 0,
        actual_calls=int(task_provider.get("actualCalls") or 0), fallback_used=False, rag_retrievals=0,
        actual_input_tokens=int(task_provider.get("inputTokens") or 0), actual_output_tokens=int(task_provider.get("outputTokens") or 0),
        reason="V16.2真实任务映射Agent基于RAG权限/SOP把70%+商品判断包生成任务；失败不回退模板任务。",
        payload={"provider": task_provider, "mode": TASK_AGENT_MODE},
    )

    for decision in decisions:
        base._save_decision(decision)
    streamed = [base._stream_decision_to_task_pool(decision, created_by=created_by) for decision in decisions]
    by_decision = Counter(str(item.get("decision")) for item in decisions)
    task_pool_created = sum(int(item.get("createdTaskCount") or 0) for item in streamed)
    formal_decision_count = int(by_decision.get("create_task_snapshot", 0) or 0) + int(by_decision.get("manager_review_required", 0) or 0)
    budget_summary = read_agent_budget_summary(ledger_id=ledger["ledgerId"])
    budget_summary["productJudgmentProvider"] = product_provider
    budget_summary["taskMappingProvider"] = task_provider
    api_budget_violation = bool(budget_summary.get("budgetViolation"))

    if not raw_judgments:
        zero_reasons = ["真实商品判断Agent未产出有效JSON判断：" + "; ".join(product_provider.get("errors") or [product_provider.get("providerStatus") or "unknown"])]
    elif not decisions:
        zero_reasons = ["真实任务映射Agent未产出有效任务JSON：" + "; ".join(task_provider.get("errors") or [task_provider.get("providerStatus") or "unknown"])]
    else:
        zero_reasons = [item.get("reason") for item in decisions if item.get("decision") == "no_task"][:20]

    generation_run = record_task_generation_run(
        data_version=data_version,
        input_bundle_count=len(signals),
        agent_judgment_count=len(raw_judgments),
        product_judgment_package_count=len(packages),
        identity_gap_count=len(identity_gaps),
        task_decision_count=len(decisions),
        by_decision=dict(by_decision),
        streamed_task_snapshot_count=sum(1 for item in streamed if item.get("ok")),
        task_pool_created_count=task_pool_created,
        skipped_formal_count=sum(1 for item in streamed if item.get("skipped")),
        zero_task_reasons=zero_reasons,
        agent1_api_call_count=int(product_provider.get("actualCalls") or 0),
        rag_retrieval_count=rag_retrieval_count,
        api_budget_violation=api_budget_violation,
        agent_budget_summary=budget_summary,
        total_agent_call_count=int(budget_summary.get("totalAgentCalls") or 0),
        total_agent_budget=int(budget_summary.get("totalAgentBudget") or 8),
        source="v16_2_real_product_and_task_agents",
    )
    try:
        from src.services.frontend_read_model_service import refresh_task_views
        refresh_task_views(data_version=data_version)
    except Exception:
        pass
    ref = f"real_task_mapping_agent:{data_version or 'latest'}"
    return {
        "version": REAL_TASK_MAPPING_VERSION,
        "mode": "v16_2_real_product_and_task_agents",
        "dataVersion": data_version,
        "outputRef": ref,
        "agentJudgmentRef": f"real_product_judgment_agent:{data_version or 'latest'}",
        "taskMappingRef": ref,
        "ragContextRef": rag_context_ref or rag_context.get("ragContextRef") or rag_context.get("outputRef"),
        "signalCount": len(signals),
        "judgmentCount": len(raw_judgments),
        "rawJudgmentCount": len(raw_judgments),
        "metricJudgmentMode": "real_llm_json",
        "agent1ApiMode": product_agent.PRODUCT_AGENT_MODE,
        "agent1ApiCallCount": int(product_provider.get("actualCalls") or 0),
        "productAgentProviderStatus": product_provider.get("providerStatus"),
        "productAgentProvider": product_provider,
        "taskMappingApiMode": TASK_AGENT_MODE,
        "taskMappingApiCallCount": int(task_provider.get("actualCalls") or 0),
        "taskMappingProviderStatus": task_provider.get("providerStatus"),
        "taskMappingProvider": task_provider,
        "totalAgentCallCount": int(budget_summary.get("totalAgentCalls") or 0),
        "totalAgentBudget": int(budget_summary.get("totalAgentBudget") or 8),
        "apiBudgetViolation": api_budget_violation,
        "agentBudgetLedger": budget_summary,
        "ragRetrievalCount": rag_retrieval_count,
        "ragRetrievalScope": "data_version_once",
        "averageJudgmentsPerSignal": round(len(raw_judgments) / len(signals), 2) if signals else 0,
        "productJudgmentPackageCount": len(packages),
        "identityGapCount": len(identity_gaps),
        "taskDecisionCount": len(decisions),
        "formalDecisionCount": formal_decision_count,
        "streamedTaskSnapshotCount": sum(1 for item in streamed if item.get("ok")),
        "streamedTaskPoolCount": task_pool_created,
        "byDecision": dict(by_decision),
        "taskGenerationRun": generation_run,
        "packages": packages[:50],
        "decisions": decisions[:50],
        "streamed": streamed[:50],
        "rule": "V16.2: product judgment and task mapping must both come from real batched Agent JSON; failure creates no fake tasks.",
    }


ensure_dual_agent_tables = base.ensure_dual_agent_tables
