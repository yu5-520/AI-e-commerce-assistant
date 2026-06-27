"""V12.1.5 import diagnostics and acceptance report.

The diagnostics endpoint is for demo trust: after uploading a report, the user can
see what the system recognized, which facts were written, and which gaps were only
logged.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.repositories.sqlite_repository import connect
from src.services.data_gap_event_service import data_gap_summary, ensure_data_gap_tables
from src.services.metric_fact_store_service import FACT_TABLES, ensure_metric_fact_tables, metric_fact_summary

IMPORT_DIAGNOSTICS_VERSION = "12.1.5"


def _table_exists(conn: Any, table: str) -> bool:
    return bool(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def _latest_data_version(conn: Any) -> str | None:
    candidates: List[str] = []
    for table in ["product_metric_facts", "store_metric_facts", "traffic_source_facts", "data_gap_events", "data_snapshots"]:
        if not _table_exists(conn, table):
            continue
        column = "data_version" if table != "data_snapshots" else None
        if column:
            row = conn.execute(f"SELECT data_version FROM {table} WHERE data_version IS NOT NULL AND data_version != '' ORDER BY updated_at DESC LIMIT 1").fetchone()
            if row and row["data_version"]:
                candidates.append(row["data_version"])
        else:
            row = conn.execute("SELECT payload FROM data_snapshots ORDER BY created_at DESC LIMIT 1").fetchone()
            # Keep this branch deliberately conservative; diagnostics still work without it.
    return candidates[0] if candidates else None


def _fact_rows(conn: Any, data_version: str | None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for table in FACT_TABLES:
        if not _table_exists(conn, table):
            continue
        if data_version:
            query = f"SELECT source_sheet, target_table, metric_code, raw_field_name, COUNT(*) AS count FROM (SELECT *, ? AS target_table FROM {table} WHERE data_version = ?) GROUP BY source_sheet, target_table, metric_code, raw_field_name"
            params = (table, data_version)
        else:
            query = f"SELECT source_sheet, target_table, metric_code, raw_field_name, COUNT(*) AS count FROM (SELECT *, ? AS target_table FROM {table}) GROUP BY source_sheet, target_table, metric_code, raw_field_name"
            params = (table,)
        rows.extend(dict(row) for row in conn.execute(query, params).fetchall())
    return rows


def _gap_rows(conn: Any, data_version: str | None) -> List[Dict[str, Any]]:
    ensure_data_gap_tables()
    if data_version:
        rows = conn.execute(
            """
            SELECT source_sheet, target_table, gap_type, metric_code, identity_field, severity, is_decision_blocking, COUNT(*) AS count
            FROM data_gap_events
            WHERE data_version = ?
            GROUP BY source_sheet, target_table, gap_type, metric_code, identity_field, severity, is_decision_blocking
            ORDER BY count DESC
            """,
            (data_version,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT source_sheet, target_table, gap_type, metric_code, identity_field, severity, is_decision_blocking, COUNT(*) AS count
            FROM data_gap_events
            GROUP BY source_sheet, target_table, gap_type, metric_code, identity_field, severity, is_decision_blocking
            ORDER BY count DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def import_diagnostics(data_version: str | None = None) -> Dict[str, Any]:
    ensure_metric_fact_tables()
    ensure_data_gap_tables()
    with connect() as conn:
        version = data_version or _latest_data_version(conn)
        facts = _fact_rows(conn, version)
        gaps = _gap_rows(conn, version)

    sheet_map: Dict[str, Dict[str, Any]] = {}
    for fact in facts:
        sheet = fact.get("source_sheet") or "未知Sheet"
        item = sheet_map.setdefault(sheet, {"sheetName": sheet, "targetTables": {}, "factCount": 0, "recognizedMetrics": {}, "gapCount": 0, "blockingGapCount": 0, "issues": []})
        target = fact.get("target_table") or "unknown"
        item["targetTables"][target] = item["targetTables"].get(target, 0) + int(fact.get("count") or 0)
        item["factCount"] += int(fact.get("count") or 0)
        metric = fact.get("metric_code") or "unknown"
        item["recognizedMetrics"][metric] = item["recognizedMetrics"].get(metric, 0) + int(fact.get("count") or 0)
    for gap in gaps:
        sheet = gap.get("source_sheet") or "未知Sheet"
        item = sheet_map.setdefault(sheet, {"sheetName": sheet, "targetTables": {}, "factCount": 0, "recognizedMetrics": {}, "gapCount": 0, "blockingGapCount": 0, "issues": []})
        count = int(gap.get("count") or 0)
        item["gapCount"] += count
        if int(gap.get("is_decision_blocking") or 0):
            item["blockingGapCount"] += count
        item["issues"].append({
            "gapType": gap.get("gap_type"),
            "metricCode": gap.get("metric_code"),
            "identityField": gap.get("identity_field"),
            "severity": gap.get("severity"),
            "decisionBlocking": bool(gap.get("is_decision_blocking")),
            "count": count,
        })

    sheets = []
    for item in sheet_map.values():
        item["targetTables"] = [{"targetTable": key, "factCount": value} for key, value in sorted(item["targetTables"].items())]
        item["recognizedMetrics"] = [{"metricCode": key, "factCount": value} for key, value in sorted(item["recognizedMetrics"].items())]
        item["acceptanceStatus"] = "blocked" if item["blockingGapCount"] else "passed_with_logged_gaps" if item["gapCount"] else "passed"
        sheets.append(item)
    sheets.sort(key=lambda item: (item["acceptanceStatus"], item["sheetName"]))

    fact_summary = metric_fact_summary()
    gap_summary = data_gap_summary()
    return {
        "version": IMPORT_DIAGNOSTICS_VERSION,
        "dataVersion": version,
        "sheetCount": len(sheets),
        "factSummary": fact_summary,
        "gapSummary": gap_summary,
        "sheets": sheets,
        "acceptance": {
            "factWritten": fact_summary.get("factCount", 0) > 0,
            "hasDecisionBlockingGap": gap_summary.get("decisionBlockingGapCount", 0) > 0,
            "status": "blocked" if gap_summary.get("decisionBlockingGapCount", 0) else "passed_with_logged_gaps" if gap_summary.get("gapCount", 0) else "passed",
            "rule": "导入验收看事实写入和决策缺口；普通缺口不代表任务失败。",
        },
        "rule": "V12.1.5：返回 Sheet 识别、字段命中、事实写入数量和阻塞问题，辅助 Demo 验收。",
    }
