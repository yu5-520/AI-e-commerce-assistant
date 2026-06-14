from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.approval.risk_rules import classify_task  # noqa: E402
from src.services.data_import_service import validate_all_imports  # noqa: E402
from src.workflow.mock_workflow import build_mock_workflow_result  # noqa: E402


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def detect_focus(title: str, body: str, comment: str) -> str:
    text = f"{title}\n{body}\n{comment}"
    if any(keyword in text for keyword in ["数据", "导入", "ERP", "CRM", "字段", "表格"]):
        return "data_import"
    if any(keyword in text for keyword in ["客户", "复购", "召回", "售后敏感", "分层"]):
        return "customer_segmentation"
    if any(keyword in text for keyword in ["审批", "确认", "拒绝", "RPA", "任务"]):
        return "task_approval"
    if any(keyword in text for keyword in ["库存", "退款", "活动价", "毛利", "SKU", "商品"]):
        return "product_diagnosis"
    return "full_workflow"


def format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_report(title: str, body: str, comment: str) -> str:
    focus = detect_focus(title, body, comment)
    validation = validate_all_imports()
    result = build_mock_workflow_result(write_outputs=False, record_logs=False)
    summary = result.get("summary") or {}
    product_diagnosis = result.get("product_diagnosis") or []
    customer_segmentation = result.get("customer_segmentation") or []
    tasks = result.get("rpa_tasks") or []
    approval_required = result.get("approval_required_tasks") or []

    focus_titles = {
        "data_import": "数据导入与校验",
        "product_diagnosis": "商品经营诊断",
        "customer_segmentation": "CRM 客户分层",
        "task_approval": "RPA 任务草案与人工审批",
        "full_workflow": "完整经营工作流",
    }

    next_actions = {
        "data_import": [
            "先检查字段完整性、必填项和数值格式。",
            "再检查商品、订单、库存、退款、客户标签之间的关系。",
            "导入通过后进入商品诊断和客户分层。",
        ],
        "product_diagnosis": [
            "优先看活动价毛利、库存压力和退款率。",
            "高库存低订单商品先做测试或清货测算，不直接加预算。",
            "退款异常商品先进入售后归因，不直接放量。",
        ],
        "customer_segmentation": [
            "高价值客户生成复购任务草案。",
            "沉睡客户生成低频召回任务表。",
            "售后敏感客户先处理售后原因，不直接营销触达。",
        ],
        "task_approval": [
            "所有任务先进入人工确认。",
            "高风险任务只输出建议，不自动执行。",
            "审批动作只记录状态，不触发真实 RPA。",
        ],
        "full_workflow": [
            "按 数据导入 → AI 诊断 → RPA 草案 → 人工确认 → 报告日志 的顺序演示。",
            "当前版本用 Mock 数据验证链路，不宣称已接真实店铺后台。",
            "下一步优先补 Excel 上传、字段映射和业务档案落库。",
        ],
    }

    high_risk_policy = classify_task("auto_price_change")
    medium_policy = classify_task("sku_price_table")

    lines = [
        f"# {focus_titles[focus]}结果卡",
        "",
        "## 结论",
        f"当前 Issue 被归入 **{focus_titles[focus]}** 场景。主产品叙事统一为 AI + RPA + ERP + CRM 电商经营自动化工作台，而不是单一平台标题 / 主图生成器。",
        "",
        "## 当前 Mock Workflow 摘要",
        f"- 商品诊断数：{summary.get('product_count', 0)}",
        f"- 客户分层数：{summary.get('customer_count', 0)}",
        f"- RPA 任务草案数：{summary.get('rpa_task_count', 0)}",
        f"- 待人工确认数：{summary.get('approval_required_count', 0)}",
        f"- 自动执行允许数：{summary.get('auto_execution_allowed_count', 0)}",
        "",
        "## 数据校验状态",
        f"- 校验状态：{validation.get('status')}",
        f"- 数据集数量：{len(validation.get('datasets', []))}",
        f"- 失败检查数：{validation.get('failed_count')}",
        f"- 警告数：{validation.get('warning_count')}",
        "",
        "## 示例诊断结果",
    ]

    for item in product_diagnosis[:3]:
        risks = "、".join(item.get("risks", [])) or "暂无明显风险"
        lines.append(f"- {item.get('product_id')}｜{item.get('product_name')}｜风险等级：{item.get('risk_level')}｜风险：{risks}")

    lines.extend(["", "## 示例客户分层"])
    for item in customer_segmentation[:3]:
        tags = "、".join(item.get("tags", [])) or "无标签"
        lines.append(f"- {item.get('customer_id')}｜{item.get('segment')}｜风险等级：{item.get('risk_level')}｜标签：{tags}")

    lines.extend([
        "",
        "## 任务与审批边界",
        f"- 示例中风险任务策略：{medium_policy.get('policy_reason')}",
        f"- 示例高风险任务策略：{high_risk_policy.get('policy_reason')}",
        f"- 当前所有任务自动执行允许数：{sum(1 for task in tasks if task.get('auto_execution_allowed') is True)}",
        f"- 当前需要人工确认任务数：{len(approval_required)}",
        "",
        "## 下一步动作",
        format_bullets(next_actions[focus]),
        "",
        "## 输入摘要",
        f"- Issue 标题：{clean_text(title) or '未填写'}",
        f"- Issue 正文：{clean_text(body)[:300] or '未填写'}",
        f"- 最新评论：{clean_text(comment)[:300] or '无'}",
    ])

    return "\n".join(lines) + "\n"


def main() -> None:
    title = os.getenv("ISSUE_TITLE", "")
    body = os.getenv("ISSUE_BODY", "") or ""
    comment = os.getenv("COMMENT_BODY", "") or ""
    out = sys.argv[1] if len(sys.argv) > 1 else "analysis-result.md"
    Path(out).write_text(build_report(title, body, comment), encoding="utf-8")


if __name__ == "__main__":
    main()
