"""V4 module Agent service.

The module Agent layer is advisory-only. In V4.4.2 it no longer returns one
generic task-breakdown template. Module signals are converted into problem types,
then the Action Plan service returns targeted execution packages.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List

from src.services.account_service import current_user, visible_store_ids_for_user
from src.services.action_plan_service import action_plan_for_problem, infer_action_problem_type
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

AGENT_VERSION = "4.4.2"
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
    return f"AGENT-V442-{module.upper()}-{entity_id}-{safe_mode}"


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


def _problem(module: str, item: Dict[str, Any]) -> str:
    return infer_action_problem_type(item, source_module=module)


def _enrich_with_plan(draft: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    package = plan.get("recommendedPackage") or {}
    draft["problemType"] = plan.get("problemType")
    draft["actionPlan"] = plan
    draft["selectedPackage"] = package
    draft["executionPackages"] = plan.get("executionPackages") or []
    draft["executionSteps"] = plan.get("executionSteps") or []
    draft["evidenceRequired"] = plan.get("evidenceRequired") or []
    draft["submitMetrics"] = plan.get("submitMetrics") or []
    draft["acceptanceCriteria"] = plan.get("acceptanceCriteria") or []
    draft["failureThreshold"] = plan.get("failureThreshold") or []
    draft["reviewFocus"] = plan.get("reviewFocus") or []
    draft["actionType"] = plan.get("actionPlanType") or draft.get("actionType")
    draft["taskType"] = "V4.4.2 问题类型处理包"
    draft["taskSignal"] = "problemType + ActionPlan + 人工确认"
    draft["task"] = f"执行“{package.get('packageName') or plan.get('actionPlanType')}”，按问题类型处理，不套通用模板。"
    draft["agentJudgment"] = {
        **(draft.get("agentJudgment") or {}),
        "version": AGENT_VERSION,
        "problemType": plan.get("problemType"),
        "actionPlanType": plan.get("actionPlanType"),
        "summary": plan.get("diagnosis"),
        "boundary": plan.get("boundary") or AGENT_BOUNDARY,
        "forbiddenActions": FORBIDDEN_ACTIONS,
    }
    return draft


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
        "actionType": "处理",
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
        "mode": "module_agent_layer_with_action_plan",
        "principle": "模块负责发现问题，Agent 按 problemType 生成处理包，不按模块套同一模板。",
        "boundary": AGENT_BOUNDARY,
        "forbiddenActions": FORBIDDEN_ACTIONS,
        "agents": [
            {"id": "competitor-analysis", "name": "竞品数据收集分析 Agent", "module": "competitor", "output": "差评反向测试包、机会点、上新假设"},
            {"id": "listing-creative", "name": "上新标题 / 主图方案 Agent", "module": "listing", "output": "标题主图测试包、卖点排序、失败阈值"},
            {"id": "aftersales-root-cause", "name": "售后归因 Agent", "module": "product", "output": "售后归因包、承诺修正、客服话术检查"},
            {"id": "traffic-review", "name": "流量复盘 Agent", "module": "traffic", "output": "ROI 止损包、标题主图包、详情页承接包"},
            {"id": "report-summary", "name": "报表摘要 Agent", "module": "report", "output": "报表异常转经营任务包"},
            {"id": "task-breakdown", "name": "任务处理包 Agent", "module": "task", "output": "problemType、executionPackages、证据与复核标准"},
            {"id": "cycle-report", "name": "日报 / 周报 Agent", "module": "task", "output": "周期摘要、完成/未完成、下轮风险"},
        ],
    }


def _product_agent(item: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    problem = _problem("product", item)
    plan = action_plan_for_problem(problem, item=item, source_module="product")
    high = item.get("afterSalesLevel") != "good" or item.get("inventoryLevel") == "danger"
    risk_domain = plan.get("actionPlanType") or ("售后" if item.get("afterSalesLevel") != "good" else "库存" if item.get("inventoryLevel") == "danger" else "商品")
    evidence = [
        {"label": "库存", "value": f"{item.get('inventory')}（{item.get('inventoryStatus')}）"},
        {"label": "售后", "value": item.get("afterSales")},
        {"label": "毛利率", "value": item.get("grossMargin")},
        {"label": "售价 / 成本", "value": f"¥{item.get('price')} / ¥{item.get('cost')}"},
    ]
    draft = _draft_base(
        "product",
        item,
        f"处理{item.get('shortName')}的{plan.get('problemLabel')}问题",
        "按问题类型处理包执行。",
        item.get("suggestion") or plan.get("diagnosis") or "商品存在经营信号，需要人工确认。",
        risk_domain,
        "高" if high else "中",
    )
    draft = _enrich_with_plan(draft, plan)
    return _common_result(
        module="product",
        entity_id=item["id"],
        mode=mode,
        agent_name="商品问题类型处理 Agent",
        summary=plan.get("diagnosis") or f"{item.get('shortName')}当前主要问题为{plan.get('problemLabel')}。",
        evidence=evidence,
        suggestions=plan.get("executionSteps") or [],
        task_drafts=[draft],
        human_decision=["选择处理包", "确认是否进入任务池", "确认复核指标"],
        next_step="选择对应处理包，人工确认后加入任务池。",
        input_snapshot={"id": item.get("id"), "title": item.get("title"), "storeId": item.get("storeId")},
        extra={"problemType": problem, "actionPlan": plan, "executionPackages": plan.get("executionPackages") or []},
        user_id=user_id,
    )


def _competitor_agent(item: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    problem = _problem("competitor", item)
    plan = action_plan_for_problem(problem, item=item, source_module="competitor")
    draft = _draft_base(
        "competitor",
        item,
        f"把{item.get('targetProduct')}竞品信号转成测试包",
        "按竞品差评反向卖点测试包执行。",
        item.get("suggestion") or plan.get("diagnosis") or "竞品出现可转化信号。",
        plan.get("actionPlanType") or "竞品",
        "中" if item.get("status") == "机会" else "高",
    )
    draft = _enrich_with_plan(draft, plan)
    return _common_result(
        module="competitor",
        entity_id=item["id"],
        mode=mode,
        agent_name="竞品数据收集分析 Agent",
        summary=plan.get("diagnosis") or f"竞品差评集中在“{item.get('badReview')}”。",
        evidence=[
            {"label": "目标商品", "value": item.get("targetProduct")},
            {"label": "价格位置", "value": item.get("pricePosition")},
            {"label": "差评关键词", "value": item.get("badReview")},
            {"label": "机会点", "value": item.get("opportunity")},
        ],
        suggestions=plan.get("executionSteps") or [],
        task_drafts=[draft],
        human_decision=["是否跟进测试", "选择哪个卖点测试包", "是否保持观察"],
        next_step="把竞品信号转成测试包，而不是直接跟价。",
        input_snapshot=deepcopy(item),
        extra={"problemType": problem, "actionPlan": plan, "executionPackages": plan.get("executionPackages") or []},
        user_id=user_id,
    )


def _listing_agent(item: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    problem = _problem("listing", item)
    plan = action_plan_for_problem(problem, item=item, source_module="listing")
    creative_variants = [
        {"type": "标题方向", "value": f"{item.get('sourceName')}｜突出{item.get('testType')}与核心使用场景"},
        {"type": "主图方向", "value": "第一屏只放核心利益点 + 使用前后对比，不堆小字。"},
        {"type": "卖点排序", "value": f"先讲{item.get('testPlan')}，再讲风险控制和适用人群。"},
    ]
    draft = _draft_base(
        "listing",
        item,
        f"上架测试{item.get('title')}处理包",
        "按标题主图 / 详情页测试包执行。",
        item.get("suggestion") or item.get("risk") or plan.get("diagnosis") or "上新测试需要人工确认。",
        plan.get("actionPlanType") or "上新",
        "高" if item.get("statusLevel") == "danger" else "中",
    )
    draft = _enrich_with_plan(draft, plan)
    return _common_result(
        module="listing",
        entity_id=item["id"],
        mode=mode,
        agent_name="上新标题 / 主图方案多样生成 Agent",
        summary=plan.get("diagnosis") or f"{item.get('title')}适合先做小范围测试。",
        evidence=[
            {"label": "测试类型", "value": item.get("testType")},
            {"label": "测试计划", "value": item.get("testPlan")},
            {"label": "目标指标", "value": item.get("targetMetric")},
            {"label": "截止时间", "value": item.get("due")},
        ],
        suggestions=plan.get("executionSteps") or [variant["value"] for variant in creative_variants],
        task_drafts=[draft],
        human_decision=["是否启动测试", "选择哪个测试包", "是否推迟上新"],
        next_step="先人工确认测试包和指标，再加入待办。",
        input_snapshot=deepcopy(item),
        extra={"creativeVariants": creative_variants, "problemType": problem, "actionPlan": plan, "executionPackages": plan.get("executionPackages") or []},
        user_id=user_id,
    )


def _traffic_agent(item: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    problem = _problem("traffic", item)
    plan = action_plan_for_problem(problem, item=item, source_module="traffic")
    priority = "高" if item.get("statusLevel") == "danger" else "中"
    draft = _draft_base(
        "traffic",
        item,
        f"处理{item.get('channel')}流量中的{plan.get('problemLabel')}问题",
        "按流量问题处理包执行。",
        item.get("nextStep") or plan.get("diagnosis") or "流量数据需要复盘。",
        plan.get("actionPlanType") or "流量",
        priority,
    )
    draft = _enrich_with_plan(draft, plan)
    return _common_result(
        module="traffic",
        entity_id=item["id"],
        mode=mode,
        agent_name="流量复盘 Agent",
        summary=plan.get("diagnosis") or f"{item.get('channel')}当前状态为“{item.get('status')}”。",
        evidence=[
            {"label": "曝光 / CTR", "value": f"{item.get('exposure')} / {item.get('ctr')}"},
            {"label": "转化率", "value": item.get("conversion")},
            {"label": "ROI", "value": item.get("roi")},
            {"label": "退款率", "value": item.get("refundRate")},
            {"label": "库存", "value": item.get("inventory")},
        ],
        suggestions=plan.get("executionSteps") or [],
        task_drafts=[draft],
        human_decision=["选择处理包", "是否暂停扩大预算", "是否转入创意 / 售后 / 库存任务"],
        next_step="把流量信号转成对应处理包，由运营执行后提交给总管复核。",
        input_snapshot=deepcopy(item),
        extra={"problemType": problem, "actionPlan": plan, "executionPackages": plan.get("executionPackages") or []},
        user_id=user_id,
    )


def _report_agent(item: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    detail = REPORT_DETAILS.get(item["id"], {})
    summary_rows = detail.get("summary") or []
    report_item = {**item, "sourceModule": "报表", "riskDomain": "报表", "taskType": "报表异常", "task": item.get("desc")}
    problem = _problem("report", report_item)
    plan = action_plan_for_problem(problem, item=report_item, source_module="report")
    evidence = [
        {"label": "报表来源", "value": item.get("source")},
        {"label": "同步状态", "value": item.get("status")},
        {"label": "记录数量", "value": item.get("count")},
        *({"label": label, "value": value} for label, value in summary_rows[:4]),
    ]
    draft = _draft_base(
        "report",
        item,
        f"把{item.get('name')}异常转成经营任务",
        "先定位异常对象，再转成具体商品、流量、库存或售后任务。",
        f"{item.get('desc')}。导入后需要转成下一轮经营任务。",
        plan.get("actionPlanType") or "报表",
        "中",
    )
    draft["productId"] = f"R-{item.get('id')}"
    draft = _enrich_with_plan(draft, plan)
    return _common_result(
        module="report",
        entity_id=item["id"],
        mode=mode,
        agent_name="报表摘要 Agent",
        summary=plan.get("diagnosis") or f"{item.get('name')}已形成可读摘要。",
        evidence=evidence,
        suggestions=plan.get("executionSteps") or [],
        task_drafts=[draft],
        human_decision=["是否重新导入", "异常对象转成哪些经营任务", "是否需要人工复核数据"],
        next_step="先定位异常对象，再转成具体经营任务。",
        input_snapshot=deepcopy(item),
        extra={"problemType": problem, "actionPlan": plan, "executionPackages": plan.get("executionPackages") or []},
        user_id=user_id,
    )


def _task_agent(task: Dict[str, Any], mode: str, user_id: str | None) -> Dict[str, Any]:
    problem = task.get("problemType") or task.get("agentJudgment", {}).get("problemType") or infer_action_problem_type(task, source_module=task.get("sourceModule"))
    plan = action_plan_for_problem(problem, item=task, source_module=task.get("sourceModule"))
    package = plan.get("recommendedPackage") or {}
    risk_domain = plan.get("actionPlanType") or task.get("riskDomain") or "通用"
    base = {
        "id": task.get("id"),
        "storeId": (task.get("storeIds") or [None])[0],
        "productId": task.get("productId") or task.get("entityId"),
        "title": task.get("title") or task.get("productTitle"),
        "shortName": task.get("productShort"),
        "platform": task.get("platform"),
        "store": task.get("store"),
        "sourceModule": task.get("sourceModule"),
        "riskDomain": task.get("riskDomain"),
        "taskType": task.get("taskType"),
        "taskSignal": task.get("taskSignal"),
        "task": task.get("task"),
        "reason": task.get("reason"),
        "judgmentTags": task.get("judgmentTags") or [],
    }
    draft = _draft_base(
        "task",
        base,
        f"执行{task.get('productShort') or task.get('title')}{package.get('packageName') or plan.get('actionPlanType')}",
        "按当前任务的问题类型处理包执行。",
        plan.get("diagnosis") or task.get("reason") or "任务需要按问题类型拆解后执行。",
        risk_domain,
        task.get("priority") or "中",
    )
    draft = _enrich_with_plan(draft, plan)
    return _common_result(
        module="task",
        entity_id=task["id"],
        mode=mode,
        agent_name="任务处理包 Agent",
        summary=plan.get("diagnosis") or f"该任务当前问题类型为“{plan.get('problemLabel')}”。",
        evidence=[
            {"label": "来源模块", "value": task.get("sourceModule") or task.get("source")},
            {"label": "任务状态", "value": task.get("status")},
            {"label": "问题类型", "value": plan.get("problemLabel")},
            {"label": "处理包", "value": package.get("packageName") or plan.get("actionPlanType")},
            {"label": "负责人", "value": task.get("assigneeName")},
        ],
        suggestions=plan.get("executionSteps") or [],
        task_drafts=[draft],
        human_decision=["选择处理包", "是否拆成子任务", "是否退回补充证据"],
        next_step="按问题类型处理包执行，提交指标和证据给总管复核。",
        risk_level=task.get("priority") or "中",
        input_snapshot={"taskId": task.get("id"), "status": task.get("status"), "workflowStatus": task.get("workflowStatus")},
        extra={"problemType": problem, "actionPlan": plan, "executionPackages": plan.get("executionPackages") or []},
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
        **(draft.get("agentJudgment") or {}),
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
