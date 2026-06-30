"""V14.8 frontend read model service.

Frontend pages must read pre-built view models only. This service creates and
refreshes lightweight read tables from already persisted runtime results. It does
not run materialize/generate/Agent/worker functions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads

FRONTEND_READ_MODEL_VERSION = "14.8.0"
VIEW_TABLES = [
    "frontend_dashboard_view",
    "frontend_product_view",
    "frontend_task_view",
    "frontend_task_detail_view",
    "frontend_store_view",
    "frontend_system_status_view",
]


def now_iso() -> str:
    return datetime.now().isoformat()


def ensure_frontend_read_model_tables() -> None:
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS frontend_dashboard_view (
                view_key TEXT PRIMARY KEY,
                payload TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS frontend_product_view (
                view_key TEXT PRIMARY KEY,
                product_id TEXT,
                store_id TEXT,
                data_version TEXT,
                payload TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS frontend_task_view (
                task_id TEXT PRIMARY KEY,
                status TEXT,
                workflow_status TEXT,
                task_layer TEXT,
                priority TEXT,
                deadline TEXT,
                store_id TEXT,
                product_id TEXT,
                payload TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS frontend_task_detail_view (
                task_id TEXT PRIMARY KEY,
                payload TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS frontend_store_view (
                store_id TEXT PRIMARY KEY,
                payload TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS frontend_system_status_view (
                view_key TEXT PRIMARY KEY,
                payload TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        ensure_columns(conn, "frontend_product_view", {"product_id": "TEXT", "store_id": "TEXT", "data_version": "TEXT", "payload": "TEXT", "updated_at": "TEXT"})
        ensure_columns(conn, "frontend_task_view", {"status": "TEXT", "workflow_status": "TEXT", "task_layer": "TEXT", "priority": "TEXT", "deadline": "TEXT", "store_id": "TEXT", "product_id": "TEXT", "payload": "TEXT", "updated_at": "TEXT"})
        conn.execute("CREATE INDEX IF NOT EXISTS idx_frontend_product_view_product ON frontend_product_view(product_id, store_id, updated_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_frontend_task_view_status ON frontend_task_view(status, workflow_status, priority, updated_at)")
        conn.commit()


def _table_exists(conn: Any, table_name: str) -> bool:
    return bool(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone())


def _latest_payload(conn: Any, table_name: str, order_col: str = "updated_at") -> Dict[str, Any] | None:
    if not _table_exists(conn, table_name):
        return None
    row = conn.execute(f"SELECT payload FROM {table_name} ORDER BY {order_col} DESC LIMIT 1").fetchone()
    return loads(row["payload"]) if row else None


def _product_bundle_summary(bundle: Dict[str, Any]) -> Dict[str, Any]:
    profile = bundle.get("profileLayer") if isinstance(bundle.get("profileLayer"), dict) else {}
    metric = bundle.get("metricLayer") if isinstance(bundle.get("metricLayer"), dict) else {}
    cross = bundle.get("crossValidation") if isinstance(bundle.get("crossValidation"), dict) else {}
    return {
        "viewVersion": FRONTEND_READ_MODEL_VERSION,
        "bundleId": bundle.get("bundleId"),
        "signalId": bundle.get("signalId"),
        "dataVersion": bundle.get("dataVersion"),
        "productId": bundle.get("productId") or profile.get("productId"),
        "storeId": bundle.get("storeId") or profile.get("storeId"),
        "storeName": profile.get("storeName"),
        "platform": bundle.get("platform") or profile.get("platform"),
        "title": profile.get("title") or profile.get("shortName") or bundle.get("productId"),
        "verticalCategory": bundle.get("verticalCategory") or profile.get("verticalCategory") or "未归类",
        "productRole": profile.get("productRole"),
        "lifecycleStage": profile.get("lifecycleStage"),
        "signalStrength": bundle.get("signalStrength"),
        "primarySignalType": bundle.get("primarySignalType"),
        "metricCode": bundle.get("metricCode"),
        "metrics": {key: metric.get(key) for key in ["paymentAmount", "roas", "roi", "adSpend", "clickRate", "conversionRate", "refundRate", "grossMargin", "inventory"]},
        "crossValidation": {"sourceVersionCount": cross.get("sourceVersionCount"), "changedMetricCount": cross.get("changedMetricCount"), "abnormalMetricCount": cross.get("abnormalMetricCount")},
        "updatedAt": now_iso(),
        "readRule": "Frontend reads this cached product view only; page switching does not trigger materialize/generate/Agent.",
    }


def refresh_product_views(data_version: str | None = None) -> Dict[str, Any]:
    ensure_frontend_read_model_tables()
    with connect() as conn:
        if not _table_exists(conn, "product_signal_snapshots_v14"):
            return {"version": FRONTEND_READ_MODEL_VERSION, "updated": 0, "status": "no_source_table"}
        if data_version:
            row = conn.execute("SELECT * FROM product_signal_snapshots_v14 WHERE data_version = ? ORDER BY updated_at DESC LIMIT 1", (data_version,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM product_signal_snapshots_v14 ORDER BY updated_at DESC LIMIT 1").fetchone()
        if not row:
            return {"version": FRONTEND_READ_MODEL_VERSION, "updated": 0, "status": "no_snapshot"}
        payload = loads(row["payload"])
        bundles = payload.get("productSignalPackages") or payload.get("signals") or []
        now = now_iso()
        for bundle in bundles:
            summary = _product_bundle_summary(bundle)
            key = f"{summary.get('storeId') or 'GLOBAL'}::{summary.get('productId') or summary.get('bundleId')}"
            conn.execute(
                """
                INSERT OR REPLACE INTO frontend_product_view (view_key, product_id, store_id, data_version, payload, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, summary.get("productId"), summary.get("storeId"), summary.get("dataVersion"), dumps(summary), now),
            )
        conn.commit()
    return {"version": FRONTEND_READ_MODEL_VERSION, "updated": len(bundles), "status": "product_views_refreshed", "rule": "Refreshed from persisted fullProductBundle snapshot only."}


