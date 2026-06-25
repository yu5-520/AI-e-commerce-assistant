"""V11.4 data-driven module projection service with strict scope gate."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from sqlite3 import OperationalError
from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, loads
from src.services.account_service import current_user, list_stores, visible_store_ids_for_user
from src.services.backend_isolation_service import DEFAULT_ORG_ID, DEFAULT_TENANT_ID, row_scope_status, strict_data_scope_enabled
from src.services.import_row_store_service import load_import_rows
from src.services.module_data_service import REPORT_GROUPS

PROJECTION_VERSION = "11.4.0"
DATASET_LABELS = {"products": "商品报表", "inventory": "库存报表", "orders": "订单报表", "refunds": "退款报表", "customers": "客户报表"}
DATASET_SOURCE = {"products": "ERP", "inventory": "ERP", "orders": "订单报表", "refunds": "CRM", "customers": "CRM"}


def _pick(row: Dict[str, Any], *fields: str, default: Any = None) -> Any:
    for field in fields:
        if row.get(field) not in {None, ""}:
            return row.get(field)
    return default


def _as_float(value: Any, default: float | None = None) -> float | None:
    if value in {None, ""}:
        return default
    text = str(value).replace(",", "").replace("%", "").replace("¥", "").strip()
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _format_number(value: float | None, default: str = "—") -> str:
    if value is None:
        return default
    return str(int(value)) if float(value).is_integer() else f"{value:.2f}"


def _store_index() -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for store in list_stores():
        mapping[store["id"]] = store
        mapping[store["name"]] = store
        mapping[f"{store.get('platform')} · {store.get('name')}"] = store
    return mapping


def _resolve_store_id(row: Dict[str, Any]) -> str | None:
    mapping = _store_index()
    explicit = str(_pick(row, "store_id", "storeId", "店铺ID", "店铺id", "店铺编号", "店铺编码", default="") or "").strip()
    if explicit:
        return explicit if explicit in mapping else explicit
    name = str(_pick(row, "store_name", "store", "店铺", "店铺名称", "店铺名", default="") or "").strip()
    if name and name in mapping:
        return mapping[name]["id"]
    return None


def _store_name(store_id: str | None) -> str:
    store = _store_index().get(store_id or "")
    return store.get("name") if store else (store_id or "未绑定店铺")


def _store_platform(store_id: str | None, fallback: str = "导入数据") -> str:
    store = _store_index().get(store_id or "")
    return store.get("platform") if store else fallback


def _visible_store_ids(user_id: str | None) -> set[str]:
    return set(visible_store_ids_for_user(user_id)) if user_id else set()


def _raw_dataset_rows(dataset_name: str | None = None) -> List[Dict[str, Any]]:
    full_rows = load_import_rows(dataset_name)
    return full_rows if full_rows else _snapshot_rows(dataset_name)


def _scope_decision(row: Dict[str, Any], store_id: str | None = None) -> Dict[str, Any]:
    return row_scope_status(row, tenant_id=DEFAULT_TENANT_ID, org_id=DEFAULT_ORG_ID, store_id=store_id, require_store=True)


def _row_visible(row: Dict[str, Any], user_id: str | None) -> bool:
    store_id = row.get("storeId") or row.get("store_id") or _resolve_store_id(row)
    if store_id:
        row.setdefault("storeId", store_id)
    if strict_data_scope_enabled():
        decision = _scope_decision(row, store_id)
        if decision.get("status") != "ok":
            row["scopeStatus"] = "quarantined"
            row["scopeMissing"] = decision.get("missing", [])
            row["scopeErrors"] = decision.get("errors", [])
            return False
    if not user_id:
        return True
    if not store_id:
        # Demo-only compatibility. Strict mode already quarantines rows without a
        # store ownership field, so production cannot leak unassigned data here.
        return True
    role = current_user(user_id).get("roleId")
    if role in {"owner", "manager", "finance"}:
        return True
    return store_id in _visible_store_ids(user_id)


def _snapshot_payloads() -> List[Dict[str, Any]]:
    try:
        with connect() as conn:
            rows = conn.execute("SELECT payload FROM data_snapshots ORDER BY created_at ASC").fetchall()
    except OperationalError:
        return []
    return [payload for row in rows if (payload := loads(row["payload"]))]


def latest_snapshots_by_dataset() -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for payload in _snapshot_payloads():
        dataset = payload.get("datasetName")
        if dataset:
            latest[dataset] = payload
    return latest


def _snapshot_rows(dataset_name: str | None = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for dataset, payload in latest_snapshots_by_dataset().items():
        if dataset_name and dataset != dataset_name:
            continue
        source_rows = payload.get("rows") or payload.get("sampleRows") or []
        if not isinstance(source_rows, list):
            continue
        for row in source_rows:
            if not isinstance(row, dict):
                continue
            item = {str(key): value for key, value in row.items()}
            item.setdefault("dataVersion", payload.get("dataVersion"))
            item.setdefault("datasetName", payload.get("datasetName"))
            store_id = _resolve_store_id(item)
            if store_id:
                item.setdefault("storeId", store_id)
            rows.append(item)
    return rows


def dataset_rows(dataset_name: str | None = None, user_id: str | None = None) -> List[Dict[str, Any]]:
    rows = _raw_dataset_rows(dataset_name)
    return [row for row in rows if _row_visible(row, user_id)]


def quarantined_dataset_rows(dataset_name: str | None = None) -> List[Dict[str, Any]]:
    rows = _raw_dataset_rows(dataset_name)
    quarantined: List[Dict[str, Any]] = []
    for row in rows:
        store_id = row.get("storeId") or row.get("store_id") or _resolve_store_id(row)
        decision = _scope_decision(row, store_id)
        if decision.get("status") != "ok":
            item = dict(row)
            item["scopeDecision"] = decision
            quarantined.append(item)
    return quarantined


def has_runtime_data(user_id: str | None = None) -> bool:
    return bool(dataset_rows(user_id=user_id))


def _product_key(product_id: str, store_id: str | None) -> str:
    return f"{store_id or 'global'}::{product_id}"


def _product_id(row: Dict[str, Any]) -> str:
    return str(_pick(row, "product_id", "productId", "商品ID", "商品id", "sku", "SKU", "商品编码", "商家编码", default="") or "").strip()


def _ensure_product(products: Dict[str, Dict[str, Any]], product_id: str, store_id: str | None) -> Dict[str, Any]:
    key = _product_key(product_id, store_id)
    if key not in products:
        products[key] = {
            "id": product_id,
            "storeId": store_id,
            "shortName": product_id,
            "title": f"导入商品 {product_id}",
            "platform": _store_platform(store_id),
            "store": _store_name(store_id),
            "imageLabel": "品",
            "link": "",
            "inventory": "—",
            "inventoryStatus": "待导入库存",
            "inventoryLevel": "good",
            "price": "—",
            "cost": "—",
            "grossMargin": "—",
            "afterSales": "正常",
            "afterSalesLevel": "good",
            "suggestion": "根据导入数据生成经营判断。",
            "sourceDataVersions": [],
            "sourceDatasets": [],
        }
    return products[key]


def projected_products(user_id: str | None = None) -> List[Dict[str, Any]]:
    products: Dict[str, Dict[str, Any]] = {}
    refund_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "amount": 0.0, "reasons": []})
    order_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"orders": 0, "paid": 0.0, "quantity": 0})
    for row in dataset_rows(user_id=user_id):
        dataset = row.get("datasetName")
        product_id = _product_id(row)
        if not product_id:
            continue
        store_id = row.get("storeId") or _resolve_store_id(row)
        item = _ensure_product(products, product_id, store_id)
        data_version = row.get("dataVersion")
        if data_version and data_version not in item["sourceDataVersions"]:
            item["sourceDataVersions"].append(data_version)
        if dataset and dataset not in item["sourceDatasets"]:
            item["sourceDatasets"].append(dataset)
        title = _pick(row, "product_name", "productTitle", "商品名称", "商品名", "title", "标题")
        if title:
            item["title"] = str(title)
            item["shortName"] = str(title)[:8]
        platform = _pick(row, "platform", "平台")
        if platform:
            item["platform"] = str(platform)
        store_name = _pick(row, "store_name", "store", "店铺", "店铺名称")
        if store_name:
            item["store"] = str(store_name)
        link = _pick(row, "link", "url", "商品链接", "链接")
        if link:
            item["link"] = str(link)
        stock = _as_float(_pick(row, "stock", "available_stock", "current_stock", "库存", "可用库存", "当前库存"))
        safety = _as_float(_pick(row, "safety_stock", "安全库存", "预警库存"))
        if stock is not None:
            item["inventory"] = _format_number(stock)
            if safety is not None and stock <= safety:
                item["inventoryStatus"] = "库存不足" if stock < safety else "触达安全线"
                item["inventoryLevel"] = "danger" if stock < safety else "warning"
            else:
                item["inventoryStatus"] = "库存正常"
                item["inventoryLevel"] = "good"
        sale_price = _as_float(_pick(row, "sale_price", "售价", "销售价", "活动价", "成交价"))
        cost_price = _as_float(_pick(row, "cost_price", "成本", "成本价", "采购价"))
        if sale_price is not None:
            item["price"] = _format_number(sale_price)
        if cost_price is not None:
            item["cost"] = _format_number(cost_price)
        if sale_price is not None and cost_price is not None and sale_price > 0:
            margin = (sale_price - cost_price) / sale_price
            item["grossMargin"] = f"{margin:.0%}"
            if margin < 0.2:
                item["suggestion"] = "毛利低于安全线，先复核活动价、成本和投放预算。"
        key = _product_key(product_id, store_id)
        if dataset == "refunds":
            refund_stats[key]["count"] += 1
            refund_stats[key]["amount"] += _as_float(_pick(row, "refund_amount", "退款金额", default=0), 0) or 0
            refund_stats[key]["reasons"].append(str(_pick(row, "refund_reason", "退款原因", "售后原因", default="未填写")))
        if dataset == "orders":
            order_stats[key]["orders"] += 1
            order_stats[key]["quantity"] += int(_as_float(_pick(row, "quantity", "数量", default=1), 1) or 1)
            order_stats[key]["paid"] += _as_float(_pick(row, "actual_paid", "实付金额", "订单金额", default=0), 0) or 0
    for key, stat in refund_stats.items():
        item = products.get(key)
        if item:
            item["afterSales"] = f"退款 {stat['count']} 笔"
            item["afterSalesLevel"] = "danger" if stat["count"] >= 2 or stat["amount"] >= 100 else "warning"
            top_reason = stat["reasons"][0] if stat["reasons"] else "售后异常"
            item["suggestion"] = f"复查退款原因：{top_reason}。售后归因完成前不继续放量。"
    for key, stat in order_stats.items():
        item = products.get(key)
        if item and stat["orders"]:
            item["orderSummary"] = f"订单 {stat['orders']} 笔 / ¥{stat['paid']:.2f}"
    return sorted((deepcopy(item) for item in products.values()), key=lambda item: (item.get("storeId") or "", item.get("id") or ""))


def projected_traffic(user_id: str | None = None) -> List[Dict[str, Any]]:
    cards: Dict[str, Dict[str, Any]] = {}
    products = {_product_key(item["id"], item.get("storeId")): item for item in projected_products(user_id)}
    for row in dataset_rows("orders", user_id=user_id):
        product_id = _product_id(row)
        if not product_id:
            continue
        store_id = row.get("storeId") or _resolve_store_id(row)
        key = _product_key(product_id, store_id)
        product = products.get(key) or _ensure_product({}, product_id, store_id)
        card = cards.setdefault(key, {"id": f"TR-{store_id or 'GLOBAL'}-{product_id}", "storeId": store_id, "productId": product_id, "title": product.get("title") or f"导入商品 {product_id}", "platform": product.get("platform") or _store_platform(store_id), "store": product.get("store") or _store_name(store_id), "imageLabel": "流", "channel": "订单数据", "source": "报表导入", "exposure": "—", "ctr": "—", "conversion": "—", "roi": "—", "refundRate": "—", "inventory": product.get("inventory") or "—", "status": "观察", "statusLevel": "warning", "backflow": "流量承接复查", "nextStep": "根据订单放大信号，复核库存、售后和承接能力。", "link": product.get("link") or "", "orderCount": 0, "paidAmount": 0.0})
        card["orderCount"] += 1
        card["paidAmount"] += _as_float(_pick(row, "actual_paid", "实付金额", "订单金额", default=0), 0) or 0
    for card in cards.values():
        if card["paidAmount"] >= 300:
            card["status"] = "放量前复核"
            card["statusLevel"] = "danger"
        card["source"] = f"订单 {card['orderCount']} 笔"
        card["roi"] = f"¥{card['paidAmount']:.2f}"
    return list(cards.values())


def projected_report_groups(user_id: str | None = None) -> List[Dict[str, Any]]:
    latest = latest_snapshots_by_dataset()
    groups: List[Dict[str, Any]] = []
    for group in REPORT_GROUPS:
        next_group = {**group, "reports": []}
        for report in group.get("reports", []):
            dataset = report["id"]
            payload = latest.get(dataset)
            rows = dataset_rows(dataset, user_id=user_id)
            next_group["reports"].append({**report, "status": "已导入" if payload else "待导入", "count": f"{len(rows)} 条", "latestDataVersion": payload.get("dataVersion") if payload else None, "latestSnapshotAt": payload.get("createdAt") if payload else None, "source": DATASET_SOURCE.get(dataset, report.get("source", "报表"))})
        groups.append(next_group)
    return groups


def projected_report_details(user_id: str | None = None) -> Dict[str, Dict[str, Any]]:
    details: Dict[str, Dict[str, Any]] = {}
    for dataset, payload in latest_snapshots_by_dataset().items():
        rows = dataset_rows(dataset, user_id=user_id)
        headers: List[str] = []
        for row in rows[:20]:
            for key in row.keys():
                if key not in {"dataVersion", "datasetName"} and key not in headers:
                    headers.append(key)
        details[dataset] = {"title": DATASET_LABELS.get(dataset, dataset), "source": DATASET_SOURCE.get(dataset, "导入"), "summary": [["数据行", str(len(rows))], ["数据版本", payload.get("dataVersion") or "—"], ["店铺数", str(len({row.get("storeId") for row in rows if row.get("storeId")}))]], "columns": headers[:12], "rows": [[str(row.get(header, "")) for header in headers[:12]] for row in rows[:50]], "dataVersion": payload.get("dataVersion"), "createdAt": payload.get("createdAt")}
    return details


def projection_summary(user_id: str | None = None) -> Dict[str, Any]:
    latest = latest_snapshots_by_dataset()
    latest_payload = list(latest.values())[-1] if latest else None
    products = projected_products(user_id)
    traffic = projected_traffic(user_id)
    reports = projected_report_groups(user_id)
    quarantined = quarantined_dataset_rows() if strict_data_scope_enabled() else []
    return {"version": PROJECTION_VERSION, "hasData": bool(latest_payload or products or traffic), "latestDataVersion": latest_payload.get("dataVersion") if latest_payload else None, "latestDatasetName": latest_payload.get("datasetName") if latest_payload else None, "latestSnapshotAt": latest_payload.get("createdAt") if latest_payload else None, "productCount": len(products), "trafficCardCount": len(traffic), "reportCount": sum(len(group.get("reports", [])) for group in reports), "dataVersionCount": len(latest), "scopedStoreIds": sorted(_visible_store_ids(user_id)), "strictDataScope": strict_data_scope_enabled(), "quarantinedRowCount": len(quarantined)}
