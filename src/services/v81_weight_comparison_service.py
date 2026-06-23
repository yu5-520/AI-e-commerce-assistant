"""V8.1 weight period comparison service.

V8.0 normalized product, store, and operator into weight metric snapshots.
V8.1 calculates period-over-period, multi-period average, volatility, and
available year-over-year comparisons. It only explains weight fluctuation and
still does not generate weight adjustment tasks.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import sqrt
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.v80_weight_snapshot_service import ensure_weight_snapshot_tables, generate_weight_snapshots, weight_snapshot_summary

V81_WEIGHT_COMPARISON_VERSION = "8.1.0"

METRIC_LABELS: Dict[str, str] = {
    "roi": "ROI",
    "traffic": "流量",
    "ctr": "点击率",
    "conversionRate": "转化率",
    "grossMargin": "毛利率",
    "stock": "库存",
    "refundRate": "售后率",
    "goodReviewRate": "好评率",
    "storeRoi": "店铺ROI",
    "naturalTraffic": "自然流量",
    "productHealthRate": "商品健康率",
    "productCount": "商品数量",
    "taskCompletionRate": "任务完成率",
    "onTimeRate": "准时率",
    "reviewQualityScore": "复盘质量分",
    "evidenceCompleteness": "证据完整度",
    "storeMaintenanceScore": "店铺维护分",
    "submittedTaskCount": "提交任务数",
    "assignedStoreCount": "负责店铺数",
}


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def ensure_weight_comparison_tables() -> None:
    ensure_weight_snapshot_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weight_metric_comparisons_v8 (
                comparison_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                metric_name TEXT NOT NULL,
                metric_label TEXT,
                comparison_type TEXT NOT NULL,
                current_value REAL,
                reference_value REAL,
                change_value REAL,
                change_rate REAL,
                direction TEXT,
                confidence TEXT,
                snapshot_version TEXT,
                reference_snapshot_version TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_comparisons_object_v8 ON weight_metric_comparisons_v8(tenant_id, org_id, object_type, object_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_comparisons_metric_v8 ON weight_metric_comparisons_v8(metric_name, comparison_type, direction)")
        conn.commit()


def _parse_snapshot_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _direction(change_rate: float | None) -> str:
    if change_rate is None:
        return "insufficient_reference"
    if abs(change_rate) < 0.03:
        return "stable"
    return "up" if change_rate > 0 else "down"


def _rate(current: float, reference: float | None) -> tuple[float | None, float | None]:
    if reference is None:
        return None, None
    change_value = current - reference
    if reference == 0:
        return change_value, None
    return change_value, change_value / abs(reference)


def _confidence(history_count: int, comparison_type: str) -> str:
    if comparison_type == "year_over_year" and history_count >= 1:
        return "medium"
    if history_count >= 3:
        return "high"
    if history_count >= 1:
        return "medium"
    return "low"


def _row_to_snapshot(row: Any) -> Dict[str, Any]:
    return {
        "snapshotId": row["snapshot_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "parentType": row["parent_type"],
        "parentId": row["parent_id"],
        "snapshotVersion": row["snapshot_version"],
        "snapshotAt": row["snapshot_at"],
        "metrics": loads(row["metrics"]),
        "dimensions": loads(row["dimensions"]),
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def _load_snapshots(ctx: UserContext, limit: int = 600) -> List[Dict[str, Any]]:
    ensure_weight_snapshot_tables()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_metric_snapshots_v8
            WHERE tenant_id = ? AND org_id = ?
            ORDER BY object_type ASC, object_id ASC, snapshot_at DESC
            LIMIT ?
            """,
            (ctx.tenant_id, ctx.org_id, limit),
        ).fetchall()
    return [_row_to_snapshot(row) for row in rows]


def _numeric_metric_keys(snapshot: Dict[str, Any]) -> List[str]:
    metrics = snapshot.get("metrics") or {}
    return [key for key, value in metrics.items() if _is_number(value)]


