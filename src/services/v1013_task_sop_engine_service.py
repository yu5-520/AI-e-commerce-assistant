"""V10.13 task SOP engine.

A task is not a useful task until it can be executed. This layer turns a
metric/trend/RAG decision into an operator-facing SOP with clear actions,
deadlines, required evidence, review gates, and company-RAG timing adjustment.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

V1013_TASK_SOP_VERSION = "10.13.0"


def step(
    no: int,
    action: str,
    hours: int,
    owner: str,
    evidence: List[str],
    fields: List[str],
    review: str,
    failure: str,
) -> Dict[str, Any]:
    return {
        "stepNo": no,
        "action": action,
        "deadlineHours": hours,
        "ownerRole": owner,
        "requiredEvidence": evidence,
        "submitFields": fields,
        "reviewRule": review,
        "failureCondition": failure,
    }


BASE_SOP_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "low_roi_high_refund": {
        "templateId": "SOP-low_roi_high_refund-v1013",
        "sopName": "低 ROI / 高退款承接与售后排查 SOP",
        "objective": "先定位承接和售后问题，禁止未归因前扩大预算。",
        "defaultSteps": [
            step(1, "检查主图、标题、详情页首屏、详情页承诺是否存在夸大、误导、尺寸/材质表达不清、发货承诺不一致。", 6, "运营", ["主图截图", "标题截图", "详情页首屏截图", "疑似问题点列表"], ["page_issue_list", "main_image_screenshot", "detail_screenshot"], "必须指出具体页面位置和对应问题，不接受只写已检查。", "未提交页面截图或没有问题点说明。"),
            step(2, "整理近 7 日退款理由 Top5，包含退款数量、占比、典型订单样本。", 6, "运营", ["退款原因 Top5 表", "退款数量和占比", "订单样本 3-5 条"], ["refund_top5", "refund_count", "refund_ratio", "sample_orders"], "Top5 必须来自 CRM/平台售后数据或订单记录。", "没有 Top5、没有数量占比或没有样本订单。"),
            step(3, "与客服团队核实售后咨询最多的原因，至少整理 5 条以上。", 12, "运营 + 客服", ["客服反馈原因 Top5", "典型聊天截图或摘要", "客服确认人"], ["service_top5", "chat_samples", "service_owner"], "客服原因必须能对应退款/咨询记录。", "未与客服核实或少于 5 条原因。"),
            step(4, "对照退款理由和页面承诺，标记是否存在页面承诺与用户预期不一致。", 12, "运营", ["页面承诺-退款原因对照表", "不一致字段", "建议修改位置"], ["promise_refund_mapping", "mismatch_fields", "edit_positions"], "必须形成承诺与退款原因的一一对应。", "只给结论但没有对照关系。"),
            step(5, "提交处理方案：修改主图/详情页、调整客服话术、暂停放大预算、保持小预算观察、下架或降权观察。", 24, "运营", ["处理方案", "选择原因", "预计复盘指标", "责任人"], ["selected_action", "reason", "review_metrics", "owner"], "方案必须绑定 ROI、CVR、退款率后续观察指标。", "没有选择动作或没有后续指标。"),
        ],
    },
    "low_ctr_low_conversion": {
        "templateId": "SOP-low_ctr_low_conversion-v1013",
        "sopName": "点击入口 / 主图标题测试 SOP",
        "objective": "先定位入口表达问题，禁止直接判死商品。",
        "defaultSteps": [
            step(1, "导出近 7 日曝光、点击、CTR 数据，并标记样本量是否满足强判断。", 6, "运营", ["曝光/点击/CTR 数据", "样本量说明"], ["impressions", "clicks", "ctr", "sample_note"], "必须说明分子分母和计算周期。", "只写 CTR 低，没有曝光点击数据。"),
            step(2, "整理当前主图、标题、关键词、人群包，列出可能影响点击的变量。", 6, "运营", ["主图截图", "标题文本", "关键词/人群记录", "变量清单"], ["image", "title", "keywords", "audience", "variables"], "变量必须可测试，不能只写优化。", "没有变量拆分。"),
            step(3, "对比 3 个同类竞品主图和标题，提炼差异点。", 12, "运营", ["竞品链接/截图 3 个", "差异点列表"], ["competitors", "difference_points"], "竞品必须同类目或同价格带。", "竞品不相关或没有差异点。"),
            step(4, "生成 2-3 个主图/标题测试方向，明确每个方向测试的假设。", 12, "运营 + 设计", ["测试方向 2-3 个", "假设说明", "素材需求"], ["test_directions", "hypothesis", "creative_request"], "每个方向必须只改一个核心变量。", "多个变量混改无法复盘。"),
            step(5, "提交 A/B 测试方案和样本量要求。", 24, "运营", ["A/B 测试计划", "预算/流量分配", "观察指标"], ["ab_plan", "traffic_split", "review_metrics"], "必须有样本量和复盘时间。", "没有样本量或复盘时间。"),
        ],
    },
    "detail_page_conversion": {
        "templateId": "SOP-detail_page_conversion-v1013",
        "sopName": "详情页转化承接 SOP",
        "objective": "定位点击后转化掉点，优先处理首屏承接、价格和评价证据。",
        "defaultSteps": [
            step(1, "检查详情页首屏卖点是否承接主图/标题承诺。", 6, "运营", ["主图截图", "详情页首屏截图", "承诺对照表"], ["promise_mapping", "first_screen_screenshot"], "必须说明承诺是否一致。", "没有主图与详情页对照。"),
            step(2, "整理近 7 日点击、加购、成交漏斗，标记掉点环节。", 6, "运营", ["点击/加购/成交数据", "漏斗掉点表"], ["clicks", "cart_adds", "orders", "dropoff_stage"], "必须有每一步转化率。", "没有漏斗数据。"),
            step(3, "对比竞品价格带、评价证据和赠品/套装结构。", 12, "运营", ["竞品价格表", "评价证据截图", "赠品/套装对比"], ["price_band", "review_proof", "package_compare"], "必须说明我方优势或缺口。", "只有链接没有对比结论。"),
            step(4, "标记影响转化的 3 个主要因素。", 12, "运营", ["转化因素 Top3", "影响证据"], ["conversion_blockers", "proof"], "因素必须来自数据或页面证据。", "主观猜测无证据。"),
            step(5, "提交详情页修改或价格/赠品测试方案。", 24, "运营 + 设计", ["修改方案", "测试指标", "复盘时间"], ["edit_plan", "test_metrics", "review_time"], "方案必须绑定 CVR、退款率和咨询量。", "没有指标或复盘时间。"),
        ],
    },
    "low_inventory_activity": {
        "templateId": "SOP-low_inventory_activity-v1013",
        "sopName": "库存承接与补货判断 SOP",
        "objective": "先确认库存可售天数、补货周期和调货能力，再决定控流或保增长。",
        "defaultSteps": [
            step(1, "确认当前库存、近 7 日日均销量、库存可售天数。", 3, "运营", ["库存记录", "近 7 日销量", "库存可售天数计算"], ["stock", "sales_7d", "sellable_days"], "必须写清公式：库存可售天数 = 当前库存 / 近7日日均销量。", "没有可售天数计算。"),
            step(2, "确认供应商补货周期和最早到货时间。", 6, "运营 + 供应链", ["供应商确认记录", "补货周期", "最早到货时间"], ["supplier_note", "lead_time", "earliest_arrival"], "必须有供应链或供应商确认。", "只写预计补货但无确认。"),
            step(3, "确认是否可以调货，最多可调货数量。", 6, "仓储 / 运营", ["可调货仓/店", "可调货数量", "调货时效"], ["transfer_source", "transfer_quantity", "transfer_time"], "必须写清可调数量和来源。", "没有调货数量。"),
            step(4, "判断是否限量、控流、下架或切换替代 SKU。", 12, "运营 + 总管", ["路径选择", "选择原因", "替代 SKU"], ["selected_path", "reason", "replacement_sku"], "路径必须与库存可售天数和补货周期一致。", "路径选择和库存证据不一致。"),
            step(5, "提交库存承接方案和风险边界。", 24, "运营", ["承接方案", "风险边界", "复盘指标"], ["supply_plan", "risk_boundary", "review_metrics"], "必须说明断货、退款和评分风险边界。", "没有风险边界。"),
        ],
    },
    "competitor_signal_to_test": {
        "templateId": "SOP-competitor_signal_to_test-v1013",
        "sopName": "竞品差评机会转测试 SOP",
        "objective": "把竞品差评转成可验证卖点，不盲目跟价。",
        "defaultSteps": [
            step(1, "整理竞品差评 Top5，按尺寸、材质、发货、安装、售后分类。", 6, "运营", ["竞品差评截图", "差评分类表"], ["bad_review_top5", "review_categories"], "差评必须来自真实评价。", "没有评价截图。"),
            step(2, "核对自身商品是否具备对应优势或可证明证据。", 6, "运营", ["自身卖点证据", "材质/尺寸/服务证明"], ["own_advantage", "proof"], "优势必须能在页面或客服中证明。", "只有口号无证据。"),
            step(3, "生成 2 个差评反向卖点测试方向。", 12, "运营 + 设计", ["测试方向", "素材需求", "预期指标"], ["test_direction", "creative_request", "expected_metric"], "测试方向必须对应某条竞品差评。", "测试方向和差评无关。"),
            step(4, "判断是否需要价格跟随、价值证明或详情页强化。", 12, "运营", ["路径选择", "毛利影响", "价格/价值对照"], ["selected_path", "margin_impact", "price_value_compare"], "价格动作必须有毛利测算。", "未测算毛利直接跟价。"),
            step(5, "提交竞品测试方案并设定复盘窗口。", 24, "运营", ["测试方案", "复盘指标", "复盘时间"], ["test_plan", "review_metrics", "review_time"], "必须绑定 CTR、CVR、退款率或咨询量。", "没有复盘指标。"),
        ],
    },
    "listing_test_path": {
        "templateId": "SOP-listing_test_path-v1013",
        "sopName": "新品 / 增长验证 SOP",
        "objective": "判断增长信号是否可放大，先小步加测，不直接猛投。",
        "defaultSteps": [
            step(1, "确认近 7 日 ROI、CTR、CVR 是否连续高于基线或未走弱。", 6, "运营", ["ROI/CTR/CVR 数据", "趋势比对"], ["roi", "ctr", "conversion_rate", "trend"], "必须同时提交当前值和趋势值。", "只有单点高值没有趋势。"),
            step(2, "确认退款率、毛利率、库存可售天数是否能承接。", 6, "运营", ["退款率", "毛利率", "库存可售天数"], ["refund_rate", "gross_margin", "sellable_days"], "增长必须被售后、利润和库存承接。", "只看 ROI 不看承接。"),
            step(3, "检查流量放大后指标是否稳定，确认是否存在小样本误判。", 12, "运营", ["放量前后数据", "样本量说明"], ["before_after_metrics", "sample_note"], "必须说明样本量置信度。", "样本量不足却建议放量。"),
            step(4, "给出加测预算比例或素材加测方向，默认 10%-15% 小步验证。", 12, "运营", ["加测比例", "素材方向", "风险边界"], ["scale_ratio", "creative_direction", "risk_boundary"], "禁止直接大幅加投。", "未设风险边界。"),
            step(5, "24-48 小时内复盘加测后的 ROI、CVR、退款率和库存消耗。", 48, "运营", ["加测复盘表", "处理前后指标", "下一步建议"], ["post_test_metrics", "before_after", "next_action"], "复盘必须决定继续加测、回退或转主推候选。", "没有复盘结论。"),
        ],
    },
    "report_data_anomaly": {
        "templateId": "SOP-report_data_anomaly-v1013",
        "sopName": "数据源异常复核 SOP",
        "objective": "先修正数据可信度，不用脏数据生成经营动作。",
        "defaultSteps": [
            step(1, "核对 ERP、CRM、平台后台、广告后台的数据更新时间和字段口径。", 6, "数据/运营", ["各数据源更新时间", "字段口径说明"], ["source_time", "field_definition"], "必须至少核对两个数据源。", "只看单一数据源。"),
            step(2, "确认商品 ID、SKU、店铺归属是否一致。", 6, "数据/运营", ["ID 映射表", "店铺归属记录"], ["id_mapping", "store_mapping"], "必须标出冲突行。", "没有冲突行清单。"),
            step(3, "标记不可直接用于经营决策的字段。", 12, "数据/运营", ["字段置信度表", "不可用字段列表"], ["field_confidence", "blocked_fields"], "低置信字段不能驱动投放/库存动作。", "未标记字段置信度。"),
            step(4, "补拉或重新导入缺失数据。", 12, "数据/运营", ["补拉记录", "导入记录", "差异对照"], ["resync_record", "import_record", "diff"], "必须说明补拉前后差异。", "没有补拉结果。"),
            step(5, "提交数据复核结论：可生成经营任务 / 继续观察 / 数据源修复。", 24, "数据/总管", ["复核结论", "后续动作", "复核人"], ["review_result", "next_action", "reviewer"], "未通过复核不得生成强经营任务。", "没有复核人或结论。"),
        ],
    },
}

GENERIC_TEMPLATE = {
    "templateId": "SOP-general_operation-v1013",
    "sopName": "经营异常复核 SOP",
    "objective": "先补齐指标、趋势和证据，再决定处理路径。",
    "defaultSteps": [
        step(1, "整理触发任务的当前指标、基线和趋势。", 6, "运营", ["指标证据", "趋势证据"], ["metric_evidence", "trend_evidence"], "必须提交当前值、基线和趋势变化。", "缺少指标证据。"),
        step(2, "补充相关页面、订单、客服或库存证据。", 12, "运营", ["截图或记录", "样本数据"], ["evidence", "sample"], "证据必须能支撑任务判断。", "无证据。"),
        step(3, "提交处理路径和复盘指标。", 24, "运营", ["处理路径", "复盘指标"], ["path", "review_metrics"], "必须绑定复盘指标。", "没有复盘指标。"),
    ],
}


def _company_adjustment(rag_items: List[Dict[str, Any]] | None, company_policy: Dict[str, Any] | None) -> Dict[str, Any]:
    policy = company_policy or {}
    text = " ".join(str(value) for item in (rag_items or []) for value in [item.get("title"), item.get("initialJudgment"), item.get("resultSummary"), *(item.get("applicableConditions") or [])])
    multiplier = float(policy.get("deadlineMultiplier") or 1.0)
    reason = policy.get("reason") or "使用基础 SOP 默认时限。"
    if "当天" in text or "实时" in text or "强处理" in text:
        multiplier = min(multiplier, 0.75)
        reason = "公司/经验 RAG 命中快速闭环或强处理要求，压缩执行时限。"
    if "客服" in text and ("延迟" in text or "晚间" in text):
        multiplier = max(multiplier, 1.5)
        reason = "公司/经验 RAG 命中客服或售后数据延迟，延长核实步骤时限。"
    return {"deadlineMultiplier": multiplier, "reason": reason, "source": "company_rag_or_default_policy"}


def _adjust_step_deadline(step_item: Dict[str, Any], adjustment: Dict[str, Any]) -> Dict[str, Any]:
    item = deepcopy(step_item)
    base = int(item.get("deadlineHours") or 24)
    multiplier = float(adjustment.get("deadlineMultiplier") or 1.0)
    adjusted = max(1, round(base * multiplier))
    item["baseDeadlineHours"] = base
    item["deadlineHours"] = adjusted
    item["deadlineLabel"] = f"{adjusted} 小时内"
    item["companyAdjustment"] = adjustment
    return item


def build_task_sop(
    problem_type: str | None,
    *,
    task_decision: Dict[str, Any] | None = None,
    metric_evidence: Dict[str, Any] | None = None,
    rag_items: List[Dict[str, Any]] | None = None,
    company_policy: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    decision = (task_decision or {}).get("decision") or ((metric_evidence or {}).get("taskDecision") or {}).get("decision")
    template_key = problem_type or "general_operation"
    if decision == "growth" and template_key not in {"listing_test_path", "competitor_signal_to_test"}:
        template_key = "listing_test_path"
    template = deepcopy(BASE_SOP_TEMPLATES.get(template_key) or GENERIC_TEMPLATE)
    adjustment = _company_adjustment(rag_items, company_policy)
    steps = [_adjust_step_deadline(item, adjustment) for item in template.get("defaultSteps") or []]
    completion_gate = {
        "mustSubmitAllRequiredEvidence": True,
        "mustPassReview": True,
        "rule": "基础 SOP 动作不可省略；公司 RAG 只能调整时限、负责人、证据格式和复核人，不能把任务降级成模糊建议。",
        "minimumEvidence": ["指标证据", "趋势证据", "执行截图或记录", "处理前后复盘指标"],
    }
    return {
        "version": V1013_TASK_SOP_VERSION,
        "sopId": template.get("templateId"),
        "sopName": template.get("sopName"),
        "objective": template.get("objective"),
        "problemType": problem_type or "general_operation",
        "decision": decision or "risk",
        "executionSteps": steps,
        "completionGate": completion_gate,
        "companyAdjustment": adjustment,
        "reviewMode": "evidence_required_before_done",
        "principle": "SOP 是骨架，公司 RAG 是调参，指标趋势是证据，复核标准是闭环。",
    }
