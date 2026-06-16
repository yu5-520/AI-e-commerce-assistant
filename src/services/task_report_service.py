"""Task and candidate report service.

The report layer explains why a warning exists, what evidence supports it, and
how an operator should handle the task. It is the future Agent insertion point:
Agent can enrich these report payloads without owning task completion.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from src.services.module_data_service import (
    COMPETITORS,
    LISTINGS,
    PRODUCTS,
    REPORT_DETAILS,
    TRAFFIC,
    all_reports,
    find_by_id,
)
from src.services.module_task_service import list_tasks

MODULE_LABELS = {
    "product": "商品经营列表",
    "competitor": "竞品观察列表",
    "listing": "上新测试台",
    "traffic": "流量测试台",
    "report": "ERP / CRM 报表管理",
}

MODULE_ROUTES = {
    "product": "business-products",
    "competitor": "business-competitors",
    "listing": "business-listing",
    "traffic": "business-traffic",
    "report": "data-check",
}


def _now() -> str:
    return datetime.now().isoformat()


def _level_from_text(text: str) -> str:
    if any(word in text for word in ["暂停", "退款", "售后", "高", "danger", "告急", "风险"]):
        return "高"
    if any(word in text for word in ["warning", "谨慎", "复查", "偏高", "待补货"]):
        return "中"
    return "低"


def _base_report(module: str, entity_id: str, title: str, summary: str, evidence: List[Dict[str, str]], suggested_actions: List[str], checklist: List[str], data_needed: List[str], human_decision: List[str], next_step: str, related_task: Dict[str, Any] | None = None) -> Dict[str, Any]:
    text = " ".join([summary, next_step, *(item.get("value", "") for item in evidence), *(suggested_actions or [])])
    risk_level = related_task.get("priority") if related_task and related_task.get("priority") else _level_from_text(text)
    return {
        "reportId": f"RPT-{module}-{entity_id}",
        "reportType": "task" if related_task else "candidate",
        "module": module,
        "sourceModule": MODULE_LABELS.get(module, related_task.get("sourceModule") if related_task else "经营模块"),
        "sourceRoute": MODULE_ROUTES.get(module, related_task.get("sourceRoute") if related_task else "dashboard"),
        "entityId": entity_id,
        "taskId": related_task.get("id") if related_task else None,
        "taskStatus": related_task.get("status") if related_task else "候选预警",
        "generatedAt": _now(),
        "title": title,
        "warningSummary": summary,
        "riskLevel": risk_level,
        "evidence": evidence,
        "aiAssessment": "这是基于当前 Mock ERP / CRM / 运营数据生成的结构化评估。后续接入 Agent 后，这里会升级为可追溯的 AI 详细判断。",
        "suggestedActions": suggested_actions,
        "operationChecklist": checklist,
        "dataNeeded": data_needed,
        "humanDecision": human_decision,
        "nextStep": next_step,
        "agentBoundary": "Agent 只生成评估和处理清单，不直接改预算、库存、价格、上新状态或店铺数据。",
        "archiveRule": "任务完成后，来源候选退出当前模块循环位，报告快照进入日志复盘。",
        "relatedTask": related_task,
    }


def _candidate_item(module: str, entity_id: str) -> Dict[str, Any] | None:
    if module == "product":
        return find_by_id(PRODUCTS, entity_id)
    if module == "competitor":
        return find_by_id(COMPETITORS, entity_id)
    if module == "listing":
        return find_by_id(LISTINGS, entity_id)
    if module == "traffic":
        return find_by_id(TRAFFIC, entity_id)
    if module == "report":
        return find_by_id(all_reports(), entity_id)
    return None


def _report_for_product(item: Dict[str, Any], task: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return _base_report(
        "product",
        item["id"],
        f"商品预警报告｜{item['shortName']}",
        item["suggestion"],
        [
            {"label": "库存", "value": f"{item['inventory']}（{item['inventoryStatus']}）"},
            {"label": "售后", "value": item["afterSales"]},
            {"label": "毛利率", "value": item["grossMargin"]},
            {"label": "售价 / 成本", "value": f"¥{item['price']} / ¥{item['cost']}"},
        ],
        ["复查商品承接能力", "检查售后归因", "确认是否继续推广或补货"],
        ["核对库存安全线", "查看退款原因分布", "复核详情页承诺和客服话术", "确认毛利是否能承接活动价"],
        ["近 7 日订单", "近 7 日退款原因", "客服咨询关键词", "当前库存周转天数"],
        ["是否暂停放量", "是否补详情页说明", "是否进入补货或清货流程"],
        "先完成商品风险归因，再决定是否扩大流量或进入上新测试。",
        task,
    )


def _report_for_competitor(item: Dict[str, Any], task: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return _base_report(
        "competitor",
        item["id"],
        f"竞品机会报告｜{item['targetProduct']}",
        item["suggestion"],
        [
            {"label": "竞品价格位置", "value": item["pricePosition"]},
            {"label": "差评关键词", "value": item["badReview"]},
            {"label": "机会点", "value": item["opportunity"]},
            {"label": "状态", "value": item["status"]},
        ],
        ["判断是否值得跟进", "把竞品差评转成测试假设", "避免盲目跟价"],
        ["确认竞品差评是否高频", "对照自家商品详情页", "确认是否需要生成上新测试版本"],
        ["竞品销量区间", "差评样本", "价格变动周期", "自家商品同类售后数据"],
        ["是否跟进测试", "是否转入上新模块", "是否保持观察"],
        "先把竞品信号转成可验证假设，再进入上新或商品优化。",
        task,
    )


def _report_for_listing(item: Dict[str, Any], task: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return _base_report(
        "listing",
        item["id"],
        f"上新测试报告｜{item['title']}",
        f"{item['risk']} {item['suggestion']}",
        [
            {"label": "测试类型", "value": item["testType"]},
            {"label": "测试计划", "value": item["testPlan"]},
            {"label": "目标指标", "value": item["targetMetric"]},
            {"label": "截止时间", "value": item["due"]},
        ],
        ["确认测试假设", "设定成功/失败阈值", "控制小范围测试成本"],
        ["确认主图/标题/SKU 版本", "确认测试周期", "确认预算和库存承接", "设定复盘时间"],
        ["上新素材", "测试流量来源", "转化率基准", "退款率基准"],
        ["是否启动测试", "是否调整测试版本", "是否推迟上新"],
        "先把测试目标和失败阈值写清楚，再进入执行队列。",
        task,
    )


def _report_for_traffic(item: Dict[str, Any], task: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return _base_report(
        "traffic",
        item["id"],
        f"流量预警报告｜{item['channel']}",
        item["nextStep"],
        [
            {"label": "曝光 / CTR", "value": f"{item['exposure']} / {item['ctr']}"},
            {"label": "转化率", "value": item["conversion"]},
            {"label": "ROI", "value": item["roi"]},
            {"label": "退款率", "value": item["refundRate"]},
            {"label": "库存", "value": item["inventory"]},
        ],
        ["判断是否继续放量", "先查售后/库存/素材短板", "避免预算直接扩大"],
        ["核对 ROI 是否达到安全线", "检查退款率是否异常", "确认库存能否承接", "复查素材和落地页一致性"],
        ["广告消耗", "成交金额", "退款原因", "素材点击分布", "库存安全线"],
        ["继续放量 / 暂停放量", "先查售后 / 先查库存", "是否更换素材"],
        "不要先改预算，先确认低 ROI 是流量问题还是商品承接问题。",
        task,
    )


def _report_for_report(item: Dict[str, Any], task: Dict[str, Any] | None = None) -> Dict[str, Any]:
    detail = REPORT_DETAILS.get(item["id"], {})
    evidence = [
        {"label": "报表来源", "value": item["source"]},
        {"label": "同步状态", "value": item["status"]},
        {"label": "记录数量", "value": item["count"]},
        {"label": "用途", "value": item["desc"]},
    ]
    if detail.get("summary"):
        evidence.extend({"label": label, "value": value} for label, value in detail["summary"][:4])
    return _base_report(
        "report",
        item["id"],
        f"报表复盘报告｜{item['name']}",
        f"{item['desc']}。导入后需要转成下一轮经营任务，而不是只停留在数据查看。",
        evidence,
        ["确认数据可信度", "定位异常字段", "生成下一轮经营任务"],
        ["确认同步时间", "检查异常字段", "确认影响商品/订单/客户范围", "把异常转入任务池"],
        ["原始报表文件", "同步日志", "异常字段样本", "影响范围明细"],
        ["是否重新导入", "是否生成经营任务", "是否需要人工复核数据"],
        "先确认报表可信度，再把异常转成可执行任务。",
        task,
    )


def get_candidate_report(module: str, entity_id: str) -> Dict[str, Any] | None:
    item = _candidate_item(module, entity_id)
    if not item:
        return None
    builders = {
        "product": _report_for_product,
        "competitor": _report_for_competitor,
        "listing": _report_for_listing,
        "traffic": _report_for_traffic,
        "report": _report_for_report,
    }
    builder = builders.get(module)
    return builder(item) if builder else None


def _module_from_task(task: Dict[str, Any]) -> str:
    source = task.get("sourceModule") or task.get("source") or ""
    route = task.get("sourceRoute") or ""
    if "商品" in source or route == "business-products":
        return "product"
    if "竞品" in source or route == "business-competitors":
        return "competitor"
    if "上新" in source or route == "business-listing":
        return "listing"
    if "流量" in source or route == "business-traffic":
        return "traffic"
    if "报表" in source or route == "data-check":
        return "report"
    return "task"


def get_task_report(task_id: str) -> Dict[str, Any] | None:
    task = next((item for item in list_tasks(active_only=False) if item.get("id") == task_id), None)
    if not task:
        return None
    module = _module_from_task(task)
    entity_id = task.get("entityId") or task.get("productId") or task_id
    if module == "report" and str(task.get("productId", "")).startswith("R-"):
        entity_id = str(task["productId"])[2:]
    candidate = get_candidate_report(module, entity_id)
    if candidate:
        candidate["reportType"] = "task"
        candidate["taskId"] = task_id
        candidate["taskStatus"] = task.get("status")
        candidate["relatedTask"] = task
        candidate["sourceModule"] = task.get("sourceModule") or candidate["sourceModule"]
        candidate["sourceRoute"] = task.get("sourceRoute") or candidate["sourceRoute"]
        candidate["title"] = f"任务详情报告｜{task.get('productShort') or task.get('title') or task_id}"
        candidate["warningSummary"] = task.get("reason") or candidate["warningSummary"]
        candidate["riskLevel"] = task.get("priority") or candidate["riskLevel"]
        return candidate
    return _base_report(
        "task",
        task_id,
        f"任务详情报告｜{task.get('title') or task_id}",
        task.get("reason") or "该任务来自服务端任务池，需要人工确认后处理。",
        [
            {"label": "来源", "value": task.get("sourceModule") or task.get("source") or "任务池"},
            {"label": "优先级", "value": task.get("priority") or "中"},
            {"label": "状态", "value": task.get("status") or "待确认"},
            {"label": "去重键", "value": task.get("dedupeKey") or "未记录"},
        ],
        ["阅读任务原因", "确认处理边界", "完成后写入日志"],
        ["核对来源模块", "核对优先级", "确认是否需要补充数据"],
        ["关联商品/报表数据", "人工处理结果"],
        ["是否完成", "是否需要退回模块等待新信号"],
        task.get("task") or "按任务说明处理后，在待办中点击完成。",
        task,
    )
