"""Operating object master store.

V12 rule:
- uploader is still the fallback ownership source for MVP imports;
- report/ERP/CRM fields are treated as external identity anchors, not as the only
  system identity;
- product objects are keyed by store + product + sku/link/ERP anchors;
- product cards expose structured定位字段 and metric facts instead of long titles.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.account_service import current_user, default_reviewer, visible_store_ids_for_user
from src.services.import_row_store_service import load_import_rows
from src.services.metric_catalog_service import (
    CATALOG_VERSION,
    display_short_title,
    extract_metric_facts,
    format_metric,
    metric_value,
    pick,
    product_identity,
    stable_code,
    system_codes,
)
from src.services.report_alert_service import now_iso

OPERATING_OBJECT_VERSION = "12.0.0"
DATA_SCOPE_SOURCE = "uploader_account_fallback_with_v12_report_profile"


def ensure_operating_object_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS operating_products (
                object_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                store_id TEXT,
                store_name TEXT,
                platform TEXT,
                title TEXT,
                category TEXT,
                latest_data_version TEXT,
                source_dataset TEXT,
                payload TEXT,
                first_seen_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(
            conn,
            "operating_products",
            {
                "imported_by_user_id": "TEXT",
                "imported_by_role_id": "TEXT",
                "owner_user_id": "TEXT",
                "assigned_operator_id": "TEXT",
                "reviewer_id": "TEXT",
                "visible_user_ids": "TEXT",
                "visible_role_ids": "TEXT",
                "raw_store_id": "TEXT",
                "raw_store_name": "TEXT",
                "normalized_store_id": "TEXT",
                "normalized_store_name": "TEXT",
                "data_scope_source": "TEXT",
            },
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_operating_products_product ON operating_products(product_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_operating_products_store ON operating_products(store_id, store_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_operating_products_operator ON operating_products(assigned_operator_id, owner_user_id)")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS operating_stores (
                store_key TEXT PRIMARY KEY,
                store_id TEXT,
                store_name TEXT NOT NULL,
                platform TEXT,
                latest_data_version TEXT,
                source_dataset TEXT,
                product_count INTEGER DEFAULT 0,
                payload TEXT,
                first_seen_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(
            conn,
            "operating_stores",
            {
                "imported_by_user_id": "TEXT",
                "imported_by_role_id": "TEXT",
                "owner_user_id": "TEXT",
                "assigned_operator_id": "TEXT",
                "reviewer_id": "TEXT",
                "visible_user_ids": "TEXT",
                "visible_role_ids": "TEXT",
                "raw_store_id": "TEXT",
                "raw_store_name": "TEXT",
                "normalized_store_id": "TEXT",
                "normalized_store_name": "TEXT",
                "data_scope_source": "TEXT",
            },
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_operating_stores_name ON operating_stores(store_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_operating_stores_operator ON operating_stores(assigned_operator_id, owner_user_id)")
        conn.commit()


def _json_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed if item]
        except json.JSONDecodeError:
            return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _row_get(row: Mapping[str, Any] | Any, *names: str, default: Any = None) -> Any:
    for name in names:
        try:
            value = row[name]
        except (KeyError, IndexError, TypeError):
            value = row.get(name) if hasattr(row, "get") else None
        if value not in {None, ""}:
            return value
    return default


def _text(value: Any) -> str:
    return str(value or "").strip()


def _product_id(row: Dict[str, Any]) -> str | None:
    ident = product_identity(row)
    return ident.get("productId") or ident.get("erpProductCode") or ident.get("productLink") or None


def _sku_id(row: Dict[str, Any]) -> str | None:
    return product_identity(row).get("skuId")


def _raw_store_id(row: Dict[str, Any]) -> str | None:
    return product_identity(row).get("storeId")


def _raw_store_name(row: Dict[str, Any]) -> str | None:
    value = product_identity(row).get("storeName")
    if value and value not in {"未绑定店铺", "导入数据店铺", "GLOBAL"}:
        return value
    return None


def _fallback_store_key(uploader_user_id: str | None) -> str:
    return f"IMPORT_STORE_{uploader_user_id or 'SYSTEM'}"


def _store_key(row: Dict[str, Any], uploader_user_id: str | None = None) -> str:
    ident = product_identity(row)
    if ident.get("storeId"):
        return str(ident["storeId"])
    if ident.get("storeName"):
        digest = hashlib.sha1(str(ident["storeName"]).encode("utf-8")).hexdigest()[:10].upper()
        return f"STORE_{digest}"
    return _fallback_store_key(uploader_user_id)


def _platform(row: Dict[str, Any]) -> str:
    return _text(product_identity(row).get("platform") or "导入平台") or "导入平台"


def _title(row: Dict[str, Any], product_id: str) -> str:
    title = _text(pick(row, "product_name", default=""))
    return title or f"导入商品 {product_id}"


def _category(row: Dict[str, Any]) -> str:
    value = pick(row, "category_l2") or pick(row, "category_l1") or pick(row, "category")
    return _text(value or "未分类") or "未分类"


def _object_id(row: Dict[str, Any], product_id: str, store_key: str | None) -> str:
    ident = product_identity(row)
    sku = ident.get("skuId") or "NO-SKU"
    link = ident.get("productLink") or "NO-LINK"
    erp = ident.get("erpProductCode") or "NO-ERP"
    return f"{store_key or 'GLOBAL'}::{product_id}::{sku}::{stable_code('EXT', link, erp)}"


def _import_result_items(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = result.get("results")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    return [result]


def _rows_for_result_item(item: Dict[str, Any], fallback_rows: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
    data_version = item.get("dataVersion")
    dataset_name = item.get("datasetName")
    if dataset_name:
        rows = [row for row in load_import_rows(str(dataset_name)) if not data_version or row.get("dataVersion") == data_version]
        if rows:
            return rows
    return [row for row in (fallback_rows or []) if isinstance(row, dict)]


def _ownership(uploader_user_id: str | None, uploader_role_id: str | None) -> Dict[str, Any]:
    user = current_user(uploader_user_id) if uploader_user_id else {}
    role_id = uploader_role_id or user.get("roleId")
    assigned_operator_id = uploader_user_id if role_id == "operator" else None
    reviewer = default_reviewer()
    visible_user_ids = [item for item in [uploader_user_id, assigned_operator_id, reviewer.get("id")] if item]
    visible_role_ids = ["owner", "manager"]
    if role_id:
        visible_role_ids.append(str(role_id))
    if assigned_operator_id:
        visible_role_ids.append("operator")
    return {
        "importedByUserId": uploader_user_id,
        "importedByRoleId": role_id,
        "ownerUserId": assigned_operator_id or uploader_user_id,
        "assignedOperatorId": assigned_operator_id,
        "reviewerId": reviewer.get("id"),
        "visibleUserIds": list(dict.fromkeys(visible_user_ids)),
        "visibleRoleIds": list(dict.fromkeys(visible_role_ids)),
        "dataScopeSource": DATA_SCOPE_SOURCE,
        "rule": "V12：上传人是兜底归属；ERP/CRM权限标签后续可覆盖，任务派发以最终经营对象归属为准。",
    }


def _merge_payload(existing: Dict[str, Any], row: Dict[str, Any], *, data_version: str | None, dataset_name: str | None, ownership: Dict[str, Any], raw_store_id: str | None, raw_store_name: str | None, normalized_store_id: str, normalized_store_name: str) -> Dict[str, Any]:
    payload = dict(existing or {})
    payload.update({str(key): value for key, value in row.items()})
    payload.update(ownership)
    payload.update({
        "rawStoreId": raw_store_id,
        "rawStoreName": raw_store_name,
        "normalizedStoreId": normalized_store_id,
        "normalizedStoreName": normalized_store_name,
        "productIdentity": product_identity(row),
        "systemCodes": system_codes(row),
        "metricFacts": extract_metric_facts(row),
        "metricCatalogVersion": CATALOG_VERSION,
    })
    if data_version:
        payload["latestDataVersion"] = data_version
    if dataset_name:
        datasets = list(dict.fromkeys([*(payload.get("sourceDatasets") or []), dataset_name]))
        payload["sourceDatasets"] = datasets
    payload["objectStoreVersion"] = OPERATING_OBJECT_VERSION
    return payload


def upsert_operating_objects_from_import(
    result: Dict[str, Any],
    rows: List[Dict[str, Any]] | None = None,
    *,
    source: str = "report_import",
    uploader_user_id: str | None = None,
    uploader_role_id: str | None = None,
) -> Dict[str, Any]:
    """Upsert product/store master objects independent of task generation."""
    ensure_operating_object_tables()
    ownership = _ownership(uploader_user_id, uploader_role_id)
    now = now_iso()
    product_ids: set[str] = set()
    store_keys: set[str] = set()
    seen_row_keys: set[str] = set()
    classified_rows = 0
    with connect() as conn:
        for item in _import_result_items(result):
            dataset_name = str(item.get("datasetName") or result.get("datasetName") or "unknown")
            data_version = str(item.get("dataVersion") or result.get("dataVersion") or "") or None
            for row in _rows_for_result_item(item, rows):
                if not isinstance(row, dict):
                    continue
                row_key = f"{data_version}:{dataset_name}:{hashlib.sha1(dumps(row).encode('utf-8')).hexdigest()}"
                seen_row_keys.add(row_key)
                product_id = _product_id(row)
                store_key = _store_key(row, uploader_user_id)
                raw_store_id = _raw_store_id(row)
                raw_store_name = _raw_store_name(row)
                normalized_store_id = store_key
                normalized_store_name = raw_store_name or f"{current_user(uploader_user_id).get('name') or '账号'}导入店铺"
                platform = _platform(row)
                existing_store = conn.execute("SELECT payload, first_seen_at FROM operating_stores WHERE store_key = ?", (store_key,)).fetchone()
                store_payload = _merge_payload(loads(existing_store["payload"]) if existing_store else {}, row, data_version=data_version, dataset_name=dataset_name, ownership=ownership, raw_store_id=raw_store_id, raw_store_name=raw_store_name, normalized_store_id=normalized_store_id, normalized_store_name=normalized_store_name)
                store_payload["source"] = source
                store_payload["newStoreAutoCreated"] = existing_store is None
                conn.execute(
                    """
                    INSERT OR REPLACE INTO operating_stores (
                        store_key, store_id, store_name, platform, latest_data_version, source_dataset, product_count, payload, first_seen_at, updated_at,
                        imported_by_user_id, imported_by_role_id, owner_user_id, assigned_operator_id, reviewer_id, visible_user_ids, visible_role_ids,
                        raw_store_id, raw_store_name, normalized_store_id, normalized_store_name, data_scope_source
                    ) VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT product_count FROM operating_stores WHERE store_key = ?), 0), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        store_key,
                        normalized_store_id,
                        normalized_store_name,
                        platform,
                        data_version,
                        dataset_name,
                        store_key,
                        dumps(store_payload),
                        existing_store["first_seen_at"] if existing_store else now,
                        now,
                        ownership.get("importedByUserId"),
                        ownership.get("importedByRoleId"),
                        ownership.get("ownerUserId"),
                        ownership.get("assignedOperatorId"),
                        ownership.get("reviewerId"),
                        json.dumps(ownership.get("visibleUserIds") or [], ensure_ascii=False),
                        json.dumps(ownership.get("visibleRoleIds") or [], ensure_ascii=False),
                        raw_store_id,
                        raw_store_name,
                        normalized_store_id,
                        normalized_store_name,
                        DATA_SCOPE_SOURCE,
                    ),
                )
                store_keys.add(store_key)
                if product_id:
                    classified_rows += 1
                    object_id = _object_id(row, product_id, store_key)
                    existing_product = conn.execute("SELECT payload, first_seen_at FROM operating_products WHERE object_id = ?", (object_id,)).fetchone()
                    product_payload = _merge_payload(loads(existing_product["payload"]) if existing_product else {}, row, data_version=data_version, dataset_name=dataset_name, ownership=ownership, raw_store_id=raw_store_id, raw_store_name=raw_store_name, normalized_store_id=normalized_store_id, normalized_store_name=normalized_store_name)
                    product_payload["source"] = source
                    title = _title(row, product_id)
                    category = _category(row)
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO operating_products (
                            object_id, product_id, store_id, store_name, platform, title, category, latest_data_version, source_dataset, payload, first_seen_at, updated_at,
                            imported_by_user_id, imported_by_role_id, owner_user_id, assigned_operator_id, reviewer_id, visible_user_ids, visible_role_ids,
                            raw_store_id, raw_store_name, normalized_store_id, normalized_store_name, data_scope_source
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            object_id,
                            product_id,
                            normalized_store_id,
                            normalized_store_name,
                            platform,
                            title,
                            category,
                            data_version,
                            dataset_name,
                            dumps(product_payload),
                            existing_product["first_seen_at"] if existing_product else now,
                            now,
                            ownership.get("importedByUserId"),
                            ownership.get("importedByRoleId"),
                            ownership.get("ownerUserId"),
                            ownership.get("assignedOperatorId"),
                            ownership.get("reviewerId"),
                            json.dumps(ownership.get("visibleUserIds") or [], ensure_ascii=False),
                            json.dumps(ownership.get("visibleRoleIds") or [], ensure_ascii=False),
                            raw_store_id,
                            raw_store_name,
                            normalized_store_id,
                            normalized_store_name,
                            DATA_SCOPE_SOURCE,
                        ),
                    )
                    product_ids.add(object_id)
        for store_key in store_keys:
            count = conn.execute("SELECT COUNT(*) AS count FROM operating_products WHERE normalized_store_id = ? OR store_id = ?", (store_key, store_key)).fetchone()["count"]
            conn.execute("UPDATE operating_stores SET product_count = ?, updated_at = ? WHERE store_key = ?", (count, now, store_key))
        conn.commit()
    return {
        "version": OPERATING_OBJECT_VERSION,
        "source": source,
        "importedByUserId": ownership.get("importedByUserId"),
        "assignedOperatorId": ownership.get("assignedOperatorId"),
        "cleanedRowCount": len(seen_row_keys),
        "classifiedRowCount": classified_rows,
        "productUpsertCount": len(product_ids),
        "storeUpsertCount": len(store_keys),
        "dataScopeSource": DATA_SCOPE_SOURCE,
        "rule": "V12：经营对象使用系统编码承接商品/店铺/SKU身份，指标事实沉淀到 payload.metricFacts。",
    }


