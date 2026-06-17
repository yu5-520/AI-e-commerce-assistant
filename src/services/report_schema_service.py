"""V3.0.6 report schema preview and field mapping service.

Upload flow:
    rows -> field mapping -> import preview -> confirm import -> alert runtime

V3.0.6 adds store ownership mapping so imported rows can bind to store-scoped
alerts, task assignees, and operator-visible report slices.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, List

from src.services.report_alert_service import import_report_dataset

SCHEMA_VERSION = "3.0.6"

FIELD_LABELS = {
    "product_id": "商品ID",
    "customer_id": "客户ID",
    "store_id": "店铺ID",
    "store_name": "店铺名称",
    "available_stock": "当前库存",
    "safety_stock": "安全库存",
    "refund_amount": "退款金额",
    "refund_reason": "退款原因",
    "quantity": "购买件数",
    "actual_paid": "实付金额",
    "stock": "商品库存",
    "sale_price": "售价",
    "cost_price": "成本",
    "total_orders": "订单数",
    "refund_count": "退款次数",
}

REPORT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "inventory": {"label": "库存报表", "identity_fields": ["product_id"], "warning_fields": ["available_stock", "safety_stock"], "optional_fields": ["store_id", "store_name", "sku", "warehouse"], "alert_hint": "用于判断库存不足、库存承接和是否继续放量。"},
    "refunds": {"label": "退款报表", "identity_fields": ["product_id"], "warning_fields": ["refund_amount", "refund_reason"], "optional_fields": ["store_id", "store_name", "refund_id", "order_id", "refund_time"], "alert_hint": "用于判断退款异常、售后原因和商品承诺风险。"},
    "orders": {"label": "订单报表", "identity_fields": ["product_id"], "warning_fields": ["quantity", "actual_paid"], "optional_fields": ["store_id", "store_name", "order_id", "order_time", "buyer_id"], "alert_hint": "用于判断订单激增、库存承接和是否适合继续放量。"},
    "products": {"label": "商品报表", "identity_fields": ["product_id"], "warning_fields": ["stock", "sale_price", "cost_price"], "optional_fields": ["store_id", "store_name", "product_name", "category", "platform"], "alert_hint": "用于判断商品库存、价格、毛利和活动承接。"},
    "customers": {"label": "客户报表", "identity_fields": ["customer_id"], "warning_fields": ["total_orders", "refund_count"], "optional_fields": ["store_id", "store_name", "customer_name", "last_order_time", "tag"], "alert_hint": "用于判断售后敏感客户和客服处理边界。"},
}

FIELD_ALIASES: Dict[str, List[str]] = {
    "product_id": ["product_id", "商品ID", "商品id", "商品编码", "商家编码", "SKU", "sku", "sku编码", "货号", "款号", "商品编号"],
    "customer_id": ["customer_id", "客户ID", "客户id", "买家ID", "买家账号", "用户ID", "会员ID"],
    "store_id": ["store_id", "storeId", "店铺ID", "店铺id", "店铺编号", "店铺编码", "店铺id编码"],
    "store_name": ["store_name", "store", "店铺", "店铺名称", "店铺名", "门店", "店名"],
    "available_stock": ["available_stock", "current_stock", "stock", "库存", "可用库存", "当前库存", "现货库存", "实际库存", "可售库存"],
    "safety_stock": ["safety_stock", "安全库存", "库存安全线", "最低库存", "预警库存", "安全线"],
    "refund_amount": ["refund_amount", "退款金额", "退款额", "售后金额", "退货金额", "金额"],
    "refund_reason": ["refund_reason", "退款原因", "售后原因", "退货原因", "原因", "问题原因"],
    "quantity": ["quantity", "数量", "购买数量", "件数", "成交件数", "商品数量", "下单件数"],
    "actual_paid": ["actual_paid", "实付金额", "买家实付", "订单金额", "支付金额", "成交金额", "应收金额", "付款金额"],
    "stock": ["stock", "库存", "商品库存", "现货库存", "可售库存", "当前库存"],
    "sale_price": ["sale_price", "售价", "销售价", "活动价", "成交价", "标价", "商品售价"],
    "cost_price": ["cost_price", "成本", "成本价", "采购价", "供货价", "商品成本"],
    "total_orders": ["total_orders", "订单数", "累计订单", "成交订单", "购买次数", "下单次数"],
    "refund_count": ["refund_count", "退款次数", "售后次数", "退货次数", "退款笔数"],
}


def normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[\s_\-—/\\（）()\[\]【】:*：]+", "", text)


NORMALIZED_ALIASES = {canonical: {normalize_text(item) for item in [canonical, *aliases]} for canonical, aliases in FIELD_ALIASES.items()}


def normalize_dataset_name(dataset_name: str | None) -> str:
    value = (dataset_name or "").strip().lower().replace("-", "_")
    aliases = {"order": "orders", "refund": "refunds", "product": "products", "stock": "inventory", "stocks": "inventory", "customer": "customers"}
    value = aliases.get(value, value)
    if value not in REPORT_TEMPLATES:
        raise ValueError(f"Unsupported dataset_name: {dataset_name}")
    return value


def get_report_templates() -> Dict[str, Any]:
    return {
        "version": SCHEMA_VERSION,
        "ownershipRule": "建议每行报表带 store_id 或店铺名称；没有时系统会尝试按商品所属店铺补齐。",
        "datasets": [
            {
                "datasetName": name,
                "label": template["label"],
                "identityFields": template["identity_fields"],
                "warningFields": template["warning_fields"],
                "optionalFields": template["optional_fields"],
                "alertHint": template["alert_hint"],
                "fields": [
                    {"field": field, "label": FIELD_LABELS.get(field, field), "aliases": FIELD_ALIASES.get(field, [])[:8]}
                    for field in [*template["identity_fields"], *template["warning_fields"], *template["optional_fields"]]
                ],
            }
            for name, template in REPORT_TEMPLATES.items()
        ],
    }


def _headers_from_rows(rows: List[Dict[str, Any]]) -> List[str]:
    seen: List[str] = []
    for row in rows[:20]:
        if not isinstance(row, dict):
            continue
        for key in row.keys():
            text = str(key)
            if text not in seen:
                seen.append(text)
    return seen


def infer_field_mapping(dataset_name: str, rows: List[Dict[str, Any]]) -> Dict[str, str]:
    dataset = normalize_dataset_name(dataset_name)
    template = REPORT_TEMPLATES[dataset]
    target_fields = [*template["identity_fields"], *template["warning_fields"], *template["optional_fields"]]
    headers = _headers_from_rows(rows)
    normalized_headers = [(header, normalize_text(header)) for header in headers]
    mapping: Dict[str, str] = {}
    for canonical in target_fields:
        aliases = NORMALIZED_ALIASES.get(canonical, {normalize_text(canonical)})
        match = next((header for header, normalized in normalized_headers if normalized in aliases), None)
        if match:
            mapping[canonical] = match
    return mapping


def normalize_rows_with_mapping(rows: List[Dict[str, Any]], field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    normalized_rows: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        next_row = deepcopy(row)
        for canonical, source_field in field_mapping.items():
            if source_field in row and canonical not in next_row:
                next_row[canonical] = row.get(source_field)
        normalized_rows.append(next_row)
    return normalized_rows


def preview_report_dataset(dataset_name: str, rows: List[Dict[str, Any]] | None, field_mapping: Dict[str, str] | None = None) -> Dict[str, Any]:
    dataset = normalize_dataset_name(dataset_name)
    dataset_rows = rows if isinstance(rows, list) else []
    template = REPORT_TEMPLATES[dataset]
    inferred_mapping = infer_field_mapping(dataset, dataset_rows)
    final_mapping = {**inferred_mapping, **(field_mapping or {})}
    identity_missing = [field for field in template["identity_fields"] if field not in final_mapping]
    warning_missing = [field for field in template["warning_fields"] if field not in final_mapping]
    optional_missing = [field for field in template["optional_fields"] if field not in final_mapping]
    normalized_rows = normalize_rows_with_mapping(dataset_rows, final_mapping)
    ownership_ready = "store_id" in final_mapping or "store_name" in final_mapping
    issues: List[Dict[str, Any]] = []
    for field in identity_missing:
        issues.append({"field": field, "label": FIELD_LABELS.get(field, field), "severity": "blocked", "message": f"缺少{FIELD_LABELS.get(field, field)}，无法确认预警对象。"})
    for field in warning_missing:
        issues.append({"field": field, "label": FIELD_LABELS.get(field, field), "severity": "warning", "message": f"缺少{FIELD_LABELS.get(field, field)}，相关预警可能不会生成或不够准确。"})
    if not ownership_ready:
        issues.append({"field": "store_id", "label": "店铺归属", "severity": "warning", "message": "未识别到店铺字段，系统会尝试按商品所属店铺补齐；真实报表建议提供 store_id。"})
    status = "blocked" if identity_missing else "needs_attention" if warning_missing or not ownership_ready else "ready"
    return {
        "version": SCHEMA_VERSION,
        "datasetName": dataset,
        "label": template["label"],
        "rowCount": len(dataset_rows),
        "headers": _headers_from_rows(dataset_rows),
        "fieldMapping": final_mapping,
        "recognizedFields": [{"field": field, "label": FIELD_LABELS.get(field, field), "sourceField": source} for field, source in final_mapping.items()],
        "missingIdentityFields": identity_missing,
        "missingWarningFields": warning_missing,
        "missingOptionalFields": optional_missing,
        "ownershipReady": ownership_ready,
        "issues": issues,
        "status": status,
        "canImport": bool(dataset_rows) and not identity_missing,
        "message": "字段和店铺归属已识别，可以导入。" if status == "ready" else "字段或店铺归属有缺失，确认影响后仍可导入。" if status == "needs_attention" else "缺少关键对象字段，暂不能导入。",
        "alertHint": template["alert_hint"],
        "previewRows": normalized_rows[:5],
        "normalizedRows": normalized_rows,
    }


def confirm_report_import(dataset_name: str, rows: List[Dict[str, Any]] | None, field_mapping: Dict[str, str] | None = None, auto_create_tasks: bool = True) -> Dict[str, Any]:
    preview = preview_report_dataset(dataset_name, rows, field_mapping)
    if not preview["canImport"]:
        raise ValueError(preview["message"])
    result = import_report_dataset(preview["datasetName"], rows=preview["normalizedRows"], auto_create_tasks=auto_create_tasks)
    result["schemaPreview"] = {key: value for key, value in preview.items() if key != "normalizedRows"}
    result["version"] = SCHEMA_VERSION
    return result
