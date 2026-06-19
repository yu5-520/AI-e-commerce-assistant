"""V4 module Agent service.

The V4 Agent layer is deliberately advisory. It reads the same module / task
payloads that the product already shows, then returns structured suggestions,
evidence, draft tasks, and human decision points. It must not directly execute
marketplace actions such as price changes, ad spend changes, refunds, publishing,
or ERP / CRM writes.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List

from src.services.account_service import current_user, visible_store_ids_for_user
from src.services.module_data_service import (
    COMPETITORS,
    LISTINGS,
    PRODUCTS,
    REPORT_DETAILS,
    TRAFFIC,
    all_reports,
    find_by_id,
)
from src.services.module_task_service import create_task, list_tasks

AGENT_VERSION = "4.0.0"
FORBIDDEN_ACTIONS = [
    "不直接改价",
    "不直接投放",
    "不直接退款",
    "不直接修改真实店铺",
    "不直接回写 ERP / CRM",
]

AGENT_BOUNDARY = "Agent 只生成建议、草案、摘要和任务拆解，不直接执行经营动作。"

MODULE_META: Dict[str, Dict[str, str]] = {
    "product": {"label": "商品经营列表", "route": "business-products", "entityType": "商品"},
    "competitor": {"label": "竞品观察列表", "route": "business-competitors", "entityType": "竞品"},
    "listing": {"label": "上新测试台", "route": "business-listing", "entityType": "上新"},
    "traffic": {"label": "流量测试台", "route": "business-traffic", "entityType": "流量"},
    "report": {"label": "ERP / CRM 报表管理", "route": "data-check", "entityType": "报表"},
    "task": {"label": "统一任务池", "route": "business-actions", "entityType": "任务"},
}


def _now() -> str:
    return datetime.now().isoformat()


def _viewer(user_id: str | None) -> Dict[str, Any]:
    return current_user(user_id)


def _visible_store_ids(user_id: str | None) -> set[str]:
    return set(visible_store_ids_for_user(user_id))


def _store_visible(item: Dict[str, Any], user_id: str | None) -> bool:
    store_id = item.get("storeId")
    if not store_id:
        return True
    return store_id in _visible_store_ids(user_id)


def _level_from_text(text: str) -> str:
    if any(word in text for word in ["暂停", "退款", "售后", "告急", "danger", "风险", "低 ROI", "ROI 低"]):
        return "高"
    if any(word in text for word in ["偏高", "偏低", "warning", "复查", "谨慎", "待补货"]):
        return "中"
    return "低"


def _meta(module: str) -> Dict[str, str]:
    return MODULE_META.get(module, {"label": "经营模块", "route": "dashboard", "entityType": "经营对象"})


def _agent_id(module: str, entity_id: str, mode: str) -> str:
    safe_mode = mode.replace(" ", "-") or "analysis"
    return f"AGENT-V4-{module.upper()}-{entity_id}-{safe_mode}"


def _common_result(
    *,
    module: str,
    entity_id: str,
    mode: str,
    agent_name: str,
    summary: str,
    evidence: List[Dict[str, Any]],
    suggestions: List[str],
    task_drafts: List[Dict[str, Any]],
    human_decision: List[str],
    next_step: str,
    risk_level: str | None = None,
    input_snapshot: Dict[str, Any] | None = None,
    extra: Dict[str, Any] | None = None,
    user_id: str | None = None,
) -> Dict[str, Any]:
    meta = _meta(module)
    text = " ".join([summary, next_step, *(suggestions or [])])
    result = {
        "agentId": _agent_id(module, entity_id, mode),
        "agentName": agent_name,
        "agentVersion": AGENT_VERSION,
        "mode": mode,
        "sourceModule": meta["label"],
        "sourceRoute": meta["route"],
        "module": module,
        "entityType": meta["entityType"],
        "entityId": entity_id,
        "generatedAt": _now(),
        "viewer": {
            "userId": _viewer(user_id).get("id"),
            "roleName": _viewer(user_id).get("roleName"),
            "insightDepth": _viewer(user_id).get("insightDepth"),
        },
        "inputSnapshot": input_snapshot or {},
        "riskLevel": risk_level or _level_from_text(text),
        "summary": summary,
        "evidence": evidence,
        "suggestions": suggestions,
        "taskDrafts": task_drafts,
        "humanDecision": human_decision,
        "forbiddenActions": FORBIDDEN_ACTIONS,
        "boundary": AGENT_BOUNDARY,
        "nextStep": next_step,
    }
    if extra:
        result.update(extra)
    return result


def _draft_base(module: str, item: Dict[str, Any], title: str, task: str, reason: str, risk_domain: str, priority: str = "中") -> Dict[str, Any]:
    meta = _meta(module)
    product_id = item.get("productId") or item.get("id")
    store_ids = [item.get("storeId")] if item.get("storeId") else []
    return {
        "title": title,
        "task": task,
        "reason": reason,
        "priority": priority,
        "priorityLevel": "danger" if priority == "高" else "warning" if priority == "中" else "good",
        "deadline": "今天内" if priority == "高" else "明天前",
        "riskDomain": risk_domain,
        "actionType": "复查",
        "taskType": f"V4 Agent {risk_domain}检查",
        "taskSignal": "Agent 建议，人工确认",
        "entityType": meta["entityType"],
        "entityId": item.get("id") or product_id,
        "source": "V4 Module Agent",
        "sourceModule": meta["label"],
        "sourceRoute": meta["route"],
        "productRoute": meta["route"],
        "storeIds": store_ids,
        "visibleStoreIds": store_ids,
        "productId": product_id,
        "productTitle": item.get("title") or item.get("name") or title,
        "productShort": item.get("shortName") or item.get("targetProduct") or item.get("sourceName") or item.get("name") or item.get("id") or "对象",
        "platform": item.get("platform") or item.get("source") or "经营单元",
        "store": item.get("store") or "经营单元",
        "judgmentTags": [value for value in [risk_domain, item.get("status"), item.get("inventoryStatus"), item.get("afterSales"), item.get("channel")] if value],
        "createdByRole": "agent",
        "agentJudgment": {
            "status": "advisory",
            "version": AGENT_VERSION,
            "summary": reason,
            "boundary": AGENT_BOUNDARY,
            "forbiddenActions": FORBIDDEN_ACTIONS,
        },
    }


def get_agent_plan() -> Dict[str, Any]:
    return {
        "version": AGENT_VERSION,
        "mode": "module_agent_layer",
        "principle": "Agent 不放在最高控制位，而是放进各经营模块做增强。",
        "boundary": AGENT_BOUNDARY,
        "forbiddenActions": FORBIDDEN_ACTIONS,
        "agents": [
            {"id": "competitor-analysis", "name": "竞品数据收集分析 Agent", "module": "competitor", "output": "机会点、风险点、上新假设"},
            {"id": "listing-creative", "name": "上新标题 / 主图方案 Agent", "module": "listing", "output": "标题方向、主图构图、卖点排序"},
            {"id": "aftersales-root-cause", "name": "售后归因 Agent", "module": "product", "output": "售后原因、详情页承诺、客服检查清单"},
            {"id": "traffic-review", "name": "流量复盘 Agent", "module": "traffic", "output": "ROI 复盘、承接短板、放量边界"},
            {"id": "report-summary", "name": "报表摘要 Agent", "module": "report", "output": "异常摘要、影响范围、下一轮任务"},
            {"id": "task-breakdown", "name": "任务拆解 Agent", "module": "task", "output": "子任务草案、证据要求、复核点"},
            {"id": "cycle-report", "name": "日报 / 周报 Agent", "module": "task", "output": "周期摘要、完成/未完成、下轮风险"},
        ],
    }


def _product_agent(item: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    high = item.get("afterSalesLevel") != "good" or item.get("inventoryLevel") == "danger"
    risk_domain = "售后" if item.get("afterSalesLevel") != "good" else "库存" if item.get("inventoryLevel") == "danger" else "商品"
    evidence = [
        {"label": "库存", "value": f"{item.get('inventory')}（{item.get('inventoryStatus')}）"},
        {"label": "售后", "value": item.get("afterSales")},
        {"label": "毛利率", "value": item.get("grossMargin")},
        {"label": "售价 / 成本", "value": f"¥{item.get('price')} / ¥{item.get('cost')}"},
    ]
    suggestions = [
        "先复查售后原因，再决定是否放量或补货。",
        "核对详情页承诺、客服话术和用户真实反馈是否一致。",
        "把库存、退款和毛利放在同一张处理单里看，避免单点决策。",
    ]
    draft = _draft_base(
        "product",
        item,
        f"复查{item.get('shortName')}的{risk_domain}风险",
        f"核对{item.get('shortName')}库存、售后和毛利承接，形成处理结论。",
        item.get("suggestion") or "商品存在经营信号，需要人工确认。",
        risk_domain,
        "高" if high else "中",
    )
    return _common_result(
        module="product",
        entity_id=item["id"],
        mode=mode,
        agent_name="售后归因 Agent" if risk_domain == "售后" else "商品承接 Agent",
        summary=f"{item.get('shortName')}当前主要风险是{risk_domain}。Agent 建议先做归因，不直接调整价格或投放。",
        evidence=evidence,
        suggestions=suggestions,
        task_drafts=[draft],
        human_decision=["是否暂停放量", "是否补充详情页说明", "是否进入补货 / 清货流程"],
        next_step="进入详情报告确认证据，再由人工把 Agent 草案加入任务清单。",
        input_snapshot={"id": item.get("id"), "title": item.get("title"), "storeId": item.get("storeId")},
        user_id=user_id,
    )


def _competitor_agent(item: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    draft = _draft_base(
        "competitor",
        item,
        f"把{item.get('targetProduct')}竞品信号转成测试假设",
        f"围绕“{item.get('badReview')}”差评点，整理自家商品可验证的详情页 / 上新测试方案。",
        item.get("suggestion") or "竞品出现可转化信号。",
        "竞品",
        "中" if item.get("status") == "机会" else "高",
    )
    return _common_result(
        module="competitor",
        entity_id=item["id"],
        mode=mode,
        agent_name="竞品数据收集分析 Agent",
        summary=f"竞品价格位置为{item.get('pricePosition')}，差评集中在“{item.get('badReview')}”。适合先转成测试假设，而不是直接跟价。",
        evidence=[
            {"label": "目标商品", "value": item.get("targetProduct")},
            {"label": "价格位置", "value": item.get("pricePosition")},
            {"label": "差评关键词", "value": item.get("badReview")},
            {"label": "机会点", "value": item.get("opportunity")},
        ],
        suggestions=["补齐竞品差评样本", "对照自家详情页承诺", "把机会点转成上新 / 详情页测试，不直接降价"],
        task_drafts=[draft],
        human_decision=["是否跟进测试", "是否转入上新模块", "是否保持观察"],
        next_step="由总管或运营确认竞品信号是否足够进入任务池。",
        input_snapshot=deepcopy(item),
        user_id=user_id,
    )


def _listing_agent(item: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    creative_variants = [
        {"type": "标题方向", "value": f"{item.get('sourceName')}｜突出{item.get('testType')}与核心使用场景"},
        {"type": "主图方向", "value": "第一屏只放核心利益点 + 使用前后对比，不堆小字。"},
        {"type": "卖点排序", "value": f"先讲{item.get('testPlan')}，再讲风险控制和适用人群。"},
    ]
    draft = _draft_base(
        "listing",
        item,
        f"确认{item.get('title')}测试版本",
        "确认标题、主图、测试指标和失败阈值，再进入小范围上新测试。",
        item.get("suggestion") or item.get("risk") or "上新测试需要人工确认。",
        "上新",
        "高" if item.get("statusLevel") == "danger" else "中",
    )
    return _common_result(
        module="listing",
        entity_id=item["id"],
        mode=mode,
        agent_name="上新标题 / 主图方案多样生成 Agent",
        summary=f"{item.get('title')}适合先做小范围测试，Agent 只生成标题 / 主图方向，不自动发布商品。",
        evidence=[
            {"label": "测试类型", "value": item.get("testType")},
            {"label": "测试计划", "value": item.get("testPlan")},
            {"label": "目标指标", "value": item.get("targetMetric")},
            {"label": "截止时间", "value": item.get("due")},
        ],
        suggestions=[variant["value"] for variant in creative_variants],
        task_drafts=[draft],
        human_decision=["是否启动测试", "是否调整测试版本", "是否推迟上新"],
        next_step="先人工确认素材与指标，再把测试任务加入待办。",
        input_snapshot=deepcopy(item),
        extra={"creativeVariants": creative_variants},
        user_id=user_id,
    )


def _traffic_agent(item: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    priority = "高" if item.get("statusLevel") == "danger" else "中"
    draft = _draft_base(
        "traffic",
        item,
        f"复盘{item.get('channel')}流量承接",
        "先复查 ROI、退款率、库存和落地页一致性，再决定是否继续放量。",
        item.get("nextStep") or "流量数据需要复盘。",
        "流量",
        priority,
    )
    return _common_result(
        module="traffic",
        entity_id=item["id"],
        mode=mode,
        agent_name="流量复盘 Agent",
        summary=f"{item.get('channel')}当前状态为“{item.get('status')}”。Agent 建议先确认低 ROI 是流量问题还是商品承接问题。",
        evidence=[
            {"label": "曝光 / CTR", "value": f"{item.get('exposure')} / {item.get('ctr')}"},
            {"label": "转化率", "value": item.get("conversion")},
            {"label": "ROI", "value": item.get("roi")},
            {"label": "退款率", "value": item.get("refundRate")},
            {"label": "库存", "value": item.get("inventory")},
        ],
        suggestions=["不要先改预算", "先查售后 / 库存 / 素材短板", "人工确认后再决定暂停、缩量或换素材"],
        task_drafts=[draft],
        human_decision=["继续放量 / 暂停放量", "先查售后 / 先查库存", "是否更换素材"],
        next_step="把流量复盘草案加入任务池，由运营处理后提交给总管复核。",
        input_snapshot=deepcopy(item),
        user_id=user_id,
    )


def _report_agent(item: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    detail = REPORT_DETAILS.get(item["id"], {})
    summary_rows = detail.get("summary") or []
    evidence = [
        {"label": "报表来源", "value": item.get("source")},
        {"label": "同步状态", "value": item.get("status")},
        {"label": "记录数量", "value": item.get("count")},
        *({"label": label, "value": value} for label, value in summary_rows[:4]),
    ]
    draft = _draft_base(
        "report",
        item,
        f"摘要复核：{item.get('name')}",
        "确认报表字段可信度、异常范围和需要进入下一轮任务的对象。",
        f"{item.get('desc')}。导入后需要转成下一轮经营任务。",
        "报表",
        "中",
    )
    draft["productId"] = f"R-{item.get('id')}"
    return _common_result(
        module="report",
        entity_id=item["id"],
        mode=mode,
        agent_name="报表摘要 Agent",
        summary=f"{item.get('name')}已形成可读摘要。Agent 建议先确认数据可信度，再把异常转成任务。",
        evidence=evidence,
        suggestions=["确认同步时间", "检查异常字段", "识别影响商品 / 订单 / 客户范围", "把异常进入任务池而不是停留在查看"],
        task_drafts=[draft],
        human_decision=["是否重新导入", "是否生成经营任务", "是否需要人工复核数据"],
        next_step="确认报表可信度后，由人工创建经营任务。",
        input_snapshot=deepcopy(item),
        user_id=user_id,
    )


def _task_agent(task: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    risk_domain = task.get("riskDomain") or "通用"
    base = {
        "id": task.get("id"),
        "storeId": (task.get("storeIds") or [None])[0],
        "productId": task.get("productId") or task.get("entityId"),
        "title": task.get("title") or task.get("productTitle"),
        "shortName": task.get("productShort"),
        "platform": task.get("platform"),
        "store": task.get("store"),
    }
    draft_1 = _draft_base(
        "task",
        base,
        f"拆解执行：{task.get('productShort') or task.get('title')}",
        task.get("task") or "按来源报告完成第一步处理。",
        task.get("reason") or "任务需要拆解后执行。",
        risk_domain,
        task.get("priority") or "中",
    )
    draft_2 = _draft_base(
        "task",
        base,
        f"补充证据：{task.get('productShort') or task.get('title')}",
        "补充处理证据、截图、字段核对结果或客服归因，提交给总管复核。",
        "当前任务需要形成可复核证据。",
        "证据",
        "中",
    )
    return _common_result(
        module="task",
        entity_id=task["id"],
        mode=mode,
        agent_name="任务拆解 Agent",
        summary=f"该任务当前状态为“{task.get('status')}”，建议拆成执行处理和证据补充两步，避免运营只点击完成。",
        evidence=[
            {"label": "来源模块", "value": task.get("sourceModule") or task.get("source")},
            {"label": "任务状态", "value": task.get("status")},
            {"label": "优先级", "value": task.get("priority")},
            {"label": "负责人", "value": task.get("assigneeName")},
            {"label": "复核人", "value": task.get("reviewerName")},
        ],
        suggestions=["先看来源详情报告", "按风险域拆成可验收动作", "处理后必须提交证据给总管复核"],
        task_drafts=[draft_1, draft_2],
        human_decision=["是否需要拆分给不同运营", "是否需要财务 / 售后协同", "是否直接退回补充证据"],
        next_step="由总管确认拆分方式；运营只执行被确认后的任务。",
        risk_level=task.get("priority") or "中",
        input_snapshot={"taskId": task.get("id"), "status": task.get("status"), "workflowStatus": task.get("workflowStatus")},
        user_id=user_id,
    )


def run_module_agent(module: str, entity_id: str, mode: str = "analysis", user_id: str | None = None) -> Dict[str, Any] | None:
    module = module.strip().lower()
    if module == "product":
        item = find_by_id(PRODUCTS, entity_id)
        return _product_agent(item, mode, user_id) if item and _store_visible(item, user_id) else None
    if module == "competitor":
        item = find_by_id(COMPETITORS, entity_id)
        return _competitor_agent(item, mode, user_id) if item else None
    if module == "listing":
        item = find_by_id(LISTINGS, entity_id)
        return _listing_agent(item, mode, user_id) if item and _store_visible(item, user_id) else None
    if module == "traffic":
        item = find_by_id(TRAFFIC, entity_id)
        return _traffic_agent(item, mode, user_id) if item and _store_visible(item, user_id) else None
    if module == "report":
        item = find_by_id(all_reports(), entity_id)
        return _report_agent(item, mode, user_id) if item else None
    if module == "task":
        task = next((item for item in list_tasks(active_only=False, viewer_id=user_id) if item.get("id") == entity_id), None)
        return _task_agent(task, mode, user_id) if task else None
    return None


def create_agent_task(module: str, entity_id: str, draft_index: int = 0, mode: str = "analysis", user_id: str | None = None) -> Dict[str, Any] | None:
    agent_result = run_module_agent(module, entity_id, mode=mode, user_id=user_id)
    if not agent_result:
        return None
    drafts = agent_result.get("taskDrafts") or []
    if draft_index < 0 or draft_index >= len(drafts):
        return None
    draft = deepcopy(drafts[draft_index])
    draft["agentJudgment"] = {
        "status": "advisory_confirmed",
        "version": AGENT_VERSION,
        "agentId": agent_result.get("agentId"),
        "summary": agent_result.get("summary"),
        "boundary": AGENT_BOUNDARY,
        "forbiddenActions": FORBIDDEN_ACTIONS,
    }
    task = create_task(draft)
    return {"agent": agent_result, "task": task, "createdBy": "V4 Module Agent", "requiresHumanConfirmation": True}


def run_cycle_agent(target: str = "日报", user_id: str | None = None) -> Dict[str, Any]:
    tasks = list_tasks(active_only=False, viewer_id=user_id)
    active = [task for task in tasks if task.get("status") not in {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}]
    completed = [task for task in tasks if task.get("status") in {"已完成", "已通过", "已写入复盘"}]
    high_risk = [task for task in active if task.get("priority") == "高"]
    summary = f"{target}范围内共有 {len(active)} 个未完成任务，{len(high_risk)} 个高优先级风险，{len(completed)} 个已完成 / 可归档结果。"
    return _common_result(
        module="task",
        entity_id=f"cycle-{target}",
        mode="cycle_report",
        agent_name="日报 / 周报 Agent",
        summary=summary,
        evidence=[
            {"label": "未完成任务", "value": len(active)},
            {"label": "高优先级", "value": len(high_risk)},
            {"label": "已完成 / 归档", "value": len(completed)},
            {"label": "当前账号", "value": _viewer(user_id).get("roleName")},
        ],
        suggestions=["先处理高优先级任务", "把已完成任务写入日报 / 周报", "对退回任务补证据，不直接关闭"],
        task_drafts=[],
        human_decision=["哪些任务进入日报", "哪些任务进入周报", "哪些任务需要总管复核"],
        next_step="由总管确认周期摘要后，再写入复盘审计。",
        risk_level="高" if high_risk else "中" if active else "低",
        input_snapshot={"activeTaskIds": [task.get("id") for task in active[:10]], "completedTaskIds": [task.get("id") for task in completed[:10]]},
        extra={"target": target, "activeTasks": active[:10], "completedTasks": completed[:10]},
        user_id=user_id,
    )
