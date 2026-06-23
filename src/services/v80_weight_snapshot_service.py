"""V8.0 weight metric snapshot foundation.

V6-V7 focus on growth trend tasks and SaaS governance. V8 starts the weight-data
fluctuation task system. V8.0 only builds the foundation: product, store, and
operator are normalized into weight metric snapshots. No weight adjustment task
is generated in V8.0.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.account_service import list_store_assignments, list_stores, list_users
from src.services import module_task_service
from src.services.trend_signal_service import ensure_trend_tables

V80_WEIGHT_VERSION = "8.0.0"

WEIGHT_OBJECT_TYPES = ["product", "store", "operator"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_weight_snapshot_tables() -> None:
    ensure_trend_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weight_metric_snapshots_v8 (
                snapshot_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                parent_type TEXT,
                parent_id TEXT,
                snapshot_version TEXT NOT NULL,
                snapshot_at TEXT NOT NULL,
                metrics TEXT,
                dimensions TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_snapshots_object_v8 ON weight_metric_snapshots_v8(tenant_id, org_id, object_type, object_id, snapshot_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_snapshots_parent_v8 ON weight_metric_snapshots_v8(parent_type, parent_id, snapshot_at)")
        conn.commit()


def _latest_product_snapshots() -> List[Dict[str, Any]]:
    ensure_trend_tables()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT ps.*, pm.title, pm.store_name, pm.platform, pm.category
            FROM product_snapshots_v6 ps
            LEFT JOIN product_master_v6 pm ON pm.product_id = ps.product_id
            WHERE ps.snapshot_at = (
                SELECT MAX(inner_ps.snapshot_at)
                FROM product_snapshots_v6 inner_ps
                WHERE inner_ps.product_id = ps.product_id
                  AND COALESCE(inner_ps.store_id, '') = COALESCE(ps.store_id, '')
            )
            ORDER BY ps.snapshot_at DESC
            LIMIT 80
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _metric(row: Dict[str, Any], key: str, default: float = 0.0) -> float:
    metrics = loads(row.get("metrics")) if isinstance(row.get("metrics"), str) else row.get("metrics") or {}
    return _float(metrics.get(key), default)


def _demo_product_rows(stores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    templates = [
        ("P-DEMO-001", "主推收纳箱", 2.8, 14800, 0.051, 0.082, 0.34, 620, 0.018, 0.965),
        ("P-DEMO-002", "厨房置物架", 1.3, 8600, 0.035, 0.044, 0.22, 1140, 0.041, 0.925),
        ("P-DEMO-003", "清洁湿巾组合", 3.4, 19600, 0.062, 0.096, 0.39, 360, 0.014, 0.981),
        ("P-DEMO-004", "测试款衣物架", 0.9, 3200, 0.025, 0.031, 0.18, 720, 0.052, 0.902),
    ]
    for index, item in enumerate(templates):
        store = stores[index % max(len(stores), 1)] if stores else {"id": "S000", "name": "演示店铺", "platform": "演示平台"}
        product_id, title, roi, traffic, ctr, cvr, margin, stock, refund, good = item
        rows.append({"product_id": product_id, "store_id": store.get("id"), "title": title, "store_name": store.get("name"), "platform": store.get("platform"), "category": "演示类目", "metrics": dumps({"roi": roi, "traffic": traffic, "ctr": ctr, "conversion_rate": cvr, "gross_margin": margin, "stock": stock, "refund_rate": refund, "good_review_rate": good}), "snapshot_at": now_iso(), "data_version": "demo-v8"})
    return rows


def _product_snapshot_payload(row: Dict[str, Any], ctx: UserContext, snapshot_version: str, created_at: str) -> Dict[str, Any]:
    metrics = {
        "roi": _metric(row, "roi"),
        "traffic": _metric(row, "traffic"),
        "ctr": _metric(row, "ctr"),
        "conversionRate": _metric(row, "conversion_rate"),
        "grossMargin": _metric(row, "gross_margin"),
        "stock": _metric(row, "stock"),
        "refundRate": _metric(row, "refund_rate"),
        "goodReviewRate": _metric(row, "good_review_rate"),
    }
    dimensions = {"platform": row.get("platform"), "category": row.get("category"), "storeName": row.get("store_name"), "weightScope": "product"}
    return {"snapshotId": make_id("WMS"), "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "objectType": "product", "objectId": row.get("product_id"), "objectName": row.get("title") or row.get("product_id"), "parentType": "store", "parentId": row.get("store_id") or "unknown", "snapshotVersion": snapshot_version, "snapshotAt": row.get("snapshot_at") or created_at, "metrics": metrics, "dimensions": dimensions, "payload": {"source": "product_snapshots_v6", "rule": "V8.0 商品权重快照只记录指标，不生成升降权任务。"}, "createdAt": created_at}


def _store_role_tag(store: Dict[str, Any], index: int) -> str:
    name = store.get("name") or ""
    if "主店" in name:
        return "brand_main_store"
    if index == 0:
        return "profit_core_store"
    if index == 1:
        return "growth_store"
    if index == 2:
        return "test_store"
    return "low_weight_store"


def _store_snapshots(product_snapshots: List[Dict[str, Any]], ctx: UserContext, snapshot_version: str, created_at: str) -> List[Dict[str, Any]]:
    stores = list_stores()
    by_store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in product_snapshots:
        by_store[item.get("parentId") or "unknown"].append(item)
    result: List[Dict[str, Any]] = []
    for index, store in enumerate(stores):
        items = by_store.get(store.get("id"), [])
        count = len(items) or 1
        roi = sum(_float(item["metrics"].get("roi")) for item in items) / count if items else 1.0 + index * 0.4
        good = sum(_float(item["metrics"].get("goodReviewRate")) for item in items) / count if items else 0.92 + index * 0.01
        traffic = sum(_float(item["metrics"].get("traffic")) for item in items) if items else 3000 + index * 2200
        ctr = sum(_float(item["metrics"].get("ctr")) for item in items) / count if items else 0.03 + index * 0.005
        healthy = len([item for item in items if _float(item["metrics"].get("roi")) >= 1.5 and _float(item["metrics"].get("goodReviewRate")) >= 0.94])
        metrics = {"storeRoi": round(roi, 4), "goodReviewRate": round(good, 4), "naturalTraffic": traffic, "ctr": round(ctr, 4), "productHealthRate": round(healthy / max(len(items), 1), 4), "productCount": len(items)}
        dimensions = {"platform": store.get("platform"), "storeRoleTag": _store_role_tag(store, index), "weightScope": "store"}
        result.append({"snapshotId": make_id("WMS"), "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "objectType": "store", "objectId": store.get("id"), "objectName": store.get("name"), "parentType": "store_group", "parentId": store.get("groupId"), "snapshotVersion": snapshot_version, "snapshotAt": created_at, "metrics": metrics, "dimensions": dimensions, "payload": {"source": "account_service + product weight snapshots", "rule": "V8.0 店铺权重快照用于后续上下文权重修正。"}, "createdAt": created_at})
    return result


def _operator_snapshots(ctx: UserContext, snapshot_version: str, created_at: str) -> List[Dict[str, Any]]:
    users = [user for user in list_users() if user.get("roleId") == "operator"]
    assignments = list_store_assignments()
    tasks = module_task_service.list_tasks(active_only=False)
    result: List[Dict[str, Any]] = []
    for index, user in enumerate(users):
        user_tasks = [task for task in tasks if task.get("assigneeId") == user.get("id")]
        total = len(user_tasks)
        done = len([task for task in user_tasks if task.get("status") in module_task_service.DONE_STATUS])
        submitted = len([task for task in user_tasks if task.get("status") in {"已提交", "待复核", "已完成", "已通过"}])
        assigned_store_count = len([item for item in assignments if item.get("primaryOperatorId") == user.get("id")])
        metrics = {"taskCompletionRate": round(done / max(total, 1), 4) if total else 0.88 - index * 0.08, "onTimeRate": 0.9 - index * 0.05, "reviewQualityScore": 82 - index * 6, "evidenceCompleteness": 0.86 - index * 0.08, "storeMaintenanceScore": 80 - index * 4, "submittedTaskCount": submitted, "assignedStoreCount": assigned_store_count}
        dimensions = {"roleId": user.get("roleId"), "storeIds": user.get("storeIds") or [], "weightScope": "operator"}
        result.append({"snapshotId": make_id("WMS"), "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "objectType": "operator", "objectId": user.get("id"), "objectName": user.get("name"), "parentType": "store_group", "parentId": (user.get("storeGroupIds") or [ctx.org_id])[0], "snapshotVersion": snapshot_version, "snapshotAt": created_at, "metrics": metrics, "dimensions": dimensions, "payload": {"source": "tasks + account assignments", "rule": "V8.0 运营权重快照只做行为指标记录，不自动评价或处罚人。"}, "createdAt": created_at})
    return result


def _insert_snapshot(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO weight_metric_snapshots_v8 (
                snapshot_id, tenant_id, org_id, object_type, object_id, object_name, parent_type, parent_id,
                snapshot_version, snapshot_at, metrics, dimensions, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["snapshotId"], item["tenantId"], item["orgId"], item["objectType"], item["objectId"], item.get("objectName"), item.get("parentType"), item.get("parentId"), item["snapshotVersion"], item["snapshotAt"], dumps(item.get("metrics") or {}), dumps(item.get("dimensions") or {}), dumps(item.get("payload") or {}), item["createdAt"]),
        )
        conn.commit()


def generate_weight_snapshots(ctx: UserContext) -> Dict[str, Any]:
    ensure_weight_snapshot_tables()
    created_at = now_iso()
    snapshot_version = f"V8.0-{created_at}"
    stores = list_stores()
    product_rows = _latest_product_snapshots() or _demo_product_rows(stores)
    product_items = [_product_snapshot_payload(row, ctx, snapshot_version, created_at) for row in product_rows]
    store_items = _store_snapshots(product_items, ctx, snapshot_version, created_at)
    operator_items = _operator_snapshots(ctx, snapshot_version, created_at)
    all_items = product_items + store_items + operator_items
    for item in all_items:
        _insert_snapshot(item)
    counts: Dict[str, int] = defaultdict(int)
    for item in all_items:
        counts[item["objectType"]] += 1
    return {"version": V80_WEIGHT_VERSION, "snapshotVersion": snapshot_version, "createdCount": len(all_items), "counts": dict(counts), "snapshots": all_items, "rule": "V8.0 只建立权重指标快照层，不做环比、同比、联动、升降权和任务生成。"}


def _row_to_snapshot(row: Any) -> Dict[str, Any]:
    return {"snapshotId": row["snapshot_id"], "tenantId": row["tenant_id"], "orgId": row["org_id"], "objectType": row["object_type"], "objectId": row["object_id"], "objectName": row["object_name"], "parentType": row["parent_type"], "parentId": row["parent_id"], "snapshotVersion": row["snapshot_version"], "snapshotAt": row["snapshot_at"], "metrics": loads(row["metrics"]), "dimensions": loads(row["dimensions"]), "payload": loads(row["payload"]), "createdAt": row["created_at"]}


def weight_snapshot_summary(ctx: UserContext, object_type: str | None = None, limit: int = 120) -> Dict[str, Any]:
    ensure_weight_snapshot_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if object_type in WEIGHT_OBJECT_TYPES:
        filters.append("object_type = ?")
        params.append(object_type)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM weight_metric_snapshots_v8 WHERE {' AND '.join(filters)} ORDER BY snapshot_at DESC LIMIT ?", tuple(params)).fetchall()
    snapshots = [_row_to_snapshot(row) for row in rows]
    counts: Dict[str, int] = defaultdict(int)
    latest_version = None
    for item in snapshots:
        counts[item["objectType"]] += 1
        latest_version = latest_version or item.get("snapshotVersion")
    return {"version": V80_WEIGHT_VERSION, "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "roleId": ctx.role_id, "snapshotCount": len(snapshots), "latestSnapshotVersion": latest_version, "counts": dict(counts), "snapshots": snapshots, "objectTypes": WEIGHT_OBJECT_TYPES, "rule": "V8.0 权重中心先统一商品、店铺、运营三类对象的指标快照。"}
