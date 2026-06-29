"""V14.4 Task Pool Station service.

Task Pool consumes persisted task snapshots and creates visible lifecycle tasks.
The pool does not pass raw Agent packages into legacy task code. It normalizes
through TaskIntent first, then adapts to the legacy visible-task payload.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, ensure_columns
from src.services.account_service import assignment_for_store, default_operator, default_reviewer, store_raw, user_display
from src.services.module_task_service import create_task, find_task
from src.services.task_intent_contract_service import to_legacy_task_payload
from src.services.task_snapshot_station_service import get_task_snapshot, list_task_snapshots

TASK_POOL_STATION_VERSION = "14.4.0"
READY_SNAPSHOT_STATUSES = {"snapshot_ready", "manager_review_required"}
READY_DECISIONS = {"create_task_snapshot", "manager_review_required"}


def now_iso() -> str:
    return datetime.now().isoformat()


def make_pool_entry_id() -> str:
    return f"TPE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def ensure_task_pool_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_pool_entries (
                pool_entry_id TEXT PRIMARY KEY,
                task_snapshot_id TEXT NOT NULL,
                task_id TEXT,
                data_version TEXT,
                status TEXT NOT NULL,
                decision TEXT,
                task_layer TEXT,
                assignee_id TEXT,
                reviewer_id TEXT,
                dedupe_key TEXT,
                reason TEXT,
                payload TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(conn, "task_pool_entries", {"task_id": "TEXT", "data_version": "TEXT", "decision": "TEXT", "task_layer": "TEXT", "assignee_id": "TEXT", "reviewer_id": "TEXT", "dedupe_key": "TEXT", "reason": "TEXT", "payload": "TEXT", "created_by": "TEXT"})
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_pool_entries_snapshot ON task_pool_entries(task_snapshot_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_pool_entries_task ON task_pool_entries(task_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_pool_entries_status ON task_pool_entries(status, created_at)")
        conn.commit()


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except Exception:
        return fallback


def _row_to_pool_entry(row: Any) -> Dict[str, Any]:
    return {"version": TASK_POOL_STATION_VERSION, "poolEntryId": row["pool_entry_id"], "taskSnapshotId": row["task_snapshot_id"], "taskId": row["task_id"], "dataVersion": row["data_version"], "status": row["status"], "decision": row["decision"], "taskLayer": row["task_layer"], "assigneeId": row["assignee_id"], "assigneeName": user_display(row["assignee_id"], "未派发"), "reviewerId": row["reviewer_id"], "reviewerName": user_display(row["reviewer_id"], "未设置复核人"), "dedupeKey": row["dedupe_key"], "reason": row["reason"], "payload": _loads(row["payload"], {}), "createdBy": row["created_by"], "createdAt": row["created_at"], "updatedAt": row["updated_at"]}


def _first_store_id(snapshot: Dict[str, Any], plan: Dict[str, Any]) -> str | None:
    system_facts = (snapshot.get("payload") or {}).get("systemFacts") if isinstance(snapshot.get("payload"), dict) else {}
    store_ids = plan.get("storeIds") or plan.get("visibleStoreIds") or (system_facts or {}).get("storeIds") or []
    if isinstance(store_ids, list) and store_ids:
        return str(store_ids[0])
    store_id = plan.get("storeId") or (system_facts or {}).get("storeId") or snapshot.get("storeId")
    return str(store_id) if store_id else None


def _ownership_for_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    plan = snapshot.get("taskPlan") or {}
    store_id = _first_store_id(snapshot, plan)
    assignment = assignment_for_store(store_id) if store_id else None
    reviewer = plan.get("reviewerId") or (assignment or {}).get("reviewerId") or (default_reviewer() or {}).get("id")
    operator = plan.get("assignedOperatorId") or (assignment or {}).get("primaryOperatorId") or (default_operator(plan.get("riskDomain") or plan.get("taskType")) or {}).get("id")
    store_ids = plan.get("storeIds") or ([store_id] if store_id else []) or ["S001", "S002", "S003", "S004"]
    need_manager = bool(snapshot.get("needManagerReview") or snapshot.get("decision") == "manager_review_required")
    visible_users = list(dict.fromkeys([user for user in [operator, reviewer, "U001"] if user]))
    return {"assignedOperatorId": None if need_manager else operator, "reviewerId": reviewer, "ownerUserId": "U001", "visibleUserIds": visible_users, "visibleRoleIds": ["owner", "manager", "operator"], "visibleStoreIds": store_ids, "storeIds": store_ids}


def _as_list(value: Any, fallback: List[Any] | None = None) -> List[Any]:
    if isinstance(value, list):
        return value
    if value:
        return [value]
    return fallback or []


def _metric_facts(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    facts: List[Dict[str, Any]] = []
    system_facts = (snapshot.get("payload") or {}).get("systemFacts") if isinstance(snapshot.get("payload"), dict) else {}
    signal = (system_facts or {}).get("signal") if isinstance(system_facts, dict) else {}
    metric_snapshot = signal.get("productMetricSnapshot") if isinstance(signal, dict) else {}
    if isinstance(metric_snapshot, dict):
        for code in ["roas", "roi", "paymentAmount", "adSpend", "clickRate", "conversionRate", "refundRate", "grossMargin", "inventory"]:
            value = metric_snapshot.get(code)
            if value not in {None, "", "—", "未识别"}:
                facts.append({"metricCode": code, "label": code, "value": value})
    review_metrics = (snapshot.get("taskPlan") or {}).get("reviewMetrics") or []
    for label in review_metrics:
        facts.append({"label": str(label), "value": None})
    return facts


def _build_task_package(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    plan = snapshot.get("taskPlan") or {}
    judgment = snapshot.get("agentJudgment") or {}
    rag_context = snapshot.get("ragContext") or {}
    evidence = _as_list(snapshot.get("evidenceRequirements")) or _as_list(plan.get("evidenceRequirements"), ["对应后台截图", "指标变化记录", "运营处理说明"])
    entity_type = snapshot.get("entityType") or plan.get("entityType") or "商品"
    entity_id = snapshot.get("entityId") or plan.get("entityId") or snapshot.get("taskSnapshotId")
    priority = plan.get("priority") or snapshot.get("priority") or "中"
    deadline = plan.get("deadline") or "24小时内"
    task_type = plan.get("taskType") or snapshot.get("taskType") or "经营任务"
    action_type = plan.get("actionType") or snapshot.get("actionType") or "agent_guided_operation"
    need_manager = bool(snapshot.get("needManagerReview") or snapshot.get("decision") == "manager_review_required")
    ownership = _ownership_for_snapshot(snapshot)
    store_id = (ownership.get("storeIds") or [None])[0]
    store = store_raw(store_id) if store_id else None
    sop_steps = _as_list(plan.get("sopSteps") or plan.get("steps"), [f"{deadline}根据系统判断处理该{entity_type}经营问题。", "提交执行前后截图、数据凭证、操作时间和影响范围。", "由系统在复盘周期回看ROAS、点击率、转化率、GMV、退款率和库存变化。"])
    review_metrics = _as_list(plan.get("reviewMetrics"), ["ROAS", "GMV", "点击率", "转化率", "退款率", "库存"])
    task_layer = "manager_dispatch" if need_manager else "operator_execution"
    title = plan.get("title") or f"{task_type}｜{entity_id}"
    subtitle = plan.get("subtitle") or judgment.get("trendType") or snapshot.get("trendType") or "系统判断"
    base = {"taskGenerationMode": "v11_8_sop_package", "taskSnapshotId": snapshot.get("taskSnapshotId"), "sourceModule": "task_snapshot_station", "sourceEvent": snapshot.get("taskSnapshotId"), "sourceRoute": "business-actions", "productRoute": "business-products", "entityType": entity_type, "entityId": entity_id, "productId": plan.get("productId") or snapshot.get("productId") or entity_id, "storeIds": ownership.get("storeIds") or [], "store": (store or {}).get("name") or "经营单元", "platform": (store or {}).get("platform") or "经营平台", "riskDomain": plan.get("riskDomain") or task_type, "actionType": action_type, "taskType": task_type, "priority": priority, "deadline": deadline, "taskLayer": task_layer, "status": "待拆分" if task_layer == "manager_dispatch" else "待接收", "workflowStatus": "待拆分" if task_layer == "manager_dispatch" else "待接收", "taskCard": {"title": title, "subtitle": subtitle, "priority": priority, "deadline": deadline, "decision": snapshot.get("decision"), "confidence": snapshot.get("confidence")}, "taskDetailReport": {"version": TASK_POOL_STATION_VERSION, "taskSnapshotId": snapshot.get("taskSnapshotId"), "warningSummary": judgment.get("reason") or plan.get("reason") or "系统判断该经营变化需要进入任务池。", "systemFacts": (snapshot.get("payload") or {}).get("systemFacts") if isinstance(snapshot.get("payload"), dict) else {}, "ragContext": rag_context, "agentJudgment": judgment, "taskPlan": plan, "poolBoundary": "任务池只完成入池，接收、派发、提交、复核由后续生命周期站处理。"}, "evidencePack": [{"title": item, "value": None} for item in evidence], "sopSteps": [str(item) for item in sop_steps], "reviewMetrics": [str(item) for item in review_metrics], "metricFacts": _metric_facts(snapshot), "operationBudget": snapshot.get("operationBudget") or plan.get("operationBudget") or {}, "completionGate": {"type": "evidence_and_recap_required", "requiredEvidence": evidence, "reviewMetrics": review_metrics}, "failureThreshold": {"rule": "复盘周期内核心指标未改善或反向恶化，则进入复核退回或二次判断。", "metrics": review_metrics}, "agentJudgment": {**judgment, "status": "agent_guided_task_snapshot", "decision": snapshot.get("decision"), "confidence": snapshot.get("confidence"), "ragContextApplied": bool(rag_context)}, "ownership": ownership}
    return to_legacy_task_payload(base)


def _existing_pool_entry(snapshot_id: str) -> Dict[str, Any] | None:
    ensure_task_pool_tables()
    with connect() as conn:
        row = conn.execute("SELECT * FROM task_pool_entries WHERE task_snapshot_id = ? ORDER BY created_at DESC LIMIT 1", (snapshot_id,)).fetchone()
    return _row_to_pool_entry(row) if row else None


def _update_snapshot_pool_status(snapshot_id: str, status: str, task_id: str | None = None) -> None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM task_snapshots WHERE task_snapshot_id = ?", (snapshot_id,)).fetchone()
        if not row:
            return
        payload = _loads(row["payload"], {})
        payload["taskPool"] = {"status": status, "taskId": task_id, "version": TASK_POOL_STATION_VERSION, "rule": "task_pool_station has processed this snapshot"}
        conn.execute("UPDATE task_snapshots SET task_pool_status = ?, payload = ?, updated_at = ? WHERE task_snapshot_id = ?", (status, _json(payload), now_iso(), snapshot_id))
        conn.commit()


def enter_task_pool_from_snapshot(task_snapshot_id: str, *, created_by: str | None = None, force: bool = False) -> Dict[str, Any]:
    ensure_task_pool_tables()
    snapshot = get_task_snapshot(task_snapshot_id)
    if not snapshot:
        return {"version": TASK_POOL_STATION_VERSION, "ok": False, "status": "failed", "error": "task_snapshot_not_found", "taskSnapshotId": task_snapshot_id}
    if snapshot.get("decision") not in READY_DECISIONS or snapshot.get("status") not in READY_SNAPSHOT_STATUSES:
        _update_snapshot_pool_status(task_snapshot_id, "not_eligible")
        return {"version": TASK_POOL_STATION_VERSION, "ok": True, "status": "skipped", "reason": "snapshot_not_eligible_for_task_pool", "snapshot": snapshot, "createdTaskCount": 0}
    existing = _existing_pool_entry(task_snapshot_id)
    if existing and not force:
        task = find_task(existing.get("taskId")) if existing.get("taskId") else None
        return {"version": TASK_POOL_STATION_VERSION, "ok": True, "status": "idempotent", "poolEntry": existing, "task": task, "createdTaskCount": 0, "rule": "同一任务快照已入池，不重复创建任务。"}
    package = _build_task_package(snapshot)
    task = create_task(package)
    pool_entry_id = make_pool_entry_id()
    created_at = now_iso()
    with connect() as conn:
        conn.execute("""
            INSERT INTO task_pool_entries (pool_entry_id, task_snapshot_id, task_id, data_version, status, decision, task_layer, assignee_id, reviewer_id, dedupe_key, reason, payload, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pool_entry_id, task_snapshot_id, task.get("id"), snapshot.get("dataVersion"), "entered_task_pool", snapshot.get("decision"), task.get("taskLayer"), task.get("assigneeId"), task.get("reviewerId"), task.get("dedupeKey"), "任务快照已通过TaskIntent契约进入任务池。", _json({"snapshot": snapshot, "taskPackage": package, "taskIntent": package.get("taskIntent"), "task": task}), created_by, created_at, created_at))
        conn.commit()
        row = conn.execute("SELECT * FROM task_pool_entries WHERE pool_entry_id = ?", (pool_entry_id,)).fetchone()
    _update_snapshot_pool_status(task_snapshot_id, "entered_task_pool", task.get("id"))
    entry = _row_to_pool_entry(row)
    return {"version": TASK_POOL_STATION_VERSION, "ok": True, "status": "entered_task_pool", "poolEntry": entry, "task": task, "createdTaskCount": 1, "rule": "TaskSnapshot -> TaskIntent -> visible task."}


