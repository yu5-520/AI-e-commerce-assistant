"""V3 report-driven alert service.

This module upgrades the demo from static module data to a data-version driven
warning loop:

    report import -> data snapshot -> alert event -> task bridge -> global sync

The implementation intentionally stays stdlib-only and reuses the existing
SQLite file plus the V2.5 task lifecycle service. It does not call marketplace
APIs and does not perform platform-side actions.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.data_import_service import DATASET_CONFIGS, read_csv
from src.services.module_data_service import PRODUCTS
from src.services.module_task_service import create_task_from_warning

V3_VERSION = "3.0.0"
PRIORITY_RANK = {"高": 1, "中": 2, "低": 3}
ACTIVE_ALERT_STATUSES = {"new", "task_created", "task_merged", "task_linked"}


PRODUCT_INDEX = {item["id"]: item for item in PRODUCTS}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_v3_tables() -> None:
    """Create V3 persistence tables without touching existing V2 tables."""
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS data_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                import_id TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                data_version TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_snapshots (
                metric_id TEXT PRIMARY KEY,
                snapshot_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                entity_type TEXT,
                entity_id TEXT,
                store_id TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_events (
                alert_id TEXT PRIMARY KEY,
                snapshot_id TEXT NOT NULL,
                import_id TEXT NOT NULL,
                data_version TEXT NOT NULL,
                source_dataset TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                risk_domain TEXT NOT NULL,
                priority TEXT NOT NULL,
                evidence TEXT,
                status TEXT NOT NULL,
                task_id TEXT,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_data_snapshots_version ON data_snapshots(data_version)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_data_snapshots_dataset ON data_snapshots(dataset_name, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metric_snapshots_entity ON metric_snapshots(entity_type, entity_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_events_entity ON alert_events(entity_type, entity_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_events_status ON alert_events(status, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_events_task ON alert_events(task_id)")
        conn.commit()


def _normalize_dataset_name(dataset_name: str | None) -> str:
    value = (dataset_name or "").strip().lower().replace("-", "_")
    aliases = {
        "order": "orders",
        "refund": "refunds",
        "product": "products",
        "stock": "inventory",
        "stocks": "inventory",
        "customer": "customers",
    }
    value = aliases.get(value, value)
    if value not in DATASET_CONFIGS:
        raise ValueError(f"Unsupported dataset_name: {dataset_name}")
    return value


def _as_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    text = str(value).replace(",", "").replace("%", "").replace("¥", "").strip()
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    number = _as_float(value)
    return int(number) if number is not None else default


def _pick(row: Dict[str, Any], *fields: str, default: Any = None) -> Any:
    for field in fields:
        if row.get(field) not in {None, ""}:
            return row.get(field)
    return default


def _rows_from_payload(rows: Any) -> List[Dict[str, Any]]:
    if not rows:
        return []
    if not isinstance(rows, list):
        raise ValueError("rows must be a list of objects")
    normalized: List[Dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized.append({str(key): value for key, value in row.items()})
    return normalized


def _product_context(product_id: str) -> Dict[str, Any]:
    product = PRODUCT_INDEX.get(product_id, {})
    return {
        "productId": product_id,
        "productShort": product.get("shortName") or product_id,
        "productTitle": product.get("title") or f"报表商品 {product_id}",
        "title": product.get("title") or f"报表商品 {product_id}",
        "platform": product.get("platform") or "报表导入",
        "store": product.get("store") or "报表导入店铺",
        "imageLabel": product.get("imageLabel") or "表",
        "link": product.get("link") or "",
    }


def _alert(
    *,
    snapshot_id: str,
    import_id: str,
    data_version: str,
    source_dataset: str,
    entity_type: str,
    entity_id: str,
    alert_type: str,
    risk_domain: str,
    priority: str,
    evidence: List[Dict[str, Any]],
    suggestion: str,
    task_signal: str,
) -> Dict[str, Any]:
    created_at = now_iso()
    return {
        "alertId": make_id("ALERT"),
        "snapshotId": snapshot_id,
        "importId": import_id,
        "dataVersion": data_version,
        "sourceDataset": source_dataset,
        "entityType": entity_type,
        "entityId": entity_id,
        "alertType": alert_type,
        "riskDomain": risk_domain,
        "priority": priority,
        "evidence": evidence,
        "suggestion": suggestion,
        "taskSignal": task_signal,
        "status": "new",
        "taskId": None,
        "createdAt": created_at,
        "updatedAt": created_at,
    }


def _save_snapshot(snapshot: Dict[str, Any]) -> None:
    ensure_v3_tables()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO data_snapshots (
                snapshot_id, import_id, dataset_name, data_version,
                row_count, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot["snapshotId"],
                snapshot["importId"],
                snapshot["datasetName"],
                snapshot["dataVersion"],
                snapshot["rowCount"],
                dumps(snapshot),
                snapshot["createdAt"],
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO metric_snapshots (
                metric_id, snapshot_id, metric_name, metric_value,
                entity_type, entity_id, store_id, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                make_id("METRIC"),
                snapshot["snapshotId"],
                f"{snapshot['datasetName']}_row_count",
                snapshot["rowCount"],
                "dataset",
                snapshot["datasetName"],
                None,
                dumps({"dataVersion": snapshot["dataVersion"]}),
                snapshot["createdAt"],
            ),
        )
        conn.commit()


def _save_alert_event(alert: Dict[str, Any]) -> None:
    ensure_v3_tables()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO alert_events (
                alert_id, snapshot_id, import_id, data_version, source_dataset,
                entity_type, entity_id, alert_type, risk_domain, priority,
                evidence, status, task_id, payload, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert["alertId"],
                alert["snapshotId"],
                alert["importId"],
                alert["dataVersion"],
                alert["sourceDataset"],
                alert["entityType"],
                alert["entityId"],
                alert["alertType"],
                alert["riskDomain"],
                alert["priority"],
                dumps({"items": alert.get("evidence", [])}),
                alert.get("status") or "new",
                alert.get("taskId"),
                dumps(alert),
                alert["createdAt"],
                alert.get("updatedAt") or now_iso(),
            ),
        )
        conn.commit()


def _update_alert_task(alert: Dict[str, Any], task_result: Dict[str, Any]) -> Dict[str, Any]:
    alert = deepcopy(alert)
    alert["taskId"] = task_result.get("id")
    alert["taskStatus"] = task_result.get("status")
    alert["taskWorkflowStatus"] = task_result.get("workflowStatus")
    alert["dedupeHit"] = bool(task_result.get("dedupeHit"))
    alert["status"] = "task_merged" if task_result.get("dedupeHit") else "task_created"
    alert["updatedAt"] = now_iso()
    _save_alert_event(alert)
    return alert


def _task_payload_from_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    context = _product_context(alert["entityId"]) if alert["entityType"] == "商品" else {}
    priority = alert.get("priority") or "中"
    task_layer = "finance_check" if alert.get("riskDomain") in {"报表", "价格", "利润", "财务"} else "operator_execution"
    return {
        **context,
        "entityType": alert["entityType"],
        "entityId": alert["entityId"],
        "riskDomain": alert["riskDomain"],
        "actionType": "导入" if alert["riskDomain"] == "报表" else "复查",
        "sourceType": "系统预警",
        "sourceModule": "报表预警中心",
        "source": "报表触发",
        "sourceRoute": "data-check",
        "taskLayer": task_layer,
        "priority": priority,
        "priorityLevel": "danger" if priority == "高" else "warning" if priority == "中" else "good",
        "deadline": "今天内" if priority == "高" else "明天前",
        "taskType": alert["alertType"],
        "taskSignal": alert.get("taskSignal") or "报表异常",
        "task": alert.get("suggestion") or "查看报表预警详情并完成处理。",
        "reason": _evidence_summary(alert),
        "judgmentTags": [alert["sourceDataset"], alert["riskDomain"], alert["priority"], alert["dataVersion"]],
        "evidence": alert.get("evidence", []),
        "sourceEvent": alert["alertId"],
        "sourceTrail": ["报表导入", alert["sourceDataset"], alert["dataVersion"]],
        "reportDataVersion": alert["dataVersion"],
        "alertId": alert["alertId"],
        "agentJudgment": {
            "status": "rule_based_v3",
            "summary": "V3.0 先用可解释规则识别报表异常，后续 Agent 只补充评估报告，不直接改价、改库存或调预算。",
        },
    }


def _evidence_summary(alert: Dict[str, Any]) -> str:
    pieces = []
    for item in alert.get("evidence", [])[:4]:
        label = item.get("label") or "证据"
        value = item.get("value") or item.get("text") or ""
        pieces.append(f"{label}：{value}")
    return "；".join(pieces) or alert.get("suggestion") or "报表导入后触发经营预警。"


def _inventory_alerts(rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for row in rows:
        product_id = str(_pick(row, "product_id", "商品ID", "sku", "SKU", default="")).strip()
        if not product_id:
            continue
        current = _as_float(_pick(row, "available_stock", "current_stock", "stock", "库存", "可用库存"))
        safety = _as_float(_pick(row, "safety_stock", "安全库存"))
        if current is None or safety is None:
            continue
        if current <= safety:
            priority = "高" if current < safety else "中"
            alerts.append(
                _alert(
                    snapshot_id=snapshot["snapshotId"],
                    import_id=snapshot["importId"],
                    data_version=snapshot["dataVersion"],
                    source_dataset="inventory",
                    entity_type="商品",
                    entity_id=product_id,
                    alert_type="库存不足预警",
                    risk_domain="库存",
                    priority=priority,
                    evidence=[
                        {"label": "当前库存", "value": str(current)},
                        {"label": "安全库存", "value": str(safety)},
                        {"label": "来源版本", "value": snapshot["dataVersion"]},
                    ],
                    suggestion="确认补货周期，再决定是否继续活动流量。",
                    task_signal="库存低于安全线",
                )
            )
    return alerts


def _refund_alerts(rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "amount": 0.0, "reasons": []})
    for row in rows:
        product_id = str(_pick(row, "product_id", "商品ID", default="")).strip()
        if not product_id:
            continue
        grouped[product_id]["count"] += 1
        grouped[product_id]["amount"] += _as_float(_pick(row, "refund_amount", "退款金额", default=0), 0) or 0
        reason = _pick(row, "refund_reason", "退款原因", default="未填写")
        grouped[product_id]["reasons"].append(str(reason))

    alerts: List[Dict[str, Any]] = []
    for product_id, stat in grouped.items():
        reason_counts: Dict[str, int] = defaultdict(int)
        for reason in stat["reasons"]:
            reason_counts[reason] += 1
        top_reason = sorted(reason_counts.items(), key=lambda item: item[1], reverse=True)[0][0]
        priority = "高" if stat["count"] >= 2 or stat["amount"] >= 100 else "中"
        alerts.append(
            _alert(
                snapshot_id=snapshot["snapshotId"],
                import_id=snapshot["importId"],
                data_version=snapshot["dataVersion"],
                source_dataset="refunds",
                entity_type="商品",
                entity_id=product_id,
                alert_type="退款异常预警",
                risk_domain="售后",
                priority=priority,
                evidence=[
                    {"label": "退款记录数", "value": str(stat["count"])},
                    {"label": "退款金额", "value": f"¥{stat['amount']:.2f}"},
                    {"label": "高频原因", "value": top_reason},
                    {"label": "来源版本", "value": snapshot["dataVersion"]},
                ],
                suggestion="复查售后原因、商品承诺和客服话术，售后归因完成前不继续放量。",
                task_signal="退款异常",
            )
        )
    return alerts


def _order_alerts(rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"orders": 0, "quantity": 0, "paid": 0.0})
    for row in rows:
        product_id = str(_pick(row, "product_id", "商品ID", default="")).strip()
        if not product_id:
            continue
        grouped[product_id]["orders"] += 1
        grouped[product_id]["quantity"] += _as_int(_pick(row, "quantity", "数量", default=1), 1)
        grouped[product_id]["paid"] += _as_float(_pick(row, "actual_paid", "order_amount", "实付金额", "订单金额", default=0), 0) or 0

    alerts: List[Dict[str, Any]] = []
    for product_id, stat in grouped.items():
        if stat["orders"] < 2 and stat["quantity"] < 5 and stat["paid"] < 100:
            continue
        priority = "中" if stat["paid"] < 300 else "高"
        alerts.append(
            _alert(
                snapshot_id=snapshot["snapshotId"],
                import_id=snapshot["importId"],
                data_version=snapshot["dataVersion"],
                source_dataset="orders",
                entity_type="商品",
                entity_id=product_id,
                alert_type="订单激增预警",
                risk_domain="流量",
                priority=priority,
                evidence=[
                    {"label": "订单数", "value": str(stat["orders"])},
                    {"label": "件数", "value": str(stat["quantity"])},
                    {"label": "实付金额", "value": f"¥{stat['paid']:.2f}"},
                    {"label": "来源版本", "value": snapshot["dataVersion"]},
                ],
                suggestion="确认库存、退款率和客服承接，再决定是否继续放量。",
                task_signal="订单短期放大",
            )
        )
    return alerts


def _product_alerts(rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for row in rows:
        product_id = str(_pick(row, "product_id", "商品ID", default="")).strip()
        if not product_id:
            continue
        stock = _as_float(_pick(row, "stock", "库存"))
        sale_price = _as_float(_pick(row, "sale_price", "售价"))
        cost_price = _as_float(_pick(row, "cost_price", "成本"))
        if stock is not None and stock <= 50:
            alerts.append(
                _alert(
                    snapshot_id=snapshot["snapshotId"],
                    import_id=snapshot["importId"],
                    data_version=snapshot["dataVersion"],
                    source_dataset="products",
                    entity_type="商品",
                    entity_id=product_id,
                    alert_type="商品库存预警",
                    risk_domain="库存",
                    priority="中",
                    evidence=[
                        {"label": "商品库存", "value": str(stock)},
                        {"label": "来源版本", "value": snapshot["dataVersion"]},
                    ],
                    suggestion="商品库存接近低位，先确认补货周期和主推节奏。",
                    task_signal="商品库存偏低",
                )
            )
        if sale_price is not None and cost_price is not None and sale_price > 0:
            margin = (sale_price - cost_price) / sale_price
            if margin < 0.2:
                alerts.append(
                    _alert(
                        snapshot_id=snapshot["snapshotId"],
                        import_id=snapshot["importId"],
                        data_version=snapshot["dataVersion"],
                        source_dataset="products",
                        entity_type="商品",
                        entity_id=product_id,
                        alert_type="毛利异常预警",
                        risk_domain="价格",
                        priority="高",
                        evidence=[
                            {"label": "售价", "value": str(sale_price)},
                            {"label": "成本", "value": str(cost_price)},
                            {"label": "毛利率", "value": f"{margin:.1%}"},
                            {"label": "来源版本", "value": snapshot["dataVersion"]},
                        ],
                        suggestion="复核活动价、成本和投放预算，避免低毛利继续放大。",
                        task_signal="毛利低于安全线",
                    )
                )
    return alerts


def _customer_alerts(rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for row in rows:
        customer_id = str(_pick(row, "customer_id", "客户ID", default="")).strip()
        if not customer_id:
            continue
        refund_count = _as_int(_pick(row, "refund_count", "退款次数", default=0), 0)
        total_orders = _as_int(_pick(row, "total_orders", "订单数", default=0), 0)
        if refund_count >= 2:
            alerts.append(
                _alert(
                    snapshot_id=snapshot["snapshotId"],
                    import_id=snapshot["importId"],
                    data_version=snapshot["dataVersion"],
                    source_dataset="customers",
                    entity_type="客户",
                    entity_id=customer_id,
                    alert_type="客户售后敏感预警",
                    risk_domain="售后",
                    priority="中",
                    evidence=[
                        {"label": "订单数", "value": str(total_orders)},
                        {"label": "退款次数", "value": str(refund_count)},
                        {"label": "来源版本", "value": snapshot["dataVersion"]},
                    ],
                    suggestion="标记售后敏感客户，后续客服处理需要人工复核话术。",
                    task_signal="客户退款偏高",
                )
            )
    return alerts


def generate_alerts(dataset_name: str, rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    builders = {
        "inventory": _inventory_alerts,
        "refunds": _refund_alerts,
        "orders": _order_alerts,
        "products": _product_alerts,
        "customers": _customer_alerts,
    }
    builder = builders.get(dataset_name)
    return builder(rows, snapshot) if builder else []


def import_report_dataset(
    dataset_name: str,
    rows: List[Dict[str, Any]] | None = None,
    *,
    auto_create_tasks: bool = True,
) -> Dict[str, Any]:
    """Import one dataset, persist a versioned snapshot, create alert tasks."""
    normalized_name = _normalize_dataset_name(dataset_name)
    dataset_rows = _rows_from_payload(rows) if rows is not None else read_csv(str(DATASET_CONFIGS[normalized_name]["filename"]))
    created_at = now_iso()
    import_id = make_id("IMPORT")
    snapshot_id = make_id("SNAP")
    data_version = f"DV_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{normalized_name.upper()}"
    snapshot = {
        "snapshotId": snapshot_id,
        "importId": import_id,
        "datasetName": normalized_name,
        "dataVersion": data_version,
        "rowCount": len(dataset_rows),
        "createdAt": created_at,
        "mode": "report_rows" if rows is not None else "mock_csv_v3",
        "sampleRows": dataset_rows[:20],
        "version": V3_VERSION,
    }
    _save_snapshot(snapshot)

    alerts = generate_alerts(normalized_name, dataset_rows, snapshot)
    synced_alerts: List[Dict[str, Any]] = []
    for alert in alerts:
        _save_alert_event(alert)
        if auto_create_tasks:
            task_result = create_task_from_warning(_task_payload_from_alert(alert))
            synced_alerts.append(_update_alert_task(alert, task_result))
        else:
            synced_alerts.append(alert)

    return {
        "version": V3_VERSION,
        "importId": import_id,
        "snapshotId": snapshot_id,
        "dataVersion": data_version,
        "datasetName": normalized_name,
        "rowCount": len(dataset_rows),
        "alertCount": len(synced_alerts),
        "createdTaskCount": len([item for item in synced_alerts if item.get("taskId")]),
        "alerts": synced_alerts,
        "globalSync": ["dashboard", "product", "traffic", "report", "todo", "log", "task_report"],
    }


def run_v3_mock_imports(dataset_names: Iterable[str] | None = None) -> Dict[str, Any]:
    selected = list(dataset_names or ["inventory", "refunds", "orders", "products"])
    results = [import_report_dataset(name, rows=None, auto_create_tasks=True) for name in selected]
    return {
        "version": V3_VERSION,
        "mode": "mock_alerts_global_refresh",
        "datasetCount": len(results),
        "alertCount": sum(item.get("alertCount", 0) for item in results),
        "createdTaskCount": sum(item.get("createdTaskCount", 0) for item in results),
        "results": results,
        "summary": get_v3_dashboard_summary(),
    }


def _row_to_alert(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    if payload:
        return payload
    return {
        "alertId": row["alert_id"],
        "snapshotId": row["snapshot_id"],
        "importId": row["import_id"],
        "dataVersion": row["data_version"],
        "sourceDataset": row["source_dataset"],
        "entityType": row["entity_type"],
        "entityId": row["entity_id"],
        "alertType": row["alert_type"],
        "riskDomain": row["risk_domain"],
        "priority": row["priority"],
        "evidence": loads(row["evidence"]).get("items", []),
        "status": row["status"],
        "taskId": row["task_id"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def list_alert_events(limit: int = 50, *, active_only: bool = False) -> List[Dict[str, Any]]:
    ensure_v3_tables()
    query = "SELECT * FROM alert_events"
    params: List[Any] = []
    if active_only:
        placeholders = ",".join("?" for _ in ACTIVE_ALERT_STATUSES)
        query += f" WHERE status IN ({placeholders})"
        params.extend(sorted(ACTIVE_ALERT_STATUSES))
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        return [_row_to_alert(row) for row in conn.execute(query, params).fetchall()]


def latest_data_version() -> Dict[str, Any] | None:
    ensure_v3_tables()
    with connect() as conn:
        row = conn.execute("SELECT * FROM data_snapshots ORDER BY created_at DESC LIMIT 1").fetchone()
    if not row:
        return None
    payload = loads(row["payload"])
    return payload or {
        "snapshotId": row["snapshot_id"],
        "importId": row["import_id"],
        "datasetName": row["dataset_name"],
        "dataVersion": row["data_version"],
        "rowCount": row["row_count"],
        "createdAt": row["created_at"],
    }


def list_data_versions(limit: int = 20) -> List[Dict[str, Any]]:
    ensure_v3_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM data_snapshots ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    versions: List[Dict[str, Any]] = []
    for row in rows:
        payload = loads(row["payload"])
        versions.append(
            payload
            or {
                "snapshotId": row["snapshot_id"],
                "importId": row["import_id"],
                "datasetName": row["dataset_name"],
                "dataVersion": row["data_version"],
                "rowCount": row["row_count"],
                "createdAt": row["created_at"],
            }
        )
    return versions


def list_alerts_for_entity(entity_type: str, entity_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    ensure_v3_tables()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM alert_events
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (entity_type, entity_id, limit),
        ).fetchall()
    return [_row_to_alert(row) for row in rows]


def attach_alert_state(item: Dict[str, Any], entity_type: str, entity_id: str) -> Dict[str, Any]:
    result = deepcopy(item)
    alerts = list_alerts_for_entity(entity_type, entity_id, limit=10)
    active_alerts = [alert for alert in alerts if alert.get("status") in ACTIVE_ALERT_STATUSES]
    result["alertState"] = {
        "activeAlertCount": len(active_alerts),
        "latestAlert": active_alerts[0] if active_alerts else alerts[0] if alerts else None,
        "highestPriority": sorted([alert.get("priority", "低") for alert in active_alerts], key=lambda value: PRIORITY_RANK.get(value, 9))[0] if active_alerts else None,
        "dataVersions": list(dict.fromkeys(alert.get("dataVersion") for alert in alerts if alert.get("dataVersion")))[:5],
        "alerts": active_alerts[:5],
    }
    return result


def find_alert_by_task_id(task_id: str | None) -> Dict[str, Any] | None:
    if not task_id:
        return None
    ensure_v3_tables()
    with connect() as conn:
        row = conn.execute("SELECT * FROM alert_events WHERE task_id = ? ORDER BY created_at DESC LIMIT 1", (task_id,)).fetchone()
    return _row_to_alert(row) if row else None


def get_v3_dashboard_summary() -> Dict[str, Any]:
    alerts = list_alert_events(limit=100)
    active = [item for item in alerts if item.get("status") in ACTIVE_ALERT_STATUSES]
    latest = latest_data_version()
    by_dataset: Dict[str, int] = defaultdict(int)
    by_risk: Dict[str, int] = defaultdict(int)
    for alert in active:
        by_dataset[alert.get("sourceDataset", "unknown")] += 1
        by_risk[alert.get("riskDomain", "通用")] += 1
    return {
        "version": V3_VERSION,
        "name": "准实时数据更新 + 报表触发预警",
        "dataRefreshMode": "report_upload_or_mock_import",
        "latestDataVersion": latest.get("dataVersion") if latest else None,
        "latestDatasetName": latest.get("datasetName") if latest else None,
        "latestSnapshotAt": latest.get("createdAt") if latest else None,
        "activeAlertCount": len(active),
        "totalAlertCount": len(alerts),
        "highPriorityAlertCount": len([item for item in active if item.get("priority") == "高"]),
        "taskLinkedAlertCount": len([item for item in active if item.get("taskId")]),
        "alertByDataset": dict(by_dataset),
        "alertByRiskDomain": dict(by_risk),
        "latestAlerts": active[:5],
        "globalSyncTargets": ["首页", "商品页", "流量页", "报表页", "待办", "日志", "详情报告"],
    }
