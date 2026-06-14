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
    if any(keyword in text for keyword in ["类目", "垂直", "价格带", "季节", "防晒服"]):
        return "category_profile"
    if any(keyword in text for keyword in ["竞品", "同行", "差评", "价格比对", "卖点比对"]):
        return "competitor_analysis"
    if any(keyword in text for keyword in ["上新", "铺货", "货盘", "新品", "扩品"]):
        return "listing_growth"
    if any(keyword in text for keyword in ["流量", "测试", "曝光", "点击", "转化", "ROI"]):
        return "traffic_test"
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
        "category_profile": "垂直类目配置",
        "competitor_analysis": "同类目竞品比对",
        "listing_growth": "同类目上新增长",
        "traffic_test": "流量测试与数据回流",
        "data_import": "数据导入与校验",
        "product_diagnosis": "商品经营诊断",
        "customer_segmentation": "CRM 客户分层",
        "task_approval": "RPA 任务草案与人工审批",
        "full_workflow": "完整经营循环",
    }

    next_actions = {
        "category_profile": [
            "先确定垂直类目的价格带、季节性、主图表达、SKU 结构和高频售后风险。",
            "把类目知识写入 knowledge_base/category_profiles/，再进入经营判断。",
            "当前建议先以防晒服样板验证类目配置机制。",
        ],
        "competitor_analysis": [
            "竞品比对应由经营问题触发，不是凭空分析竞品。",
            "优先比对价格带、标题关键词、主图卖点、SKU 结构和差评机会。",
            "输出应判断优化老品、扩相似品，还是暂停投入。",
        ],
        "listing_growth": [
            "上新增长应基于已有经营数据、竞品差距和供应链货盘。",
            "先生成新品候选评分、标题 / 主图 / SKU / 定价草案和上新检查表。",
            "真实上架动作必须人工确认，MVP 不自动上架。",
        ],
        "traffic_test": [
            "上新或优化后必须进入小流量测试，否则只是一次性生成。",
            "重点观察曝光、点击、转化、退款、ROI 和库存消耗速度。",
            "测试结果要回写经营判断系统，形成循环。",
        ],
        "data_import": [
            "先检查字段完整性、必填项和数值格式。",
            "再检查商品、订单、库存、退款、客户标签之间的关系。",
            "导入通过后进入商品诊断和客户分层。",
        ],
        "product_diagnosis": [
            "优先看活动价毛利、库存压力和退款率。",
            "高库存低订单商品先做测试或清货测算，不直接加预算。",
            "低点击、低转化、高退款、高库存问题后续可触发同类目竞品比对。",
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
            "按 垂直类目 → 经营判断 → 竞品比对 → 上新增长 → 流量回流 的顺序演示。",
            "当前版本用 Mock ERP / CRM 数据验证 V0.8，不宣称已接真实店铺后台。",
            "下一步优先补垂直类目配置层，再做同类目竞品比对。",
        ],
    }

    high_risk_policy = classify_task("auto_price_change")
    medium_policy = classify_task("sku_price_table")

    lines = [
        f"# {focus_titles[focus]}结果卡",
        "",
        "## 结论",
        f"当前 Issue 被归入 **{focus_titles[focus]}** 场景。主产品叙事统一为 AI 垂直货架电商经营循环系统：先基于 ERP / CRM 做已有经营判断，再触发同类目竞品比对、上新增长和流量测试回流。",
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
