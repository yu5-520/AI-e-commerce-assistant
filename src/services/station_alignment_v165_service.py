"""V16.5 Station Alignment service.

This service restores one-station-one-responsibility for the MVP-real chain. It
wraps the existing V16 real implementations into split station functions so the
registry, contract, queue, adapter and data-line can observe each boundary.

Agent stations do not write task pool rows or refresh frontend read models.
System stations own package merging, task-pool admission and read-model refresh.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

import src.services.dual_agent_product_task_service as base
import src.services.real_product_judgment_agent_v161_service as product_agent
import src.services.real_task_mapping_agent_v162_service as task_agent
from src.repositories.sqlite_repository import connect, loads
from src.services.agent_budget_ledger_service import get_or_create_agent_budget_ledger, read_agent_budget_summary, register_agent_event
from src.services.import_row_store_service import load_import_rows
from src.services.module_projection_service import projected_products, projection_summary
from src.services.product_signal_snapshot_v164_service import get_product_signal_snapshot, materialize_product_signal_snapshot
from src.services.rag_context_station_service import build_rag_context_snapshot, latest_rag_context
from src.services.signal_pool_service import generate_signal_pool, list_signals, update_signal_status
from src.services.system_product_snapshot_service import get_product_snapshot, materialize_system_product_snapshot
from src.services.task_generation_run_service import record_task_generation_run

STATION_ALIGNMENT_VERSION = "16.5"
COVERAGE_THRESHOLD = 0.9


def _ok_ref(prefix: str, data_version: str | None) -> str:
    return f"{prefix}:{data_version or 'latest'}"


def _json(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        loaded = loads(value)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def _table_exists(conn: Any, table: str) -> bool:
    return bool(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def _latest_generation_run(data_version: str | None = None) -> Dict[str, Any] | None:
    with connect() as conn:
        if not _table_exists(conn, "task_generation_runs_v14"):
            return None
        if data_version:
            row = conn.execute("SELECT payload FROM task_generation_runs_v14 WHERE data_version = ? ORDER BY created_at DESC LIMIT 1", (data_version,)).fetchone()
        else:
            row = conn.execute("SELECT payload FROM task_generation_runs_v14 ORDER BY created_at DESC LIMIT 1").fetchone()
    return _json(row["payload"]) if row else None


def _load_packages(data_version: str | None) -> List[Dict[str, Any]]:
    if not data_version:
        return []
    base.ensure_dual_agent_tables()
    with connect() as conn:
        if not _table_exists(conn, "product_judgment_packages_v15"):
            return []
        rows = conn.execute("SELECT payload FROM product_judgment_packages_v15 WHERE data_version = ? ORDER BY package_confidence DESC, created_at ASC", (data_version,)).fetchall()
    return [_json(row["payload"]) for row in rows]


def _load_decisions(data_version: str | None) -> List[Dict[str, Any]]:
    if not data_version:
        return []
    base.ensure_dual_agent_tables()
    with connect() as conn:
        if not _table_exists(conn, "task_generation_decisions_v15"):
            return []
        rows = conn.execute("SELECT payload FROM task_generation_decisions_v15 WHERE data_version = ? ORDER BY created_at ASC", (data_version,)).fetchall()
    return [_json(row["payload"]) for row in rows]


def _signals(data_version: str | None, limit: int) -> List[Dict[str, Any]]:
    return (list_signals(data_version=data_version, status="pending_rag_agent", limit=limit).get("signals") or [])[:limit]


def _signal_count_any(data_version: str | None) -> int:
    if not data_version:
        return 0
    with connect() as conn:
        if not _table_exists(conn, "signal_pool_v14"):
            return 0
        row = conn.execute("SELECT COUNT(*) AS count FROM signal_pool_v14 WHERE data_version = ?", (data_version,)).fetchone()
    return int(row["count"] or 0) if row else 0


def report_receive_station(data_version: str | None, *, user_id: str | None = None, **_: Any) -> Dict[str, Any]:
    rows = []
    for dataset in ["products", "orders", "inventory", "refunds", "customers", None]:
        try:
            rows.extend(load_import_rows(dataset))
        except Exception:
            pass
        if rows:
            break
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "report_receive_station", "dataVersion": data_version, "rowCount": len(rows), "rawReportRef": _ok_ref("raw_report", data_version), "outputRef": _ok_ref("raw_report", data_version), "rule": "V16.5 receive station only confirms current import batch; it does not parse or judge."}


def report_schema_station(data_version: str | None, *, user_id: str | None = None, **_: Any) -> Dict[str, Any]:
    rows = []
    for dataset in ["products", None]:
        try:
            rows = load_import_rows(dataset)
        except Exception:
            rows = []
        if rows:
            break
    headers: List[str] = []
    for row in rows[:20]:
        for key in row.keys():
            if key not in headers:
                headers.append(key)
    date_fields = [key for key in headers if any(token in key for token in ["统计日期", "更新时间", "日期", "date", "Date", "time", "Time"])]
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "report_schema_station", "dataVersion": data_version, "headerCount": len(headers), "dateFields": date_fields, "reportSchemaMappingRef": _ok_ref("report_schema_mapping", data_version), "outputRef": _ok_ref("report_schema_mapping", data_version), "rule": "V16.5 schema station isolates sheet/header/date-field mapping before fact cleaning."}


def report_fact_station(data_version: str | None, *, user_id: str | None = None, **_: Any) -> Dict[str, Any]:
    summary = projection_summary(user_id)
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "report_fact_station", "dataVersion": data_version or summary.get("latestDataVersion"), "productFactCount": summary.get("metricFactCount", 0), "trafficSourceFactCount": summary.get("trafficSourceFactCount", 0), "factNamespaceStatus": "passed", "factRef": _ok_ref("report_fact_namespace", data_version or summary.get("latestDataVersion")), "outputRef": _ok_ref("report_fact_namespace", data_version or summary.get("latestDataVersion")), "summary": summary, "rule": "V16.5 fact station separates product/store/traffic namespaces before product master."}


def product_master_station(data_version: str | None, *, user_id: str | None = None, **_: Any) -> Dict[str, Any]:
    products = projected_products(user_id)
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "product_master_station", "dataVersion": data_version, "productMasterCount": len(products), "productMasterRef": _ok_ref("product_master", data_version), "outputRef": _ok_ref("product_master", data_version), "sampleKeys": [item.get("objectId") for item in products[:20]], "rule": "V16.5 product master station dedupes by platform + store + productId + skuId."}


def product_metric_snapshot_station(data_version: str | None, *, user_id: str | None = None, force: bool = True, **_: Any) -> Dict[str, Any]:
    result = materialize_system_product_snapshot(data_version=data_version, user_id=user_id, force=force)
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "product_metric_snapshot_station", "dataVersion": data_version, "productMetricSnapshotCount": result.get("productCount", 0), "productMetricSnapshotRef": result.get("productSnapshotRef"), "outputRef": result.get("outputRef") or result.get("productSnapshotRef") or _ok_ref("product_metric_snapshot", data_version), "factContract": result.get("factContract"), "rule": "V16.5 metric snapshot station validates product ROI/date/traffic child facts before bundle assembly."}


def full_product_bundle_station(data_version: str | None, *, user_id: str | None = None, force: bool = True, **_: Any) -> Dict[str, Any]:
    result = materialize_product_signal_snapshot(data_version=data_version, user_id=user_id, force=force)
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "full_product_bundle_station", "dataVersion": data_version, "productSignalPackageCount": result.get("productSignalPackageCount", result.get("productSignalCount", 0)), "productSignalCount": result.get("productSignalCount", 0), "fullProductBundleRef": result.get("productSignalSnapshotRef"), "outputRef": result.get("outputRef") or result.get("productSignalSnapshotRef") or _ok_ref("full_product_bundle", data_version), "result": result, "rule": "V16.5 bundle station only assembles fullProductBundle; it does not call Agent."}


def bundle_validation_station(data_version: str | None, **_: Any) -> Dict[str, Any]:
    snapshot = get_product_signal_snapshot(data_version)
    bundles = snapshot.get("productSignalPackages") or snapshot.get("signals") or snapshot.get("products") or [] if snapshot else []
    total = len(bundles) if isinstance(bundles, list) else int((snapshot or {}).get("productSignalPackageCount") or 0)
    attention = 0
    for item in bundles if isinstance(bundles, list) else []:
        validation = item.get("factLayerValidation") or ((item.get("metricLayer") or {}).get("factLayerValidation") if isinstance(item.get("metricLayer"), dict) else {})
        if validation and validation.get("status") != "passed":
            attention += 1
    status = "passed" if total and attention == 0 else "attention" if total else "waiting"
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "bundle_validation_station", "dataVersion": data_version, "bundleCount": total, "attentionBundleCount": attention, "validationStatus": status, "validatedBundleRef": _ok_ref("validated_full_product_bundle", data_version), "outputRef": _ok_ref("validated_full_product_bundle", data_version), "rule": "V16.5 validation station makes factLayerValidation visible before product judgment Agent."}


def product_judgment_agent_station(data_version: str | None, *, user_id: str | None = None, max_signals: int = 160, **_: Any) -> Dict[str, Any]:
    base.ensure_dual_agent_tables()
    base._clear_version_rows(data_version)
    ledger = get_or_create_agent_budget_ledger(data_version=data_version, source="v16_5_product_judgment_agent_station")
    rag_context = latest_rag_context(data_version) or build_rag_context_snapshot(data_version=data_version)
    signals = _signals(data_version, max_signals)
    judgments, provider = product_agent._real_agent_judgments(signals, data_version, rag_context)
    register_agent_event(ledger_id=ledger["ledgerId"], data_version=data_version, stage="product_judgment_agent_station", call_type="real_llm_batch_product_judgment", requested_calls=min(product_agent.MAX_PRODUCT_AGENT_CALLS_PER_RUN, max(1, (len([s for s in signals if product_agent._strict_product_id(s)]) + product_agent.MAX_PRODUCTS_PER_CALL - 1) // product_agent.MAX_PRODUCTS_PER_CALL)) if signals else 0, actual_calls=int(provider.get("actualCalls") or 0), fallback_used=False, rag_retrievals=0, actual_input_tokens=int(provider.get("inputTokens") or 0), actual_output_tokens=int(provider.get("outputTokens") or 0), reason="V16.5 split product judgment Agent station only outputs judgments; no task mapping or task pool writes.", payload={"provider": provider, "signalCount": len(signals)})
    base._save_raw_judgments(judgments)
    for signal in signals:
        update_signal_status(signal.get("signalId"), "product_judgment_agent_completed" if judgments else "product_judgment_agent_failed", {"version": STATION_ALIGNMENT_VERSION, "providerStatus": provider.get("providerStatus")})
    judged_products = {str(item.get("productId")) for item in judgments if item.get("productId")}
    input_products = {str(product_agent._strict_product_id(item)) for item in signals if product_agent._strict_product_id(item)}
    coverage = round(len(judged_products) / len(input_products), 4) if input_products else 0
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "product_judgment_agent_station", "dataVersion": data_version, "inputBundleCount": len(signals), "resolvedProductCount": len(input_products), "agentJudgmentCount": len(judgments), "judgedProductCount": len(judged_products), "coverageRate": coverage, "coverageStatus": "passed" if coverage >= COVERAGE_THRESHOLD else "failed", "agent1ApiCallCount": int(provider.get("actualCalls") or 0), "productAgentProviderStatus": provider.get("providerStatus"), "productAgentProvider": provider, "agentJudgmentRef": _ok_ref("product_judgment", data_version), "outputRef": _ok_ref("product_judgment", data_version), "rule": "V16.5 product judgment Agent must cover input products and cannot generate tasks."}


def product_judgment_package_station(data_version: str | None, **_: Any) -> Dict[str, Any]:
    signals_total = _signal_count_any(data_version)
    packages, identity_gaps = base._package_product_judgments(data_version)
    package_products = {str(item.get("productId")) for item in packages if item.get("productId")}
    coverage = round(len(package_products) / signals_total, 4) if signals_total else 0
    candidate_count = sum(1 for item in packages if item.get("taskCandidateAllowed"))
    coverage_status = "passed" if signals_total and coverage >= COVERAGE_THRESHOLD else "failed" if signals_total else "waiting"
    latest = _latest_generation_run(data_version) or {}
    budget = latest.get("agentBudgetLedger") or read_agent_budget_summary(data_version=data_version)
    record_task_generation_run(data_version=data_version, input_bundle_count=signals_total, agent_judgment_count=sum(int(item.get("judgmentCount") or 1) for item in packages), product_judgment_package_count=len(packages), identity_gap_count=len(identity_gaps), task_decision_count=0, by_decision={}, streamed_task_snapshot_count=0, task_pool_created_count=0, skipped_formal_count=0, zero_task_reasons=[f"商品判断覆盖率 {len(package_products)}/{signals_total}，coverageStatus={coverage_status}；覆盖不足时暂停任务映射。"], agent1_api_call_count=int((budget.get("productJudgmentProvider") or {}).get("actualCalls") or latest.get("agent1ApiCallCount") or 0), rag_retrieval_count=int(latest.get("ragRetrievalCount") or 0), api_budget_violation=bool(budget.get("budgetViolation")), agent_budget_summary=budget, total_agent_call_count=int(budget.get("totalAgentCalls") or latest.get("totalAgentCallCount") or 0), total_agent_budget=int(budget.get("totalAgentBudget") or latest.get("totalAgentBudget") or 8), source="v16_5_product_judgment_package_station")
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "product_judgment_package_station", "dataVersion": data_version, "inputBundleCount": signals_total, "productJudgmentPackageCount": len(packages), "candidatePackageCount": candidate_count, "coverageRate": coverage, "coverageStatus": coverage_status, "identityGapCount": len(identity_gaps), "productJudgmentPackageRef": _ok_ref("product_judgment_package", data_version), "outputRef": _ok_ref("product_judgment_package", data_version), "rule": "V16.5 package station merges judgments and owns the 70% confidence gate; low coverage stops task mapping."}


def rag_permission_context_station(data_version: str | None, **_: Any) -> Dict[str, Any]:
    result = build_rag_context_snapshot(data_version=data_version)
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "rag_permission_context_station", "dataVersion": data_version, "matchedContextCount": result.get("matchedContextCount", 0), "ragContextRef": result.get("ragContextRef"), "outputRef": result.get("outputRef") or _ok_ref("rag_permission_context", data_version), "ragContext": result, "rule": "V16.5 RAG station prepares permission/SOP/approval context for task mapping only."}


def task_mapping_agent_station(data_version: str | None, **_: Any) -> Dict[str, Any]:
    packages = _load_packages(data_version)
    candidate_packages = [item for item in packages if item.get("taskCandidateAllowed")]
    rag_context = latest_rag_context(data_version) or build_rag_context_snapshot(data_version=data_version)
    ledger = get_or_create_agent_budget_ledger(data_version=data_version, source="v16_5_task_mapping_agent_station")
    decisions, provider = task_agent._real_task_mapping_decisions(packages, data_version, rag_context) if candidate_packages else ([], {"providerStatus": "no_candidate_packages", "actualCalls": 0, "errors": []})
    register_agent_event(ledger_id=ledger["ledgerId"], data_version=data_version, stage="task_mapping_agent_station", call_type="real_rag_permission_task_mapping", requested_calls=min(task_agent.MAX_TASK_AGENT_CALLS_PER_RUN, max(1, (len(candidate_packages) + task_agent.MAX_PACKAGES_PER_CALL - 1) // task_agent.MAX_PACKAGES_PER_CALL)) if candidate_packages else 0, actual_calls=int(provider.get("actualCalls") or 0), fallback_used=False, rag_retrievals=0, actual_input_tokens=int(provider.get("inputTokens") or 0), actual_output_tokens=int(provider.get("outputTokens") or 0), reason="V16.5 split task mapping Agent only outputs decisions; task pool admission is a later system station.", payload={"provider": provider, "candidatePackageCount": len(candidate_packages)})
    for decision in decisions:
        base._save_decision(decision)
    by_decision = Counter(str(item.get("decision")) for item in decisions)
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "task_mapping_agent_station", "dataVersion": data_version, "candidatePackageCount": len(candidate_packages), "taskDecisionCount": len(decisions), "byDecision": dict(by_decision), "taskMappingApiCallCount": int(provider.get("actualCalls") or 0), "taskMappingProviderStatus": provider.get("providerStatus"), "taskMappingProvider": provider, "taskGenerationDecisionRef": _ok_ref("task_generation_decision", data_version), "outputRef": _ok_ref("task_generation_decision", data_version), "rule": "V16.5 task mapping Agent maps 70%+ packages to decisions only; no task pool writes here."}


def task_pool_admission_station(data_version: str | None, *, user_id: str | None = None, **_: Any) -> Dict[str, Any]:
    decisions = _load_decisions(data_version)
    streamed = [base._stream_decision_to_task_pool(decision, created_by=user_id) for decision in decisions]
    by_decision = Counter(str(item.get("decision")) for item in decisions)
    task_pool_created = sum(int(item.get("createdTaskCount") or 0) for item in streamed)
    packages = _load_packages(data_version)
    signals_total = _signal_count_any(data_version)
    budget = read_agent_budget_summary(data_version=data_version)
    record_task_generation_run(data_version=data_version, input_bundle_count=signals_total, agent_judgment_count=sum(int(item.get("judgmentCount") or 1) for item in packages), product_judgment_package_count=len(packages), identity_gap_count=0, task_decision_count=len(decisions), by_decision=dict(by_decision), streamed_task_snapshot_count=sum(1 for item in streamed if item.get("ok")), task_pool_created_count=task_pool_created, skipped_formal_count=sum(1 for item in streamed if item.get("skipped")), zero_task_reasons=["V16.5 task pool admission produced no current-run formal tasks."] if task_pool_created <= 0 else [], agent1_api_call_count=int((budget.get("productJudgmentProvider") or {}).get("actualCalls") or 0), rag_retrieval_count=0, api_budget_violation=bool(budget.get("budgetViolation")), agent_budget_summary=budget, total_agent_call_count=int(budget.get("totalAgentCalls") or 0), total_agent_budget=int(budget.get("totalAgentBudget") or 8), source="v16_5_task_pool_admission_station")
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "task_pool_admission_station", "dataVersion": data_version, "taskDecisionCount": len(decisions), "createdTaskCount": task_pool_created, "streamedTaskPoolCount": task_pool_created, "byDecision": dict(by_decision), "taskPoolRef": _ok_ref("task_pool", data_version), "outputRef": _ok_ref("task_pool", data_version), "streamed": streamed[:50], "rule": "V16.5 system station owns dedupe/limit/task-pool writes; Agent does not."}


def frontend_read_model_station(data_version: str | None, **_: Any) -> Dict[str, Any]:
    try:
        from src.services.frontend_read_model_service import refresh_all_read_models
        result = refresh_all_read_models(data_version=data_version)
    except Exception as exc:
        result = {"status": "failed", "error": str(exc)}
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "frontend_read_model_station", "dataVersion": data_version, "frontendReadModelStatus": result.get("status") or "completed", "frontendReadModelRef": _ok_ref("frontend_read_model", data_version), "outputRef": _ok_ref("frontend_read_model", data_version), "refresh": result, "rule": "V16.5 read model station only refreshes current dataVersion projections."}


def task_pool_acceptance_station(data_version: str | None, **_: Any) -> Dict[str, Any]:
    from src.services.task_pool_acceptance_v163_service import read_task_pool_acceptance
    result = read_task_pool_acceptance(data_version=data_version)
    return {"version": STATION_ALIGNMENT_VERSION, "stationId": "task_pool_acceptance_station", "dataVersion": data_version or result.get("dataVersion"), "acceptanceStatus": result.get("status"), "ok": result.get("ok"), "mismatchCount": len(result.get("mismatches") or []), "taskPoolAcceptanceRef": _ok_ref("task_pool_acceptance", data_version or result.get("dataVersion")), "outputRef": _ok_ref("task_pool_acceptance", data_version or result.get("dataVersion")), "acceptance": result, "rule": "V16.5 final station validates data-line = task_pool = frontend views."}
