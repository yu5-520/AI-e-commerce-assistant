from __future__ import annotations

from typing import Dict, List


def build_cycle_policy(operating_unit: Dict[str, object]) -> Dict[str, object]:
    """Build a run cadence policy from the inferred operating unit.

    MVP boundary: this creates schedule metadata only. It does not register a
    real cron job or background task by itself.
    """
    cycle_type = str(operating_unit.get("cycle_suggestion") or "weekly_operation_review_loop")
    unit_name = str(operating_unit.get("unit_name") or "经营单元")

    if cycle_type == "daily_fast_moving_goods_loop":
        return {
            "cycle_policy_id": "CYCLE_DAILY_FAST_MOVING_001",
            "operating_unit_id": operating_unit.get("operating_unit_id"),
            "unit_name": unit_name,
            "cycle_frequency": "daily",
            "cycle_type": cycle_type,
            "run_time": "09:00",
            "report_type": "daily_operation_report",
            "trigger_rules": [
                "库存异常",
                "退款率异常",
                "ROI 低",
                "点击率异常",
                "转化率异常",
            ],
            "human_review_required": True,
            "auto_run_scope": "generate_report_and_task_drafts_only",
            "description": f"{unit_name} 属于低客单、高周转或季节性商品，适合每日生成经营日报和异常提醒。",
        }

    if cycle_type == "weekly_bulk_goods_review_loop":
        return {
            "cycle_policy_id": "CYCLE_WEEKLY_BULK_001",
            "operating_unit_id": operating_unit.get("operating_unit_id"),
            "unit_name": unit_name,
            "cycle_frequency": "weekly",
            "cycle_type": cycle_type,
            "run_day": "Monday",
            "run_time": "10:00",
            "report_type": "weekly_business_review",
            "trigger_rules": [
                "线索超过7天未跟进",
                "报价转化异常",
                "库存周转慢",
                "客户复购周期到期",
            ],
            "human_review_required": True,
            "auto_run_scope": "generate_report_and_task_drafts_only",
            "description": f"{unit_name} 更接近高客单或低频商品，适合每周复盘线索、报价、库存和客户阶段。",
        }

    return {
        "cycle_policy_id": "CYCLE_WEEKLY_OPERATION_001",
        "operating_unit_id": operating_unit.get("operating_unit_id"),
        "unit_name": unit_name,
        "cycle_frequency": "weekly",
        "cycle_type": cycle_type,
        "run_day": "Monday",
        "run_time": "09:30",
        "report_type": "weekly_operation_report",
        "trigger_rules": [
            "库存变化",
            "退款异常",
            "上新测试结果",
            "客户分层变化",
        ],
        "human_review_required": True,
        "auto_run_scope": "generate_report_and_task_drafts_only",
        "description": f"{unit_name} 当前建议每周复盘，后续可根据销量、库存和测试频率调整。",
    }