def sync_ready_task_snapshots(*, data_version: str | None = None, limit: int = 50, created_by: str | None = None) -> Dict[str, Any]:
    ensure_task_pool_tables()
    snapshot_result = list_task_snapshots(data_version=data_version, limit=limit)
    snapshots = [item for item in snapshot_result.get("snapshots", []) if item.get("decision") in READY_DECISIONS and item.get("status") in READY_SNAPSHOT_STATUSES and item.get("taskPoolStatus") != "entered_task_pool"]
    results = [enter_task_pool_from_snapshot(item["taskSnapshotId"], created_by=created_by) for item in snapshots]
    created = sum(int(item.get("createdTaskCount") or 0) for item in results)
    return {"version": TASK_POOL_STATION_VERSION, "status": "completed", "dataVersion": data_version, "candidateSnapshotCount": len(snapshots), "createdTaskCount": created, "results": results, "rule": "只同步已判断为可入池的任务快照；observe_only和ignore_noise不会进入任务池。"}


def list_task_pool_entries(limit: int = 80) -> Dict[str, Any]:
    ensure_task_pool_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM task_pool_entries ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    items = [_row_to_pool_entry(row) for row in rows]
    return {"version": TASK_POOL_STATION_VERSION, "entries": items, "entryCount": len(items)}


def task_pool_summary(limit: int = 80) -> Dict[str, Any]:
    entries = list_task_pool_entries(limit=limit).get("entries") or []
    by_status: Dict[str, int] = {}
    by_layer: Dict[str, int] = {}
    for item in entries:
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1
        by_layer[item["taskLayer"]] = by_layer.get(item["taskLayer"], 0) + 1
    return {"version": TASK_POOL_STATION_VERSION, "entryCount": len(entries), "byStatus": by_status, "byTaskLayer": by_layer, "latest": entries[0] if entries else None, "entries": entries, "rule": "任务池站只负责把任务快照变成可见任务池记录；不自动接收、不提交、不复核。"}
