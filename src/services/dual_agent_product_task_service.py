"""V15 dual-Agent product task pipeline with full-chain Agent budget ledger.

Agent1 expands one resolved fullProductBundle into multiple metric-level
judgments without one-judgment-one-LLM calls. The system compresses those local
judgments into one product_judgment_package per real product. Agent2 maps only
70%+ package candidates into permission-aware product-level tasks, and both
Agent stages are registered in the V15 Agent Budget Ledger.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.agent_budget_ledger_service import get_or_create_agent_budget_ledger, read_agent_budget_summary, register_agent_event
from src.services.rag_context_station_service import build_rag_context_snapshot, latest_rag_context
from src.services.signal_pool_service import list_signals, update_signal_status
from src.services.task_generation_run_service import record_task_generation_run
from src.services.task_pool_station_service import enter_task_pool_from_snapshot
from src.services.task_snapshot_station_service import create_task_snapshot

DUAL_AGENT_PIPELINE_VERSION = "15.0"
FORMAL_DECISIONS = {"create_task_snapshot", "manager_review_required"}
SEVERITY_RANK = {"normal": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
MAX_TASKS_PER_RUN = 8
MAX_METRIC_JUDGMENTS_PER_SIGNAL = 8
PACKAGE_CONFIDENCE_THRESHOLD = 0.70
AGENT1_API_MODE = "local_metric_expansion_no_per_metric_llm"
AGENT1_API_CALLS_PER_BUNDLE = 0
TASK_MAPPING_API_CALLS_PER_RUN = 0
RAG_RETRIEVAL_SCOPE = "data_version_once"
BLANK_VALUES = {None, "", "—", "未识别", "UNKNOWN", "PRODUCT"}
CORE_METRICS = ["paymentAmount", "roi", "roas", "adSpend", "refundRate", "inventory", "conversionRate", "grossMargin", "clickRate"]
HIGH_IMPACT_METRICS = {"roi", "roas", "refundRate", "inventory", "conversionRate", "grossMargin", "paymentAmount"}
ENGINEERING_ID_PREFIXES = ("PSIG-", "TS-", "LINK-", "SPU-", "SKU-", "STORE-", "AJ-", "PJP-", "TGD-")
PRODUCT_ID_PATTERN = re.compile(r"^(P\d+|PROD[-_A-Z0-9]+|PRODUCT[-_A-Z0-9]+)$", re.IGNORECASE)


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


def _candidate_text(value: Any) -> str | None:
    if value in BLANK_VALUES:
        return None
    text = str(value).strip()
    if not text or text in BLANK_VALUES:
        return None
    upper = text.upper()
    if upper.startswith(ENGINEERING_ID_PREFIXES):
        return None
    if ":" in text or "|" in text:
        return None
    return text


def _strict_product_id(bundle: Dict[str, Any]) -> str | None:
    profile = _profile_layer(bundle)
    product_obj = bundle.get("product") if isinstance(bundle.get("product"), dict) else {}
    candidates = [bundle.get("productId"), bundle.get("product_id"), bundle.get("productCode"), bundle.get("product_code"), profile.get("productId"), profile.get("product_id"), profile.get("productCode"), profile.get("product_code"), product_obj.get("productId"), product_obj.get("id")]
    for value in candidates:
        text = _candidate_text(value)
        if text and (PRODUCT_ID_PATTERN.match(text) or str(value) == str(bundle.get("productId") or profile.get("productId"))):
            return text
    return None


def _store_id(bundle: Dict[str, Any]) -> str:
    profile = _profile_layer(bundle)
    return str(bundle.get("storeId") or bundle.get("store_id") or profile.get("storeId") or profile.get("store_id") or "GLOBAL")


def _known(value: Any) -> bool:
    return value not in BLANK_VALUES


def _signal_primary_metric(bundle: Dict[str, Any]) -> str:
    return str(bundle.get("metricCode") or bundle.get("primaryRisk") or "all_metrics")


def _extract_metric_codes(bundle: Dict[str, Any]) -> List[str]:
    metric = _metric_layer(bundle)
    primary = _signal_primary_metric(bundle)
    ordered: List[str] = []
    if primary and primary != "all_metrics":
        ordered.append(primary)
    for key in CORE_METRICS:
        if key in metric and _known(metric.get(key)):
            ordered.append(key)
    for key in CORE_METRICS:
        if key in metric and key not in ordered:
            ordered.append(key)
    if not ordered:
        ordered.append(primary or "all_metrics")
    seen: set[str] = set()
    result: List[str] = []
    for key in ordered:
        if not key or key in seen:
            continue
        seen.add(str(key))
        result.append(str(key))
        if len(result) >= MAX_METRIC_JUDGMENTS_PER_SIGNAL:
            break
    return result


def _score_signal(bundle: Dict[str, Any]) -> Dict[str, Any]:
    strength = str(bundle.get("signalStrength") or "normal")
    cross = bundle.get("crossValidation") if isinstance(bundle.get("crossValidation"), dict) else {}
    abnormal = int(cross.get("abnormalMetricCount") or 0)
    changed = int(cross.get("changedMetricCount") or 0)
    source_count = int(cross.get("sourceVersionCount") or cross.get("sourceDatasetCount") or 0)
    metric = _metric_layer(bundle)
    missing = [key for key in CORE_METRICS if key in metric and not _known(metric.get(key))]
    base = {"high": 0.76, "medium": 0.56, "low": 0.32, "normal": 0.18}.get(strength, 0.18)
    score = base + min(0.16, abnormal * 0.05) + min(0.08, changed * 0.02) + min(0.08, source_count * 0.015)
    critical_gap = any(key in missing for key in ["paymentAmount", "inventory", "refundRate"]) or {"roi", "roas"}.issubset(set(missing))
    return {"strength": strength, "score": round(max(0.35, min(0.92, score)), 4), "abnormal": abnormal, "changed": changed, "sourceCount": source_count, "missingFields": missing, "criticalGap": critical_gap}


def _score_metric(bundle: Dict[str, Any], metric_code: str, signal_score: Dict[str, Any]) -> Dict[str, Any]:
    metric = _metric_layer(bundle)
    primary = _signal_primary_metric(bundle)
    strength = str(signal_score.get("strength") or "normal")
    base_score = float(signal_score.get("score") or 0.45)
    value = metric.get(metric_code)
    is_primary = metric_code == primary or primary == "all_metrics"
    is_high_impact = metric_code in HIGH_IMPACT_METRICS
    missing = not _known(value) and metric_code in CORE_METRICS
    if missing and metric_code in {"paymentAmount", "inventory", "refundRate", "roi", "roas"}:
        severity, hint, score = "medium", "data_gap_candidate", max(base_score, 0.62)
    elif is_primary and strength == "high":
        severity, hint, score = "high", "risk_candidate", max(base_score, 0.82)
    elif is_primary and strength == "medium":
        severity, hint, score = "medium", "risk_candidate", max(base_score, 0.66)
    elif is_high_impact and strength == "high":
        severity, hint, score = "medium", "related_risk", max(base_score - 0.08, 0.68)
    elif is_high_impact and (strength == "medium" or int(signal_score.get("changed") or 0) > 0):
        severity, hint, score = "low", "related_observation", max(base_score - 0.12, 0.52)
    elif _known(value):
        severity, hint, score = ("low" if int(signal_score.get("changed") or 0) > 0 else "normal"), "metric_observation", max(base_score - 0.18, 0.42)
    else:
        severity, hint, score = "normal", "metric_observation", max(base_score - 0.2, 0.35)
    return {"metricCode": metric_code, "severity": severity, "decisionHint": hint, "confidence": round(max(0.35, min(0.92, score)), 4), "metricValue": value, "isPrimaryMetric": is_primary, "isHighImpactMetric": is_high_impact, "missing": missing, **signal_score}


def _agent1_analyze_signal(signal: Dict[str, Any], rag_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    store_id = _store_id(signal)
    product_id = _strict_product_id(signal)
    product_key = product_id or "UNRESOLVED_PRODUCT"
    signal_score = _score_signal(signal)
    if not product_id:
        scored = {**signal_score, "metricCode": _signal_primary_metric(signal), "severity": "low", "decisionHint": "identity_gap", "confidence": 0.45, "metricValue": None, "missing": True}
        return [{"version": DUAL_AGENT_PIPELINE_VERSION, "judgmentId": make_id("APJ"), "dataVersion": signal.get("dataVersion"), "storeId": store_id, "productId": product_key, "productIdentityResolved": False, "signalId": signal.get("signalId"), "bundleId": signal.get("bundleId"), "metricCode": scored["metricCode"], "severity": "low", "decisionHint": "identity_gap", "confidence": scored["confidence"], "finding": f"{product_key} 缺少真实商品ID，不能进入商品判断包整合。", "evidence": {"missingProductId": True, "sourceSignalId": signal.get("signalId"), "sourceBundleId": signal.get("bundleId")}, "signal": signal, "softScore": scored, "metricGranularity": "identity_gap", "agent1ApiCallCount": 0, "ragRetrievalScope": RAG_RETRIEVAL_SCOPE, "rule": "Agent1 identity gap stays in judgment layer and never enters Agent2."}]
    judgments: List[Dict[str, Any]] = []
    for metric_code in _extract_metric_codes(signal):
        scored = _score_metric(signal, metric_code, signal_score)
        severity = str(scored.get("severity") or "normal")
        if severity not in SEVERITY_RANK:
            severity = "normal"
        value = scored.get("metricValue")
        value_text = "未识别" if value in BLANK_VALUES else value
        finding = f"{product_key} 的 {metric_code} 指标判断为 {severity}；当前值 {value_text}。"
        if scored.get("isPrimaryMetric"):
            finding = f"{product_key} 主风险指标 {metric_code} 判断为 {severity}；当前值 {value_text}。"
        judgments.append({"version": DUAL_AGENT_PIPELINE_VERSION, "judgmentId": make_id("APJ"), "dataVersion": signal.get("dataVersion"), "storeId": store_id, "productId": product_key, "productIdentityResolved": True, "signalId": signal.get("signalId"), "bundleId": signal.get("bundleId"), "metricCode": metric_code, "severity": severity, "decisionHint": scored.get("decisionHint"), "confidence": float(scored.get("confidence") or 0), "finding": finding, "evidence": {"metricValue": value, "isPrimaryMetric": scored.get("isPrimaryMetric"), "isHighImpactMetric": scored.get("isHighImpactMetric"), "signalStrength": scored.get("strength"), "abnormal": scored.get("abnormal"), "changed": scored.get("changed"), "sourceCount": scored.get("sourceCount"), "missingFields": scored.get("missingFields")}, "signal": signal, "softScore": scored, "metricGranularity": "metric_level", "agent1ApiCallCount": 0, "ragRetrievalScope": RAG_RETRIEVAL_SCOPE, "rule": "V15 Agent1 metric judgments are local records; no per-metric LLM/API call is allowed."})
    return judgments


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


def _system_package_confidence(items: List[Dict[str, Any]]) -> float:
    if not items:
        return 0.0
    risk_candidates = [item for item in items if item.get("decisionHint") in {"risk_candidate", "related_risk", "data_gap_candidate"}]
    max_conf = max([float(item.get("confidence") or 0) for item in items], default=0.0)
    avg_conf = sum(float(item.get("confidence") or 0) for item in items) / len(items)
    multi_metric_bonus = min(0.12, max(0, len({item.get("metricCode") for item in items}) - 1) * 0.03)
    risk_bonus = min(0.16, len(risk_candidates) * 0.04)
    return round(min(0.98, (max_conf * 0.45) + (avg_conf * 0.35) + multi_metric_bonus + risk_bonus), 4)


def _package_candidate_allowed(*, package_confidence: float, max_severity: str, has_data_gap: bool) -> bool:
    if has_data_gap and package_confidence >= 0.62:
        return True
    if SEVERITY_RANK.get(max_severity, 0) >= 3 and package_confidence >= 0.66:
        return True
    return package_confidence >= PACKAGE_CONFIDENCE_THRESHOLD


def _package_product_judgments(data_version: str | None) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    raw = _load_raw_judgments(data_version)
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    identity_gaps: List[Dict[str, Any]] = []
    for item in raw:
        if not item.get("productIdentityResolved") or not _candidate_text(item.get("productId")):
            identity_gaps.append(item)
            continue
        grouped[(str(item.get("storeId") or "GLOBAL"), str(item.get("productId")))].append(item)
    packages: List[Dict[str, Any]] = []
    for (store_id, product_id), items in grouped.items():
        max_severity = _severity_max(items)
        risk_items = [item for item in items if SEVERITY_RANK.get(str(item.get("severity") or "normal"), 0) >= 1]
        risk_counts = Counter(str(item.get("metricCode") or "all_metrics") for item in risk_items)
        primary_risk = risk_counts.most_common(1)[0][0] if risk_counts else "all_metrics"
        secondary = [risk for risk, _ in risk_counts.most_common(5) if risk != primary_risk]
        package_confidence = _system_package_confidence(items)
        has_data_gap = any((item.get("softScore") or {}).get("criticalGap") for item in items)
        risk_candidate_count = sum(1 for item in items if item.get("decisionHint") in {"risk_candidate", "related_risk", "data_gap_candidate"})
        allowed = _package_candidate_allowed(package_confidence=package_confidence, max_severity=max_severity, has_data_gap=has_data_gap)
        overall = "allow_task_mapping" if allowed else "observe_only"
        evidence_pack = [{"metricCode": item.get("metricCode"), "severity": item.get("severity"), "confidence": item.get("confidence"), "finding": item.get("finding"), "evidence": item.get("evidence")} for item in sorted(items, key=lambda x: SEVERITY_RANK.get(str(x.get("severity") or "normal"), 0), reverse=True)[:8]]
        packages.append({"version": DUAL_AGENT_PIPELINE_VERSION, "packageId": make_id("PJP"), "dataVersion": data_version or (items[0].get("dataVersion") if items else None), "storeId": store_id, "productId": product_id, "judgmentCount": len(items), "primaryRisk": primary_risk, "secondaryRisks": secondary, "maxSeverity": max_severity, "overallDecision": overall, "taskCandidateAllowed": bool(allowed), "confidence": package_confidence, "packageConfidence": package_confidence, "packageConfidenceThreshold": PACKAGE_CONFIDENCE_THRESHOLD, "riskCandidateCount": risk_candidate_count, "metricJudgmentCount": len(items), "summary": f"{product_id} 汇总 {len(items)} 条指标判断，判断包置信值 {package_confidence}，主风险为 {primary_risk}。", "evidencePack": evidence_pack, "rawJudgmentIds": [item.get("judgmentId") for item in items], "identityStatus": "resolved", "rule": "V15 system compression: Agent judgments are merged by real product, and only 70%+ package confidence enters task mapping."})
    _save_packages(packages)
    return packages, identity_gaps


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


def _priority(max_severity: str, package_confidence: float) -> str:
    if max_severity in {"high", "critical"} or package_confidence >= 0.86:
        return "高"
    return "中" if package_confidence >= PACKAGE_CONFIDENCE_THRESHOLD else "低"


def _agent2_task_decision(package: Dict[str, Any], rank_index: int) -> Dict[str, Any]:
    product_id = package.get("productId") or "PRODUCT"
    primary = package.get("primaryRisk") or "经营状态"
    max_sev = package.get("maxSeverity") or "normal"
    package_confidence = float(package.get("packageConfidence") or package.get("confidence") or 0)
    allowed = bool(package.get("taskCandidateAllowed")) and package_confidence >= PACKAGE_CONFIDENCE_THRESHOLD and rank_index < MAX_TASKS_PER_RUN
    if not allowed:
        decision = "no_task"
        reason = "商品判断包未达到 70% 任务映射准入，沉淀为观察记录。" if rank_index < MAX_TASKS_PER_RUN else "本轮任务已达到单轮上限，剩余商品进入观察队列。"
        task_plan = {"title": f"商品观察记录｜{product_id}｜{primary}", "taskType": "observe_only", "priority": "低", "deadline": "后台观察", "reason": reason, "sopSteps": [], "evidenceRequirements": []}
    else:
        decision = "manager_review_required" if max_sev in {"high", "critical"} else "create_task_snapshot"
        priority = _priority(max_sev, package_confidence)
        deadline = "6小时内" if priority == "高" else "24小时内"
        task_plan = {"title": f"商品经营复核｜{product_id}｜{primary}联动异常", "subtitle": "权限约束任务映射", "entityType": "product", "entityId": product_id, "productId": product_id, "storeId": package.get("storeId"), "taskType": "product_operation_review", "actionType": "permission_aware_product_package_sop", "priority": priority, "riskLevel": "high" if priority == "高" else "medium", "deadline": deadline, "riskDomain": primary, "operationBudget": {"taskType": "product_operation_review", "riskLevel": "high" if priority == "高" else "medium", "budgetUpperBound": 0, "operatorBudgetApplies": False, "requiresApproval": decision == "manager_review_required"}, "sopSteps": [f"{deadline}核查 {product_id} 的 {primary} 相关后台数据，先确认本轮商品判断包中的主风险与证据。", "按账号权限整理退款、库存、转化、投放和毛利中与主风险相关的截图；运营不得执行超权限预算或下架动作。", "输出一个商品级处理结论：继续观察、调整页面/投放建议、库存建议、或提交总管复核。", "提交处理截图、数据口径、权限边界和下一次复盘指标。"], "evidenceRequirements": ["商品判断包截图", "主风险后台数据截图", "相关指标联动截图", "权限边界说明", "处理结论与复盘指标"], "reviewMetrics": ["支付金额", "ROAS/ROI", "点击率", "转化率", "退款率", "毛利率", "库存"], "needManagerReview": decision == "manager_review_required", "reason": f"商品判断包汇总 {package.get('judgmentCount')} 条指标判断，置信值 {package_confidence}，主风险 {primary}。"}
    return {"version": DUAL_AGENT_PIPELINE_VERSION, "decisionId": make_id("TGD"), "packageId": package.get("packageId"), "dataVersion": package.get("dataVersion"), "storeId": package.get("storeId"), "productId": product_id, "decision": decision, "taskTitle": task_plan.get("title"), "priority": task_plan.get("priority"), "reason": task_plan.get("reason"), "taskPlan": task_plan, "productJudgmentPackage": package, "rule": "V15 task mapping consumes only 70%+ product_judgment_package rows and applies permission-aware SOP templates."}


def _save_decision(decision: Dict[str, Any]) -> None:
    ensure_dual_agent_tables()
    with connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO task_generation_decisions_v15 (decision_id, package_id, data_version, store_id, product_id, decision, task_title, priority, payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (decision.get("decisionId"), decision.get("packageId"), decision.get("dataVersion"), decision.get("storeId"), decision.get("productId"), decision.get("decision"), decision.get("taskTitle"), decision.get("priority"), dumps(decision), now_iso()))
        conn.commit()


def _existing_product_pool_task(data_version: str | None, store_id: str | None, product_id: str | None) -> Dict[str, Any] | None:
    if not product_id:
        return None
    with connect() as conn:
        if not _table_exists(conn, "task_pool_entries"):
            return None
        rows = conn.execute("SELECT payload FROM task_pool_entries WHERE data_version = ? ORDER BY created_at DESC", (data_version,)).fetchall() if data_version else conn.execute("SELECT payload FROM task_pool_entries ORDER BY created_at DESC").fetchall()
    for row in rows:
        payload = _safe_load(row["payload"])
        task = payload.get("task") if isinstance(payload, dict) else {}
        snapshot = payload.get("snapshot") if isinstance(payload, dict) else {}
        plan = snapshot.get("taskPlan") if isinstance(snapshot, dict) else {}
        task_product = task.get("productId") or plan.get("productId") or snapshot.get("productId")
        task_store = (task.get("storeIds") or [None])[0] if isinstance(task.get("storeIds"), list) else plan.get("storeId") or snapshot.get("storeId")
        if str(task_product) == str(product_id) and (not store_id or not task_store or str(task_store) == str(store_id)):
            return payload
    return None


def _stream_decision_to_task_pool(decision: Dict[str, Any], created_by: str | None = None) -> Dict[str, Any]:
    if decision.get("decision") not in FORMAL_DECISIONS:
        return {"ok": False, "skipped": True, "reason": "decision_not_formal_task", "decisionId": decision.get("decisionId")}
    if _existing_product_pool_task(decision.get("dataVersion"), decision.get("storeId"), decision.get("productId")):
        return {"ok": False, "skipped": True, "reason": "same_product_task_already_in_pool", "decisionId": decision.get("decisionId"), "createdTaskCount": 0}
    plan = decision.get("taskPlan") or {}
    package = decision.get("productJudgmentPackage") or {}
    snapshot = create_task_snapshot({"dataVersion": decision.get("dataVersion"), "decision": decision.get("decision"), "confidence": package.get("packageConfidence") or package.get("confidence") or 0.72, "entityType": "product", "entityId": decision.get("productId"), "productId": decision.get("productId"), "storeId": decision.get("storeId"), "signalRef": decision.get("packageId"), "bundleRef": decision.get("packageId"), "ragContext": {"source": "product_judgment_package", "version": DUAL_AGENT_PIPELINE_VERSION}, "agentJudgment": {"decision": decision.get("decision"), "confidence": package.get("packageConfidence") or package.get("confidence") or 0.72, "reason": decision.get("reason"), "status": "task_generated_from_product_judgment_package"}, "taskPlan": plan, "operationBudget": plan.get("operationBudget") or {}, "evidenceRequirements": plan.get("evidenceRequirements") or [], "systemFacts": {"productJudgmentPackage": package, "taskGenerationDecision": decision}, "source": "v15_permission_aware_task_mapping"}, created_by=created_by)
    pool = enter_task_pool_from_snapshot(str(snapshot.get("taskSnapshotId")), created_by=created_by, force=False)
    return {"ok": True, "snapshot": snapshot, "poolResult": pool, "createdTaskCount": int((pool or {}).get("createdTaskCount") or 0)}


def _latest_or_build_rag_context(data_version: str | None) -> tuple[Dict[str, Any], int]:
    latest = latest_rag_context(data_version)
    if latest:
        return latest, 0
    return build_rag_context_snapshot(data_version=data_version), 1


def run_dual_agent_product_task_pipeline(data_version: str | None = None, *, rag_context_ref: str | None = None, max_signals: int = 160, created_by: str | None = None) -> Dict[str, Any]:
    ensure_dual_agent_tables()
    ledger = get_or_create_agent_budget_ledger(data_version=data_version, source="v15_product_task_pipeline")
    _clear_version_rows(data_version)
    rag_context, rag_retrieval_count = _latest_or_build_rag_context(data_version)
    signals = (list_signals(data_version=data_version, status="pending_rag_agent", limit=max_signals).get("signals") or [])[:max_signals]
    agent1_api_call_count = len(signals) * AGENT1_API_CALLS_PER_BUNDLE
    register_agent_event(ledger_id=ledger["ledgerId"], data_version=data_version, stage="product_judgment_agent", call_type="local_metric_expansion", requested_calls=1 if signals else 0, actual_calls=agent1_api_call_count, fallback_used=True, rag_retrievals=rag_retrieval_count, reason="商品全量包批量判断；指标判断本地展开，不按判断调用API。", payload={"signalCount": len(signals), "apiMode": AGENT1_API_MODE})
    raw_judgments: List[Dict[str, Any]] = []
    for signal in signals:
        raw_judgments.extend(_agent1_analyze_signal(signal, rag_context))
    _save_raw_judgments(raw_judgments)
    for signal in signals:
        update_signal_status(signal.get("signalId"), "product_analysis_judged", {"version": DUAL_AGENT_PIPELINE_VERSION, "metricJudgmentMode": "expanded", "agent1ApiMode": AGENT1_API_MODE, "agent1ApiCallsPerBundle": AGENT1_API_CALLS_PER_BUNDLE})
    packages, identity_gaps = _package_product_judgments(data_version)
    sorted_packages = sorted(packages, key=lambda item: (1 if item.get("taskCandidateAllowed") else 0, float(item.get("packageConfidence") or item.get("confidence") or 0), SEVERITY_RANK.get(str(item.get("maxSeverity") or "normal"), 0)), reverse=True)
    candidate_packages = [item for item in sorted_packages if item.get("taskCandidateAllowed")]
    task_mapping_calls = TASK_MAPPING_API_CALLS_PER_RUN if candidate_packages else 0
    register_agent_event(ledger_id=ledger["ledgerId"], data_version=data_version, stage="task_mapping_agent", call_type="permission_sop_template", requested_calls=1 if candidate_packages else 0, actual_calls=task_mapping_calls, fallback_used=True, reason="70%+商品判断包进入任务映射；当前用权限SOP模板，不按包调用API。", payload={"candidatePackageCount": len(candidate_packages), "maxTasksPerRun": MAX_TASKS_PER_RUN})
    decisions: List[Dict[str, Any]] = []
    streamed: List[Dict[str, Any]] = []
    candidate_index = 0
    for package in sorted_packages:
        decision = _agent2_task_decision(package, candidate_index if package.get("taskCandidateAllowed") else MAX_TASKS_PER_RUN + 1)
        if package.get("taskCandidateAllowed"):
            candidate_index += 1
        _save_decision(decision)
        decisions.append(decision)
        streamed.append(_stream_decision_to_task_pool(decision, created_by=created_by))
    by_decision = Counter(str(item.get("decision")) for item in decisions)
    task_pool_created = sum(int(item.get("createdTaskCount") or 0) for item in streamed)
    formal_decision_count = int(by_decision.get("create_task_snapshot", 0) or 0) + int(by_decision.get("manager_review_required", 0) or 0)
    budget_summary = read_agent_budget_summary(ledger_id=ledger["ledgerId"])
    api_budget_violation = bool(budget_summary.get("budgetViolation"))
    generation_run = record_task_generation_run(data_version=data_version, input_bundle_count=len(signals), agent_judgment_count=len(raw_judgments), product_judgment_package_count=len(packages), identity_gap_count=len(identity_gaps), task_decision_count=len(decisions), by_decision=dict(by_decision), streamed_task_snapshot_count=sum(1 for item in streamed if item.get("ok")), task_pool_created_count=task_pool_created, skipped_formal_count=sum(1 for item in streamed if item.get("skipped")), zero_task_reasons=[item.get("reason") for item in decisions if item.get("decision") == "no_task"][:20], agent1_api_call_count=agent1_api_call_count, rag_retrieval_count=rag_retrieval_count, api_budget_violation=api_budget_violation, agent_budget_summary=budget_summary, total_agent_call_count=int(budget_summary.get("totalAgentCalls") or 0), total_agent_budget=int(budget_summary.get("totalAgentBudget") or 8), source="v15_full_chain_agent_budget_pipeline")
    try:
        from src.services.frontend_read_model_service import refresh_dashboard_view, refresh_task_views
        refresh_task_views() if task_pool_created else refresh_dashboard_view()
    except Exception:
        pass
    ref = f"dual_agent_product_task:{data_version or 'latest'}"
    return {"version": DUAL_AGENT_PIPELINE_VERSION, "mode": "v15_full_chain_agent_budget_pipeline", "dataVersion": data_version, "outputRef": ref, "agentJudgmentRef": ref, "ragContextRef": rag_context_ref or rag_context.get("ragContextRef") or rag_context.get("outputRef"), "signalCount": len(signals), "judgmentCount": len(raw_judgments), "rawJudgmentCount": len(raw_judgments), "metricJudgmentMode": "expanded", "agent1ApiMode": AGENT1_API_MODE, "agent1ApiCallCount": agent1_api_call_count, "taskMappingApiCallCount": task_mapping_calls, "totalAgentCallCount": int(budget_summary.get("totalAgentCalls") or 0), "totalAgentBudget": int(budget_summary.get("totalAgentBudget") or 8), "apiBudgetViolation": api_budget_violation, "agentBudgetLedger": budget_summary, "ragRetrievalCount": rag_retrieval_count, "ragRetrievalScope": RAG_RETRIEVAL_SCOPE, "averageJudgmentsPerSignal": round(len(raw_judgments) / len(signals), 2) if signals else 0, "productJudgmentPackageCount": len(packages), "identityGapCount": len(identity_gaps), "taskDecisionCount": len(decisions), "formalDecisionCount": formal_decision_count, "streamedTaskSnapshotCount": sum(1 for item in streamed if item.get("ok")), "streamedTaskPoolCount": task_pool_created, "byDecision": dict(by_decision), "taskGenerationRun": generation_run, "packages": packages[:50], "identityGaps": identity_gaps[:50], "decisions": decisions[:50], "streamed": streamed[:50], "rule": "V15: three Agent stages are budgeted globally; product and task stages are ledger-registered, no per-metric or per-package API calls."}
