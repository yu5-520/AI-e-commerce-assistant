"""Report-driven alert service with V11 MVP governance.

V11 changes the alert/task boundary:
- imported rows are always analyzed and persisted;
- product history is decided by product runtime id, not by upload count;
- low/medium risk is converted into product/store tags and observation alerts;
- only high-risk, high-time-sensitivity alerts enter the front-end task queue;
- task details can still cite alert evidence through task_id.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.account_service import current_user, list_stores, visible_store_ids_for_user
from src.services.data_import_service import DATASET_CONFIGS, read_csv
from src.services.module_data_service import PRODUCTS
from src.services.module_task_service import create_task_from_warning
from src.services.v11_mvp_governance_service import apply_alert_policy, process_report_import

V3_VERSION = "11.0.0"
PRIORITY_RANK = {"高": 1, "中": 2, "低": 3}
ACTIVE_ALERT_STATUSES = {"new", "task_created", "task_merged", "task_linked"}
PRODUCT_INDEX = {item["id"]: item for item in PRODUCTS}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_v3_tables() -> None:
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
                store_id TEXT,
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
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(alert_events)").fetchall()}
        if "store_id" not in columns:
            conn.execute("ALTER TABLE alert_events ADD COLUMN store_id TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_data_snapshots_version ON data_snapshots(data_version)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_events_entity ON alert_events(entity_type, entity_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_events_store ON alert_events(store_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_events_status ON alert_events(status, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_events_task ON alert_events(task_id)")
        conn.commit()


def _normalize_dataset_name(dataset_name: str | None) -> str:
    value = (dataset_name or "").strip().lower().replace("-", "_")
    aliases = {"order": "orders", "refund": "refunds", "product": "products", "stock": "inventory", "stocks": "inventory", "customer": "customers"}
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


def _as_rate(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    text = str(value).replace(",", "").replace("¥", "").strip()
    percent = text.endswith("%")
    text = text[:-1] if percent else text
    try:
        number = float(text)
    except (TypeError, ValueError):
        return default
    return number / 100 if percent else number


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
    return [{str(key): value for key, value in row.items()} for row in rows if isinstance(row, dict)]


def _store_index() -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for store in list_stores():
        mapping[store["id"]] = store
        mapping[store["name"]] = store
        mapping[f"{store.get('platform')} · {store.get('name')}"] = store
    return mapping


def _store_name(store_id: str | None) -> str | None:
    store = _store_index().get(store_id or "")
    return store.get("name") if store else None


def _store_platform(store_id: str | None) -> str | None:
    store = _store_index().get(store_id or "")
    return store.get("platform") if store else None


def _resolve_store_id(row: Dict[str, Any] | None = None, product_id: str | None = None) -> str | None:
    row = row or {}
    explicit = str(_pick(row, "store_id", "storeId", "店铺ID", "店铺id", "店铺编号", default="") or "").strip()
    if explicit and explicit in _store_index():
        return explicit
    product = PRODUCT_INDEX.get(str(product_id or ""), {})
    if product.get("storeId"):
        return product.get("storeId")
    store_name = str(_pick(row, "store_name", "store", "店铺", "店铺名称", default="") or "").strip()
    if store_name and store_name in _store_index():
        return _store_index()[store_name]["id"]
    return explicit or None


def _product_context(product_id: str, store_id: str | None = None) -> Dict[str, Any]:
    product = PRODUCT_INDEX.get(product_id, {})
    resolved_store = store_id or product.get("storeId")
    return {
        "productId": product_id,
        "productShort": product.get("shortName") or product_id,
        "productTitle": product.get("title") or f"报表商品 {product_id}",
        "title": product.get("title") or f"报表商品 {product_id}",
        "platform": _store_platform(resolved_store) or product.get("platform") or "报表导入",
        "store": _store_name(resolved_store) or product.get("store") or "报表导入店铺",
        "storeId": resolved_store,
        "imageLabel": product.get("imageLabel") or "表",
        "link": product.get("link") or "",
    }


def _alert(*, snapshot_id: str, import_id: str, data_version: str, source_dataset: str, entity_type: str, entity_id: str, alert_type: str, risk_domain: str, priority: str, evidence: List[Dict[str, Any]], suggestion: str, task_signal: str, store_id: str | None = None) -> Dict[str, Any]:
    created_at = now_iso()
    return {
        "alertId": make_id("ALERT"),
        "snapshotId": snapshot_id,
        "importId": import_id,
        "dataVersion": data_version,
        "sourceDataset": source_dataset,
        "entityType": entity_type,
        "entityId": entity_id,
        "storeId": store_id,
        "storeName": _store_name(store_id),
        "visibleStoreIds": [store_id] if store_id else [],
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
        conn.execute("INSERT OR REPLACE INTO data_snapshots (snapshot_id, import_id, dataset_name, data_version, row_count, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (snapshot["snapshotId"], snapshot["importId"], snapshot["datasetName"], snapshot["dataVersion"], snapshot["rowCount"], dumps(snapshot), snapshot["createdAt"]))
        conn.execute("INSERT OR REPLACE INTO metric_snapshots (metric_id, snapshot_id, metric_name, metric_value, entity_type, entity_id, store_id, payload, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (make_id("METRIC"), snapshot["snapshotId"], f"{snapshot['datasetName']}_row_count", snapshot["rowCount"], "dataset", snapshot["datasetName"], None, dumps({"dataVersion": snapshot["dataVersion"]}), snapshot["createdAt"]))
        conn.commit()


def _save_alert_event(alert: Dict[str, Any]) -> None:
    ensure_v3_tables()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO alert_events (
                alert_id, snapshot_id, import_id, data_version, source_dataset,
                entity_type, entity_id, store_id, alert_type, risk_domain, priority,
                evidence, status, task_id, payload, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (alert["alertId"], alert["snapshotId"], alert["importId"], alert["dataVersion"], alert["sourceDataset"], alert["entityType"], alert["entityId"], alert.get("storeId"), alert["alertType"], alert["riskDomain"], alert["priority"], dumps({"items": alert.get("evidence", [])}), alert.get("status") or "new", alert.get("taskId"), dumps(alert), alert["createdAt"], alert.get("updatedAt") or now_iso()),
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


def _evidence_summary(alert: Dict[str, Any]) -> str:
    pieces = []
    for item in alert.get("evidence", [])[:4]:
        pieces.append(f"{item.get('label') or '证据'}：{item.get('value') or item.get('text') or ''}")
    return "；".join(pieces) or alert.get("suggestion") or "报表导入后触发经营预警。"


def _task_payload_from_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    store_id = alert.get("storeId")
    context = _product_context(alert["entityId"], store_id) if alert["entityType"] == "商品" else {"storeId": store_id, "store": _store_name(store_id), "platform": _store_platform(store_id)}
    priority = alert.get("priority") or "中"
    store_ids = [store_id] if store_id else []
    policy = alert.get("v11MvpPolicy") or {}
    queue_type = policy.get("queueType") or "urgent_execution"
    return {
        **context,
        "entityType": alert["entityType"],
        "entityId": alert["entityId"],
        "riskDomain": alert["riskDomain"],
        "actionType": "复查",
        "sourceType": "系统预警",
        "sourceModule": "报表预警中心",
        "source": "报表触发",
        "sourceRoute": "data-check",
        "taskLayer": "operator_execution",
        "storeIds": store_ids,
        "visibleStoreIds": store_ids,
        "priority": priority,
        "priorityLevel": "danger" if priority == "高" else "warning" if priority == "中" else "good",
        "deadline": "今天内" if priority == "高" else "明天前",
        "urgencyLevel": "urgent" if priority == "高" else "observe",
        "queueType": queue_type,
        "displayState": "expanded" if queue_type == "urgent_execution" else "backend_only",
        "taskType": alert["alertType"],
        "taskSignal": alert.get("taskSignal") or "报表异常",
        "task": alert.get("suggestion") or "查看报表预警详情并完成处理。",
        "reason": _evidence_summary(alert),
        "judgmentTags": [alert["sourceDataset"], alert["riskDomain"], alert["priority"], alert["dataVersion"], "V11高风险执行队列"],
        "evidence": alert.get("evidence", []),
        "sourceEvent": alert["alertId"],
        "sourceTrail": ["报表导入", alert["sourceDataset"], alert["dataVersion"], _store_name(store_id) or "未绑定店铺"],
        "reportDataVersion": alert["dataVersion"],
        "alertId": alert["alertId"],
        "v11MvpPolicy": policy,
        "productHistoryDepth": policy.get("productHistoryDepth"),
        "analysisStage": policy.get("analysisStage"),
        "agentJudgment": {"status": "v11_mvp_governance", "summary": "V11只让高风险高时效进入任务栏；低风险沉淀为商品/店铺标签。"},
    }


def _base_evidence(snapshot: Dict[str, Any], store_id: str | None = None) -> List[Dict[str, Any]]:
    items = [{"label": "来源版本", "value": snapshot["dataVersion"]}]
    if store_id:
        items.append({"label": "责任店铺", "value": _store_name(store_id) or store_id})
    return items


def _inventory_alerts(rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for row in rows:
        product_id = str(_pick(row, "product_id", "商品ID", "sku", "SKU", default="")).strip()
        if not product_id:
            continue
        store_id = _resolve_store_id(row, product_id)
        current = _as_float(_pick(row, "available_stock", "current_stock", "stock", "库存", "库存数量", "可售库存"))
        safety = _as_float(_pick(row, "safety_stock", "安全库存", "库存安全线"), 50)
        if current is None or safety is None:
            continue
        if current <= safety:
            priority = "高" if current < safety * 0.5 else "中"
            alerts.append(_alert(snapshot_id=snapshot["snapshotId"], import_id=snapshot["importId"], data_version=snapshot["dataVersion"], source_dataset="inventory", entity_type="商品", entity_id=product_id, store_id=store_id, alert_type="库存基线预警", risk_domain="库存", priority=priority, evidence=[{"label": "当前库存", "value": str(current)}, {"label": "安全库存", "value": str(safety)}, *_base_evidence(snapshot, store_id)], suggestion="库存低于基线，请核查补货周期和活动承接。", task_signal="库存低于基线"))
    return alerts


def _refund_alerts(rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[str, str | None], Dict[str, Any]] = defaultdict(lambda: {"count": 0, "amount": 0.0, "reasons": []})
    for row in rows:
        product_id = str(_pick(row, "product_id", "商品ID", default="")).strip()
        if not product_id:
            continue
        store_id = _resolve_store_id(row, product_id)
        key = (product_id, store_id)
        grouped[key]["count"] += 1
        grouped[key]["amount"] += _as_float(_pick(row, "refund_amount", "退款金额", default=0), 0) or 0
        reason = str(_pick(row, "refund_reason", "退款原因", default="未填写"))
        grouped[key]["reasons"].append(reason)
    alerts: List[Dict[str, Any]] = []
    for (product_id, store_id), stat in grouped.items():
        reason_counts: Dict[str, int] = defaultdict(int)
        for reason in stat["reasons"]:
            reason_counts[reason] += 1
        top_reason = sorted(reason_counts.items(), key=lambda item: item[1], reverse=True)[0][0]
        priority = "高" if stat["count"] >= 3 or stat["amount"] >= 300 else "中"
        alerts.append(_alert(snapshot_id=snapshot["snapshotId"], import_id=snapshot["importId"], data_version=snapshot["dataVersion"], source_dataset="refunds", entity_type="商品", entity_id=product_id, store_id=store_id, alert_type="退款基线预警", risk_domain="售后", priority=priority, evidence=[{"label": "退款记录数", "value": str(stat["count"])}, {"label": "退款金额", "value": f"¥{stat['amount']:.2f}"}, {"label": "高频原因", "value": top_reason}, *_base_evidence(snapshot, store_id)], suggestion="补充CRM售后明细后再确认售后归因，不能用ERA经营报表直接替代售后原因。", task_signal="退款基线异常"))
    return alerts


def _order_alerts(rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[str, str | None], Dict[str, Any]] = defaultdict(lambda: {"orders": 0, "quantity": 0, "paid": 0.0})
    for row in rows:
        product_id = str(_pick(row, "product_id", "商品ID", default="")).strip()
        if not product_id:
            continue
        store_id = _resolve_store_id(row, product_id)
        key = (product_id, store_id)
        grouped[key]["orders"] += _as_int(_pick(row, "paid_orders", "支付订单数", "total_orders", "订单数", default=1), 1)
        grouped[key]["quantity"] += _as_int(_pick(row, "quantity", "paid_units", "支付件数", "数量", default=1), 1)
        grouped[key]["paid"] += _as_float(_pick(row, "actual_paid", "payment_amount", "支付金额", "订单金额", default=0), 0) or 0
    alerts: List[Dict[str, Any]] = []
    for (product_id, store_id), stat in grouped.items():
        if stat["paid"] < 300:
            continue
        priority = "高" if stat["paid"] >= 3000 else "中"
        alerts.append(_alert(snapshot_id=snapshot["snapshotId"], import_id=snapshot["importId"], data_version=snapshot["dataVersion"], source_dataset="orders", entity_type="商品", entity_id=product_id, store_id=store_id, alert_type="成交基线预警", risk_domain="流量", priority=priority, evidence=[{"label": "订单数", "value": str(stat["orders"])}, {"label": "件数", "value": str(stat["quantity"])}, {"label": "实付金额", "value": f"¥{stat['paid']:.2f}"}, *_base_evidence(snapshot, store_id)], suggestion="成交放大后先核查库存、退款率和客服承接，再决定是否继续放量。", task_signal="成交短期放大"))
    return alerts


def _product_alerts(rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for row in rows:
        product_id = str(_pick(row, "product_id", "商品ID", default="")).strip()
        if not product_id:
            continue
        store_id = _resolve_store_id(row, product_id)
        stock = _as_float(_pick(row, "stock", "available_stock", "库存", "库存数量", "可售库存"))
        sale_price = _as_float(_pick(row, "sale_price", "售价", "销售价"))
        cost_price = _as_float(_pick(row, "cost_price", "成本", "商品成本"))
        roi = _as_float(_pick(row, "roi", "ROI", "投产", "投产比"))
        refund_rate = _as_rate(_pick(row, "refund_rate", "退款率", "售后率"))
        conversion = _as_rate(_pick(row, "conversion_rate", "支付转化率", "转化率"))
        ad_spend = _as_float(_pick(row, "ad_spend", "广告消耗", "投放消耗"), 0) or 0
        revenue = _as_float(_pick(row, "revenue", "payment_amount", "支付金额", "销售额"), 0) or 0
        if stock is not None and stock <= 50:
            priority = "高" if stock <= 20 else "中"
            alerts.append(_alert(snapshot_id=snapshot["snapshotId"], import_id=snapshot["importId"], data_version=snapshot["dataVersion"], source_dataset="products", entity_type="商品", entity_id=product_id, store_id=store_id, alert_type="商品库存基线预警", risk_domain="库存", priority=priority, evidence=[{"label": "商品库存", "value": str(stock)}, *_base_evidence(snapshot, store_id)], suggestion="商品库存接近低位，先确认补货周期和主推节奏。", task_signal="商品库存偏低"))
        if sale_price is not None and cost_price is not None and sale_price > 0:
            margin = (sale_price - cost_price) / sale_price
            if margin < 0.2:
                alerts.append(_alert(snapshot_id=snapshot["snapshotId"], import_id=snapshot["importId"], data_version=snapshot["dataVersion"], source_dataset="products", entity_type="商品", entity_id=product_id, store_id=store_id, alert_type="毛利基线预警", risk_domain="价格", priority="高", evidence=[{"label": "售价", "value": str(sale_price)}, {"label": "成本", "value": str(cost_price)}, {"label": "毛利率", "value": f"{margin:.1%}"}, *_base_evidence(snapshot, store_id)], suggestion="复核活动价、成本和投放预算，避免低毛利继续放大。", task_signal="毛利低于基线"))
        if roi is not None and roi < 1.2:
            priority = "高" if roi < 0.8 or (ad_spend and revenue / max(ad_spend, 1) < 1.0) else "中"
            alerts.append(_alert(snapshot_id=snapshot["snapshotId"], import_id=snapshot["importId"], data_version=snapshot["dataVersion"], source_dataset="products", entity_type="商品", entity_id=product_id, store_id=store_id, alert_type="ROI基线预警", risk_domain="流量", priority=priority, evidence=[{"label": "ROI", "value": str(roi)}, {"label": "广告消耗", "value": str(ad_spend)}, {"label": "支付金额", "value": str(revenue)}, *_base_evidence(snapshot, store_id)], suggestion="ROI明显低于基线，先核查流量来源、转化承接和投放成本。", task_signal="ROI低于基线"))
        if refund_rate is not None and refund_rate > 0.08:
            priority = "高" if refund_rate > 0.15 else "中"
            alerts.append(_alert(snapshot_id=snapshot["snapshotId"], import_id=snapshot["importId"], data_version=snapshot["dataVersion"], source_dataset="products", entity_type="商品", entity_id=product_id, store_id=store_id, alert_type="退款率基线预警", risk_domain="售后", priority=priority, evidence=[{"label": "退款率", "value": f"{refund_rate:.1%}"}, *_base_evidence(snapshot, store_id)], suggestion="ERA只能确认退款率异常，需补充CRM售后原因后再归因。", task_signal="退款率高于基线"))
        if conversion is not None and conversion < 0.01:
            alerts.append(_alert(snapshot_id=snapshot["snapshotId"], import_id=snapshot["importId"], data_version=snapshot["dataVersion"], source_dataset="products", entity_type="商品", entity_id=product_id, store_id=store_id, alert_type="转化基线观察", risk_domain="流量", priority="中", evidence=[{"label": "支付转化率", "value": f"{conversion:.2%}"}, *_base_evidence(snapshot, store_id)], suggestion="转化率低于基线，先沉淀商品标签，等待更多周期验证。", task_signal="转化率低于基线"))
    return alerts


def _customer_alerts(rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    for row in rows:
        customer_id = str(_pick(row, "customer_id", "客户ID", default="")).strip()
        if not customer_id:
            continue
        store_id = _resolve_store_id(row, None)
        refund_count = _as_int(_pick(row, "refund_count", "退款次数", default=0), 0)
        total_orders = _as_int(_pick(row, "total_orders", "订单数", default=0), 0)
        if refund_count >= 2:
            alerts.append(_alert(snapshot_id=snapshot["snapshotId"], import_id=snapshot["importId"], data_version=snapshot["dataVersion"], source_dataset="customers", entity_type="客户", entity_id=customer_id, store_id=store_id, alert_type="客户售后敏感预警", risk_domain="售后", priority="中", evidence=[{"label": "订单数", "value": str(total_orders)}, {"label": "退款次数", "value": str(refund_count)}, *_base_evidence(snapshot, store_id)], suggestion="标记售后敏感客户，后续客服处理需要人工复核话术。", task_signal="客户退款偏高"))
    return alerts


def generate_alerts(dataset_name: str, rows: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    builders = {"inventory": _inventory_alerts, "refunds": _refund_alerts, "orders": _order_alerts, "products": _product_alerts, "customers": _customer_alerts}
    builder = builders.get(dataset_name)
    return builder(rows, snapshot) if builder else []


def import_report_dataset(dataset_name: str, rows: List[Dict[str, Any]] | None = None, *, auto_create_tasks: bool = True) -> Dict[str, Any]:
    normalized_name = _normalize_dataset_name(dataset_name)
    dataset_rows = _rows_from_payload(rows) if rows is not None else read_csv(str(DATASET_CONFIGS[normalized_name]["filename"]))
    created_at = now_iso()
    import_id = make_id("IMPORT")
    snapshot_id = make_id("SNAP")
    data_version = f"DV_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{normalized_name.upper()}"
    snapshot = {"snapshotId": snapshot_id, "importId": import_id, "datasetName": normalized_name, "dataVersion": data_version, "rowCount": len(dataset_rows), "createdAt": created_at, "mode": "report_rows" if rows is not None else "mock_csv_v11", "sampleRows": dataset_rows[:20], "version": V3_VERSION}
    _save_snapshot(snapshot)
    governance = process_report_import(normalized_name, dataset_rows, data_version)
    raw_alerts = generate_alerts(normalized_name, dataset_rows, snapshot)
    synced_alerts: List[Dict[str, Any]] = []
    policy_counts: Dict[str, int] = defaultdict(int)
    for raw_alert in raw_alerts:
        alert = apply_alert_policy(raw_alert, governance)
        policy = alert.get("v11MvpPolicy") or {}
        policy_counts["task" if policy.get("createTask") else "tag"] += 1
        _save_alert_event(alert)
        if auto_create_tasks and policy.get("createTask"):
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
        "taggedAlertCount": len([item for item in synced_alerts if not item.get("taskId")]),
        "alerts": synced_alerts,
        "v11MvpGovernance": governance,
        "v11PolicyCounts": dict(policy_counts),
        "globalSync": ["dashboard", "product", "store", "traffic", "report", "todo", "log", "task_report"],
        "storeScopeBound": True,
        "rule": "V11 MVP：完整分析但不把中低风险放进任务栏；中低风险沉淀为商品/店铺标签。",
    }


def run_v3_mock_imports(dataset_names: Iterable[str] | None = None) -> Dict[str, Any]:
    selected = list(dataset_names or ["inventory", "refunds", "orders", "products"])
    results = [import_report_dataset(name, rows=None, auto_create_tasks=True) for name in selected]
    return {"version": V3_VERSION, "mode": "v11_mvp_mock_alerts", "datasetCount": len(results), "alertCount": sum(item.get("alertCount", 0) for item in results), "createdTaskCount": sum(item.get("createdTaskCount", 0) for item in results), "taggedAlertCount": sum(item.get("taggedAlertCount", 0) for item in results), "results": results, "summary": get_v3_dashboard_summary()}


def _row_to_alert(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    if payload:
        if not payload.get("storeId") and row.keys() and "store_id" in row.keys():
            payload["storeId"] = row["store_id"]
        if payload.get("storeId") and not payload.get("visibleStoreIds"):
            payload["visibleStoreIds"] = [payload["storeId"]]
        return payload
    store_id = row["store_id"] if "store_id" in row.keys() else None
    return {"alertId": row["alert_id"], "snapshotId": row["snapshot_id"], "importId": row["import_id"], "dataVersion": row["data_version"], "sourceDataset": row["source_dataset"], "entityType": row["entity_type"], "entityId": row["entity_id"], "storeId": store_id, "storeName": _store_name(store_id), "visibleStoreIds": [store_id] if store_id else [], "alertType": row["alert_type"], "riskDomain": row["risk_domain"], "priority": row["priority"], "evidence": loads(row["evidence"]).get("items", []), "status": row["status"], "taskId": row["task_id"], "createdAt": row["created_at"], "updatedAt": row["updated_at"]}


def _alert_visible_for_user(alert: Dict[str, Any], user_id: str | None) -> bool:
    if not user_id:
        return True
    user = current_user(user_id)
    role = user.get("roleId")
    allowed = set(visible_store_ids_for_user(user_id))
    store_ids = set(alert.get("visibleStoreIds") or ([alert.get("storeId")] if alert.get("storeId") else []))
    if role in {"owner", "manager", "finance"}:
        return not store_ids or bool(store_ids & allowed)
    return bool(store_ids and store_ids & allowed)


def filter_alerts_for_user(alerts: List[Dict[str, Any]], user_id: str | None = None) -> List[Dict[str, Any]]:
    return [alert for alert in alerts if _alert_visible_for_user(alert, user_id)]


def list_alert_events(limit: int = 50, *, active_only: bool = False, user_id: str | None = None) -> List[Dict[str, Any]]:
    ensure_v3_tables()
    query = "SELECT * FROM alert_events"
    params: List[Any] = []
    if active_only:
        placeholders = ",".join("?" for _ in ACTIVE_ALERT_STATUSES)
        query += f" WHERE status IN ({placeholders})"
        params.extend(sorted(ACTIVE_ALERT_STATUSES))
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(max(limit * 4, limit) if user_id else limit)
    with connect() as conn:
        alerts = [_row_to_alert(row) for row in conn.execute(query, params).fetchall()]
    return filter_alerts_for_user(alerts, user_id)[:limit]


def latest_data_version() -> Dict[str, Any] | None:
    ensure_v3_tables()
    with connect() as conn:
        row = conn.execute("SELECT * FROM data_snapshots ORDER BY created_at DESC LIMIT 1").fetchone()
    if not row:
        return None
    payload = loads(row["payload"])
    return payload or {"snapshotId": row["snapshot_id"], "importId": row["import_id"], "datasetName": row["dataset_name"], "dataVersion": row["data_version"], "rowCount": row["row_count"], "createdAt": row["created_at"]}


def list_data_versions(limit: int = 20) -> List[Dict[str, Any]]:
    ensure_v3_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM data_snapshots ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    versions: List[Dict[str, Any]] = []
    for row in rows:
        payload = loads(row["payload"])
        versions.append(payload or {"snapshotId": row["snapshot_id"], "importId": row["import_id"], "datasetName": row["dataset_name"], "dataVersion": row["data_version"], "rowCount": row["row_count"], "createdAt": row["created_at"]})
    return versions


def list_alerts_for_entity(entity_type: str, entity_id: str, limit: int = 20, user_id: str | None = None) -> List[Dict[str, Any]]:
    ensure_v3_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM alert_events WHERE entity_type = ? AND entity_id = ? ORDER BY created_at DESC LIMIT ?", (entity_type, entity_id, max(limit * 4, limit) if user_id else limit)).fetchall()
    alerts = [_row_to_alert(row) for row in rows]
    return filter_alerts_for_user(alerts, user_id)[:limit]


def attach_alert_state(item: Dict[str, Any], entity_type: str, entity_id: str, user_id: str | None = None) -> Dict[str, Any]:
    result = deepcopy(item)
    alerts = list_alerts_for_entity(entity_type, entity_id, limit=10, user_id=user_id)
    active_alerts = [alert for alert in alerts if alert.get("status") in ACTIVE_ALERT_STATUSES]
    result["alertState"] = {"activeAlertCount": len(active_alerts), "latestAlert": active_alerts[0] if active_alerts else alerts[0] if alerts else None, "highestPriority": sorted([alert.get("priority", "低") for alert in active_alerts], key=lambda value: PRIORITY_RANK.get(value, 9))[0] if active_alerts else None, "dataVersions": list(dict.fromkeys(alert.get("dataVersion") for alert in alerts if alert.get("dataVersion")))[:5], "alerts": active_alerts[:5]}
    return result


def find_alert_by_task_id(task_id: str | None) -> Dict[str, Any] | None:
    if not task_id:
        return None
    ensure_v3_tables()
    with connect() as conn:
        row = conn.execute("SELECT * FROM alert_events WHERE task_id = ? ORDER BY created_at DESC LIMIT 1", (task_id,)).fetchone()
    return _row_to_alert(row) if row else None


def get_v3_dashboard_summary(user_id: str | None = None) -> Dict[str, Any]:
    alerts = list_alert_events(limit=100, user_id=user_id)
    active = [item for item in alerts if item.get("status") in ACTIVE_ALERT_STATUSES]
    tagged = [item for item in alerts if item.get("status") in {"tagged_only", "observation_tagged"}]
    latest = latest_data_version()
    by_dataset: Dict[str, int] = defaultdict(int)
    by_risk: Dict[str, int] = defaultdict(int)
    by_store: Dict[str, int] = defaultdict(int)
    for alert in active:
        by_dataset[alert.get("sourceDataset", "unknown")] += 1
        by_risk[alert.get("riskDomain", "通用")] += 1
        if alert.get("storeId"):
            by_store[alert["storeId"]] += 1
    return {"version": V3_VERSION, "name": "V11 MVP 报表导入 + 标签治理 + 任务队列", "dataRefreshMode": "report_upload_or_mock_import", "latestDataVersion": latest.get("dataVersion") if latest else None, "latestDatasetName": latest.get("datasetName") if latest else None, "latestSnapshotAt": latest.get("createdAt") if latest else None, "activeAlertCount": len(active), "totalAlertCount": len(alerts), "taggedAlertCount": len(tagged), "highPriorityAlertCount": len([item for item in active if item.get("priority") == "高"]), "taskLinkedAlertCount": len([item for item in active if item.get("taskId")]), "alertByDataset": dict(by_dataset), "alertByRiskDomain": dict(by_risk), "alertByStore": dict(by_store), "latestAlerts": active[:5], "latestTaggedSignals": tagged[:5], "storeScoped": True, "globalSyncTargets": ["首页", "商品页", "店铺页", "数据页", "待办", "日志", "详情报告"], "rule": "低风险不进入任务栏，沉淀为商品/店铺标签。"}
