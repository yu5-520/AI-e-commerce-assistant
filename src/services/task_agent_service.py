"""V4.2 task generation and playbook Agent service.

V4.2 uses the V4.1 structured experience memory as a lightweight RAG source.
It turns module signals into task candidates and explains active tasks with
multiple operating styles. The service is advisory-only and never performs real
store operations.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from src.services.account_service import current_user
from src.services.experience_memory_service import infer_problem_type_from_task, search_cases
from src.services.module_data_service import COMPETITORS, LISTINGS, PRODUCTS, REPORT_DETAILS, TRAFFIC, find_by_id
from src.services.module_task_service import create_task, find_task

TASK_AGENT_VERSION = "4.2.0"
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
    for key in ["riskDomain", "taskType", "status", "statusLevel", "suggestion", "nextStep", "risk", "refundRate", "roi", "inventoryStatus", "afterSales", "badReview", "opportunity", "testType", "testPlan", "title"]:
        if item.get(key) is not None:
            values.append(str(item[key]))
    return " ".join(values)


def _problem_type(source_module: str, item: Dict[str, Any], metrics: Dict[str, Any] | None = None) -> str:
    payload = deepcopy(item)
    payload.update(metrics or {})
    text = _text_from_item(payload)
    if any(word in text for word in ["ROI", "ROAS", "roi", "退款", "售后", "暂停放量", "先查售后"]):
        return "low_roi_high_refund"
    if any(word in text for word in ["库存", "补货", "库存告急", "库存偏低", "活动流量"]):
        return "low_inventory_activity"
    if any(word in text for word in ["点击", "CTR", "ctr", "主图", "标题", "转化"]):
        return "low_ctr_low_conversion"
    if source_module == "competitor" or any(word in text for word in ["竞品", "差评", "机会点"]):
        return "competitor_signal_to_test"
    return infer_problem_type_from_task(payload)


def _priority_from_problem(problem_type: str, item: Dict[str, Any], confidence: float) -> str:
    if confidence >= 0.82 or item.get("statusLevel") == "danger" or problem_type in {"low_roi_high_refund", "low_inventory_activity"}:
        return "高"
    if confidence >= 0.6:
        return "中"
    return "低"


def _risk_domain(problem_type: str, source_module: str, item: Dict[str, Any]) -> str:
    if problem_type == "low_roi_high_refund":
        return "售后"
    if problem_type == "low_inventory_activity":
        return "库存"
    if problem_type == "low_ctr_low_conversion":
        return "流量"
    if problem_type == "competitor_signal_to_test":
        return "竞品"
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
    if any(word in text for word in ["ROI", "ROAS", "roi", "0.9", "1.1"]):
        hits.append("ROI / ROAS 低于安全线")
    if any(word in text for word in ["退款", "售后敏感", "退款偏高", "refundRate"]):
        hits.append("退款率或售后风险偏高")
    if any(word in text for word in ["库存告急", "库存偏低", "待补货", "库存"]):
        hits.append("库存承接需要复核")
    if source_module == "competitor" or any(word in text for word in ["竞品", "差评"]):
        hits.append("竞品差评可转为测试假设")
    if source_module == "listing" or any(word in text for word in ["主图", "标题", "上新", "测试"]):
        hits.append("标题 / 主图 / 上新测试需要人工确认")
    return hits or ["模块数据出现待判断经营信号"]


def _task_title(problem_type: str, item: Dict[str, Any]) -> str:
    name = item.get("shortName") or item.get("sourceName") or item.get("targetProduct") or item.get("title") or item.get("id") or "经营对象"
    mapping = {
        "low_roi_high_refund": f"复盘{name}低 ROI 与高退款承接问题",
        "low_inventory_activity": f"确认{name}库存承接与补货节奏",
        "low_ctr_low_conversion": f"复查{name}标题主图与转化问题",
        "competitor_signal_to_test": f"把{name}竞品信号转成测试假设",
    }
    return mapping.get(problem_type, f"复查{name}经营异常")


def _evidence_required(problem_type: str) -> List[str]:
    mapping = {
        "low_roi_high_refund": ["近 7 日退款原因", "客服咨询关键词", "详情页承诺", "推广素材点击分布", "调整后 24 小时 ROI / 退款率"],
        "low_inventory_activity": ["当前库存", "安全库存", "供应商补货周期", "活动流量计划", "缺货退款风险"],
        "low_ctr_low_conversion": ["标题关键词覆盖", "主图版本", "点击率", "转化率", "竞品主图对照"],
        "competitor_signal_to_test": ["竞品差评样本", "自家详情页承诺", "价格位置", "可测试卖点", "不跟价原因"],
    }
    return mapping.get(problem_type, ["来源数据", "处理动作", "结果指标", "复核结论"])


def _build_task_draft(source_module: str, entity_id: str, item: Dict[str, Any], problem_type: str, confidence: float, rag_items: List[Dict[str, Any]], rule_hits: List[str]) -> Dict[str, Any]:
    priority = _priority_from_problem(problem_type, item, confidence)
    risk_domain = _risk_domain(problem_type, source_module, item)
    product_id = item.get("productId") or item.get("id") or entity_id
    store_ids = [item.get("storeId")] if item.get("storeId") and item.get("storeId") != "global" else []
    return {
        "title": _task_title(problem_type, item),
        "task": "按规则命中与 RAG 历史打法生成任务草案，先补齐证据，再由人工确认处理动作。",
        "reason": f"命中：{'、'.join(rule_hits)}。参考 {len(rag_items)} 条复核经验，置信度 {confidence}。",
        "priority": priority,
        "priorityLevel": "danger" if priority == "高" else "warning" if priority == "中" else "good",
        "deadline": "今天内" if priority == "高" else "明天前",
        "riskDomain": risk_domain,
        "actionType": "复查",
        "taskType": "V4.2 RAG任务生成",
        "taskSignal": "规则 + RAG 生成，人工确认",
        "entityType": MODULE_LABELS.get(source_module, "经营模块"),
        "entityId": entity_id,
        "source": "V4.2 Task Generation Agent",
        "sourceModule": MODULE_LABELS.get(source_module, source_module),
        "sourceRoute": MODULE_ROUTES.get(source_module, "dashboard"),
        "productRoute": MODULE_ROUTES.get(source_module, "dashboard"),
        "storeIds": store_ids,
        "visibleStoreIds": store_ids,
        "productId": product_id,
        "productTitle": item.get("title") or item.get("name") or _task_title(problem_type, item),
        "productShort": item.get("shortName") or item.get("sourceName") or item.get("targetProduct") or item.get("id") or "对象",
        "platform": item.get("platform") or "通用",
        "store": item.get("store") or "经营单元",
        "judgmentTags": [problem_type, risk_domain, *rule_hits[:3]],
        "evidenceRequired": _evidence_required(problem_type),
        "createdByRole": "agent",
        "agentJudgment": {
            "status": "advisory",
            "version": TASK_AGENT_VERSION,
            "confidence": confidence,
            "problemType": problem_type,
            "ragReferences": [case.get("caseId") for case in rag_items],
            "boundary": "Agent 只生成任务草案，不直接执行经营动作。",
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
        effective_only=False if problem_type == "low_ctr_low_conversion" else True,
        min_quality=0.0,
        limit=5,
    )
    rag_items = rag.get("items") or []
    conf = _confidence(hits, rag_items, item)
    task_draft = _build_task_draft(source_module, final_entity_id, item, problem_type, conf, rag_items, hits)
    candidate = {
        "candidateId": f"CAND-V420-{source_module}-{final_entity_id}",
        "sourceModule": source_module,
        "entityId": final_entity_id,
        "problemType": problem_type,
        "confidence": conf,
        "confidenceLevel": "high" if conf >= 0.75 else "medium" if conf >= 0.45 else "low",
        "ruleHits": hits,
        "taskDraft": task_draft,
        "evidenceRequired": task_draft["evidenceRequired"],
        "ragReferences": [case.get("caseId") for case in rag_items],
        "retrievedCases": rag_items,
        "humanDecision": ["是否加入任务池", "是否拆分为售后 / 流量 / 库存子任务", "是否需要补充更多报表证据"],
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
        "retrieval": {"mode": "rules + structured RAG memory", "query": rag.get("query"), "filters": rag.get("filters"), "totalMatched": rag.get("totalMatched")},
        "candidates": [candidate],
        "createdTask": created_task,
        "boundary": "只生成任务草案或进入人工确认，不直接执行店铺动作。",
    }


def _strategy_steps(problem_type: str, style: str) -> List[str]:
    if problem_type == "low_roi_high_refund":
        base = {
            "稳健型": ["暂停扩大预算", "复查退款原因", "核对详情页承诺", "统一客服话术", "观察 24 小时 ROI / 退款率变化"],
            "增长型": ["保留小额预算", "快速换素材", "只测高点击人群", "同步监控退款率", "若退款继续升高则停止放量"],
            "利润型": ["核算退款后真实毛利", "低于安全线则停止投放", "保留自然流量观察", "复盘退款责任归因"],
        }
        return base[style]
    if problem_type == "low_inventory_activity":
        return ["确认补货周期", "估算活动消耗", "限制活动流量", "设置缺货预警", "复核是否需要暂缓活动"]
    if problem_type == "low_ctr_low_conversion":
        return ["拆分标题关键词", "生成主图 A/B 方向", "保留小额测试预算", "对比点击率与转化率", "胜出版本再进入上新测试"]
    if problem_type == "competitor_signal_to_test":
        return ["收集竞品差评样本", "对照自家详情页承诺", "生成测试卖点", "设计小范围上新 / 详情页测试", "复核不直接跟价"]
    return ["补齐数据证据", "确认问题归因", "小范围测试处理动作", "提交结果给总管复核"]


def _style_fit(problem_type: str, style: str) -> float:
    table = {
        "low_roi_high_refund": {"稳健型": 0.88, "增长型": 0.54, "利润型": 0.79},
        "low_inventory_activity": {"稳健型": 0.86, "增长型": 0.48, "利润型": 0.72},
        "low_ctr_low_conversion": {"稳健型": 0.62, "增长型": 0.82, "利润型": 0.55},
        "competitor_signal_to_test": {"稳健型": 0.68, "增长型": 0.76, "利润型": 0.58},
    }
    return table.get(problem_type, {}).get(style, 0.6)


def task_playbook(task_id: str, *, user_id: str | None = None, preferred_style: str | None = None) -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    problem_type = task.get("agentJudgment", {}).get("problemType") or infer_problem_type_from_task(task)
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
    styles = [preferred_style] if preferred_style else ["稳健型", "增长型", "利润型"]
    strategies = []
    for style in styles:
        if not style:
            continue
        fit = _style_fit(problem_type, style)
        strategies.append(
            {
                "style": style,
                "fitScore": fit,
                "steps": _strategy_steps(problem_type, style),
                "risk": "打法需结合当前毛利、库存和退款变化，不能自动执行。",
                "applicableConditions": [case.get("applicableConditions") for case in (rag.get("items") or [])[:1]][0] if rag.get("items") else ["指标组合相近", "同类目 / 同平台优先"],
                "notApplicableConditions": [case.get("notApplicableConditions") for case in (rag.get("items") or [])[:1]][0] if rag.get("items") else ["目标不同", "缺少结果指标", "未复核经验"],
            }
        )
    recommended = max(strategies, key=lambda item: item["fitScore"]) if strategies else None
    return {
        "version": TASK_AGENT_VERSION,
        "agentName": "任务解析运营方式 Agent",
        "taskId": task_id,
        "viewer": _viewer(user_id),
        "problemType": problem_type,
        "summary": "根据任务信号和 RAG 经验库，生成多种运营打法供人工选择。",
        "recommendedStyle": recommended.get("style") if recommended else "稳健型",
        "strategies": strategies,
        "acceptanceCriteria": ["核心异常指标改善", "处理动作有证据", "复核人确认可归档", "必要时生成经验卡草案"],
        "evidenceToSubmit": _evidence_required(problem_type),
        "ragReferences": [case.get("caseId") for case in rag.get("items") or []],
        "retrievedCases": rag.get("items") or [],
        "humanDecision": ["选择哪种运营打法", "是否拆分子任务", "是否将处理结果回流为经验卡"],
        "forbiddenActions": FORBIDDEN_ACTIONS,
        "boundary": "Agent 给出打法和证据要求，不直接执行改价、投放、退款或发布动作。",
    }
