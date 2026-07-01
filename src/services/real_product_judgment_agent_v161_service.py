"""V16.1 real product judgment Agent.

This is the MVP-real product judgment stage: product judgments come from a real
LLM provider call over batched fullProductBundle records. If the provider is not
configured or returns invalid JSON, the pipeline records the failure and does not
fall back to fake/local judgments. System code still owns package compression,
70% confidence gate, task-pool admission and current-run read-model refresh.
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
from src.repositories.sqlite_repository import dumps
from src.services.agent_budget_ledger_service import get_or_create_agent_budget_ledger, read_agent_budget_summary, register_agent_event
from src.services.rag_context_station_service import build_rag_context_snapshot, latest_rag_context
from src.services.signal_pool_service import list_signals, update_signal_status
from src.services.task_generation_run_service import record_task_generation_run

REAL_PRODUCT_AGENT_VERSION = "16.1"
PRODUCT_AGENT_STAGE = "product_judgment_agent"
PRODUCT_AGENT_MODE = "real_llm_batch_product_judgment_strict_json"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_BASE_URL = "https://api.deepseek.com/chat/completions"
MAX_PRODUCTS_PER_CALL = int(os.getenv("PRODUCT_JUDGMENT_AGENT_BATCH_SIZE", "30"))
MAX_PRODUCT_AGENT_CALLS_PER_RUN = int(os.getenv("PRODUCT_JUDGMENT_AGENT_MAX_CALLS", "3"))
TIMEOUT_SECONDS = int(os.getenv("PRODUCT_JUDGMENT_AGENT_TIMEOUT", "90"))
ALLOWED_SEVERITY = {"normal", "low", "medium", "high", "critical"}
ALLOWED_HINTS = {"risk_candidate", "related_risk", "data_gap_candidate", "observe_only", "metric_observation", "product_level_observation"}


def _provider_api_key() -> str | None:
    return os.getenv("PRODUCT_JUDGMENT_AGENT_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")


def _provider_base_url() -> str:
    return os.getenv("PRODUCT_JUDGMENT_AGENT_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or DEFAULT_BASE_URL


def _provider_model() -> str:
    return os.getenv("PRODUCT_JUDGMENT_AGENT_MODEL") or os.getenv("DEEPSEEK_MODEL") or DEFAULT_MODEL


def _provider_enabled() -> bool:
    flag = os.getenv("PRODUCT_JUDGMENT_AGENT_ENABLED", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def _chunks(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    size = max(1, size)
    for index in range(0, len(items), size):
        yield items[index:index + size]


def _safe_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return value


def _strict_product_id(bundle: Dict[str, Any]) -> str | None:
    return base._strict_product_id(bundle)


def _store_id(bundle: Dict[str, Any]) -> str:
    return base._store_id(bundle)


def _field_signals(bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    snapshot = bundle.get("snapshotLayer") if isinstance(bundle.get("snapshotLayer"), dict) else {}
    signals = snapshot.get("fieldSignals") or bundle.get("fieldSignals") or []
    return signals if isinstance(signals, list) else []


def _compact_metric_layer(bundle: Dict[str, Any]) -> Dict[str, Any]:
    metric = bundle.get("metricLayer") if isinstance(bundle.get("metricLayer"), dict) else {}
    keys = ["paymentAmount", "roi", "roas", "adSpend", "refundRate", "inventory", "conversionRate", "grossMargin", "clickRate", "visitorCount", "orderCount"]
    return {key: metric.get(key) for key in keys if key in metric}


def _compact_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    profile = bundle.get("profileLayer") if isinstance(bundle.get("profileLayer"), dict) else {}
    cross = bundle.get("crossValidation") if isinstance(bundle.get("crossValidation"), dict) else {}
    trend = bundle.get("trendWindows") if isinstance(bundle.get("trendWindows"), dict) else {}
    product_id = _strict_product_id(bundle)
    return {
        "productId": product_id,
        "storeId": _store_id(bundle),
        "title": profile.get("title") or profile.get("shortName"),
        "verticalCategory": bundle.get("verticalCategory") or profile.get("verticalCategory"),
        "productRole": profile.get("productRole"),
        "lifecycleStage": profile.get("lifecycleStage"),
        "metricLayer": _compact_metric_layer(bundle),
        "fieldSignals": [{"metricCode": item.get("metricCode"), "signalStrength": item.get("signalStrength"), "reason": item.get("reason"), "current": item.get("current"), "previous": item.get("previous"), "delta": item.get("delta")} for item in _field_signals(bundle)[:12]],
        "crossValidation": {"changedMetricCount": cross.get("changedMetricCount"), "abnormalMetricCount": cross.get("abnormalMetricCount"), "sourceVersionCount": cross.get("sourceVersionCount")},
        "trendWindows": trend,
        "dataFingerprint": bundle.get("dataFingerprint"),
        "bundleFingerprint": bundle.get("bundleFingerprint"),
        "signalId": bundle.get("signalId"),
        "bundleId": bundle.get("bundleId"),
    }


def _compact_rag_context(rag_context: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(rag_context, dict):
        return {}
    items = rag_context.get("items") or rag_context.get("matchedContexts") or rag_context.get("contexts") or []
    if isinstance(items, list):
        items = items[:10]
    return {"ragContextRef": rag_context.get("ragContextRef") or rag_context.get("outputRef"), "matchedContextCount": rag_context.get("matchedContextCount"), "items": items}


def _build_messages(data_version: str | None, batch: List[Dict[str, Any]], rag_context: Dict[str, Any]) -> List[Dict[str, str]]:
    payload = {"dataVersion": data_version, "products": [_compact_bundle(item) for item in batch], "ragContext": _compact_rag_context(rag_context)}
    system_prompt = (
        "你是电商经营商品判断Agent。只判断商品经营状态，不生成任务、不写SOP、不决定任务池。"
        "你必须只返回严格JSON，不要Markdown。"
        "根据商品全量包中的垂直类目、指标变化、趋势、环比/同比/连比、fieldSignals、RAG基准进行判断。"
        "不要编造输入中没有的数字；证据必须来自输入字段。"
        "低置信或证据不足时，返回observe_only或较低confidence，而不是强行生成风险。"
        "输出格式：{\"judgments\":[{\"productId\":str,\"storeId\":str,\"metricCode\":str,\"severity\":\"normal|low|medium|high|critical\",\"confidence\":0-1,\"decisionHint\":\"risk_candidate|related_risk|data_gap_candidate|observe_only|metric_observation|product_level_observation\",\"finding\":str,\"evidence\":[str]}]}。"
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
            raise ValueError("provider_response_has_no_json_object")
        return json.loads(match.group(0))


def _call_provider(messages: List[Dict[str, str]]) -> Tuple[Dict[str, Any], Dict[str, int]]:
    api_key = _provider_api_key()
    if not _provider_enabled():
        raise RuntimeError("product_judgment_agent_disabled")
    if not api_key:
        raise RuntimeError("missing_PRODUCT_JUDGMENT_AGENT_API_KEY_or_DEEPSEEK_API_KEY")
    body = json.dumps({"model": _provider_model(), "messages": messages, "temperature": 0.1, "response_format": {"type": "json_object"}}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(_provider_base_url(), data=body, method="POST", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")[:500]
        raise RuntimeError(f"provider_http_{exc.code}:{detail}") from exc
    data = json.loads(raw)
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
    if not content:
        raise ValueError("provider_response_empty_content")
    return _extract_json_object(content), {"input": int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0), "output": int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)}


def _source_map(signals: List[Dict[str, Any]]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    result: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for item in signals:
        product_id = _strict_product_id(item)
        if product_id:
            result[(str(_store_id(item)), str(product_id))] = item
    return result


def _clamp_confidence(value: Any) -> float:
    try:
        number = float(value)
    except Exception:
        number = 0.0
    return round(max(0.0, min(0.98, number)), 4)


def _normalize_judgments(provider_payload: Dict[str, Any], source_by_key: Dict[Tuple[str, str], Dict[str, Any]], data_version: str | None) -> List[Dict[str, Any]]:
    raw_items = provider_payload.get("judgments") if isinstance(provider_payload, dict) else []
    if not isinstance(raw_items, list):
        raise ValueError("provider_json_missing_judgments_array")
    normalized: List[Dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        product_id = str(item.get("productId") or "").strip()
        store_id = str(item.get("storeId") or "GLOBAL").strip()
        source = source_by_key.get((store_id, product_id)) or next((src for (sid, pid), src in source_by_key.items() if pid == product_id), None)
        if not source:
            continue
        severity = str(item.get("severity") or "normal").strip().lower()
        if severity not in ALLOWED_SEVERITY:
            severity = "normal"
        confidence = _clamp_confidence(item.get("confidence"))
        metric_code = str(item.get("metricCode") or source.get("metricCode") or "all_metrics").strip()
        hint = str(item.get("decisionHint") or "metric_observation").strip()
        if hint not in ALLOWED_HINTS:
            hint = "metric_observation"
        evidence = item.get("evidence") if isinstance(item.get("evidence"), list) else []
        finding = str(item.get("finding") or f"{product_id} 的 {metric_code} 由真实商品判断Agent输出。")
        normalized.append({
            "version": REAL_PRODUCT_AGENT_VERSION,
            "judgmentId": base.make_id("APJ"),
            "dataVersion": data_version or source.get("dataVersion"),
            "storeId": store_id,
            "productId": product_id,
            "productIdentityResolved": True,
            "signalId": source.get("signalId"),
            "bundleId": source.get("bundleId"),
            "metricCode": metric_code,
            "severity": severity,
            "decisionHint": hint,
            "confidence": confidence,
            "finding": finding,
            "evidence": {"agentEvidence": evidence[:8], "source": "real_product_judgment_agent", "providerModel": _provider_model()},
            "signal": source,
            "softScore": {"criticalGap": hint == "data_gap_candidate", "strength": severity, "score": confidence, "source": "real_llm_provider"},
            "metricGranularity": "real_agent_metric_level",
            "agent1ApiCallCount": 1,
            "ragRetrievalScope": "data_version_once",
            "rule": "V16.1 real product judgment Agent output; no local fake judgment fallback.",
        })
    return normalized


def _real_agent_judgments(signals: List[Dict[str, Any]], data_version: str | None, rag_context: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    source_by_key = _source_map(signals)
    valid_signals = [item for item in signals if _strict_product_id(item)]
    provider_errors: List[str] = []
    judgments: List[Dict[str, Any]] = []
    actual_calls = 0
    input_tokens = 0
    output_tokens = 0
    attempted_batches = 0
    if not valid_signals:
        return [], {"providerStatus": "no_resolved_products", "actualCalls": 0, "attemptedBatches": 0, "errors": []}
    for batch_index, batch in enumerate(_chunks(valid_signals, MAX_PRODUCTS_PER_CALL)):
        if batch_index >= MAX_PRODUCT_AGENT_CALLS_PER_RUN:
            provider_errors.append("product_agent_call_budget_reached_remaining_products_skipped")
            break
        attempted_batches += 1
        try:
            payload, usage = _call_provider(_build_messages(data_version, batch, rag_context))
            actual_calls += 1
            input_tokens += usage.get("input", 0)
            output_tokens += usage.get("output", 0)
            judgments.extend(_normalize_judgments(payload, source_by_key, data_version))
        except Exception as exc:
            provider_errors.append(str(exc)[:500])
            break
    status = "ok" if judgments and not provider_errors else "partial" if judgments else "failed"
    return judgments, {"providerStatus": status, "actualCalls": actual_calls, "attemptedBatches": attempted_batches, "errors": provider_errors, "inputTokens": input_tokens, "outputTokens": output_tokens, "model": _provider_model(), "baseUrl": _provider_base_url(), "maxProductsPerCall": MAX_PRODUCTS_PER_CALL, "maxCallsPerRun": MAX_PRODUCT_AGENT_CALLS_PER_RUN}


def _latest_or_build_rag_context(data_version: str | None) -> Tuple[Dict[str, Any], int]:
    latest = latest_rag_context(data_version)
    if latest:
        return latest, 0
    return build_rag_context_snapshot(data_version=data_version), 1


def run_dual_agent_product_task_pipeline(data_version: str | None = None, *, rag_context_ref: str | None = None, max_signals: int = 160, created_by: str | None = None) -> Dict[str, Any]:
    base.ensure_dual_agent_tables()
    ledger = get_or_create_agent_budget_ledger(data_version=data_version, source="v16_1_real_product_judgment_agent")
    base._clear_version_rows(data_version)
    rag_context, rag_retrieval_count = _latest_or_build_rag_context(data_version)
    signals = (list_signals(data_version=data_version, status="pending_rag_agent", limit=max_signals).get("signals") or [])[:max_signals]
    raw_judgments, provider = _real_agent_judgments(signals, data_version, rag_context)
    register_agent_event(
        ledger_id=ledger["ledgerId"],
        data_version=data_version,
        stage=PRODUCT_AGENT_STAGE,
        call_type="real_llm_batch_product_judgment",
        requested_calls=min(MAX_PRODUCT_AGENT_CALLS_PER_RUN, max(1, (len([s for s in signals if _strict_product_id(s)]) + MAX_PRODUCTS_PER_CALL - 1) // MAX_PRODUCTS_PER_CALL)) if signals else 0,
        actual_calls=int(provider.get("actualCalls") or 0),
        fallback_used=False,
        rag_retrievals=rag_retrieval_count,
        actual_input_tokens=int(provider.get("inputTokens") or 0),
        actual_output_tokens=int(provider.get("outputTokens") or 0),
        reason="V16.1真实商品判断Agent批量分析fullProductBundle；失败不回退假判断。",
        payload={"provider": provider, "signalCount": len(signals), "mode": PRODUCT_AGENT_MODE},
    )
    base._save_raw_judgments(raw_judgments)
    next_status = "real_product_agent_judged" if raw_judgments else "real_product_agent_failed"
    for signal in signals:
        update_signal_status(signal.get("signalId"), next_status, {"version": REAL_PRODUCT_AGENT_VERSION, "providerStatus": provider.get("providerStatus"), "productAgentMode": PRODUCT_AGENT_MODE})
    packages, identity_gaps = base._package_product_judgments(data_version)
    sorted_packages = sorted(packages, key=lambda item: (1 if item.get("taskCandidateAllowed") else 0, float(item.get("packageConfidence") or item.get("confidence") or 0), base.SEVERITY_RANK.get(str(item.get("maxSeverity") or "normal"), 0)), reverse=True)
    candidate_packages = [item for item in sorted_packages if item.get("taskCandidateAllowed")]
    register_agent_event(ledger_id=ledger["ledgerId"], data_version=data_version, stage="task_mapping_agent", call_type="permission_sop_template", requested_calls=1 if candidate_packages else 0, actual_calls=0, fallback_used=True, reason="V16.1只打开真实商品判断Agent；任务映射仍使用权限SOP模板，等待V16.2接真实RAG任务Agent。", payload={"candidatePackageCount": len(candidate_packages), "maxTasksPerRun": base.MAX_TASKS_PER_RUN})
    decisions: List[Dict[str, Any]] = []
    streamed: List[Dict[str, Any]] = []
    candidate_index = 0
    for package in sorted_packages:
        decision = base._agent2_task_decision(package, candidate_index if package.get("taskCandidateAllowed") else base.MAX_TASKS_PER_RUN + 1)
        if package.get("taskCandidateAllowed"):
            candidate_index += 1
        base._save_decision(decision)
        decisions.append(decision)
        streamed.append(base._stream_decision_to_task_pool(decision, created_by=created_by))
    by_decision = Counter(str(item.get("decision")) for item in decisions)
    task_pool_created = sum(int(item.get("createdTaskCount") or 0) for item in streamed)
    formal_decision_count = int(by_decision.get("create_task_snapshot", 0) or 0) + int(by_decision.get("manager_review_required", 0) or 0)
    budget_summary = read_agent_budget_summary(ledger_id=ledger["ledgerId"])
    budget_summary["productJudgmentProvider"] = provider
    api_budget_violation = bool(budget_summary.get("budgetViolation"))
    if not raw_judgments:
        zero_reasons = ["真实商品判断Agent未产出有效JSON判断：" + "; ".join(provider.get("errors") or [provider.get("providerStatus") or "unknown"])]
    else:
        zero_reasons = [item.get("reason") for item in decisions if item.get("decision") == "no_task"][:20]
    generation_run = record_task_generation_run(data_version=data_version, input_bundle_count=len(signals), agent_judgment_count=len(raw_judgments), product_judgment_package_count=len(packages), identity_gap_count=len(identity_gaps), task_decision_count=len(decisions), by_decision=dict(by_decision), streamed_task_snapshot_count=sum(1 for item in streamed if item.get("ok")), task_pool_created_count=task_pool_created, skipped_formal_count=sum(1 for item in streamed if item.get("skipped")), zero_task_reasons=zero_reasons, agent1_api_call_count=int(provider.get("actualCalls") or 0), rag_retrieval_count=rag_retrieval_count, api_budget_violation=api_budget_violation, agent_budget_summary=budget_summary, total_agent_call_count=int(budget_summary.get("totalAgentCalls") or 0), total_agent_budget=int(budget_summary.get("totalAgentBudget") or 8), source="v16_1_real_product_judgment_agent")
    try:
        from src.services.frontend_read_model_service import refresh_task_views
        refresh_task_views(data_version=data_version)
    except Exception:
        pass
    ref = f"real_product_judgment_agent:{data_version or 'latest'}"
    return {"version": REAL_PRODUCT_AGENT_VERSION, "mode": "v16_1_real_product_judgment_agent", "dataVersion": data_version, "outputRef": ref, "agentJudgmentRef": ref, "ragContextRef": rag_context_ref or rag_context.get("ragContextRef") or rag_context.get("outputRef"), "signalCount": len(signals), "judgmentCount": len(raw_judgments), "rawJudgmentCount": len(raw_judgments), "metricJudgmentMode": "real_llm_json", "agent1ApiMode": PRODUCT_AGENT_MODE, "agent1ApiCallCount": int(provider.get("actualCalls") or 0), "productAgentProviderStatus": provider.get("providerStatus"), "productAgentProvider": provider, "taskMappingApiCallCount": 0, "totalAgentCallCount": int(budget_summary.get("totalAgentCalls") or 0), "totalAgentBudget": int(budget_summary.get("totalAgentBudget") or 8), "apiBudgetViolation": api_budget_violation, "agentBudgetLedger": budget_summary, "ragRetrievalCount": rag_retrieval_count, "ragRetrievalScope": "data_version_once", "averageJudgmentsPerSignal": round(len(raw_judgments) / len(signals), 2) if signals else 0, "productJudgmentPackageCount": len(packages), "identityGapCount": len(identity_gaps), "taskDecisionCount": len(decisions), "formalDecisionCount": formal_decision_count, "streamedTaskSnapshotCount": sum(1 for item in streamed if item.get("ok")), "streamedTaskPoolCount": task_pool_created, "byDecision": dict(by_decision), "taskGenerationRun": generation_run, "packages": packages[:50], "identityGaps": identity_gaps[:50], "decisions": decisions[:50], "streamed": streamed[:50], "rule": "V16.1: product judgments must come from real batched Agent JSON; provider failure creates no fake judgments or tasks."}


ensure_dual_agent_tables = base.ensure_dual_agent_tables
