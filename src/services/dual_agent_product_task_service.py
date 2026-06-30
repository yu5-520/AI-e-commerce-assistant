"""V14.9 dual-Agent product task pipeline.

Agent 1 creates metric-level product judgments only. The system then compresses
judgments into one product_judgment_package per product. Agent 2 consumes the
product package and creates at most one actionable SOP task per product.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.llm_provider_service import generate_json
from src.services.rag_context_station_service import build_rag_context_snapshot, latest_rag_context
from src.services.signal_pool_service import list_signals, update_signal_status
from src.services.task_generation_run_service import record_task_generation_run
from src.services.task_pool_station_service import enter_task_pool_from_snapshot
from src.services.task_snapshot_station_service import create_task_snapshot

DUAL_AGENT_PIPELINE_VERSION = "14.9"
FORMAL_DECISIONS = {"create_task_snapshot", "manager_review_required"}
SEVERITY_RANK = {"normal": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
MAX_TASKS_PER_RUN = 10
BLANK_VALUES = {None, "", "—", "未识别"}
CORE_METRICS = ["paymentAmount", "roi", "roas", "adSpend", "refundRate", "inventory", "conversionRate", "grossMargin", "clickRate"]


def now_iso() -> str:
    return datetime.now().isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}"


def _table_exists(conn: Any, table_name: str) -> bool:
    return bool(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone())


def _safe_load(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return loads(value)
    except Exception:
        return value


def ensure_dual_agent_tables() -> None:
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_product_judgments_v15 (
                judgment_id TEXT PRIMARY KEY,
                data_version TEXT,
                store_id TEXT,
                product_id TEXT,
                signal_id TEXT,
                metric_code TEXT,
                severity TEXT,
                decision_hint TEXT,
                confidence REAL DEFAULT 0,
                payload TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS product_judgment_packages_v15 (
                package_id TEXT PRIMARY KEY,
                data_version TEXT,
                store_id TEXT,
                product_id TEXT,
                judgment_count INTEGER DEFAULT 0,
                primary_risk TEXT,
                max_severity TEXT,
                overall_decision TEXT,
                task_candidate_allowed INTEGER DEFAULT 0,
                payload TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_generation_decisions_v15 (
                decision_id TEXT PRIMARY KEY,
                package_id TEXT,
                data_version TEXT,
                store_id TEXT,
                product_id TEXT,
                decision TEXT,
                task_title TEXT,
                priority TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
        """)
        ensure_columns(conn, "agent_product_judgments_v15", {"data_version": "TEXT", "store_id": "TEXT", "product_id": "TEXT", "signal_id": "TEXT", "metric_code": "TEXT", "severity": "TEXT", "decision_hint": "TEXT", "confidence": "REAL DEFAULT 0", "payload": "TEXT", "created_at": "TEXT"})
        ensure_columns(conn, "product_judgment_packages_v15", {"data_version": "TEXT", "store_id": "TEXT", "product_id": "TEXT", "judgment_count": "INTEGER DEFAULT 0", "primary_risk": "TEXT", "max_severity": "TEXT", "overall_decision": "TEXT", "task_candidate_allowed": "INTEGER DEFAULT 0", "payload": "TEXT", "created_at": "TEXT"})
        ensure_columns(conn, "task_generation_decisions_v15", {"package_id": "TEXT", "data_version": "TEXT", "store_id": "TEXT", "product_id": "TEXT", "decision": "TEXT", "task_title": "TEXT", "priority": "TEXT", "payload": "TEXT", "created_at": "TEXT"})
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_product_judgments_v15_product ON agent_product_judgments_v15(data_version, store_id, product_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_product_judgment_packages_v15_product ON product_judgment_packages_v15(data_version, store_id, product_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_generation_decisions_v15_package ON task_generation_decisions_v15(package_id, decision)")
        conn.commit()


def _metric_layer(bundle: Dict[str, Any]) -> Dict[str, Any]:
    value = bundle.get("metricLayer")
    return value if isinstance(value, dict) else {}


def _profile_layer(bundle: Dict[str, Any]) -> Dict[str, Any]:
    value = bundle.get("profileLayer")
    return value if isinstance(value, dict) else {}


def _product_key(bundle: Dict[str, Any]) -> Tuple[str, str]:
    profile = _profile_layer(bundle)
    store_id = str(bundle.get("storeId") or profile.get("storeId") or "GLOBAL")
    product_id = str(bundle.get("productId") or profile.get("productId") or bundle.get("entityId") or bundle.get("bundleId") or "PRODUCT")
    return store_id, product_id


def _known(value: Any) -> bool:
    return value not in BLANK_VALUES


def _score_signal(bundle: Dict[str, Any]) -> Dict[str, Any]:
    strength = str(bundle.get("signalStrength") or "normal")
    cross = bundle.get("crossValidation") if isinstance(bundle.get("crossValidation"), dict) else {}
    abnormal = int(cross.get("abnormalMetricCount") or 0)
    changed = int(cross.get("changedMetricCount") or 0)
    source_count = int(cross.get("sourceVersionCount") or cross.get("sourceDatasetCount") or 0)
    metric = _metric_layer(bundle)
    metric_code = bundle.get("metricCode") or bundle.get("primaryRisk") or "all_metrics"
    missing = [key for key in CORE_METRICS if key in metric and not _known(metric.get(key))]
    base = {"high": 0.76, "medium": 0.56, "low": 0.32, "normal": 0.18}.get(strength, 0.18)
    score = base + min(0.16, abnormal * 0.05) + min(0.08, changed * 0.02) + min(0.08, source_count * 0.015)
    critical_gap = any(key in missing for key in ["paymentAmount", "inventory", "refundRate"]) or {"roi", "roas"}.issubset(set(missing))
    if critical_gap:
        severity = "medium" if strength in {"normal", "low"} else "high"
        hint = "data_gap_candidate"
    elif strength == "high" or score >= 0.82:
        severity = "high"
        hint = "risk_candidate"
    elif strength == "medium" or (abnormal and score >= 0.62):
        severity = "medium"
        hint = "risk_candidate"
    elif strength == "low" or changed:
        severity = "low"
        hint = "observe_only"
    else:
        severity = "normal"
        hint = "observe_only"
    return {"metricCode": metric_code, "severity": severity, "decisionHint": hint, "confidence": round(max(0.35, min(0.92, score)), 4), "score": round(score, 4), "abnormal": abnormal, "changed": changed, "sourceCount": source_count, "missingFields": missing, "criticalGap": critical_gap}


def _agent1_analyze_signal(signal: Dict[str, Any], rag_context: Dict[str, Any]) -> Dict[str, Any]:
    store_id, product_id = _product_key(signal)
    scored = _score_signal(signal)
    fallback = {"metricCode": scored["metricCode"], "severity": scored["severity"], "decisionHint": scored["decisionHint"], "confidence": scored["confidence"], "finding": f"{product_id} 的 {scored['metricCode']} 处于 {scored['severity']} 判断层级。", "evidence": {"score": scored["score"], "abnormal": scored["abnormal"], "changed": scored["changed"], "sourceCount": scored["sourceCount"], "missingFields": scored["missingFields"]}}
    try:
        llm_result = generate_json(prompt_name="v149_agent1_product_analysis", payload={"fullProductBundle": signal, "ragContext": rag_context, "fallback": fallback, "hardRule": "Agent1只做指标级分析判断，不允许生成任务标题、SOP或入池动作。"}, expected_keys=["metricCode", "severity", "decisionHint", "confidence", "finding", "evidence"], agent_name="V14.9 Agent1 Product Analysis", schema_name="v149_agent1_product_analysis")
        output = llm_result.get("output") or {}
    except Exception as exc:
        llm_result = {"status": "fallback", "error": str(exc)}
        output = {}
    severity = str(output.get("severity") or fallback["severity"])
    if severity not in SEVERITY_RANK:
        severity = fallback["severity"]
    return {"version": DUAL_AGENT_PIPELINE_VERSION, "judgmentId": make_id("APJ"), "dataVersion": signal.get("dataVersion"), "storeId": store_id, "productId": product_id, "signalId": signal.get("signalId"), "bundleId": signal.get("bundleId"), "metricCode": output.get("metricCode") or fallback["metricCode"], "severity": severity, "decisionHint": output.get("decisionHint") or fallback["decisionHint"], "confidence": float(output.get("confidence") or fallback["confidence"]), "finding": output.get("finding") or fallback["finding"], "evidence": output.get("evidence") or fallback["evidence"], "signal": signal, "softScore": scored, "llm": {"provider": llm_result.get("provider"), "model": llm_result.get("model"), "status": llm_result.get("status"), "error": llm_result.get("error")}, "rule": "Agent1 output is judgment only, never a task."}


def _clear_version_rows(data_version: str | None) -> None:
    if not data_version:
        return
    with connect() as conn:
        for table in ["agent_product_judgments_v15", "product_judgment_packages_v15", "task_generation_decisions_v15"]:
            if _table_exists(conn, table):
                conn.execute(f"DELETE FROM {table} WHERE data_version = ?", (data_version,))
        conn.commit()


def _save_raw_judgments(judgments: List[Dict[str, Any]]) -> None:
    ensure_dual_agent_tables()
    now = now_iso()
    with connect() as conn:
        for item in judgments:
            conn.execute("""
                INSERT OR REPLACE INTO agent_product_judgments_v15 (judgment_id, data_version, store_id, product_id, signal_id, metric_code, severity, decision_hint, confidence, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item.get("judgmentId"), item.get("dataVersion"), item.get("storeId"), item.get("productId"), item.get("signalId"), item.get("metricCode"), item.get("severity"), item.get("decisionHint"), float(item.get("confidence") or 0), dumps(item), now))
        conn.commit()


def _load_raw_judgments(data_version: str | None) -> List[Dict[str, Any]]:
    ensure_dual_agent_tables()
    with connect() as conn:
        if data_version:
            rows = conn.execute("SELECT payload FROM agent_product_judgments_v15 WHERE data_version = ? ORDER BY created_at", (data_version,)).fetchall()
        else:
            rows = conn.execute("SELECT payload FROM agent_product_judgments_v15 ORDER BY created_at DESC").fetchall()
    return [_safe_load(row["payload"]) for row in rows]


def _severity_max(items: Iterable[Dict[str, Any]]) -> str:
    max_item = "normal"
    for item in items:
        sev = str(item.get("severity") or "normal")
        if SEVERITY_RANK.get(sev, 0) > SEVERITY_RANK.get(max_item, 0):
            max_item = sev
    return max_item


def _package_product_judgments(data_version: str | None) -> List[Dict[str, Any]]:
    raw = _load_raw_judgments(data_version)
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for item in raw:
        grouped[(str(item.get("storeId") or "GLOBAL"), str(item.get("productId") or "PRODUCT"))].append(item)
    packages: List[Dict[str, Any]] = []
    for (store_id, product_id), items in grouped.items():
        max_severity = _severity_max(items)
        risk_counts = Counter(str(item.get("metricCode") or "all_metrics") for item in items if SEVERITY_RANK.get(str(item.get("severity") or "normal"), 0) >= 1)
        primary_risk = risk_counts.most_common(1)[0][0] if risk_counts else "all_metrics"
        secondary = [risk for risk, _ in risk_counts.most_common(5) if risk != primary_risk]
        confidence = round(max([float(item.get("confidence") or 0) for item in items], default=0.45), 4)
        has_data_gap = any((item.get("softScore") or {}).get("criticalGap") for item in items)
        allowed = SEVERITY_RANK.get(max_severity, 0) >= 2 or has_data_gap
        overall = "task_candidate" if allowed else "observe_only"
        evidence_pack = [{"metricCode": item.get("metricCode"), "severity": item.get("severity"), "finding": item.get("finding"), "evidence": item.get("evidence")} for item in sorted(items, key=lambda x: SEVERITY_RANK.get(str(x.get("severity") or "normal"), 0), reverse=True)[:8]]
        package = {"version": DUAL_AGENT_PIPELINE_VERSION, "packageId": make_id("PJP"), "dataVersion": data_version or (items[0].get("dataVersion") if items else None), "storeId": store_id, "productId": product_id, "judgmentCount": len(items), "primaryRisk": primary_risk, "secondaryRisks": secondary, "maxSeverity": max_severity, "overallDecision": overall, "taskCandidateAllowed": bool(allowed), "confidence": confidence, "summary": f"{product_id} 汇总 {len(items)} 条判断，主风险为 {primary_risk}，最高等级 {max_severity}。", "evidencePack": evidence_pack, "rawJudgmentIds": [item.get("judgmentId") for item in items], "rule": "System compression: metric-level judgments are merged into one product-level package."}
        packages.append(package)
    _save_packages(packages)
    return packages


def _save_packages(packages: List[Dict[str, Any]]) -> None:
    ensure_dual_agent_tables()
    now = now_iso()
    with connect() as conn:
        for item in packages:
            conn.execute("""
                INSERT OR REPLACE INTO product_judgment_packages_v15 (package_id, data_version, store_id, product_id, judgment_count, primary_risk, max_severity, overall_decision, task_candidate_allowed, payload, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (item.get("packageId"), item.get("dataVersion"), item.get("storeId"), item.get("productId"), int(item.get("judgmentCount") or 0), item.get("primaryRisk"), item.get("maxSeverity"), item.get("overallDecision"), 1 if item.get("taskCandidateAllowed") else 0, dumps(item), now))
        conn.commit()


def _priority(max_severity: str) -> str:
    return "高" if max_severity in {"high", "critical"} else "中" if max_severity == "medium" else "低"


def _agent2_task_decision(package: Dict[str, Any], rank_index: int) -> Dict[str, Any]:
    product_id = package.get("productId") or "PRODUCT"
    primary = package.get("primaryRisk") or "经营状态"
    max_sev = package.get("maxSeverity") or "normal"
    allowed = bool(package.get("taskCandidateAllowed")) and rank_index < MAX_TASKS_PER_RUN
    if not allowed:
        decision = "no_task"
        reason = "商品判断包未达到任务准入，沉淀为观察记录。" if rank_index < MAX_TASKS_PER_RUN else "本轮任务已达到单轮上限，剩余商品进入观察队列。"
        task_plan = {"title": f"商品观察记录｜{product_id}｜{primary}", "taskType": "observe_only", "priority": "低", "deadline": "后台观察", "reason": reason, "sopSteps": [], "evidenceRequirements": []}
    else:
        decision = "manager_review_required" if max_sev in {"high", "critical"} else "create_task_snapshot"
        priority = _priority(max_sev)
        deadline = "6小时内" if priority == "高" else "24小时内"
        task_title = f"商品经营复核｜{product_id}｜{primary}联动异常"
        reason = f"商品判断包汇总 {package.get('judgmentCount')} 条指标判断，主风险 {primary}，最高等级 {max_sev}。"
        task_plan = {"title": task_title, "subtitle": "商品判断包生成任务", "entityType": "product", "entityId": product_id, "productId": product_id, "storeId": package.get("storeId"), "taskType": "product_operation_review", "actionType": "product_package_sop", "priority": priority, "riskLevel": "high" if priority == "高" else "medium", "deadline": deadline, "riskDomain": primary, "operationBudget": {"taskType": "product_operation_review", "riskLevel": "high" if priority == "高" else "medium", "budgetUpperBound": 0, "operatorBudgetApplies": False, "requiresApproval": decision == "manager_review_required"}, "sopSteps": [f"{deadline}核查 {product_id} 的 {primary} 相关后台数据，先确认本轮商品判断包中的主风险与证据。", "合并核查退款、库存、转化、投放和毛利中与主风险相关的截图，避免按单指标重复处理。", "输出一个商品级处理结论：继续观察、调整页面/投放/库存、或提交主管复核。", "提交处理截图、数据口径和下一次复盘指标。"], "evidenceRequirements": ["商品判断包截图", "主风险后台数据截图", "相关指标联动截图", "处理结论与复盘指标"], "reviewMetrics": ["支付金额", "ROAS/ROI", "点击率", "转化率", "退款率", "毛利率", "库存"], "needManagerReview": decision == "manager_review_required", "reason": reason}
    return {"version": DUAL_AGENT_PIPELINE_VERSION, "decisionId": make_id("TGD"), "packageId": package.get("packageId"), "dataVersion": package.get("dataVersion"), "storeId": package.get("storeId"), "productId": product_id, "decision": decision, "taskTitle": task_plan.get("title"), "priority": task_plan.get("priority"), "reason": task_plan.get("reason"), "taskPlan": task_plan, "productJudgmentPackage": package, "rule": "Agent2 consumes product_judgment_package and may create at most one product-level task."}


def _save_decision(decision: Dict[str, Any]) -> None:
    ensure_dual_agent_tables()
    with connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO task_generation_decisions_v15 (decision_id, package_id, data_version, store_id, product_id, decision, task_title, priority, payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (decision.get("decisionId"), decision.get("packageId"), decision.get("dataVersion"), decision.get("storeId"), decision.get("productId"), decision.get("decision"), decision.get("taskTitle"), decision.get("priority"), dumps(decision), now_iso()))
        conn.commit()


def _stream_decision_to_task_pool(decision: Dict[str, Any], created_by: str | None = None) -> Dict[str, Any]:
    if decision.get("decision") not in FORMAL_DECISIONS:
        return {"ok": False, "skipped": True, "reason": "decision_not_formal_task", "decisionId": decision.get("decisionId")}
    plan = decision.get("taskPlan") or {}
    package = decision.get("productJudgmentPackage") or {}
    snapshot = create_task_snapshot({"dataVersion": decision.get("dataVersion"), "decision": decision.get("decision"), "confidence": package.get("confidence") or 0.72, "entityType": "product", "entityId": decision.get("productId"), "productId": decision.get("productId"), "storeId": decision.get("storeId"), "signalRef": decision.get("packageId"), "bundleRef": decision.get("packageId"), "ragContext": {"source": "product_judgment_package", "version": DUAL_AGENT_PIPELINE_VERSION}, "agentJudgment": {"decision": decision.get("decision"), "confidence": package.get("confidence") or 0.72, "reason": decision.get("reason"), "status": "task_generated_from_product_judgment_package"}, "taskPlan": plan, "operationBudget": plan.get("operationBudget") or {}, "evidenceRequirements": plan.get("evidenceRequirements") or [], "systemFacts": {"productJudgmentPackage": package, "taskGenerationDecision": decision}, "source": "v149_dual_agent_task_generation"}, created_by=created_by)
    pool = enter_task_pool_from_snapshot(str(snapshot.get("taskSnapshotId")), created_by=created_by, force=False)
    return {"ok": True, "snapshot": snapshot, "poolResult": pool, "createdTaskCount": int((pool or {}).get("createdTaskCount") or 0)}


def run_dual_agent_product_task_pipeline(data_version: str | None = None, *, rag_context_ref: str | None = None, max_signals: int = 160, created_by: str | None = None) -> Dict[str, Any]:
    ensure_dual_agent_tables()
    _clear_version_rows(data_version)
    rag_context = latest_rag_context(data_version) or build_rag_context_snapshot(data_version=data_version)
    signals = (list_signals(data_version=data_version, status="pending_rag_agent", limit=max_signals).get("signals") or [])[:max_signals]
    raw_judgments = [_agent1_analyze_signal(signal, rag_context) for signal in signals]
    _save_raw_judgments(raw_judgments)
    for signal in signals:
        update_signal_status(signal.get("signalId"), "product_analysis_judged", {"version": DUAL_AGENT_PIPELINE_VERSION})
    packages = _package_product_judgments(data_version)
    sorted_packages = sorted(packages, key=lambda item: (SEVERITY_RANK.get(str(item.get("maxSeverity") or "normal"), 0), float(item.get("confidence") or 0), int(item.get("judgmentCount") or 0)), reverse=True)
    decisions: List[Dict[str, Any]] = []
    streamed: List[Dict[str, Any]] = []
    candidate_index = 0
    for package in sorted_packages:
        if package.get("taskCandidateAllowed"):
            decision = _agent2_task_decision(package, candidate_index)
            candidate_index += 1
        else:
            decision = _agent2_task_decision(package, MAX_TASKS_PER_RUN + 1)
        _save_decision(decision)
        decisions.append(decision)
        streamed.append(_stream_decision_to_task_pool(decision, created_by=created_by))
    by_decision = Counter(str(item.get("decision")) for item in decisions)
    task_pool_created = sum(int(item.get("createdTaskCount") or 0) for item in streamed)
    formal_decision_count = int(by_decision.get("create_task_snapshot", 0) or 0) + int(by_decision.get("manager_review_required", 0) or 0)
    generation_run = record_task_generation_run(data_version=data_version, input_bundle_count=len(signals), agent_judgment_count=len(raw_judgments), product_judgment_package_count=len(packages), task_decision_count=len(decisions), by_decision=dict(by_decision), streamed_task_snapshot_count=sum(1 for item in streamed if item.get("ok")), task_pool_created_count=task_pool_created, skipped_formal_count=sum(1 for item in streamed if item.get("skipped")), zero_task_reasons=[item.get("reason") for item in decisions if item.get("decision") == "no_task"][:20], source="v149_dual_agent_product_task_pipeline")
    try:
        from src.services.frontend_read_model_service import refresh_dashboard_view, refresh_task_views
        if task_pool_created:
            refresh_task_views()
        else:
            refresh_dashboard_view()
    except Exception:
        pass
    ref = f"dual_agent_product_task:{data_version or 'latest'}"
    return {"version": DUAL_AGENT_PIPELINE_VERSION, "mode": "v149_dual_agent_product_judgment_package_task_pipeline", "dataVersion": data_version, "outputRef": ref, "agentJudgmentRef": ref, "ragContextRef": rag_context_ref or rag_context.get("ragContextRef") or rag_context.get("outputRef"), "signalCount": len(signals), "judgmentCount": len(raw_judgments), "rawJudgmentCount": len(raw_judgments), "productJudgmentPackageCount": len(packages), "taskDecisionCount": len(decisions), "formalDecisionCount": formal_decision_count, "streamedTaskSnapshotCount": sum(1 for item in streamed if item.get("ok")), "streamedTaskPoolCount": task_pool_created, "byDecision": dict(by_decision), "taskGenerationRun": generation_run, "packages": packages[:50], "decisions": decisions[:50], "streamed": streamed[:50], "rule": "V14.9: Agent1 judges metrics, system compresses by product, Agent2 generates product-level SOP tasks, task pool admits only product-level decisions."}