def _visible_for_user(row: Mapping[str, Any] | Any, user_id: str | None) -> bool:
    if not user_id:
        return True
    user = current_user(user_id)
    role = user.get("roleId")
    if role in {"owner", "manager", "finance"}:
        return True
    visible_user_ids = set(_json_list(_row_get(row, "visible_user_ids", "visibleUserIds")))
    if user_id in visible_user_ids:
        return True
    if user_id in {_row_get(row, "assigned_operator_id", "assignedOperatorId"), _row_get(row, "owner_user_id", "ownerUserId"), _row_get(row, "imported_by_user_id", "importedByUserId")}:
        return True
    store_id = _text(_row_get(row, "store_id", "normalized_store_id", "storeId", "normalizedStoreId"))
    if not store_id:
        return True
    return store_id in set(visible_store_ids_for_user(user_id))


def _formatted_payload_metrics(payload: Dict[str, Any]) -> Dict[str, str]:
    return {
        "inventory": format_metric("inventory_qty", metric_value(payload, "inventory_qty")),
        "sellableDays": format_metric("sellable_days", metric_value(payload, "sellable_days")),
        "avgOrderValue": format_metric("avg_order_value", metric_value(payload, "avg_order_value")),
        "paymentAmount": format_metric("payment_amount", metric_value(payload, "payment_amount")),
        "costAmount": format_metric("product_cost_amount", metric_value(payload, "product_cost_amount")),
        "grossProfitAmount": format_metric("gross_profit_amount", metric_value(payload, "gross_profit_amount")),
        "grossMargin": format_metric("gross_margin_rate", metric_value(payload, "gross_margin_rate")),
        "roi": format_metric("roi", metric_value(payload, "roi")),
        "clickRate": format_metric("click_rate", metric_value(payload, "click_rate")),
        "conversionRate": format_metric("payment_conversion_rate", metric_value(payload, "payment_conversion_rate")),
        "refundRate": format_metric("refund_rate", metric_value(payload, "refund_rate")),
        "adSpend": format_metric("ad_spend", metric_value(payload, "ad_spend")),
        "organicVisitors": format_metric("organic_visitor_count", metric_value(payload, "organic_visitor_count")),
        "paidVisitors": format_metric("paid_visitor_count", metric_value(payload, "paid_visitor_count")),
    }


