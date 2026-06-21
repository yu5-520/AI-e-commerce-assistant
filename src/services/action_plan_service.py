"""Problem-type action plan service.

This layer prevents Agent outputs from falling back to one generic template. The
module detects a signal, then this service turns the signal's problem type into
an execution package for operators and a review package for managers.

It is deterministic and advisory-only. LLM providers can later fill in richer
copy, titles, image text, and category wording, but the problem type and action
package contract should stay stable.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

ACTION_PLAN_VERSION = "4.4.2"

FORBIDDEN_ACTIONS = [
    "不直接改价",
    "不直接投放",
    "不直接退款",
    "不直接发布商品",
    "不直接回写 ERP / CRM / 店铺后台",
]

PROBLEM_LABELS = {
    "low_ctr_low_conversion": "点击率 / 转化率下降",
    "low_roi_high_refund": "低 ROI / 高退款",
    "low_inventory_activity": "库存承接风险",
    "competitor_signal_to_test": "竞品差评 / 机会点",
    "detail_page_conversion": "详情页承接不足",
    "report_data_anomaly": "报表数据异常",
    "general_operation": "经营异常",
}


def _text(item: Dict[str, Any] | None) -> str:
    if not item:
        return ""
    values: List[str] = []
    for key in [
        "title",
        "productTitle",
        "productShort",
        "riskDomain",
        "taskType",
        "taskSignal",
        "task",
        "reason",
        "status",
        "statusLevel",
        "suggestion",
        "nextStep",
        "risk",
        "refundRate",
        "roi",
        "conversion",
        "ctr",
        "inventoryStatus",
        "afterSales",
        "badReview",
        "opportunity",
        "testType",
        "testPlan",
        "sourceModule",
        "source",
    ]:
        if item.get(key) is not None:
            values.append(str(item[key]))
    values.extend(str(value) for value in item.get("judgmentTags") or [])
    return " ".join(values)


def infer_action_problem_type(item: Dict[str, Any] | None, *, source_module: str | None = None, fallback: str = "general_operation") -> str:
    text = _text(item)
    source = source_module or str((item or {}).get("sourceModule") or "")
    if any(word in text for word in ["点击", "CTR", "ctr", "主图", "标题", "素材", "创意"]):
        return "low_ctr_low_conversion"
    if any(word in text for word in ["转化率", "详情页", "承接", "落地页", "首屏卖点"]):
        return "detail_page_conversion"
    if any(word in text for word in ["ROI", "ROAS", "roi", "退款", "售后", "客服", "材质", "尺寸", "安装", "暂停放量", "先查售后"]):
        return "low_roi_high_refund"
    if any(word in text for word in ["库存", "补货", "缺货", "安全库存", "活动流量", "待补货"]):
        return "low_inventory_activity"
    if "competitor" in source.lower() or "竞品" in source or any(word in text for word in ["竞品", "差评", "机会点", "跟价"]):
        return "competitor_signal_to_test"
    if "report" in source.lower() or "报表" in source or any(word in text for word in ["字段", "同步", "导入", "ERP", "CRM"]):
        return "report_data_anomaly"
    return fallback


def _product_name(item: Dict[str, Any] | None) -> str:
    item = item or {}
    return str(item.get("productShort") or item.get("shortName") or item.get("sourceName") or item.get("targetProduct") or item.get("title") or item.get("id") or "经营对象")


def _package(
    *,
    package_id: str,
    name: str,
    target_metric: str,
    diagnosis: str,
    operator_actions: List[str],
    submit_metrics: List[str],
    evidence_required: List[str],
    acceptance_criteria: List[str],
    failure_threshold: List[str],
    review_focus: List[str],
    fit_condition: List[str],
    risk: str,
    duration: str = "24-48 小时",
) -> Dict[str, Any]:
    return {
        "packageId": package_id,
        "packageName": name,
        "targetMetric": target_metric,
        "diagnosis": diagnosis,
        "operatorAction": operator_actions,
        "submitMetrics": submit_metrics,
        "evidenceRequired": evidence_required,
        "acceptanceCriteria": acceptance_criteria,
        "failureThreshold": failure_threshold,
        "reviewFocus": review_focus,
        "fitCondition": fit_condition,
        "risk": risk,
        "testDuration": duration,
    }


def _ctr_conversion_packages(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    name = _product_name(item)
    return [
        _package(
            package_id="AP-low-ctr-title-image",
            name="标题主图点击率测试包",
            target_metric="点击率",
            diagnosis=f"{name}疑似标题关键词或首图吸引力不足，需要测试可点击变量。",
            operator_actions=[
                "选择 Agent 生成的 2-3 组标题 / 主图方案",
                "把方案上架到测试商品或测试计划",
                "保持价格、库存、详情页不变，只测试标题和首图变量",
                "小流量观察 24-48 小时",
                "提交每组方案的曝光、点击率、转化率、收藏加购和退款率",
            ],
            submit_metrics=["曝光", "点击率", "转化率", "收藏加购", "退款率", "测试版本截图"],
            evidence_required=["旧标题 / 旧主图", "新标题 / 新主图", "测试开始时间", "测试结束时间", "分版本数据"],
            acceptance_criteria=["点击率提升", "转化率不明显下滑", "退款率不异常升高", "胜出版本可复用"],
            failure_threshold=["点击率无提升", "转化率明显下滑", "退款率升高", "平台提示违规或夸大"],
            review_focus=["是否只变更标题 / 主图", "是否有足够曝光", "胜出版本是否有复用价值"],
            fit_condition=["点击率下降", "主图 / 标题疑似弱", "商品库存可承接", "价格暂不调整"],
            risk="不要同时改价、改详情页和换主图，否则无法判断哪个变量有效。",
        ),
        _package(
            package_id="AP-low-conversion-detail",
            name="详情页承接测试包",
            target_metric="转化率",
            diagnosis=f"{name}点击后转化偏弱时，优先测试详情页首屏卖点和承诺可信度。",
            operator_actions=[
                "对比竞品详情页前三屏表达",
                "调整首屏卖点顺序，把核心利益点提前",
                "补充尺寸、材质、安装或使用场景说明",
                "保持主图标题不变，小范围观察转化变化",
                "提交新旧详情页截图和转化率变化",
            ],
            submit_metrics=["转化率", "停留 / 咨询关键词", "收藏加购", "退款率", "新旧详情页截图"],
            evidence_required=["竞品前三屏截图", "旧详情页首屏", "新详情页首屏", "测试时间", "转化数据"],
            acceptance_criteria=["转化率提升", "咨询关键词减少", "退款率不升高", "详情页承诺更清楚"],
            failure_threshold=["转化无提升", "咨询或退款变多", "新增表达被判定夸大"],
            review_focus=["卖点顺序是否改变", "承诺是否可证明", "是否和标题 / 主图一致"],
            fit_condition=["点击率尚可但转化低", "详情页承接弱", "退款原因与认知偏差有关"],
            risk="详情页优化不能新增无法证明的承诺，也不能掩盖商品真实限制。",
        ),
    ]


def _roi_refund_packages(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    name = _product_name(item)
    return [
        _package(
            package_id="AP-refund-root-cause",
            name="售后归因与承诺修正包",
            target_metric="退款率 / ROI",
            diagnosis=f"{name}出现 ROI 低或退款偏高时，先处理承接和售后预期，再决定是否继续放量。",
            operator_actions=[
                "导出近 7 日退款原因并按关键词归类",
                "核对详情页承诺、主图文案和客服话术是否一致",
                "补充尺寸 / 材质 / 安装 / 使用限制说明",
                "暂停扩大预算，只保留必要测试流量",
                "观察 24-48 小时 ROI、退款率和咨询关键词变化",
            ],
            submit_metrics=["退款率", "退款原因关键词", "ROI", "客服咨询关键词", "修改前后截图"],
            evidence_required=["退款原因列表", "详情页承诺截图", "客服话术", "调整记录", "调整后数据"],
            acceptance_criteria=["退款率下降", "ROI 回升或止损", "咨询关键词更集中", "承诺表达更清楚"],
            failure_threshold=["退款率继续上升", "ROI 继续低于安全线", "出现新的高频投诉词"],
            review_focus=["是否先止损", "是否修正承诺", "是否保留可追溯证据"],
            fit_condition=["退款率高", "ROI 低", "售后原因集中", "详情页或客服承诺可能不一致"],
            risk="不要在退款原因未查清前继续放大投放。",
        ),
        _package(
            package_id="AP-traffic-loss-control",
            name="流量止损复盘包",
            target_metric="ROI / 转化率",
            diagnosis=f"{name}需要判断流量问题、承接问题还是退款损耗，而不是直接加预算。",
            operator_actions=[
                "找出高消耗低转化关键词或渠道",
                "拆分点击率、转化率、退款率三个指标判断先掉哪一环",
                "对低效流量先缩量或暂停扩大",
                "若是素材问题转入标题主图测试包；若是承接问题转入详情页测试包",
                "提交 ROI 复盘结论和下一步建议",
            ],
            submit_metrics=["花费", "点击率", "转化率", "ROI", "退款率", "高消耗低转化来源"],
            evidence_required=["渠道消耗表", "关键词 / 人群数据", "商品转化数据", "退款损耗数据"],
            acceptance_criteria=["明确问题环节", "预算风险被控制", "下一步测试路径清楚"],
            failure_threshold=["继续扩大预算", "没有区分点击 / 转化 / 退款原因", "缺少渠道数据"],
            review_focus=["是否先控制损耗", "是否能解释 ROI 下降原因", "是否有下一步测试包"],
            fit_condition=["ROI 低", "投放或活动流量参与", "退款或转化有异常"],
            risk="流量复盘不是直接停投或加投，而是先定位掉点环节。",
        ),
    ]


def _inventory_packages(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    name = _product_name(item)
    return [
        _package(
            package_id="AP-inventory-activity-control",
            name="库存与活动节奏控制包",
            target_metric="缺货风险 / 活动承接",
            diagnosis=f"{name}存在库存承接风险，先确认补货与活动节奏，避免爆单缺货和退款。",
            operator_actions=[
                "确认当前可售库存和安全库存",
                "确认供应商补货周期和最早到货时间",
                "估算当前活动 / 推广流量的库存消耗",
                "必要时限制活动、缩小推广或设置限量",
                "提交库存处理结论和是否继续放量建议",
            ],
            submit_metrics=["当前库存", "安全库存", "补货周期", "活动消耗预估", "缺货退款风险"],
            evidence_required=["库存截图", "补货计划", "活动报名 / 流量计划", "库存消耗估算"],
            acceptance_criteria=["补货周期清楚", "活动节奏可控", "缺货风险有处理方案"],
            failure_threshold=["补货时间不明确", "继续放大活动", "缺货退款风险未处理"],
            review_focus=["库存是否能承接", "是否需要暂缓活动", "是否需要调整推广节奏"],
            fit_condition=["库存偏低", "活动流量上升", "补货周期不确定"],
            risk="库存任务的核心是承接风险，不是单纯看当前库存数字。",
        )
    ]


def _competitor_packages(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    name = _product_name(item)
    bad_review = item.get("badReview") or "竞品差评"
    return [
        _package(
            package_id="AP-competitor-review-to-selling-point",
            name="竞品差评反向卖点测试包",
            target_metric="点击率 / 转化率",
            diagnosis=f"{name}可把“{bad_review}”转成自家可证明卖点，但不能直接跟价或攻击竞品。",
            operator_actions=[
                "收集 5-10 条同类竞品差评样本",
                "提取可验证痛点，转成自家标题 / 主图 / 详情页卖点",
                "生成不点名竞品的对比表达",
                "上架小范围测试卖点表达",
                "提交点击率、转化率和咨询关键词变化",
            ],
            submit_metrics=["竞品差评样本", "点击率", "转化率", "咨询关键词", "测试版本截图"],
            evidence_required=["竞品差评截图", "自家商品事实证明", "测试标题 / 主图 / 详情页截图", "测试数据"],
            acceptance_criteria=["差评痛点被转成可验证卖点", "点击或转化改善", "没有直接攻击竞品"],
            failure_threshold=["无事实支撑", "直接跟价", "违规对比或攻击竞品"],
            review_focus=["痛点是否真实", "自家是否能证明", "表达是否合规"],
            fit_condition=["竞品差评集中", "自家存在对应优势", "需要生成测试假设"],
            risk="竞品信号要转成测试假设，不是直接跟价。",
        )
    ]


def _report_packages(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        _package(
            package_id="AP-report-to-operation-task",
            name="报表异常转经营任务包",
            target_metric="异常对象识别",
            diagnosis="报表异常属于 Agent 判定链路，不应直接变成运营执行动作，需先转成具体商品 / 流量 / 售后 / 库存任务。",
            operator_actions=[
                "确认本次报表来源和同步时间",
                "筛出异常商品 / 订单 / 客户对象",
                "按异常类型转成商品、流量、售后、库存或竞品任务",
                "不把报表复核本身当作长期待办",
                "提交异常对象列表和转任务结果",
            ],
            submit_metrics=["异常对象数", "异常字段", "转任务数量", "退回补充数量"],
            evidence_required=["导入记录", "异常字段列表", "异常对象 ID", "转任务清单"],
            acceptance_criteria=["异常对象被定位", "可执行任务已生成", "无效报表已退回补充"],
            failure_threshold=["只停留在查看报表", "没有定位对象", "没有转成经营任务"],
            review_focus=["报表是否可信", "异常是否转成具体任务", "是否避免重复任务"],
            fit_condition=["报表刚导入", "字段或数据异常", "需要转成经营任务"],
            risk="报表处理是 Agent / 总管判定工作，不应让运营做无边界的数据排查。",
        )
    ]


def _general_packages(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    name = _product_name(item)
    return [
        _package(
            package_id="AP-general-small-test",
            name="通用小范围验证包",
            target_metric="异常指标改善",
            diagnosis=f"{name}问题类型暂不明确，先用小范围验证避免大动作误伤。",
            operator_actions=["补齐关键指标", "选择一个最小变量测试", "记录前后数据", "提交处理结果", "由总管决定是否扩展"],
            submit_metrics=["处理前指标", "处理后指标", "操作截图", "异常说明"],
            evidence_required=["来源数据", "处理动作", "结果指标", "复核结论"],
            acceptance_criteria=["问题归因更清楚", "动作可回滚", "证据完整"],
            failure_threshold=["动作过大", "证据不足", "无法判断变量"],
            review_focus=["是否小范围", "是否可回滚", "是否有数据结果"],
            fit_condition=["问题类型不明确", "缺少历史经验", "需要先验证"],
            risk="通用方案只能用于过渡，后续必须沉淀成明确问题类型。",
        )
    ]


def action_plan_for_problem(
    problem_type: str,
    *,
    item: Dict[str, Any] | None = None,
    source_module: str | None = None,
    rag_items: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    item = deepcopy(item or {})
    if not problem_type or problem_type == "general_operation":
        problem_type = infer_action_problem_type(item, source_module=source_module, fallback=problem_type or "general_operation")
    if problem_type == "low_ctr_low_conversion":
        packages = _ctr_conversion_packages(item)
        action_type = "标题主图 / 详情页测试"
    elif problem_type == "detail_page_conversion":
        packages = [_ctr_conversion_packages(item)[1]]
        action_type = "详情页承接优化"
    elif problem_type == "low_roi_high_refund":
        packages = _roi_refund_packages(item)
        action_type = "售后归因 / 流量止损"
    elif problem_type == "low_inventory_activity":
        packages = _inventory_packages(item)
        action_type = "库存承接 / 活动节奏"
    elif problem_type == "competitor_signal_to_test":
        packages = _competitor_packages(item)
        action_type = "竞品差评反向测试"
    elif problem_type == "report_data_anomaly":
        packages = _report_packages(item)
        action_type = "报表异常转任务"
    else:
        packages = _general_packages(item)
        action_type = "小范围验证"
    selected = packages[0]
    return {
        "version": ACTION_PLAN_VERSION,
        "problemType": problem_type,
        "problemLabel": PROBLEM_LABELS.get(problem_type, PROBLEM_LABELS["general_operation"]),
        "actionPlanType": action_type,
        "diagnosis": selected["diagnosis"],
        "recommendedPackage": selected,
        "executionPackages": packages,
        "executionSteps": selected["operatorAction"],
        "evidenceRequired": selected["evidenceRequired"],
        "submitMetrics": selected["submitMetrics"],
        "acceptanceCriteria": selected["acceptanceCriteria"],
        "failureThreshold": selected["failureThreshold"],
        "reviewFocus": selected["reviewFocus"],
        "ragReferences": [case.get("caseId") for case in rag_items or []],
        "boundary": "模块发现问题，Action Plan 按问题类型生成处理包；Agent 不按模块套同一模板，也不直接执行经营动作。",
        "forbiddenActions": FORBIDDEN_ACTIONS,
    }
