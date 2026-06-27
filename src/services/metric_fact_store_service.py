"""V12.1 independent metric fact store.

V12 kept metric facts inside operating object payloads so the demo could validate
field mapping quickly. V12.1 promotes those facts into queryable SQLite tables:
product_metric_facts, store_metric_facts, and traffic_source_facts.

V12.1.1 adds explicit sheet-profile routing: upload confirmation writes facts
by reportProfile.sheetProfiles + parsed.sheetRows instead of treating a multi-sheet
Excel as one flattened table.

Boundary:
    This layer stores evidence. It does not generate tasks. Task creation must
    read facts through a later evidence gate so ordinary missing fields do not
    become task noise.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List

from src.repositories.sqlite_repository import connect, dumps
from src.services.metric_catalog_service import (
    CATALOG_VERSION,
    METRIC_ALIASES,
    extract_metric_facts,
    pick,
    product_identity,
    stable_code,
    system_codes,
)
from src.services.report_alert_service import now_iso

METRIC_FACT_STORE_VERSION = "12.1.1"

FACT_TABLES = ("product_metric_facts", "store_metric_facts", "traffic_source_facts")


def ensure_metric_fact_tables() -> None:
    with connect() as conn:
        for table in FACT_TABLES:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    fact_id TEXT PRIMARY KEY,
                    tenant_id TEXT,
                    org_id TEXT,
                    data_version TEXT,
                    dataset_name TEXT,
                    source_system TEXT,
                    source_sheet TEXT,
                    source_report_id TEXT,
                    entity_level TEXT NOT NULL,
                    store_code TEXT,
                    spu_code TEXT,
                    link_code TEXT,
                    sku_code TEXT,
                    platform TEXT,
                    store_id TEXT,
                    store_name TEXT,
                    product_id TEXT,
                    sku_id TEXT,
                    erp_product_code TEXT,
                    product_link TEXT,
                    traffic_source TEXT,
                    metric_code TEXT NOT NULL,
                    metric_value REAL,
                    display_value TEXT,
                    raw_field_name TEXT,
                    raw_value TEXT,
                    stat_date TEXT,
                    time_window TEXT,
                    confidence REAL DEFAULT 1,
                    payload TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_entity ON {table}(store_code, spu_code, link_code, sku_code)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_metric ON {table}(metric_code, stat_date)")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_version ON {table}(data_version, dataset_name)")
        conn.commit()


def _import_items(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = result.get("results")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    return [result]


def _first_import_item(result: Dict[str, Any]) -> Dict[str, Any]:
    items = _import_items(result)
    return items[0] if items else result


def _row_dataset(row: Dict[str, Any], fallback: str | None = None) -> str | None:
    value = row.get("datasetName") or row.get("dataset_name") or fallback
    return str(value) if value not in {None, ""} else None


def _row_version(row: Dict[str, Any], fallback: str | None = None) -> str | None:
    value = row.get("dataVersion") or row.get("data_version") or fallback
    return str(value) if value not in {None, ""} else None


def _profile_sheets(report_profile: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    if not isinstance(report_profile, dict):
        return []
    return [sheet for sheet in (report_profile.get("sheetProfiles") or []) if isinstance(sheet, dict)]


def _profile_routes(report_profile: Dict[str, Any] | None) -> Dict[str, str]:
    routes: Dict[str, str] = {}
    for sheet in _profile_sheets(report_profile):
        name = str(sheet.get("sheetName") or "")
        target = str(sheet.get("targetTable") or "")
        if name and target in FACT_TABLES:
            routes[name] = target
    return routes


def _profile_by_sheet(report_profile: Dict[str, Any] | None) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for sheet in _profile_sheets(report_profile):
        name = str(sheet.get("sheetName") or "")
        if name:
            result[name] = sheet
    return result


def _sheet_blocked(sheet_profile: Dict[str, Any] | None) -> bool:
    if not isinstance(sheet_profile, dict):
        return False
    for issue in sheet_profile.get("issues") or []:
        if isinstance(issue, dict) and issue.get("severity") == "blocked":
            return True
    return False


def _infer_target_table(row: Dict[str, Any], routes: Dict[str, str]) -> str:
    sheet_name = str(row.get("__source_sheet") or "")
    if sheet_name in routes:
        return routes[sheet_name]
    if any(keyword in sheet_name for keyword in ["流量", "来源", "渠道"]):
        return "traffic_source_facts"
    if any(keyword in sheet_name for keyword in ["店铺", "汇总", "经营单元"]):
        return "store_metric_facts"
    if pick(row, "traffic_source"):
        return "traffic_source_facts"
    ident = product_identity(row)
    if ident.get("productId") or ident.get("skuId") or ident.get("erpProductCode") or ident.get("productLink"):
        return "product_metric_facts"
    return "store_metric_facts"


def _entity_level(table: str, row: Dict[str, Any]) -> str:
    if table == "traffic_source_facts":
        return "traffic_source"
    if table == "store_metric_facts":
        return "store"
    ident = product_identity(row)
    if ident.get("skuId"):
        return "sku"
    if ident.get("productLink") or ident.get("productId"):
        return "link"
    return "spu"


def _raw_field_name(row: Dict[str, Any], metric_code: str) -> str | None:
    aliases = [metric_code, *(METRIC_ALIASES.get(metric_code) or [])]
    normalized_aliases = {str(alias).lower().replace(" ", "") for alias in aliases}
    for key, value in row.items():
        if value in {None, ""}:
            continue
        normalized_key = str(key).lower().replace(" ", "")
        if normalized_key in normalized_aliases:
            return str(key)
    return metric_code


def _fact_id(table: str, row: Dict[str, Any], metric_code: str, *, data_version: str | None, dataset_name: str | None) -> str:
    ident = product_identity(row)
    codes = system_codes(row)
    source = "::".join(
        str(part or "")
        for part in [
            table,
            data_version,
            dataset_name,
            row.get("__source_sheet"),
            codes.get("systemStoreCode"),
            None if table == "store_metric_facts" else codes.get("systemSpuCode"),
            None if table == "store_metric_facts" else codes.get("systemLinkCode"),
            None if table == "store_metric_facts" else codes.get("systemSkuCode"),
            ident.get("statDate"),
            pick(row, "traffic_source") if table == "traffic_source_facts" else None,
            metric_code,
        ]
    )
    return hashlib.sha1(source.encode("utf-8")).hexdigest()


def _insert_fact(conn: Any, table: str, row: Dict[str, Any], fact: Dict[str, Any], *, data_version: str | None, dataset_name: str | None, source_system: str | None, source_report_id: str | None) -> None:
    ident = product_identity(row)
    codes = system_codes(row)
    metric_code = str(fact.get("metricCode") or "")
    raw_field_name = _raw_field_name(row, metric_code)
    now = now_iso()
    entity_level = _entity_level(table, row)
    traffic_source = str(pick(row, "traffic_source", default="") or "").strip() or None
    fact_id = _fact_id(table, row, metric_code, data_version=data_version, dataset_name=dataset_name)
    store_code = codes.get("systemStoreCode")
    spu_code = None if table == "store_metric_facts" else codes.get("systemSpuCode")
    link_code = None if table == "store_metric_facts" else codes.get("systemLinkCode")
    sku_code = None if table == "store_metric_facts" else codes.get("systemSkuCode")
    fact_payload = {
        "factStoreVersion": METRIC_FACT_STORE_VERSION,
        "catalogVersion": CATALOG_VERSION,
        "identity": ident,
        "systemCodes": codes,
        "sourceRowSheet": row.get("__source_sheet"),
        "sourceRowHash": stable_code("ROW", json.dumps(row, ensure_ascii=False, sort_keys=True)),
        "targetTable": table,
    }
    conn.execute(
        f"""
        INSERT OR REPLACE INTO {table} (
            fact_id, tenant_id, org_id, data_version, dataset_name, source_system, source_sheet, source_report_id,
            entity_level, store_code, spu_code, link_code, sku_code, platform, store_id, store_name, product_id, sku_id,
            erp_product_code, product_link, traffic_source, metric_code, metric_value, display_value, raw_field_name,
            raw_value, stat_date, time_window, confidence, payload, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM {table} WHERE fact_id = ?), ?), ?)
        """,
        (
            fact_id,
            str(row.get("tenant_id") or row.get("tenantId") or "default-tenant"),
            str(row.get("org_id") or row.get("orgId") or "default-org"),
            data_version,
            dataset_name,
            source_system,
            row.get("__source_sheet"),
            source_report_id,
            entity_level,
            store_code,
            spu_code,
            link_code,
            sku_code,
            ident.get("platform"),
            ident.get("storeId"),
            ident.get("storeName"),
            ident.get("productId"),
            ident.get("skuId"),
            ident.get("erpProductCode"),
            ident.get("productLink"),
            traffic_source,
            metric_code,
            fact.get("metricValue"),
            fact.get("displayValue"),
            raw_field_name,
            str(fact.get("rawValue")),
            ident.get("statDate"),
            str(row.get("timeWindow") or row.get("time_window") or "") or None,
            1.0,
            dumps(fact_payload),
            fact_id,
            now,
            now,
        ),
    )


def _fallback_dataset_version(result: Dict[str, Any]) -> tuple[str, str | None]:
    item = _first_import_item(result)
    fallback_dataset = str(item.get("datasetName") or result.get("datasetName") or "unknown")
    fallback_version = str(item.get("dataVersion") or result.get("dataVersion") or "") or None
    return fallback_dataset, fallback_version


def _ingest_row_list(
    conn: Any,
    rows: Iterable[Dict[str, Any]],
    *,
    table: str | None,
    routes: Dict[str, str],
    fallback_dataset: str,
    fallback_version: str | None,
    source_system: str | None,
    source_report_id: str | None,
) -> Dict[str, Any]:
    scanned = 0
    skipped_no_metric = 0
    inserted_by_table = {name: 0 for name in FACT_TABLES}
    for row in rows:
        if not isinstance(row, dict):
            continue
        scanned += 1
        facts = extract_metric_facts(row)
        if not facts:
            skipped_no_metric += 1
            continue
        target_table = table or _infer_target_table(row, routes)
        if target_table not in FACT_TABLES:
            continue
        dataset_name = _row_dataset(row, fallback_dataset)
        data_version = _row_version(row, fallback_version)
        for fact in facts:
            _insert_fact(conn, target_table, row, fact, data_version=data_version, dataset_name=dataset_name, source_system=source_system, source_report_id=source_report_id)
            inserted_by_table[target_table] += 1
    return {"scannedRowCount": scanned, "skippedNoMetricRowCount": skipped_no_metric, "insertedByTable": inserted_by_table}


def ingest_metric_facts_from_import(
    result: Dict[str, Any],
    rows: Iterable[Dict[str, Any]] | None,
    *,
    report_profile: Dict[str, Any] | None = None,
    source_system: str | None = None,
    source_report_id: str | None = None,
) -> Dict[str, Any]:
    """Persist metric facts from normalized import rows.

    Rows without recognized metric values are ignored. Missing fields are not
    emitted as tasks or gaps here; a later data gap store will separate ordinary
    gaps from decision-blocking gaps.
    """
    ensure_metric_fact_tables()
    materialized = [row for row in (rows or []) if isinstance(row, dict)]
    routes = _profile_routes(report_profile)
    fallback_dataset, fallback_version = _fallback_dataset_version(result)
    with connect() as conn:
        summary = _ingest_row_list(
            conn,
            materialized,
            table=None,
            routes=routes,
            fallback_dataset=fallback_dataset,
            fallback_version=fallback_version,
            source_system=source_system,
            source_report_id=source_report_id,
        )
        conn.commit()
    inserted_by_table = summary["insertedByTable"]
    return {
        "version": METRIC_FACT_STORE_VERSION,
        "mode": "independent_metric_fact_tables_flattened_rows",
        "scannedRowCount": summary["scannedRowCount"],
        "skippedNoMetricRowCount": summary["skippedNoMetricRowCount"],
        "factCount": sum(inserted_by_table.values()),
        "productMetricFactCount": inserted_by_table["product_metric_facts"],
        "storeMetricFactCount": inserted_by_table["store_metric_facts"],
        "trafficSourceFactCount": inserted_by_table["traffic_source_facts"],
        "targetRoutes": routes,
        "rule": "V12.1.1：指标事实可按扁平行兜底入库；缺字段不在本层生成任务。",
    }


def ingest_metric_facts_from_sheet_rows(
    result: Dict[str, Any],
    parsed: Dict[str, Any],
    *,
    report_profile: Dict[str, Any] | None = None,
    source_system: str | None = None,
    source_report_id: str | None = None,
) -> Dict[str, Any]:
    """Persist metric facts by parsed.sheetRows and reportProfile.sheetProfiles.

    This is the V12.1.1 path for uploaded Excel files. It explicitly keeps the
    business meaning of each sheet instead of relying on a flattened row stream.
    """
    sheet_rows = parsed.get("sheetRows") if isinstance(parsed, dict) else None
    if not isinstance(sheet_rows, dict) or not sheet_rows:
        return ingest_metric_facts_from_import(result, parsed.get("rows") if isinstance(parsed, dict) else [], report_profile=report_profile, source_system=source_system, source_report_id=source_report_id)

    ensure_metric_fact_tables()
    profile = report_profile if isinstance(report_profile, dict) else {}
    routes = _profile_routes(profile)
    profiles = _profile_by_sheet(profile)
    fallback_dataset, fallback_version = _fallback_dataset_version(result)
    inserted_by_table = {name: 0 for name in FACT_TABLES}
    scanned_rows = 0
    skipped_no_metric = 0
    blocked_sheet_count = 0
    staging_sheet_count = 0
    sheet_summaries: List[Dict[str, Any]] = []

    with connect() as conn:
        sheet_names = list(sheet_rows.keys())
        for sheet_name in sheet_names:
            raw_rows = sheet_rows.get(sheet_name) or []
            sheet_profile = profiles.get(sheet_name)
            target_table = (sheet_profile or {}).get("targetTable") or routes.get(sheet_name)
            if _sheet_blocked(sheet_profile):
                blocked_sheet_count += 1
                sheet_summaries.append({"sheetName": sheet_name, "targetTable": target_table, "rowCount": len(raw_rows), "factCount": 0, "skipped": True, "reason": "profile_blocked"})
                continue
            if target_table not in FACT_TABLES:
                staging_sheet_count += 1
                sheet_summaries.append({"sheetName": sheet_name, "targetTable": target_table or "staging_rows", "rowCount": len(raw_rows), "factCount": 0, "skipped": True, "reason": "target_not_fact_table"})
                continue
            routed_rows: List[Dict[str, Any]] = []
            for row in raw_rows:
                if not isinstance(row, dict):
                    continue
                item = dict(row)
                item.setdefault("__source_sheet", sheet_name)
                routed_rows.append(item)
            before = dict(inserted_by_table)
            summary = _ingest_row_list(
                conn,
                routed_rows,
                table=str(target_table),
                routes=routes,
                fallback_dataset=fallback_dataset,
                fallback_version=fallback_version,
                source_system=source_system,
                source_report_id=source_report_id,
            )
            scanned_rows += summary["scannedRowCount"]
            skipped_no_metric += summary["skippedNoMetricRowCount"]
            for table_name, count in summary["insertedByTable"].items():
                inserted_by_table[table_name] += count
            sheet_fact_count = sum(inserted_by_table[name] - before.get(name, 0) for name in FACT_TABLES)
            sheet_summaries.append({
                "sheetName": sheet_name,
                "sheetKind": (sheet_profile or {}).get("sheetKind"),
                "targetTable": target_table,
                "rowCount": len(routed_rows),
                "factCount": sheet_fact_count,
                "skippedNoMetricRowCount": summary["skippedNoMetricRowCount"],
                "confidence": (sheet_profile or {}).get("confidence"),
            })
        conn.commit()

    return {
        "version": METRIC_FACT_STORE_VERSION,
        "mode": "profile_sheet_rows_metric_fact_routing",
        "scannedRowCount": scanned_rows,
        "skippedNoMetricRowCount": skipped_no_metric,
        "blockedSheetCount": blocked_sheet_count,
        "stagingSheetCount": staging_sheet_count,
        "factCount": sum(inserted_by_table.values()),
        "productMetricFactCount": inserted_by_table["product_metric_facts"],
        "storeMetricFactCount": inserted_by_table["store_metric_facts"],
        "trafficSourceFactCount": inserted_by_table["traffic_source_facts"],
        "targetRoutes": routes,
        "sheetSummaries": sheet_summaries,
        "rule": "V12.1.1：上传文件按 reportProfile.sheetProfiles + sheetRows 分 Sheet 写入事实表；普通缺字段不生成任务。",
    }


def metric_fact_summary() -> Dict[str, Any]:
    ensure_metric_fact_tables()
    summary: Dict[str, Any] = {"version": METRIC_FACT_STORE_VERSION}
    with connect() as conn:
        for table in FACT_TABLES:
            row = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
            summary[table] = row["count"] if row else 0
    summary["factCount"] = sum(summary.get(table, 0) for table in FACT_TABLES)
    summary["rule"] = "V12.1.1：事实层可被商品详情、趋势系统、任务证据闸门复用；上传文件按 Sheet 画像分流。"
    return summary