def _comparison_payload(item: Dict[str, Any], metric: str, comparison_type: str, current: float, reference: float | None, reference_snapshot: Dict[str, Any] | None, history_count: int, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    change_value, change_rate = _rate(current, reference)
    payload = {
        "comparisonId": make_id("WMC"),
        "tenantId": item["tenantId"],
        "orgId": item["orgId"],
        "objectType": item["objectType"],
        "objectId": item["objectId"],
        "objectName": item.get("objectName"),
        "metricName": metric,
        "metricLabel": METRIC_LABELS.get(metric, metric),
        "comparisonType": comparison_type,
        "currentValue": current,
        "referenceValue": reference,
        "changeValue": change_value,
        "changeRate": change_rate,
        "direction": _direction(change_rate),
        "confidence": _confidence(history_count, comparison_type),
        "snapshotVersion": item.get("snapshotVersion"),
        "referenceSnapshotVersion": (reference_snapshot or {}).get("snapshotVersion"),
        "payload": {
            "version": V81_WEIGHT_COMPARISON_VERSION,
            "snapshotAt": item.get("snapshotAt"),
            "referenceSnapshotAt": (reference_snapshot or {}).get("snapshotAt"),
            "dimension": item.get("dimensions") or {},
            "rule": "V8.1 只计算周期比较，不生成升降权任务。",
            **(extra or {}),
        },
        "createdAt": now_iso(),
    }
    return payload


def _insert_comparison(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO weight_metric_comparisons_v8 (
                comparison_id, tenant_id, org_id, object_type, object_id, object_name, metric_name, metric_label,
                comparison_type, current_value, reference_value, change_value, change_rate, direction, confidence,
                snapshot_version, reference_snapshot_version, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["comparisonId"], item["tenantId"], item["orgId"], item["objectType"], item["objectId"], item.get("objectName"), item["metricName"], item.get("metricLabel"), item["comparisonType"], item.get("currentValue"), item.get("referenceValue"), item.get("changeValue"), item.get("changeRate"), item.get("direction"), item.get("confidence"), item.get("snapshotVersion"), item.get("referenceSnapshotVersion"), dumps(item.get("payload") or {}), item["createdAt"]),
        )
        conn.commit()


def _find_yoy_reference(latest: Dict[str, Any], history: List[Dict[str, Any]], metric: str) -> Dict[str, Any] | None:
    latest_time = _parse_snapshot_time(latest.get("snapshotAt"))
    if not latest_time:
        return None
    candidates: List[tuple[float, Dict[str, Any]]] = []
    for item in history:
        metrics = item.get("metrics") or {}
        if not _is_number(metrics.get(metric)):
            continue
        ref_time = _parse_snapshot_time(item.get("snapshotAt"))
        if not ref_time:
            continue
        day_gap = abs((latest_time - ref_time).days - 365)
        if day_gap <= 45:
            candidates.append((day_gap, item))
    candidates.sort(key=lambda pair: pair[0])
    return candidates[0][1] if candidates else None


def _stddev(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return sqrt(variance)


def generate_weight_comparisons(ctx: UserContext) -> Dict[str, Any]:
    ensure_weight_comparison_tables()
    snapshots = _load_snapshots(ctx)
    if not snapshots:
        generate_weight_snapshots(ctx)
        snapshots = _load_snapshots(ctx)
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in snapshots:
        grouped[f"{item['objectType']}::{item['objectId']}"].append(item)
    created: List[Dict[str, Any]] = []
    for group_items in grouped.values():
        group_items.sort(key=lambda item: item.get("snapshotAt") or "", reverse=True)
        latest = group_items[0]
        history = group_items[1:]
        previous = history[0] if history else None
        for metric in _numeric_metric_keys(latest):
            current = float(latest["metrics"][metric])
            if previous and _is_number((previous.get("metrics") or {}).get(metric)):
                created.append(_comparison_payload(latest, metric, "period_over_period", current, float(previous["metrics"][metric]), previous, len(history), {"displayName": "环比 / 本次对上次"}))
            metric_history = [float(item["metrics"][metric]) for item in history[:3] if _is_number((item.get("metrics") or {}).get(metric))]
            if metric_history:
                reference_average = sum(metric_history) / len(metric_history)
                created.append(_comparison_payload(latest, metric, "multi_period_average", current, reference_average, history[0], len(metric_history), {"displayName": "多周期均值", "sampleCount": len(metric_history)}))
            volatility_values = [current] + metric_history
            if len(volatility_values) >= 2:
                mean = sum(volatility_values) / len(volatility_values)
                volatility = _stddev(volatility_values) / abs(mean) if mean else 0.0
                created.append(_comparison_payload(latest, metric, "volatility", current, volatility, history[0] if history else None, len(volatility_values), {"displayName": "波动率", "sampleCount": len(volatility_values), "volatility": volatility}))
            yoy_ref = _find_yoy_reference(latest, history, metric)
            if yoy_ref:
                created.append(_comparison_payload(latest, metric, "year_over_year", current, float(yoy_ref["metrics"][metric]), yoy_ref, 1, {"displayName": "同比 / 年度周期"}))
    for item in created:
        _insert_comparison(item)
    counts: Dict[str, int] = defaultdict(int)
    by_direction: Dict[str, int] = defaultdict(int)
    for item in created:
        counts[item["comparisonType"]] += 1
        by_direction[item["direction"]] += 1
    return {"version": V81_WEIGHT_COMPARISON_VERSION, "createdCount": len(created), "byComparisonType": dict(counts), "byDirection": dict(by_direction), "comparisons": created, "rule": "V8.1 只解释权重指标波动，不生成升降权和交叉任务。"}


def _row_to_comparison(row: Any) -> Dict[str, Any]:
    return {
        "comparisonId": row["comparison_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "metricName": row["metric_name"],
        "metricLabel": row["metric_label"],
        "comparisonType": row["comparison_type"],
        "currentValue": row["current_value"],
        "referenceValue": row["reference_value"],
        "changeValue": row["change_value"],
        "changeRate": row["change_rate"],
        "direction": row["direction"],
        "confidence": row["confidence"],
        "snapshotVersion": row["snapshot_version"],
        "referenceSnapshotVersion": row["reference_snapshot_version"],
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def weight_comparison_summary(ctx: UserContext, object_type: str | None = None, comparison_type: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_weight_comparison_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if object_type in {"product", "store", "operator"}:
        filters.append("object_type = ?")
        params.append(object_type)
    if comparison_type in {"period_over_period", "multi_period_average", "volatility", "year_over_year"}:
        filters.append("comparison_type = ?")
        params.append(comparison_type)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM weight_metric_comparisons_v8 WHERE {' AND '.join(filters)} ORDER BY created_at DESC LIMIT ?", tuple(params)).fetchall()
    comparisons = [_row_to_comparison(row) for row in rows]
    by_type: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    by_direction: Dict[str, int] = defaultdict(int)
    for item in comparisons:
        by_type[item["comparisonType"]] += 1
        by_object[item["objectType"]] += 1
        by_direction[item["direction"]] += 1
    return {
        "version": V81_WEIGHT_COMPARISON_VERSION,
        "tenantId": ctx.tenant_id,
        "orgId": ctx.org_id,
        "roleId": ctx.role_id,
        "comparisonCount": len(comparisons),
        "byComparisonType": dict(by_type),
        "byObjectType": dict(by_object),
        "byDirection": dict(by_direction),
        "comparisons": comparisons,
        "snapshotSummary": weight_snapshot_summary(ctx, limit=30),
        "rule": "V8.1 计算环比、多周期均值、波动率和可用同比；V8.2 才接 RAG 标准线。",
    }
