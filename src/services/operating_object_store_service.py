"""Operating object master store.

V11.8 rule:

- report content is business data, not the permission source;
- the uploading account is the source of data ownership for normal operator imports;
- a new store discovered in a report is created directly under the uploader's
  operating scope;
- store migration between operators is a separate permission workflow.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.account_service import current_user, default_reviewer, visible_store_ids_for_user
from src.services.import_row_store_service import load_import_rows
from src.services.report_alert_service import now_iso

OPERATING_OBJECT_VERSION = "11.8.0"
DATA_SCOPE_SOURCE = "uploader_account"


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


def _pick(row: Dict[str, Any], *fields: str, default: Any = None) -> Any:
    for field in fields:
        value = row.get(field)
        if value not in {None, ""}:
            return value
    return default


def _text(value: Any) -> str:
    return str(value or "").strip()


def _product_id(row: Dict[str, Any]) -> str | None:
    value = _pick(row, "product_id", "productId", "商品ID", "商品id", "sku", "SKU", "商品编码", "商家编码", "商品编号", "宝贝ID", "货号")
    text = _text(value)
    return text or None


def _raw_store_id(row: Dict[str, Any]) -> str | None:
    value = _pick(row, "store_id", "storeId", "店铺ID", "店铺id", "店铺编号", "店铺编码")
    text = _text(value)
    return text or None


def _raw_store_name(row: Dict[str, Any]) -> str | None:
    value = _pick(row, "store_name", "store", "storeName", "店铺", "店铺名称", "店铺名", "门店", "店名")
    text = _text(value)
    if text and text not in {"未绑定店铺", "导入数据店铺", "GLOBAL"}:
        return text
    return None


def _fallback_store_key(uploader_user_id: str | None) -> str:
    return f"IMPORT_STORE_{uploader_user_id or 'SYSTEM'}"


def _store_key(row: Dict[str, Any], uploader_user_id: str | None = None) -> str:
    raw_id = _raw_store_id(row)
    if raw_id:
        return raw_id
    name = _raw_store_name(row)
    if name:
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10].upper()
        return f"STORE_{digest}"
    return _fallback_store_key(uploader_user_id)


def _platform(row: Dict[str, Any]) -> str:
    return _text(_pick(row, "platform", "平台", "渠道", "来源平台", default="导入平台")) or "导入平台"


def _title(row: Dict[str, Any], product_id: str) -> str:
    return _text(_pick(row, "product_name", "productTitle", "商品名称", "商品名", "title", "标题", "宝贝标题", default=f"导入商品 {product_id}")) or f"导入商品 {product_id}"


def _category(row: Dict[str, Any]) -> str:
    return _text(_pick(row, "category", "类目", "商品类目", "垂直类目", "品类", "平台类目", default="未分类")) or "未分类"


def _object_id(product_id: str, store_key: str | None) -> str:
    return f"{store_key or 'GLOBAL'}::{product_id}"


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
        "rule": "正常报表导入由上传账号决定商品/店铺归属；新店铺直接创建，权限迁移才需要接收确认。",
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
                    object_id = _object_id(product_id, store_key)
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
        "rule": "上传账号决定导入数据归属；报表出现新店铺时直接创建并归属上传账号，权限迁移才需要确认接收。",
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


def list_operating_products(user_id: str | None = None) -> List[Dict[str, Any]]:
    ensure_operating_object_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM operating_products ORDER BY updated_at DESC, product_id ASC").fetchall()
    result: List[Dict[str, Any]] = []
    for row in rows:
        if not _visible_for_user(row, user_id):
            continue
        payload = loads(row["payload"])
        result.append({
            "id": row["product_id"],
            "productId": row["product_id"],
            "storeId": row["normalized_store_id"] or row["store_id"],
            "store": row["normalized_store_name"] or row["store_name"],
            "storeName": row["normalized_store_name"] or row["store_name"],
            "platform": row["platform"],
            "title": row["title"],
            "shortName": str(row["title"] or row["product_id"])[:8],
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
            "inventory": _text(_pick(payload, "stock", "available_stock", "current_stock", "库存", "可用库存", "当前库存", default="—")) or "—",
            "inventoryStatus": "已入库",
            "inventoryLevel": "good",
            "price": _text(_pick(payload, "sale_price", "售价", "销售价", "活动价", "成交价", default="—")) or "—",
            "cost": _text(_pick(payload, "cost_price", "成本", "成本价", "采购价", default="—")) or "—",
            "grossMargin": _text(_pick(payload, "gross_margin", "毛利率", default="—")) or "—",
            "afterSales": "标签观察",
            "afterSalesLevel": "good",
            "suggestion": "已完成清洗入库；是否生成任务由风险判断单独决定。",
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
            "businessTags": ["已入库"],
            "riskTags": ["已入库"],
            "productRoleTags": [f"商品 {row['product_count'] or 0}"],
            "storeWeightTag": "经营对象",
            "activeTaskCount": 0,
            "alertCount": 0,
            "taskIntensity": "标签观察",
            "level": "watch",
            "judgment": "已完成清洗入库",
            "objectStoreVersion": OPERATING_OBJECT_VERSION,
            "payload": payload,
        })
    return result


def operating_object_summary(user_id: str | None = None) -> Dict[str, Any]:
    products = list_operating_products(user_id)
    stores = list_operating_stores(user_id)
    return {
        "version": OPERATING_OBJECT_VERSION,
        "productCount": len(products),
        "storeCount": len(stores),
        "latestDataVersion": next((item.get("latestDataVersion") for item in products if item.get("latestDataVersion")), None),
        "rule": "经营对象入库优先于标签和任务；上传账号决定正常报表导入归属。",
    }