def _task_summary(task: Dict[str, Any]) -> Dict[str, Any]:
    card = task.get("taskCard") if isinstance(task.get("taskCard"), dict) else {}
    auth = task.get("actionAuthorization") if isinstance(task.get("actionAuthorization"), dict) else {}
    return {
        "viewVersion": FRONTEND_READ_MODEL_VERSION,
        "taskId": task.get("id"),
        "title": task.get("title") or card.get("title"),
        "subtitle": card.get("subtitle"),
        "status": task.get("status"),
        "workflowStatus": task.get("workflowStatus"),
        "taskLayer": task.get("taskLayer"),
        "priority": task.get("priority"),
        "deadline": task.get("deadline"),
        "productId": task.get("productId"),
        "storeIds": task.get("storeIds") or task.get("visibleStoreIds") or [],
        "storeId": (task.get("storeIds") or task.get("visibleStoreIds") or [None])[0],
        "assigneeId": task.get("assigneeId"),
        "assigneeName": task.get("assigneeName"),
        "reviewerId": task.get("reviewerId"),
        "reviewerName": task.get("reviewerName"),
        "managerApproval": auth.get("decision") in {"manager_approval_required", "owner_approval_required"} or task.get("taskLayer") in {"manager_dispatch", "manager_approval"},
        "availableActions": task.get("availableActions") or [],
        "updatedAt": task.get("updatedAt") or now_iso(),
    }


