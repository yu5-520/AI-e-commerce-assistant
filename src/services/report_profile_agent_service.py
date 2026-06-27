"""V12 report profile agent service.

This is a deterministic agent-shaped gateway: it reads file metadata, sheet names,
headers, and sample rows, then returns a structured import plan.  It does not read
full product rows with an LLM and it does not create tasks.  The goal is to decide
how code should read the report before facts enter product/store/traffic tables.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from src.services.metric_catalog_service import CATALOG_VERSION, canonical_field, recognized_fields

REPORT_PROFILE_VERSION = "12.0.0"

SHEET_RULES = [
    {
        "target": "product_metric_facts",
        "kind": "商品经营明细",
        "keywords": ["商品", "经营", "明细", "SKU", "商品ID"],
        "required_any": ["product_id", "sku_id", "roi", "gross_margin_rate", "inventory_qty", "payment_amount"],
    },
    {
        "target": "store_metric_facts",
        "kind": "店铺经营汇总",
        "keywords": ["店铺", "汇总", "经营单元"],
        "required_any": ["store_id", "store_name", "payment_amount", "roi", "refund_rate"],
    },
    {
        "target": "traffic_source_facts",
        "kind": "流量来源明细",
        "keywords": ["流量", "来源", "渠道"],
        "required_any": ["traffic_source", "visitor_count", "click_rate", "roi", "ad_spend"],
    },
]


def _sheet_rows(parsed: Dict[str, Any], sheet_name: str) -> List[Dict[str, Any]]:
    sheet_rows = parsed.get("sheetRows") or {}
    if isinstance(sheet_rows, dict) and isinstance(sheet_rows.get(sheet_name), list):
        return [row for row in sheet_rows[sheet_name] if isinstance(row, dict)]
    rows = parsed.get("rows") or []
    return [row for row in rows if isinstance(row, dict) and row.get("__source_sheet") == sheet_name]


def _headers_from_sheet(sheet: Dict[str, Any], rows: List[Dict[str, Any]]) -> List[str]:
    headers = [str(item) for item in sheet.get("headers", []) if item not in {None, ""}]
    if headers:
        return headers
    seen: List[str] = []
    for row in rows[:10]:
        for key in row.keys():
            if key not in seen and key != "__source_sheet":
                seen.append(str(key))
    return seen


def _noise_ratio(rows: List[Dict[str, Any]], headers: List[str]) -> Dict[str, Any]:
    if not rows or not headers:
        return {"emptyCellRatio": 0, "garbledCellCount": 0, "sampleSize": 0}
    total = 0
    empty = 0
    garbled = 0
    for row in rows[:50]:
        for header in headers:
            value = row.get(header)
            total += 1
            if value in {None, ""}:
                empty += 1
            if isinstance(value, str) and "�" in value:
                garbled += 1
    return {
        "emptyCellRatio": round(empty / total, 4) if total else 0,
        "garbledCellCount": garbled,
        "sampleSize": min(len(rows), 50),
    }


def _target_for_sheet(sheet_name: str, headers: List[str]) -> Dict[str, Any]:
    canonical_headers = {canonical_field(header) for header in headers if canonical_field(header)}
    name_text = sheet_name.lower()
    scored: List[Dict[str, Any]] = []
    for rule in SHEET_RULES:
        keyword_hits = sum(1 for keyword in rule["keywords"] if keyword.lower() in name_text or keyword in sheet_name)
        field_hits = sum(1 for field in rule["required_any"] if field in canonical_headers)
        score = keyword_hits * 3 + field_hits
        scored.append({"rule": rule, "score": score, "keywordHits": keyword_hits, "fieldHits": field_hits})
    best = max(scored, key=lambda item: item["score"])
    rule = best["rule"]
    confidence = min(0.98, 0.45 + best["keywordHits"] * 0.15 + best["fieldHits"] * 0.07)
    if best["score"] <= 1:
        return {"targetTable": "staging_rows", "sheetKind": "未知报表", "confidence": 0.35, "routeReason": "未识别到足够字段，只进入候选暂存。"}
    return {
        "targetTable": rule["target"],
        "sheetKind": rule["kind"],
        "confidence": round(confidence, 2),
        "routeReason": f"命中 {best['keywordHits']} 个名称关键词、{best['fieldHits']} 个标准字段。",
    }


def _profile_sheet(parsed: Dict[str, Any], sheet: Dict[str, Any]) -> Dict[str, Any]:
    sheet_name = str(sheet.get("sheetName") or "Sheet")
    rows = _sheet_rows(parsed, sheet_name)
    headers = _headers_from_sheet(sheet, rows)
    recognized = recognized_fields(headers)
    canonical_counts = Counter(item["canonicalField"] for item in recognized)
    route = _target_for_sheet(sheet_name, headers)
    identity_fields = [field for field in ["platform", "store_id", "store_name", "product_id", "sku_id", "erp_product_code", "product_link", "stat_date", "traffic_source"] if canonical_counts.get(field)]
    metric_fields = [field for field in canonical_counts if field not in identity_fields and field not in {"product_name", "product_tag", "category_l1", "category_l2"}]
    display_only = [field for field in ["product_name", "product_tag", "category_l1", "category_l2"] if canonical_counts.get(field)]
    issues: List[Dict[str, Any]] = []
    if route["targetTable"] in {"product_metric_facts", "traffic_source_facts"} and not any(field in identity_fields for field in ["product_id", "sku_id", "erp_product_code", "product_link"]):
        issues.append({"severity": "blocked", "message": "缺少商品可定位锚点，不能进入正式商品事实。"})
    if not any(field in identity_fields for field in ["store_id", "store_name"]):
        issues.append({"severity": "warning", "message": "未识别到店铺归属字段，将使用上传人/历史映射兜底。"})
    noise = _noise_ratio(rows, headers)
    if noise["garbledCellCount"]:
        issues.append({"severity": "warning", "message": f"发现 {noise['garbledCellCount']} 个局部乱码单元格，相关字段会降低置信度。"})
    return {
        "sheetName": sheet_name,
        "sheetKind": route["sheetKind"],
        "targetTable": route["targetTable"],
        "rowCount": int(sheet.get("rowCount") or len(rows)),
        "headers": headers,
        "recognizedFields": recognized,
        "identityFields": identity_fields,
        "metricFields": metric_fields,
        "displayOnlyFields": display_only,
        "ignoredAsPrimaryKey": ["product_name"] if "product_name" in display_only else [],
        "confidence": route["confidence"],
        "routeReason": route["routeReason"],
        "quality": noise,
        "issues": issues,
        "sampleRows": rows[:3],
    }


def build_report_profile(parsed: Dict[str, Any]) -> Dict[str, Any]:
    sheets = parsed.get("sheets") or []
    sheet_profiles = [_profile_sheet(parsed, sheet) for sheet in sheets if isinstance(sheet, dict)]
    blocking = [issue for sheet in sheet_profiles for issue in sheet.get("issues", []) if issue.get("severity") == "blocked"]
    warnings = [issue for sheet in sheet_profiles for issue in sheet.get("issues", []) if issue.get("severity") == "warning"]
    targets = sorted({sheet.get("targetTable") for sheet in sheet_profiles if sheet.get("targetTable")})
    avg_conf = round(sum(float(sheet.get("confidence") or 0) for sheet in sheet_profiles) / len(sheet_profiles), 2) if sheet_profiles else 0
    return {
        "version": REPORT_PROFILE_VERSION,
        "metricCatalogVersion": CATALOG_VERSION,
        "fileName": parsed.get("fileName"),
        "format": parsed.get("format"),
        "sheetCount": parsed.get("sheetCount", len(sheet_profiles)),
        "totalRows": parsed.get("totalRows", 0),
        "targetFactTables": targets,
        "sheetProfiles": sheet_profiles,
        "confidence": avg_conf,
        "status": "blocked" if blocking else "needs_attention" if warnings else "ready",
        "blockingIssueCount": len(blocking),
        "warningIssueCount": len(warnings),
        "rule": "V12：Agent只判断报表结构和字段映射，代码脚本按画像批量读取，任务不因普通缺字段自动生成。",
    }