def list_operating_products(user_id: str | None = None) -> List[Dict[str, Any]]:
    ensure_operating_object_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM operating_products ORDER BY updated_at DESC, product_id ASC").fetchall()
    result: List[Dict[str, Any]] = []
    for row in rows:
        if not _visible_for_user(row, user_id):
            continue
        payload = loads(row["payload"])
        identity = payload.get("productIdentity") or product_identity(payload)
        codes = payload.get("systemCodes") or system_codes(payload)
        metrics = _formatted_payload_metrics(payload)
        title = row["title"] or identity.get("productId") or row["product_id"]
        result.append({
            "id": row["product_id"],
            "objectId": row["object_id"],
            "productId": row["product_id"],
            "skuId": identity.get("skuId"),
            "erpProductCode": identity.get("erpProductCode"),
            "productLink": identity.get("productLink"),
            "systemStoreCode": codes.get("systemStoreCode"),
            "systemSpuCode": codes.get("systemSpuCode"),
            "systemLinkCode": codes.get("systemLinkCode"),
            "systemSkuCode": codes.get("systemSkuCode"),
            "storeId": row["normalized_store_id"] or row["store_id"],
            "store": row["normalized_store_name"] or row["store_name"],
            "storeName": row["normalized_store_name"] or row["store_name"],
            "platform": row["platform"],
            "title": title,
            "shortName": display_short_title(payload, fallback=str(row["product_id"])),
            "category": row["category"],
            "latestDataVersion": row["latest_data_version"],
            "sourceDataset": row["source_dataset"],
            "sourceDatasets": payload.get("sourceDatasets") or ([row["source_dataset"]] if row["source_dataset"] else []),
            "sourceDataVersions": [row["latest_data_version"]] if row["latest_data_version"] else [],
            "importedByUserId": row["imported_by_user_id"],
            "ownerUserId": row["owner_user_id"],
            "assignedOperatorId": row["assigned_operator_id"],
            "reviewerId": row["reviewer_id"],
            "visibleUserIds": _json_list(row["visible_user_ids"]),
            "visibleRoleIds": _json_list(row["visible_role_ids"]),
            "rawStoreId": row["raw_store_id"],
            "rawStoreName": row["raw_store_name"],
            "normalizedStoreId": row["normalized_store_id"],
            "normalizedStoreName": row["normalized_store_name"],
            "dataScopeSource": row["data_scope_source"] or DATA_SCOPE_SOURCE,
            "imageLabel": "品",
            "inventory": metrics["inventory"],
            "inventoryStatus": "已入库" if metrics["inventory"] != "—" else "待补库存",
            "inventoryLevel": "good",
            "price": metrics["avgOrderValue"],
            "avgOrderValue": metrics["avgOrderValue"],
            "paymentAmount": metrics["paymentAmount"],
            "cost": metrics["costAmount"],
            "costAmount": metrics["costAmount"],
            "grossProfitAmount": metrics["grossProfitAmount"],
            "grossMargin": metrics["grossMargin"],
            "roi": metrics["roi"],
            "clickRate": metrics["clickRate"],
            "conversionRate": metrics["conversionRate"],
            "refundRate": metrics["refundRate"],
            "adSpend": metrics["adSpend"],
            "organicVisitors": metrics["organicVisitors"],
            "paidVisitors": metrics["paidVisitors"],
            "afterSales": "标签观察" if metrics["refundRate"] == "—" else f"退款率 {metrics['refundRate']}",
            "afterSalesLevel": "good",
            "suggestion": "商品档案已完成V12指标事实入库；任务由经营判断和证据闸门单独生成。",
            "metricFacts": payload.get("metricFacts") or [],
            "objectStoreVersion": OPERATING_OBJECT_VERSION,
            "payload": payload,
        })
    return result


