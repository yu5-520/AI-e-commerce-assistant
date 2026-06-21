"""V4.2+ task generation and playbook Agent service.

The task Agent converts module signals into task candidates, then routes each
candidate through the V4.4.2 problem-type Action Plan layer. This keeps handling
plans targeted: modules discover signals, problem types decide the execution
package.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from src.services.account_service import current_user
from src.services.action_plan_service import action_plan_for_problem, infer_action_problem_type
from src.services.experience_memory_service import infer_problem_type_from_task, search_cases
from src.services.module_data_service import COMPETITORS, LISTINGS, PRODUCTS, REPORT_DETAILS, TRAFFIC, find_by_id
from src.services.module_task_service import create_task, find_task

TASK_AGENT_VERSION = "4.4.2"
FORBIDDEN_ACTIONS = ["不直接改价", "不直接投放", "不直接退款", "不直接发布商品", "不直接回写 ERP / CRM"]

MODULE_DATA = {
    "product": PRODUCTS,
    "traffic": TRAFFIC,
    "competitor": COMPETITORS,
    "listing": LISTINGS,
}

MODULE_ROUTES = {
    "product": "business-products",
    "traffic": "business-traffic",
    "competitor": "business-competitors",
    "listing": "business-listing",
    "report": "data-check",
}

MODULE_LABELS = {
    "product": "商品经营列表",
    "traffic": "流量测试台",
    "competitor": "竞品观察列表",
    "listing": "上新测试台",
    "report": "ERP / CRM 报表",
}


def _viewer(user_id: str | None) -> Dict[str, Any]:
    user = current_user(user_id)
    return {"userId": user.get("id"), "roleId": user.get("roleId"), "roleName": user.get("roleName")}


def _source_item(source_module: str, entity_id: str | None = None, body: Dict[str, Any] | None = None) -> Dict[str, Any]:
    body = body or {}
    if body.get("sourcePayload"):
        return deepcopy(body["sourcePayload"])
    if source_module == "report":
        report_id = entity_id or body.get("reportId") or body.get("entityId") or "products"
        item = REPORT_DETAILS.get(report_id) or {}
        if item:
            result = deepcopy(item)
            result["id"] = report_id
            result.setdefault("platform", "通用")
            result.setdefault("storeId", "global")
            result.setdefault("store", "报表中心")
            return result
    items = MODULE_DATA.get(source_module) or []
    found = find_by_id(items, entity_id or body.get("entityId") or body.get("id") or "")
    return deepcopy(found or body)


def _text_from_item(item: Dict[str, Any]) -> str:
    values: List[str] = []
    for key in [
        "riskDomain",
        "taskType",
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
        "title",
        "sourceModule",
    ]:
        if item.get(key) is not None:
            values.append(str(item[key]))
    values.extend(str(value) for value in item.get("judgmentTags") or [])
    return " ".join(values)


def _problem_type(source_module: str, item: Dict[str, Any], metrics: Dict[str, Any] | None = None) -> str:
    payload = deepcopy(item)
    payload.update(metrics or {})
    text = _text_from_item(payload)
    if any(word in text for word in ["点击", "CTR", "ctr", "主图", "标题", "素材", "创意"]):
        return "low_ctr_low_conversion"
    if any(word in text for word in ["转化率", "详情页", "落地页", "承接"]):
        return "detail_page_conversion"
    if any(word in text for word in ["ROI", "ROAS", "roi", "退款", "售后", "暂停放量", "先查售后", "客服", "材质", "尺寸", "安装"]):
        return "low_roi_high_refund"
    if any(word in text for word in ["库存", "补货", "库存告急", "库存偏低", "活动流量", "待补货"]):
        return "low_inventory_activity"
    if source_module == "competitor" or any(word in text for word in ["竞品", "差评", "机会点"]):
        return "competitor_signal_to_test"
    if source_module == "report" or any(word in text for word in ["字段", "同步", "导入", "ERP", "CRM"]):
        return "report_data_anomaly"
    return infer_action_problem_type(payload, source_module=source_module, fallback=infer_problem_type_from_task(payload))


def _priority_from_problem(problem_type: str, item: Dict[str, Any], confidence: float) -> str:
    if confidence >= 0.82 or item.get("statusLevel") == "danger" or problem_type in {"low_roi_high_refund", "low_inventory_activity"}:
        return "高"
    if confidence >= 0.6:
        return "中"
    return "低"


def _risk_domain(problem_type: str, source_module: str, item: Dict[str, Any]) -> str:
    if problem_type == "low_roi_high_refund":
        return "售后 / ROI"
    if problem_type == "low_inventory_activity":
        return "库存"
    if problem_type == "low_ctr_low_conversion":
        return "标题主图"
    if problem_type == "detail_page_conversion":
        return "详情页承接"
    if problem_type == "competitor_signal_to_test":
        return "竞品"
    if problem_type == "report_data_anomaly":
        return "报表"
    if source_module == "listing":
        return "上新"
    return item.get("riskDomain") or "通用"


def _confidence(rule_hits: List[str], rag_items: List[Dict[str, Any]], item: Dict[str, Any]) -> float:
    score = 0.42
    score += min(0.2, len(rule_hits) * 0.06)
    if item.get("statusLevel") == "danger":
        score += 0.13
    if item.get("inventoryLevel") == "danger" or item.get("afterSalesLevel") in {"warning", "danger"}:
        score += 0.12
    if rag_items:
        score += min(0.22, float(rag_items[0].get("retrievalScore") or 0) / 8)
    return min(0.96, round(score, 2))


def _rule_hits(source_module: str, item: Dict[str, Any], metrics: Dict[str, Any] | None = None) -> List[str]:
    metrics = metrics or {}
    text = _text_from_item({**item, **metrics})
    hits: List[str] = []
    if any(word in text for word in ["点击", "CTR", "ctr", "主图", "标题", "素材"]):
        hits.append("点击 / 标题 / 主图测试信号")
    if any(word in text for word in ["转化率", "详情页", "承接", "落地页"]):
        hits.append("转化承接需要优化")
    if any(word in text for word in ["ROI", "ROAS", "roi", "0.9", "1.1"]):
        hits.append("ROI / ROAS 低于安全线")
    if any(word in text for word in ["退款", "售后敏感", "退款偏高", "refundRate", "材质", "尺寸", "安装"]):
        hits.append("退款率或售后风险偏高")
    if any(word in text for word in ["库存告急", "库存偏低", "待补货", "库存"]):
        hits.append("库存承接需要复核")
    if source_module == "competitor" or any(word in text for word in ["竞品", "差评"]):
        hits.append("竞品差评可转为测试假设")
    if source_module == "listing" or any(word in text for word in ["上新", "测试"]):
        hits.append("上新测试需要人工确认")
    if source_module == "report" or any(word in text for word in ["字段", "同步", "导入", "ERP", "CRM"]):
        hits.append("报表异常需要转成具体经营任务")
    return hits or ["模块数据出现待判断经营信号"]


def _task_title(problem_type: str, item: Dict[str, Any], plan: Dict[str, Any]) -> str:
    name = item.get("shortName") or item.get("sourceName") or item.get("targetProduct") or item.get("title") or item.get("id") or "经营对象"
    mapping = {
        "low_roi_high_refund": f"处理{name}低 ROI / 高退款问题",
        "low_inventory_activity": f"处理{name}库存承接风险",
        "low_ctr_low_conversion": f"测试{name}标题主图点击率",
        "detail_page_conversion": f"优化{name}详情页转化承接",
        "competitor_signal_to_test": f"把{name}竞品差评转成测试方案",
        "report_data_anomaly": f"把{name}报表异常转成经营任务",
    }
    return mapping.get(problem_type, f"{name}{plan.get('actionPlanType') or '经营异常处理'}")


def _build_task_draft(
    source_module: str,
    entity_id: str,
    item: Dict[str, Any],
    problem_type: str,
    confidence: float,
    rag_items: List[Dict[str, Any]],
    rule_hits: List[str],
) -> Dict[str, Any]:
    priority = _priority_from_problem(problem_type, item, confidence)
    risk_domain = _risk_domain(problem_type, source_module, item)
    product_id = item.get("productId") or item.get("id") or entity_id
    store_ids = [item.get("storeId")] if item.get("storeId") and item.get("storeId") != "global" else []
    plan = action_plan_for_problem(problem_type, item=item, source_module=source_module, rag_items=rag_items)
    package = plan.get("recommendedPackage") or {}
    return {
        "title": _task_title(problem_type, item, plan),
        "task": f"执行“{package.get('packageName') or plan.get('actionPlanType')}”，按问题类型处理，不套用通用复查模板。",
        "reason": f"命中：{'、'.join(rule_hits)}。参考 {len(rag_items)} 条复核经验，置信度 {confidence}。{plan.get('diagnosis')}",
        "priority": priority,
        "priorityLevel": "danger" if priority == "高" else "warning" if priority == "中" else "good",
        "deadline": package.get("testDuration") or ("今天内" if priority == "高" else "明天前"),
        "riskDomain": risk_domain,
        "actionType": plan.get("actionPlanType") or "处理",
        "taskType": "V4.4.2 问题类型处理包",
        "taskSignal": "模块信号 + problemType + ActionPlan + RAG",
        "entityType": MODULE_LABELS.get(source_module, "经营模块"),
        "entityId": entity_id,
        "source": "V4.4.2 Task ActionPlan Agent",
        "sourceModule": MODULE_LABELS.get(source_module, source_module),
        "sourceRoute": MODULE_ROUTES.get(source_module, "dashboard"),
        "productRoute": MODULE_ROUTES.get(source_module, "dashboard"),
        "storeIds": store_ids,
        "visibleStoreIds": store_ids,
        "productId": product_id,
        "productTitle": item.get("title") or item.get("name") or _task_title(problem_type, item, plan),
        "productShort": item.get("shortName") or item.get("sourceName") or item.get("targetProduct") or item.get("id") or "对象",
        "platform": item.get("platform") or "通用",
        "store": item.get("store") or "经营单元",
        "problemType": problem_type,
        "actionPlan": plan,
        "selectedPackage": package,
        "executionPackages": plan.get("executionPackages") or [],
        "executionSteps": plan.get("executionSteps") or [],
        "evidenceRequired": plan.get("evidenceRequired") or [],
        "submitMetrics": plan.get("submitMetrics") or [],
        "acceptanceCriteria": plan.get("acceptanceCriteria") or [],
        "failureThreshold": plan.get("failureThreshold") or [],
        "reviewFocus": plan.get("reviewFocus") or [],
        "judgmentTags": [problem_type, risk_domain, plan.get("actionPlanType"), *rule_hits[:3]],
        "createdByRole": "agent",
        "agentJudgment": {
            "status": "advisory",
            "version": TASK_AGENT_VERSION,
            "confidence": confidence,
            "problemType": problem_type,
            "actionPlanType": plan.get("actionPlanType"),
            "ragReferences": [case.get("caseId") for case in rag_items],
            "boundary": "模块发现问题，Agent 按问题类型生成处理包，不直接执行经营动作。",
            "forbiddenActions": FORBIDDEN_ACTIONS,
        },
    }


def generate_task_candidates(
    *,
    source_module: str,
    entity_id: str | None = None,
    body: Dict[str, Any] | None = None,
    user_id: str | None = None,
) -> Dict[str, Any]:
    body = body or {}
    item = _source_item(source_module, entity_id=entity_id, body=body)
    if not item:
        return {"version": TASK_AGENT_VERSION, "candidates": [], "message": "source item not found"}
    final_entity_id = entity_id or body.get("entityId") or item.get("id") or item.get("productId") or source_module
    metrics = body.get("metrics") or {}
    category_id = body.get("categoryId") or item.get("categoryId") or "home_living_goods"
    platform = body.get("platform") or item.get("platform") or "通用"
    store_id = body.get("storeId") or item.get("storeId") or "global"
    problem_type = body.get("problemType") or _problem_type(source_module, item, metrics)
    hits = _rule_hits(source_module, item, metrics)
    rag = search_cases(
        query=" ".join(hits),
        category_id=category_id,
        platform=platform,
        store_id=store_id,
        problem_type=problem_type,
        effective_only=False if problem_type in {"low_ctr_low_conversion", "competitor_signal_to_test", "report_data_anomaly"} else True,
        min_quality=0.0,
        limit=5,
    )
    rag_items = rag.get("items") or []
    conf = _confidence(hits, rag_items, item)
    task_draft = _build_task_draft(source_module, final_entity_id, item, problem_type, conf, rag_items, hits)
    candidate = {
        "candidateId": f"CAND-V442-{source_module}-{final_entity_id}",
        "sourceModule": source_module,
        "entityId": final_entity_id,
        "problemType": problem_type,
        "problemLabel": task_draft.get("actionPlan", {}).get("problemLabel"),
        "actionPlanType": task_draft.get("actionPlan", {}).get("actionPlanType"),
        "confidence": conf,
        "confidenceLevel": "high" if conf >= 0.75 else "medium" if conf >= 0.45 else "low",
        "ruleHits": hits,
        "taskDraft": task_draft,
        "executionPackages": task_draft.get("executionPackages") or [],
        "recommendedPackage": task_draft.get("selectedPackage"),
        "evidenceRequired": task_draft.get("evidenceRequired") or [],
        "ragReferences": [case.get("caseId") for case in rag_items],
        "retrievedCases": rag_items,
        "humanDecision": ["是否加入任务池", "选择哪个处理包", "是否需要补充更多证据"],
        "forbiddenActions": FORBIDDEN_ACTIONS,
    }
    created_task = None
    if body.get("autoCreate") and conf >= float(body.get("minConfidence", 0.75)):
        created_task = create_task(task_draft)
    return {
        "version": TASK_AGENT_VERSION,
        "agentName": "自动解析生成任务 Agent",
        "viewer": _viewer(user_id),
        "sourceModule": source_module,
        "entityId": final_entity_id,
        "sourceSnapshot": item,
        "retrieval": {"mode": "rules + structured RAG memory + problem-type action plan", "query": rag.get("query"), "filters": rag.get("filters"), "totalMatched": rag.get("totalMatched")},
        "candidates": [candidate],
        "createdTask": created_task,
        "boundary": "只生成问题类型处理包或进入人工确认，不直接执行店铺动作。",
    }


def _style_fit(problem_type: str, style: str) -> float:
    table = {
        "low_roi_high_refund": {"稳健型": 0.9, "增长型": 0.52, "利润型": 0.8},
        "low_inventory_activity": {"稳健型": 0.88, "增长型": 0.46, "利润型": 0.72},
        "low_ctr_low_conversion": {"稳健型": 0.65, "增长型": 0.84, "利润型": 0.56},
        "detail_page_conversion": {"稳健型": 0.72, "增长型": 0.74, "利润型": 0.63},
        "competitor_signal_to_test": {"稳健型": 0.7, "增长型": 0.78, "利润型": 0.58},
        "report_data_anomaly": {"稳健型": 0.86, "增长型": 0.4, "利润型": 0.5},
    }
    return table.get(problem_type, {}).get(style, 0.6)


def _style_package(plan: Dict[str, Any], style: str) -> Dict[str, Any]:
    package = deepcopy(plan.get("recommendedPackage") or {})
    if style == "增长型" and len(plan.get("executionPackages") or []) > 1:
        package = deepcopy(plan["executionPackages"][0])
    if style == "利润型" and plan.get("problemType") in {"low_roi_high_refund", "low_inventory_activity"}:
        package["operatorAction"] = [*package.get("operatorAction", [])[:2], "核算动作后的毛利和退款损耗", "低于安全线则停止继续放量", "提交利润口径复核"]
        package["targetMetric"] = f"{package.get('targetMetric', '经营指标')} / 毛利安全线"
    if style == "稳健型":
        package["operatorAction"] = [*package.get("operatorAction", [])[:3], "先小范围执行，等待总管复核后再扩大", "提交完整证据"]
    package["style"] = style
    return package


def task_playbook(task_id: str, *, user_id: str | None = None, preferred_style: str | None = None) -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    problem_type = task.get("problemType") or task.get("agentJudgment", {}).get("problemType") or infer_action_problem_type(task, source_module=task.get("sourceModule"), fallback=infer_problem_type_from_task(task))
    platform = task.get("platform") or "通用"
    store_ids = task.get("storeIds") or task.get("visibleStoreIds") or ["global"]
    rag = search_cases(
        query=" ".join([task.get("task") or "", task.get("reason") or "", *(task.get("judgmentTags") or [])]),
        category_id=task.get("categoryId") or "home_living_goods",
        platform=platform,
        store_id=store_ids[0] if store_ids else "global",
        problem_type=problem_type,
        effective_only=False,
        limit=6,
    )
    rag_items = rag.get("items") or []
    action_plan = action_plan_for_problem(problem_type, item=task, source_module=task.get("sourceModule"), rag_items=rag_items)
    styles = [preferred_style] if preferred_style else ["稳健型", "增长型", "利润型"]
    strategies = []
    for style in styles:
        if not style:
            continue
        fit = _style_fit(problem_type, style)
        package = _style_package(action_plan, style)
        strategies.append(
            {
                "style": style,
                "fitScore": fit,
                "packageName": package.get("packageName"),
                "actionPlanType": action_plan.get("actionPlanType"),
                "steps": package.get("operatorAction") or action_plan.get("executionSteps") or [],
                "submitMetrics": package.get("submitMetrics") or action_plan.get("submitMetrics") or [],
                "risk": package.get("risk") or "打法需结合当前毛利、库存和退款变化，不能自动执行。",
                "applicableConditions": package.get("fitCondition") or ["指标组合相近", "同类目 / 同平台优先"],
                "notApplicableConditions": ["目标不同", "缺少结果指标", "未复核经验"],
                "acceptanceCriteria": package.get("acceptanceCriteria") or action_plan.get("acceptanceCriteria") or [],
                "failureThreshold": package.get("failureThreshold") or action_plan.get("failureThreshold") or [],
            }
        )
    recommended = max(strategies, key=lambda item: item["fitScore"]) if strategies else None
    return {
        "version": TASK_AGENT_VERSION,
        "agentName": "任务解析运营方式 Agent",
        "taskId": task_id,
        "viewer": _viewer(user_id),
        "problemType": problem_type,
        "problemLabel": action_plan.get("problemLabel"),
        "summary": "根据任务信号、问题类型和 RAG 经验库生成处理包，避免所有任务套同一个拆解模板。",
        "actionPlan": action_plan,
        "executionPackages": action_plan.get("executionPackages") or [],
        "recommendedStyle": recommended.get("style") if recommended else "稳健型",
        "strategies": strategies,
        "acceptanceCriteria": action_plan.get("acceptanceCriteria") or [],
        "evidenceToSubmit": action_plan.get("evidenceRequired") or [],
        "ragReferences": [case.get("caseId") for case in rag_items],
        "retrievedCases": rag_items,
        "humanDecision": ["选择哪种运营打法", "是否拆分子任务", "是否将处理结果回流为经验卡"],
        "forbiddenActions": FORBIDDEN_ACTIONS,
        "boundary": "Agent 给出问题类型处理包和证据要求，不直接执行改价、投放、退款或发布动作。",
    }