def refresh_task_views(limit: int = 300) -> Dict[str, Any]:
    ensure_frontend_read_model_tables()
    with connect() as conn:
        if not _table_exists(conn, "task_pool_entries"):
            return {"version": FRONTEND_READ_MODEL_VERSION, "updated": 0, "status": "no_source_table"}
        rows = conn.execute("SELECT * FROM task_pool_entries ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        updated = 0
        now = now_iso()
        for row in rows:
            payload = loads(row["payload"])
            task = payload.get("task") if isinstance(payload.get("task"), dict) else None
            if not task:
                continue
            summary = _task_summary(task)
            task_id = summary.get("taskId")
            if not task_id:
                continue
            conn.execute(
                """
                INSERT OR REPLACE INTO frontend_task_view (task_id, status, workflow_status, task_layer, priority, deadline, store_id, product_id, payload, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, summary.get("status"), summary.get("workflowStatus"), summary.get("taskLayer"), summary.get("priority"), summary.get("deadline"), summary.get("storeId"), summary.get("productId"), dumps(summary), now),
            )
            detail = {"viewVersion": FRONTEND_READ_MODEL_VERSION, "taskId": task_id, "taskCard": task.get("taskCard"), "taskDetailReport": task.get("taskDetailReport"), "evidencePack": task.get("evidencePack"), "sopSteps": task.get("sopSteps"), "reviewMetrics": task.get("reviewMetrics"), "completionGate": task.get("completionGate"), "failureThreshold": task.get("failureThreshold"), "agentJudgment": task.get("agentJudgment"), "ownership": task.get("ownership"), "updatedAt": summary.get("updatedAt")}
            conn.execute("INSERT OR REPLACE INTO frontend_task_detail_view (task_id, payload, updated_at) VALUES (?, ?, ?)", (task_id, dumps(detail), now))
            updated += 1
        conn.commit()
    refresh_dashboard_view()
    return {"version": FRONTEND_READ_MODEL_VERSION, "updated": updated, "status": "task_views_refreshed", "rule": "Refreshed from persisted task_pool_entries only."}


def refresh_dashboard_view() -> Dict[str, Any]:
    ensure_frontend_read_model_tables()
    with connect() as conn:
        tasks = [loads(row["payload"]) for row in conn.execute("SELECT payload FROM frontend_task_view ORDER BY updated_at DESC LIMIT 500").fetchall()]
        products = [loads(row["payload"]) for row in conn.execute("SELECT payload FROM frontend_product_view ORDER BY updated_at DESC LIMIT 500").fetchall()]
        queues = []
        if _table_exists(conn, "station_queue"):
            queues = [dict(row) for row in conn.execute("SELECT station_id, status, COUNT(*) AS count FROM station_queue GROUP BY station_id, status").fetchall()]
        active = [item for item in tasks if item.get("status") not in {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}]
        manager = [item for item in active if item.get("managerApproval") or item.get("status") in {"待复核", "待拆分"}]
        processing = [item for item in active if item.get("status") == "处理中"]
        recap = [item for item in active if item.get("status") in {"已完成", "待复盘"}]
        high_products = [item for item in products if item.get("signalStrength") == "high"]
        dashboard = {"viewVersion": FRONTEND_READ_MODEL_VERSION, "topTasks": active[:5], "counts": {"activeTasks": len(active), "managerReview": len(manager), "processing": len(processing), "waitingRecap": len(recap), "products": len(products), "highRiskProducts": len(high_products)}, "workerQueue": queues, "updatedAt": now_iso(), "readRule": "Dashboard reads cached view rows only; no compute chain is triggered by page switching."}
        conn.execute("INSERT OR REPLACE INTO frontend_dashboard_view (view_key, payload, updated_at) VALUES ('main', ?, ?)", (dumps(dashboard), dashboard["updatedAt"]))
        conn.execute("INSERT OR REPLACE INTO frontend_system_status_view (view_key, payload, updated_at) VALUES ('main', ?, ?)", (dumps({"viewVersion": FRONTEND_READ_MODEL_VERSION, "queue": queues, "updatedAt": dashboard["updatedAt"], "readModelReady": True}), dashboard["updatedAt"]))
        conn.commit()
    return {"version": FRONTEND_READ_MODEL_VERSION, "status": "dashboard_refreshed", "counts": dashboard["counts"]}


def refresh_after_station(station_id: str | None = None, data_version: str | None = None, output: Dict[str, Any] | None = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {"version": FRONTEND_READ_MODEL_VERSION, "stationId": station_id, "dataVersion": data_version, "updates": []}
    if station_id in {"product_signal_snapshot_station", "task_signal_station"}:
        result["updates"].append(refresh_product_views(data_version=data_version))
    if station_id in {"task_pool_station", "task_snapshot_station"}:
        result["updates"].append(refresh_task_views())
    if station_id in {"agent_judgment_station", "rag_context_station", "station_queue"}:
        result["updates"].append(refresh_dashboard_view())
    if not result["updates"]:
        result["updates"].append(refresh_dashboard_view())
    return result


def read_dashboard_view() -> Dict[str, Any]:
    ensure_frontend_read_model_tables()
    with connect() as conn:
        row = conn.execute("SELECT payload, updated_at FROM frontend_dashboard_view WHERE view_key = 'main'").fetchone()
    if not row:
        return {"version": FRONTEND_READ_MODEL_VERSION, "ready": False, "topTasks": [], "counts": {}, "rule": "No cached dashboard view yet. Worker or manual refresh must build read model."}
    return {**loads(row["payload"]), "ready": True, "cachedAt": row["updated_at"]}


def read_product_views(store_id: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_frontend_read_model_tables()
    where = "WHERE store_id = ?" if store_id else ""
    params: List[Any] = [store_id] if store_id else []
    with connect() as conn:
        rows = conn.execute(f"SELECT payload, updated_at FROM frontend_product_view {where} ORDER BY updated_at DESC LIMIT ?", (*params, limit)).fetchall()
    items = [loads(row["payload"]) for row in rows]
    return {"version": FRONTEND_READ_MODEL_VERSION, "ready": bool(rows), "count": len(items), "items": items, "rule": "Read-only cached product view."}


def read_product_detail(product_id: str, store_id: str | None = None) -> Dict[str, Any]:
    ensure_frontend_read_model_tables()
    with connect() as conn:
        if store_id:
            row = conn.execute("SELECT payload, updated_at FROM frontend_product_view WHERE product_id = ? AND store_id = ? ORDER BY updated_at DESC LIMIT 1", (product_id, store_id)).fetchone()
        else:
            row = conn.execute("SELECT payload, updated_at FROM frontend_product_view WHERE product_id = ? ORDER BY updated_at DESC LIMIT 1", (product_id,)).fetchone()
    return {"version": FRONTEND_READ_MODEL_VERSION, "ready": bool(row), "item": loads(row["payload"]) if row else None, "cachedAt": row["updated_at"] if row else None}


def read_task_views(status: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_frontend_read_model_tables()
    where = "WHERE status = ?" if status else ""
    params: List[Any] = [status] if status else []
    with connect() as conn:
        rows = conn.execute(f"SELECT payload, updated_at FROM frontend_task_view {where} ORDER BY updated_at DESC LIMIT ?", (*params, limit)).fetchall()
    items = [loads(row["payload"]) for row in rows]
    return {"version": FRONTEND_READ_MODEL_VERSION, "ready": bool(rows), "count": len(items), "items": items, "rule": "Read-only cached task list view."}


def read_task_detail(task_id: str) -> Dict[str, Any]:
    ensure_frontend_read_model_tables()
    with connect() as conn:
        row = conn.execute("SELECT payload, updated_at FROM frontend_task_detail_view WHERE task_id = ?", (task_id,)).fetchone()
    return {"version": FRONTEND_READ_MODEL_VERSION, "ready": bool(row), "item": loads(row["payload"]) if row else None, "cachedAt": row["updated_at"] if row else None}


def read_system_status_view() -> Dict[str, Any]:
    ensure_frontend_read_model_tables()
    with connect() as conn:
        row = conn.execute("SELECT payload, updated_at FROM frontend_system_status_view WHERE view_key = 'main'").fetchone()
    return {"version": FRONTEND_READ_MODEL_VERSION, "ready": bool(row), "item": loads(row["payload"]) if row else None, "cachedAt": row["updated_at"] if row else None}


def refresh_all_read_models(data_version: str | None = None) -> Dict[str, Any]:
    return {"version": FRONTEND_READ_MODEL_VERSION, "product": refresh_product_views(data_version=data_version), "task": refresh_task_views(), "dashboard": refresh_dashboard_view(), "rule": "Manual read-model refresh is an explicit compute endpoint; normal GET /api/view/* remains read-only."}