def list_operating_stores(user_id: str | None = None) -> List[Dict[str, Any]]:
    ensure_operating_object_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM operating_stores ORDER BY updated_at DESC, store_name ASC").fetchall()
    result: List[Dict[str, Any]] = []
    for row in rows:
        if not _visible_for_user(row, user_id):
            continue
        payload = loads(row["payload"])
        result.append({
            "storeId": row["normalized_store_id"] or row["store_id"],
            "storeName": row["normalized_store_name"] or row["store_name"],
            "displayName": row["normalized_store_name"] or row["store_name"],
            "platform": row["platform"],
            "productCount": row["product_count"] or 0,
            "latestDataVersion": row["latest_data_version"],
            "sourceDataset": row["source_dataset"],
            "importedByUserId": row["imported_by_user_id"],
            "ownerUserId": row["owner_user_id"],
            "assignedOperatorId": row["assigned_operator_id"],
            "reviewerId": row["reviewer_id"],
            "visibleUserIds": _json_list(row["visible_user_ids"]),
            "visibleRoleIds": _json_list(row["visible_role_ids"]),
            "rawStoreId": row["raw_store_id"],
            "rawStoreName": row["raw_store_name"],
            "normalizedStoreId": row["normalized_store_id"],
            "normalizedStoreName": row["normalized_store_name"],
            "dataScopeSource": row["data_scope_source"] or DATA_SCOPE_SOURCE,
            "businessTags": ["已入库", "V12指标事实"],
            "riskTags": ["已入库"],
            "productRoleTags": [f"商品 {row['product_count'] or 0}"],
            "storeWeightTag": "经营对象",
            "activeTaskCount": 0,
            "alertCount": 0,
            "taskIntensity": "标签观察",
            "level": "watch",
            "judgment": "已完成清洗入库，店铺事实由V12画像和指标目录承接",
            "objectStoreVersion": OPERATING_OBJECT_VERSION,
            "payload": payload,
        })
    return result


def operating_object_summary(user_id: str | None = None) -> Dict[str, Any]:
    products = list_operating_products(user_id)
    stores = list_operating_stores(user_id)
    metric_fact_count = sum(len(item.get("metricFacts") or []) for item in products)
    return {
        "version": OPERATING_OBJECT_VERSION,
        "productCount": len(products),
        "storeCount": len(stores),
        "metricFactCount": metric_fact_count,
        "latestDataVersion": next((item.get("latestDataVersion") for item in products if item.get("latestDataVersion")), None),
        "rule": "V12：经营对象入库优先于任务；商品页展示定位和指标事实，任务页展示交叉验证和SOP。",
    }
