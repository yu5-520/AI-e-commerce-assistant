"""V14.5 data-driven module projection service.

商品模块只做商品资产和定位展示；任务模块负责交叉验证和SOP。
V14.5：投影层先验权限印章，再验旧店铺范围。谁上传报表，谁默认拥有该报表商品/店铺处理权限；ERP显式归属优先。
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from sqlite3 import OperationalError
from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect, loads
from src.services.account_service import current_user, list_stores, visible_store_ids_for_user
from src.services.backend_isolation_service import DEFAULT_ORG_ID, DEFAULT_TENANT_ID, row_scope_status, strict_data_scope_enabled
from src.services.import_row_store_service import load_import_rows
from src.services.metric_catalog_service import (
    display_short_title,
    extract_metric_facts,
    format_metric,
    metric_value,
    pick,
    product_identity,
    stable_code,
    system_codes,
)
from src.services.module_data_service import REPORT_GROUPS
from src.services.permission_stamp_service import permission_stamp_allows, row_permission_stamp

PROJECTION_VERSION = "14.5.0"
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


def _store_index() -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    for store in list_stores():
        mapping[store["id"]] = store
        mapping[store["name"]] = store
        mapping[f"{store.get('platform')} · {store.get('name')}"] = store
    return mapping


def _resolve_store_id(row: Dict[str, Any]) -> str | None:
    ident = product_identity(row)
    explicit = str(ident.get("storeId") or "").strip()
    if explicit:
        return explicit
    name = str(ident.get("storeName") or "").strip()
    mapping = _store_index()
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
    role = current_user(user_id).get("roleId")
    if role in {"owner", "manager", "finance"}:
        return True
    if permission_stamp_allows(row, user_id, role):
        row["permissionStampAccepted"] = True
        return True
    if not store_id:
        return True
    return store_id in _visible_store_ids(user_id)


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


def _product_id(row: Dict[str, Any]) -> str:
    ident = product_identity(row)
    return str(ident.get("productId") or ident.get("skuId") or ident.get("erpProductCode") or ident.get("productLink") or "").strip()


def _product_key(row: Dict[str, Any], store_id: str | None) -> str:
    product_id = _product_id(row)
    sku = product_identity(row).get("skuId") or "NO-SKU"
    ext = stable_code("EXT", product_identity(row).get("productLink"), product_identity(row).get("erpProductCode"))
    return f"{store_id or 'global'}::{product_id}::{sku}::{ext}"


def _fmt(row: Dict[str, Any], metric_code: str) -> str:
    return format_metric(metric_code, metric_value(row, metric_code))


def _ensure_product(products: Dict[str, Dict[str, Any]], row: Dict[str, Any], store_id: str | None) -> Dict[str, Any]:
    product_id = _product_id(row)
    key = _product_key(row, store_id)
    ident = product_identity(row)
    codes = system_codes(row)
    stamp = row_permission_stamp(row)
    if key not in products:
        title = str(pick(row, "product_name", default=f"导入商品 {product_id}") or f"导入商品 {product_id}")
        products[key] = {
            "id": product_id,
            "objectId": key,
            "productId": product_id,
            "skuId": ident.get("skuId"),
            "erpProductCode": ident.get("erpProductCode"),
            "productLink": ident.get("productLink"),
            "systemStoreCode": codes.get("systemStoreCode"),
            "systemSpuCode": codes.get("systemSpuCode"),
            "systemLinkCode": codes.get("systemLinkCode"),
            "systemSkuCode": codes.get("systemSkuCode"),
            "storeId": store_id,
            "shortName": display_short_title(row, fallback=product_id),
            "title": title,
            "platform": ident.get("platform") or _store_platform(store_id),
            "store": ident.get("storeName") or _store_name(store_id),
            "imageLabel": "品",
            "link": ident.get("productLink") or "",
            "inventory": "—",
            "inventoryStatus": "待导入库存",
            "inventoryLevel": "good",
            "price": "—",
            "avgOrderValue": "—",
            "paymentAmount": "—",
            "cost": "—",
            "costAmount": "—",
            "grossProfitAmount": "—",
            "grossMargin": "—",
            "roi": "—",
            "clickRate": "—",
            "conversionRate": "—",
            "refundRate": "—",
            "adSpend": "—",
            "organicVisitors": "—",
            "paidVisitors": "—",
            "afterSales": "标签观察",
            "afterSalesLevel": "good",
            "suggestion": "V14.5商品档案：权限印章随报表行进入商品投影；任务SOP在任务详情页处理。",
            "sourceDataVersions": [],
            "sourceDatasets": [],
            "metricFacts": [],
            "permissionStamp": stamp,
            "permissionStampId": stamp.get("permissionStampId"),
            "uploadedByUserId": stamp.get("uploadedByUserId"),
            "ownerUserId": stamp.get("ownerUserId"),
            "assignedOperatorId": stamp.get("assignedOperatorId"),
            "visibleUserIds": stamp.get("visibleUserIds") or [],
            "permissionSource": stamp.get("permissionSource"),
            "importBatchId": stamp.get("importBatchId"),
        }
    return products[key]


def _apply_metric_display(item: Dict[str, Any], row: Dict[str, Any]) -> None:
    mapping = {
        "inventory": "inventory_qty",
        "sellableDays": "sellable_days",
        "avgOrderValue": "avg_order_value",
        "price": "avg_order_value",
        "paymentAmount": "payment_amount",
        "cost": "product_cost_amount",
        "costAmount": "product_cost_amount",
        "grossProfitAmount": "gross_profit_amount",
        "grossMargin": "gross_margin_rate",
        "roi": "roi",
        "clickRate": "click_rate",
        "conversionRate": "payment_conversion_rate",
        "refundRate": "refund_rate",
        "adSpend": "ad_spend",
        "organicVisitors": "organic_visitor_count",
        "paidVisitors": "paid_visitor_count",
    }
    for target, metric_code in mapping.items():
        value = _fmt(row, metric_code)
        if value != "—":
            item[target] = value
    if item.get("inventory") != "—":
        item["inventoryStatus"] = "已入库"
    if item.get("refundRate") and item["refundRate"] != "—":
        item["afterSales"] = f"退款率 {item['refundRate']}"


def projected_products(user_id: str | None = None) -> List[Dict[str, Any]]:
    products: Dict[str, Dict[str, Any]] = {}
    for row in dataset_rows(user_id=user_id):
        product_id = _product_id(row)
        if not product_id:
            continue
        store_id = row.get("storeId") or _resolve_store_id(row)
        item = _ensure_product(products, row, store_id)
        data_version = row.get("dataVersion")
        dataset = row.get("datasetName")
        if data_version and data_version not in item["sourceDataVersions"]:
            item["sourceDataVersions"].append(data_version)
        if dataset and dataset not in item["sourceDatasets"]:
            item["sourceDatasets"].append(dataset)
        _apply_metric_display(item, row)
        facts = extract_metric_facts(row)
        if facts:
            seen = {fact.get("metricCode") for fact in item.get("metricFacts", [])}
            for fact in facts:
                if fact.get("metricCode") not in seen:
                    item["metricFacts"].append(fact)
    return sorted((deepcopy(item) for item in products.values()), key=lambda item: (item.get("storeId") or "", item.get("id") or ""))


def projected_traffic(user_id: str | None = None) -> List[Dict[str, Any]]:
    cards: Dict[str, Dict[str, Any]] = {}
    products = {_product_key(item, item.get("storeId")): item for item in projected_products(user_id)}
    for row in dataset_rows(user_id=user_id):
        product_id = _product_id(row)
        if not product_id:
            continue
        store_id = row.get("storeId") or _resolve_store_id(row)
        key = _product_key(row, store_id)
        product = products.get(key) or _ensure_product({}, row, store_id)
        source = str(pick(row, "traffic_source", default="报表数据") or "报表数据")
        card = cards.setdefault(key, {
            "id": f"TR-{store_id or 'GLOBAL'}-{product_id}",
            "storeId": store_id,
            "productId": product_id,
            "title": product.get("title") or f"导入商品 {product_id}",
            "platform": product.get("platform") or _store_platform(store_id),
            "store": product.get("store") or _store_name(store_id),
            "imageLabel": "流",
            "channel": source,
            "source": "报表导入",
            "exposure": _fmt(row, "visitor_count"),
            "ctr": _fmt(row, "click_rate"),
            "conversion": _fmt(row, "payment_conversion_rate"),
            "roi": _fmt(row, "roi"),
            "refundRate": _fmt(row, "refund_rate"),
            "inventory": product.get("inventory") or "—",
            "status": "观察",
            "statusLevel": "warning",
            "backflow": "流量承接复查",
            "nextStep": "流量来源明细只作为交叉验证证据，正式动作由任务闸门决定。",
            "link": product.get("link") or "",
            "trafficSources": [],
        })
        if source not in card["trafficSources"]:
            card["trafficSources"].append(source)
        if card["roi"] != "—":
            card["status"] = "流量结构已入库"
            card["statusLevel"] = "good"
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
    metric_fact_count = sum(len(item.get("metricFacts") or []) for item in products)
    return {"version": PROJECTION_VERSION, "hasData": bool(latest_payload or products or traffic), "latestDataVersion": latest_payload.get("dataVersion") if latest_payload else None, "latestDatasetName": latest_payload.get("datasetName") if latest_payload else None, "latestSnapshotAt": latest_payload.get("createdAt") if latest_payload else None, "productCount": len(products), "trafficCardCount": len(traffic), "reportCount": sum(len(group.get("reports", [])) for group in reports), "dataVersionCount": len(latest), "metricFactCount": metric_fact_count, "scopedStoreIds": sorted(_visible_store_ids(user_id)), "strictDataScope": strict_data_scope_enabled(), "quarantinedRowCount": len(quarantined), "permissionStampProjection": True}
