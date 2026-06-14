"""Product-facing API service for the AI operation advisor.

This layer translates the internal workflow result into merchant-facing sections.
The old workflow/demo APIs stay available for compatibility, while /api/operation
uses product language for the frontend.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.services.approval_service import get_task_status_overrides
from src.services.workflow_service import get_demo_report_text, run_full_workflow


def module_label(module: str | None) -> str:
    labels = {
        "crm_after_sales_diagnosis": "售后归因",
        "erp_profit_and_budget_review": "利润与预算复核",
        "competitor_title_image_review": "标题 / 主图复查",
        "listing_sku_pricing_review": "规格 / 定价复查",
        "erp_product_risk_review": "商品风险复查",
        "controlled_scale_review": "小幅放量复核",
        "continue_operating_loop": "继续循环",
    }
    return labels.get(module or "", module or "继续循环")


def frequency_label(frequency: str | None) -> str:
    labels = {
        "daily": "每天",
        "weekly": "每周",
        "monthly": "每月",
    }
    return labels.get(frequency or "", frequency or "未设置")


def decision_label(decision: str | None) -> str:
    labels = {
        "enter_after_sales_diagnosis": "先查售后",
        "stop_or_reduce_budget": "先止损",
        "change_title_or_main_image": "换标题 / 主图",
        "adjust_sku_price_or_detail_page": "调规格 / 价格",
        "scale_carefully": "谨慎放量",
        "continue_testing": "继续观察",
    }
    return labels.get(decision or "", decision or "继续观察")


def run_operation_cycle(write_outputs: bool = True, record_logs: bool = True) -> Dict[str, Any]:
    """Run the current ERP-based operation cycle and attach saved action status."""
    result = run_full_workflow(write_outputs=write_outputs, record_logs=record_logs)
    overrides = get_task_status_overrides()
    if overrides:
        result["task_status_overrides"] = overrides
    return result


def build_today_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    """Build the main merchant-facing page payload."""
    summary = result.get("summary") or {}
    loop = result.get("operating_loop_summary") or {}
    traffic = result.get("traffic_feedback_report") or {}
    operating_unit = result.get("operating_unit") or {}
    cycle_policy = result.get("cycle_policy") or {}
    approval_tasks = result.get("approval_required_tasks") or result.get("rpa_tasks") or []

    next_module = summary.get("loop_next_module") or loop.get("next_module")
    cycle_frequency = summary.get("cycle_frequency") or cycle_policy.get("cycle_frequency")

    return {
        "page_title": "今日经营建议",
        "today_focus": {
            "title": module_label(next_module),
            "reason": traffic.get("next_action") or "先完成商品、竞品、上新和流量复盘，再生成下一轮动作。",
            "next_module": next_module,
            "next_steps": loop.get("next_iteration_plan") or [],
        },
        "operating_unit_card": {
            "unit_name": summary.get("unit_name") or operating_unit.get("unit_name"),
            "operating_unit_id": summary.get("operating_unit_id") or operating_unit.get("operating_unit_id"),
            "cycle_label": f"{frequency_label(cycle_frequency)}循环",
            "cycle_frequency": cycle_frequency,
            "reason": operating_unit.get("reason"),
        },
        "kpis": {
            "product_count": summary.get("product_count", 0),
            "customer_count": summary.get("customer_count", 0),
            "competitor_count": summary.get("competitor_count", 0),
            "listing_candidate_count": summary.get("listing_candidate_count", 0),
            "traffic_experiment_count": summary.get("traffic_experiment_count", 0),
            "approval_required_count": summary.get("approval_required_count", len(approval_tasks)),
        },
        "boundaries": [
            "只生成判断、草案和报告。",
            "不自动上架、改价、投放。",
            "不自动触达客户或退款。",
            "关键动作确认后再进入下一步。",
        ],
        "raw": result,
    }


def build_operating_unit_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    operating_unit = result.get("operating_unit") or {}
    cycle_policy = result.get("cycle_policy") or {}
    return {
        "unit_name": operating_unit.get("unit_name"),
        "operating_unit_id": operating_unit.get("operating_unit_id"),
        "base_source": "店铺商品、库存和订单数据",
        "dominant_product_group": operating_unit.get("dominant_product_group"),
        "product_group_summary": operating_unit.get("product_group_summary") or {},
        "keyword_signals": operating_unit.get("keyword_signals") or {},
        "reason": operating_unit.get("reason"),
        "cycle_policy": {
            "frequency": cycle_policy.get("cycle_frequency"),
            "frequency_label": frequency_label(cycle_policy.get("cycle_frequency")),
            "cycle_type": cycle_policy.get("cycle_type"),
            "run_time": cycle_policy.get("run_time"),
            "report_type": cycle_policy.get("report_type"),
            "description": cycle_policy.get("description"),
            "trigger_rules": cycle_policy.get("trigger_rules") or [],
        },
    }


def build_data_check_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    operating_unit = result.get("operating_unit") or {}
    summary = result.get("summary") or {}
    return {
        "status": "ready",
        "message": "当前演示数据可以支撑本轮经营判断。",
        "datasets": [
            {"name": "商品数据", "status": "ready", "description": "用于识别经营单元、商品体检和上新判断。"},
            {"name": "订单数据", "status": "ready", "description": "用于判断销售表现和经营节奏。"},
            {"name": "库存数据", "status": "ready", "description": "用于判断库存压力和补货 / 清货风险。"},
            {"name": "退款数据", "status": "ready", "description": "用于定位售后、尺寸、材质、物流等问题。"},
            {"name": "客户数据", "status": "ready", "description": "用于客户分层和售后敏感判断。"},
        ],
        "summary": {
            "unit_name": operating_unit.get("unit_name"),
            "product_count": summary.get("product_count", 0),
            "customer_count": summary.get("customer_count", 0),
        },
    }


def build_products_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    products = result.get("product_diagnosis") or []
    return {
        "title": "商品体检",
        "description": "优先处理库存高、利润薄、退款异常和承诺不清的商品。",
        "items": products,
        "high_priority_items": [item for item in products if item.get("risk_level") in {"high", "medium"}],
    }


def build_competitors_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    analysis = result.get("competitor_analysis") or {}
    return {
        "title": "竞品机会",
        "description": "只拆解同经营单元里的机会，不复制素材。",
        "reference_product": analysis.get("reference_product") or {},
        "competitor_count": analysis.get("competitor_count", 0),
        "price_gap": analysis.get("price_gap") or {},
        "sku_gap": analysis.get("sku_gap") or {},
        "review_gap": analysis.get("review_gap") or {},
        "next_action": analysis.get("next_action"),
        "safe_use_policy": analysis.get("safe_use_policy"),
    }


def build_listing_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    plan = result.get("listing_growth_plan") or {}
    return {
        "title": "上新建议",
        "description": "从货盘里找值得测试的商品，并生成上新资料草案。",
        "candidate_count": plan.get("candidate_count", 0),
        "top_candidate": plan.get("top_candidate") or {},
        "all_candidates": plan.get("all_candidates") or [],
        "listing_draft": plan.get("listing_draft") or {},
        "next_action": plan.get("next_action"),
        "safe_use_policy": plan.get("safe_use_policy"),
    }


def build_traffic_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    report = result.get("traffic_feedback_report") or {}
    diagnoses = report.get("diagnoses") or []
    productized_diagnoses = [
        {
            **item,
            "decision_label": decision_label(item.get("decision")),
        }
        for item in diagnoses
    ]
    return {
        "title": "流量复盘",
        "description": "不直接加预算，先看点击、转化、退款和投入产出。",
        "experiment_count": report.get("experiment_count", 0),
        "decision_summary": report.get("decision_summary") or {},
        "risk_summary": report.get("risk_summary") or {},
        "next_action": report.get("next_action"),
        "loopback_actions": report.get("loopback_actions") or [],
        "diagnoses": productized_diagnoses,
        "safe_use_policy": report.get("safe_use_policy"),
    }


def build_actions_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    tasks = result.get("approval_required_tasks") or result.get("rpa_tasks") or []
    overrides = result.get("task_status_overrides") or {}
    items = []
    for task in tasks:
        task_id = task.get("task_id")
        status_override = overrides.get(task_id, {}) if isinstance(overrides, dict) else {}
        items.append(
            {
                **task,
                "display_name": task.get("task_type") or "待确认动作",
                "approval_status": status_override.get("status") or task.get("approval_status") or "pending",
                "can_auto_execute": False,
                "display_policy": "确认后才进入下一步。",
            }
        )
    return {
        "title": "待确认动作",
        "description": "所有涉及上架、改价、投放、客户触达的动作，都先放到这里确认。",
        "items": items,
        "count": len(items),
    }


def build_operation_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    """Return all product-facing sections in one response for the frontend."""
    return {
        "today": build_today_payload(result),
        "operating_unit": build_operating_unit_payload(result),
        "data_check": build_data_check_payload(result),
        "products": build_products_payload(result),
        "competitors": build_competitors_payload(result),
        "listing": build_listing_payload(result),
        "traffic": build_traffic_payload(result),
        "actions": build_actions_payload(result),
        "report": {
            "title": "经营报告",
            "text": get_demo_report_text(),
        },
        "raw": result,
    }
