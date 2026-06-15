"""Merchant-facing view service built on top of the internal workflow.

The internal workflow keeps detailed engineering fields. This service converts
that structure into product API payloads that match the AI operating advisor UI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from src.services.data_import_service import validate_all_imports
from src.workflow.mock_workflow import build_mock_workflow_result

ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT_DIR / "outputs"


def _workflow(write_outputs: bool = False, record_logs: bool = False) -> Dict[str, Any]:
    return build_mock_workflow_result(write_outputs=write_outputs, record_logs=record_logs)


def _risk_label(level: str | None) -> str:
    return {"high": "重点风险", "medium": "需要关注", "low": "状态正常"}.get(level or "", "需要关注")


def _decision_label(decision: str | None) -> str:
    return {
        "enter_after_sales_diagnosis": "先查售后",
        "stop_or_reduce_budget": "先止损",
        "change_title_or_main_image": "换标题 / 主图",
        "adjust_sku_price_or_detail_page": "调规格 / 定价",
        "scale_carefully": "谨慎放量",
        "continue_testing": "继续观察",
    }.get(decision or "", decision or "继续观察")


def _module_label(module: str | None) -> str:
    return {
        "crm_after_sales_diagnosis": "售后归因",
        "erp_profit_and_budget_review": "利润与预算复核",
        "competitor_title_image_review": "标题 / 主图复查",
        "listing_sku_pricing_review": "规格 / 定价复查",
        "erp_product_risk_review": "商品风险复查",
        "controlled_scale_review": "小幅放量复核",
        "continue_operating_loop": "继续循环",
    }.get(module or "", module or "继续循环")


def _frequency_label(frequency: str | None) -> str:
    return {"daily": "每天", "weekly": "每周", "monthly": "每月"}.get(frequency or "", frequency or "未设置")


def get_today_advice(write_outputs: bool = False, record_logs: bool = False) -> Dict[str, Any]:
    result = _workflow(write_outputs=write_outputs, record_logs=record_logs)
    summary = result.get("summary", {})
    loop = result.get("operating_loop_summary", {})
    traffic = result.get("traffic_feedback_report", {})
    operating_unit = result.get("operating_unit", {})
    cycle_policy = result.get("cycle_policy", {})

    return {
        "page_title": "今日经营建议",
        "priority": {
            "title": _module_label(summary.get("loop_next_module") or loop.get("next_module")),
            "reason": traffic.get("next_action") or "先完成商品、竞品、上新和流量复盘，再生成下一轮动作。",
            "next_steps": loop.get("next_iteration_plan", []),
        },
        "operating_unit": {
            "name": summary.get("unit_name") or operating_unit.get("unit_name"),
            "id": summary.get("operating_unit_id") or operating_unit.get("operating_unit_id"),
            "source": "根据 ERP 商品结构识别",
        },
        "cycle": {
            "frequency": summary.get("cycle_frequency") or cycle_policy.get("cycle_frequency"),
            "frequency_label": _frequency_label(summary.get("cycle_frequency") or cycle_policy.get("cycle_frequency")),
            "type": summary.get("cycle_type") or cycle_policy.get("cycle_type"),
            "run_time": cycle_policy.get("run_time"),
            "report_type": cycle_policy.get("report_type"),
        },
        "cards": [
            {"title": "商品体检", "value": summary.get("product_count", 0), "desc": "已检查商品"},
            {"title": "竞品机会", "value": summary.get("competitor_count", 0), "desc": "同经营单元参考对象"},
            {"title": "流量测试", "value": summary.get("traffic_experiment_count", 0), "desc": "已复盘测试"},
            {"title": "待确认", "value": summary.get("approval_required_count", 0), "desc": "关键动作不自动执行"},
        ],
        "boundaries": [
            "只生成判断、草案和报告",
            "不自动上架、改价、投放",
            "不自动触达客户或退款",
            "确认后再进入下一步",
        ],
        "raw": result,
    }


def get_operating_unit_view() -> Dict[str, Any]:
    result = _workflow()
    unit = result.get("operating_unit", {})
    policy = result.get("cycle_policy", {})
    return {
        "unit_name": unit.get("unit_name"),
        "unit_id": unit.get("operating_unit_id"),
        "source": "根据 ERP 商品结构识别",
        "dominant_product_group": unit.get("dominant_product_group"),
        "reason": unit.get("reason"),
        "product_group_summary": unit.get("product_group_summary", {}),
        "keyword_signals": unit.get("keyword_signals", {}),
        "cycle_policy": {
            "frequency": policy.get("cycle_frequency"),
            "frequency_label": _frequency_label(policy.get("cycle_frequency")),
            "type": policy.get("cycle_type"),
            "run_time": policy.get("run_time"),
            "report_type": policy.get("report_type"),
            "description": policy.get("description"),
            "trigger_rules": policy.get("trigger_rules", []),
        },
    }


def get_data_health() -> Dict[str, Any]:
    validation = validate_all_imports()
    return {
        "status": validation.get("status"),
        "summary": {
            "dataset_count": len(validation.get("datasets", [])),
            "failed_count": validation.get("failed_count", 0),
            "relationship_check_count": len(validation.get("relationship_checks", [])),
        },
        "datasets": [
            {
                "name": item.get("label") or item.get("dataset_name"),
                "filename": item.get("filename"),
                "row_count": item.get("row_count"),
                "status": item.get("status"),
            }
            for item in validation.get("datasets", [])
        ],
        "message": "数据足够支撑本轮经营判断。" if validation.get("status") == "passed" else "数据仍需补齐后再判断。",
    }


def get_product_health() -> Dict[str, Any]:
    result = _workflow()
    products = result.get("product_diagnosis", [])
    return {
        "title": "商品体检结果",
        "summary": result.get("summary", {}),
        "items": [
            {
                "product_id": item.get("product_id"),
                "product_name": item.get("product_name"),
                "risk_level": item.get("risk_level"),
                "risk_label": _risk_label(item.get("risk_level")),
                "risks": item.get("risks", []),
                "suggestions": item.get("suggested_actions", []),
                "stock": item.get("stock"),
                "gross_margin": item.get("gross_margin"),
                "activity_margin": item.get("activity_margin"),
            }
            for item in products
        ],
    }


def get_competitor_opportunities() -> Dict[str, Any]:
    result = _workflow()
    analysis = result.get("competitor_analysis", {})
    review_gap = analysis.get("review_gap", {})
    return {
        "title": "竞品机会",
        "category_name": analysis.get("category_name"),
        "competitor_count": analysis.get("competitor_count", 0),
        "trigger_product": analysis.get("reference_product", {}),
        "price_gap": analysis.get("price_gap", {}),
        "bad_review_keywords": review_gap.get("top_bad_review_keywords", []),
        "opportunity_actions": review_gap.get("opportunity_actions", []),
        "next_action": analysis.get("next_action"),
        "safe_use_policy": analysis.get("safe_use_policy"),
    }


def get_listing_suggestions() -> Dict[str, Any]:
    result = _workflow()
    plan = result.get("listing_growth_plan", {})
    draft = plan.get("listing_draft", {})
    return {
        "title": "上新建议",
        "candidate_count": plan.get("candidate_count", 0),
        "top_candidate": plan.get("top_candidate", {}),
        "title_draft": draft.get("title_draft"),
        "image_plan": draft.get("image_plan", []),
        "sku_plan": draft.get("sku_plan", []),
        "compliance_checklist": draft.get("compliance_checklist", []),
        "next_action": plan.get("next_action"),
        "safe_use_policy": plan.get("safe_use_policy"),
    }


def get_traffic_review() -> Dict[str, Any]:
    result = _workflow()
    report = result.get("traffic_feedback_report", {})
    return {
        "title": "流量复盘",
        "experiment_count": report.get("experiment_count", 0),
        "decision_summary": report.get("decision_summary", {}),
        "risk_summary": report.get("risk_summary", {}),
        "next_action": report.get("next_action"),
        "loopback_actions": report.get("loopback_actions", []),
        "items": [
            {
                **item,
                "decision_label": _decision_label(item.get("decision")),
                "risk_label": _risk_label(item.get("risk_level")),
            }
            for item in report.get("diagnoses", [])
        ],
        "safe_use_policy": report.get("safe_use_policy"),
    }


def get_action_confirmations() -> Dict[str, List[Dict[str, Any]]]:
    result = _workflow()
    tasks = result.get("approval_required_tasks") or result.get("rpa_tasks", [])
    return {
        "items": [
            {
                "action_id": task.get("task_id"),
                "action_name": task.get("task_type"),
                "risk_level": task.get("risk_level"),
                "risk_label": _risk_label(task.get("risk_level")),
                "suggestion": task.get("ai_suggestion"),
                "status": task.get("approval_status") or task.get("status") or "pending",
                "auto_execution_allowed": task.get("auto_execution_allowed", False),
                "policy_reason": task.get("policy_reason"),
            }
            for task in tasks
        ]
    }


def get_business_report_text() -> str:
    report_path = OUTPUT_DIR / "operating_report.md"
    if not report_path.exists():
        _workflow(write_outputs=True, record_logs=True)
    return report_path.read_text(encoding="utf-8")
