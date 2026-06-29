"""V12.12 RAG + LLM Agent SOP enhancement.

This layer sits after V12.11's deterministic change-pack builder. It seeds a
basic RAG database, retrieves operation playbooks, builds an LLM prompt payload,
validates the SOP contract, and writes product-level action cards back to the
task detail package.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, List

from src.services.experience_memory_service import search_cases, upsert_case
from src.services.llm_provider_service import generate_json, llm_status
from src.services.rag_business_memory_service import business_memory_context

V1212_RAG_LLM_AGENT_VERSION = "12.12.0"

_PATCHED = False
_ORIGINAL_TASK_PAYLOAD: Callable[[Dict[str, Any]], Dict[str, Any]] | None = None

BANNED_OPERATOR_ACTIONS = ["拆分流量来源", "拆分广告计划", "人工复盘", "人工判断原因", "排查原因", "复核数据", "观察一下", "持续关注"]

V1212_RAG_SEED_CARDS: List[Dict[str, Any]] = [
    {
        "caseId": "V1212-METRIC-paid-scale-roi-pullback",
        "caseType": "metric_rule_card",
        "level": "L4",
        "status": "seed_approved",
        "categoryId": "global",
        "platform": "通用",
        "storeId": "global",
        "problemType": "paid_scale_roi_pullback",
        "operatorStyle": "稳健型",
        "title": "GMV上涨且广告消耗涨更快时，先判断付费放量ROI回撤",
        "initialJudgment": "ROI下降但GMV上涨不一定是商品变差，必须看广告消耗、点击率、转化率、退款率和库存承接。",
        "effectiveActions": ["暂停继续新增预算", "保留高于ROI底线的计划", "只测试标题/素材一个变量", "提交修改截图和测试范围"],
        "applicableConditions": ["GMV上涨", "广告消耗上涨", "转化率稳定或小幅下降", "退款率未触发红线"],
        "notApplicableConditions": ["退款率明显上升", "转化率大幅下降", "库存不足"],
        "resultSummary": "先控加预算节奏，再做入口素材测试，避免误砍有效放量。",
        "evidenceRequired": ["商品链接", "标题/素材修改截图", "测试开始时间", "影响商品范围"],
        "crossValidationRules": ["ROI × GMV × 广告消耗 × 点击率 × 转化率 × 库存 × 退款率"],
        "qualityScore": 0.94,
        "effective": True,
    },
    {
        "caseId": "V1212-GUARD-no-operator-data-split",
        "caseType": "sop_guardrail_card",
        "level": "L5",
        "status": "seed_approved",
        "categoryId": "global",
        "platform": "通用",
        "storeId": "global",
        "problemType": "general_operation",
        "operatorStyle": "系统边界",
        "title": "运营任务不得要求拆数据或人工复盘",
        "initialJudgment": "拆分数据、交叉计算和复盘都属于系统职责；运营只执行动作并提交证据。",
        "effectiveActions": ["系统生成变化包", "Agent生成SOP", "运营提交材料", "系统自动复盘"],
        "applicableConditions": ["所有经营任务"],
        "notApplicableConditions": ["人工审计", "总管复核"],
        "resultSummary": "任务前台保持可执行，后台保持可追溯。",
        "evidenceRequired": ["处理截图", "处理说明", "商品范围"],
        "crossValidationRules": ["系统拆数据 × Agent生成SOP × 运营提交材料 × 系统自动复盘"],
        "qualityScore": 0.99,
        "effective": True,
    },
    {
        "caseId": "V1212-ACTION-seasonal-apparel-title-material",
        "caseType": "action_playbook_card",
        "level": "L4",
        "status": "seed_approved",
        "categoryId": "seasonal_apparel",
        "platform": "天猫",
        "storeId": "global",
        "problemType": "low_ctr_low_conversion",
        "operatorStyle": "测试型",
        "title": "季节服饰点击下降时，先测标题/素材，不同时改价格详情",
        "initialJudgment": "防晒、季节服饰点击下降通常先看搜索词、面料表达、上身场景和主图证据，不要多变量同时改。",
        "effectiveActions": ["测试标题A", "保留原标题B", "只换一组主图或标题", "提交商品链接和修改截图"],
        "applicableConditions": ["点击率下降", "转化率稳定或小幅下降", "退款率未异常"],
        "notApplicableConditions": ["库存不足", "退款率红线", "转化率大幅下降"],
        "resultSummary": "用低风险测试确认入口问题，减少误判承接。",
        "evidenceRequired": ["商品链接", "标题前后截图", "主图前后截图", "测试开始时间"],
        "crossValidationRules": ["点击率 × 转化率 × 退款率 × 季节窗口 × 库存"],
        "qualityScore": 0.92,
        "effective": True,
    },
    {
        "caseId": "V1212-RECAP-system-auto-recap-rule",
        "caseType": "recap_rule_card",
        "level": "L5",
        "status": "seed_approved",
        "categoryId": "global",
        "platform": "通用",
        "storeId": "global",
        "problemType": "general_operation",
        "operatorStyle": "系统复盘",
        "title": "运营提交后由系统自动复盘并写入日报周报",
        "initialJudgment": "复盘依赖后续报表或接口数据更新，不应生成运营人工复盘任务。",
        "effectiveActions": ["等待后续数据更新", "系统自动比对前后指标", "自动写入日报/周报/复盘库", "未达标自动生成下一轮任务"],
        "applicableConditions": ["所有提交完成任务"],
        "notApplicableConditions": ["无后续数据更新"],
        "resultSummary": "复盘闭环由系统完成，运营只提交材料。",
        "evidenceRequired": ["提交材料", "后续数据版本", "系统复盘结果"],
        "crossValidationRules": ["提交时间 × 后续报表版本 × 前后指标差异"],
        "qualityScore": 0.98,
        "effective": True,
    },
]


def _text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _arr(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def seed_v1212_rag_baseline() -> Dict[str, Any]:
    seeded: List[str] = []
    for card in V1212_RAG_SEED_CARDS:
        upsert_case({**card, "source": "v1212_rag_seed", "seedVersion": V1212_RAG_LLM_AGENT_VERSION})
        seeded.append(card["caseId"])
    return {"version": V1212_RAG_LLM_AGENT_VERSION, "seededCount": len(seeded), "caseIds": seeded}


def _metric_map(pack: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for item in pack.get("lines") or []:
        if isinstance(item, dict) and item.get("metricCode"):
            result[str(item["metricCode"])] = item
    return result


def _change(metrics: Dict[str, Dict[str, Any]], code: str) -> float | None:
    value = (metrics.get(code) or {}).get("changeRate")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_change(value: float | None) -> str:
    return "无法计算" if value is None else f"{value * 100:+.1f}%"


def _problem_type(task: Dict[str, Any], pack: Dict[str, Any]) -> str:
    text = " ".join(str(value or "") for value in [task.get("title"), task.get("riskDomain"), task.get("actionType"), task.get("taskType")])
    metrics = _metric_map(pack)
    roi = _change(metrics, "roi")
    gmv = _change(metrics, "payment_amount")
    ad = _change(metrics, "ad_spend")
    click = _change(metrics, "click_rate")
    conv = _change(metrics, "payment_conversion_rate")
    if any(word in text for word in ["库存", "补货", "可售", "断货"]):
        return "low_inventory_activity"
    if roi is not None and gmv is not None and ad is not None and roi < 0 and gmv > 0 and ad > 0:
        return "paid_scale_roi_pullback"
    if click is not None and click < -0.05 and (conv is None or conv > -0.08):
        return "low_ctr_low_conversion"
    if conv is not None and conv < -0.08:
        return "detail_page_conversion"
    if any(word in text for word in ["退款", "售后", "毛利"]):
        return "low_roi_high_refund"
    return "general_operation"


def _product_context(signal: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
    product_id = signal.get("productId") or task.get("productId") or task.get("entityId") or task.get("id")
    title = signal.get("productTitle") or task.get("productTitle") or task.get("productShort") or task.get("title") or product_id or "商品"
    object_id = task.get("objectId") or task.get("archiveId") or product_id
    return {
        "productId": product_id,
        "productTitle": title,
        "objectId": object_id,
        "storeId": signal.get("storeId") or task.get("storeId") or (task.get("storeIds") or [None])[0],
        "storeName": signal.get("storeName") or task.get("storeName") or task.get("store"),
        "platform": signal.get("platform") or task.get("platform") or "通用",
        "productLink": signal.get("productLink") or task.get("productLink") or task.get("link") or "",
        "openProductRoute": "business-products",
        "openProductState": {"productId": product_id, "productObjectId": object_id, "storeId": signal.get("storeId") or task.get("storeId") or "", "storeName": signal.get("storeName") or task.get("storeName") or task.get("store") or ""},
    }


def _retrieve_rag(task: Dict[str, Any], pack: Dict[str, Any], product: Dict[str, Any]) -> Dict[str, Any]:
    seed = seed_v1212_rag_baseline()
    problem = _problem_type(task, pack)
    query = " ".join(str(value or "") for value in [task.get("title"), task.get("reason"), task.get("task"), product.get("productTitle"), problem])
    category_id = task.get("categoryId") or ("seasonal_apparel" if any(token in query for token in ["防晒", "衣", "服饰", "尺码", "面料"]) else None)
    retrieved = search_cases(query=query, category_id=category_id, platform=product.get("platform"), store_id=product.get("storeId") or "global", problem_type=problem, effective_only=True, min_quality=0.7, limit=6)
    guardrail = search_cases(query="运营不得拆分流量来源 人工复盘 SOP禁止规则", problem_type="general_operation", effective_only=True, min_quality=0.7, limit=4)
    memory = business_memory_context({**task, "problemType": problem, "categoryId": category_id, "platform": product.get("platform"), "storeIds": [product.get("storeId") or "global"]})
    return {"version": V1212_RAG_LLM_AGENT_VERSION, "seed": seed, "problemType": problem, "categoryId": category_id, "businessMemory": memory, "retrievedCards": retrieved.get("items") or [], "guardrailCards": guardrail.get("items") or [], "retrieval": retrieved}


def _select_action(problem: str, cards: List[Dict[str, Any]]) -> List[str]:
    actions: List[str] = []
    for card in cards:
        for action in card.get("effectiveActions") or []:
            if action not in actions:
                actions.append(str(action))
    if problem == "paid_scale_roi_pullback":
        defaults = ["不继续新增预算", "保留高于ROI底线的ROAS计划", "测试标题/素材单一变量", "提交商品链接和修改截图"]
    elif problem == "low_inventory_activity":
        defaults = ["确认库存和可售天数", "库存不足时优先补货或替换主推位", "提交库存截图和补货结论"]
    elif problem == "detail_page_conversion":
        defaults = ["只修改详情页首屏或评价证据一个变量", "不同时改价和素材", "提交详情页修改截图"]
    else:
        defaults = ["选择一个低风险变量测试", "保留原版本对照", "提交修改截图和影响范围"]
    for item in defaults:
        if item not in actions:
            actions.append(item)
    return actions[:5]


def _deterministic_rag_synthesis(task: Dict[str, Any], pack: Dict[str, Any], product: Dict[str, Any], rag: Dict[str, Any]) -> Dict[str, Any]:
    metrics = _metric_map(pack)
    problem = rag.get("problemType") or "general_operation"
    product_title = product.get("productTitle") or "商品"
    roi = _fmt_change(_change(metrics, "roi"))
    gmv = _fmt_change(_change(metrics, "payment_amount"))
    ad = _fmt_change(_change(metrics, "ad_spend"))
    click = _fmt_change(_change(metrics, "click_rate"))
    conv = _fmt_change(_change(metrics, "payment_conversion_rate"))
    actions = _select_action(problem, rag.get("retrievedCards") or [])
    if problem == "paid_scale_roi_pullback":
        title = "付费放量ROI回撤｜商品级标题/ROAS低风险测试"
        judgment = f"{product_title} 的GMV {gmv}、广告消耗 {ad}，ROI {roi}。RAG判断这更像付费放量后的ROI回撤，点击 {click}、转化 {conv} 决定先测入口表达，不让运营再拆数据。"
    elif problem == "low_inventory_activity":
        title = "库存承接风险｜先保主推与补货节奏"
        judgment = f"{product_title} 进入库存承接风险，RAG判断先确认库存/可售天数和主推位置，避免GMV继续承接后触发缺货、退款和评分反噬。"
    elif problem == "detail_page_conversion":
        title = "转化承接变弱｜详情页首屏与评价证据测试"
        judgment = f"{product_title} 的转化 {conv} 已弱于入口表现，RAG判断优先修详情页首屏、价格/评价证据，不直接扩大预算。"
    else:
        title = "商品级低风险测试｜保留原版本对照"
        judgment = f"{product_title} 当前未形成单一红线，RAG判断只做一个变量的小范围测试，避免多动作同时改导致系统无法复盘。"
    operator_steps = [
        f"今日打开商品《{product_title}》，只执行一个变量动作：{actions[0]}。",
        f"保留原版本作为对照；若涉及投放，只保留系统已标记高于底线的计划，不要求运营手动拆计划。",
        f"提交《{product_title}》的商品链接、修改前后截图、测试开始时间和影响范围。",
    ]
    if len(actions) > 1:
        operator_steps.insert(1, f"优先动作顺序：{actions[1]}；不要同时改价格、详情页和素材。")
    recap = [
        f"系统在后续报表/接口更新后自动比对《{product_title}》的ROI、GMV、广告消耗、点击率、转化率、库存和退款率，不要求运营人工复盘。",
        "若未达复盘线，系统自动生成下一轮商品级任务并写入日报、周报和复盘库。",
    ]
    card = {"productId": product.get("productId"), "productTitle": product_title, "primaryAction": actions[0], "why": judgment, "submitEvidence": ["商品链接", "修改前后截图", "测试开始时间", "影响范围"], "openProductLabel": "查看商品"}
    return {"version": V1212_RAG_LLM_AGENT_VERSION, "title": title, "judgment": judgment, "operatorSopSteps": operator_steps, "systemRecapLine": recap, "productActionCards": [card], "riskCheck": ["不得让运营拆分数据", "不得要求运营人工复盘", "无小时级数据不生成分时投放动作"], "generationMode": "deterministic_rag_synthesis"}


def _validate(output: Dict[str, Any], product: Dict[str, Any]) -> Dict[str, Any]:
    steps = [str(item) for item in output.get("operatorSopSteps") or []]
    joined = " ".join(steps + [str(output.get("judgment") or "")])
    banned_hits = [word for word in BANNED_OPERATOR_ACTIONS if word in joined]
    missing: List[str] = []
    if not output.get("title"):
        missing.append("title")
    if not output.get("judgment"):
        missing.append("judgment")
    if len(steps) < 2:
        missing.append("operatorSopSteps>=2")
    if not output.get("systemRecapLine"):
        missing.append("systemRecapLine")
    if not output.get("productActionCards"):
        missing.append("productActionCards")
    if product.get("productTitle") and product.get("productTitle") not in joined:
        missing.append("productTitle_in_sop")
    valid = not missing and not banned_hits
    return {"version": V1212_RAG_LLM_AGENT_VERSION, "valid": valid, "missing": missing, "bannedHits": banned_hits, "rule": "SOP必须包含商品、动作、提交材料、系统复盘线；禁止让运营拆数据或人工复盘。"}


def _llm_generate(task: Dict[str, Any], pack: Dict[str, Any], product: Dict[str, Any], rag: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"task": {key: task.get(key) for key in ["id", "title", "riskDomain", "actionType", "taskType", "priority"]}, "productContextPack": product, "systemChangePack": pack, "ragRetrievedContext": {"problemType": rag.get("problemType"), "cards": rag.get("retrievedCards"), "guardrails": rag.get("guardrailCards"), "companyBaseline": (rag.get("businessMemory") or {}).get("companyBaseline")}, "forbiddenOperatorActions": BANNED_OPERATOR_ACTIONS}
    result = generate_json(prompt_name="rag_agent_sop_generation", payload=payload, expected_keys=["title", "judgment", "operatorSopSteps", "systemRecapLine", "productActionCards"], agent_name="V12.12 RAG Agent", schema_name="rag_agent_sop")
    output = result.get("output") or {}
    validation = _validate(output, product)
    return {"llm": result, "output": output, "validation": validation, "promptPayload": payload}


def _merge(task: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    item = deepcopy(task)
    detail = dict(item.get("taskDetailReport") or {})
    pack = detail.get("systemChangePack") or item.get("systemChangePack") or {}
    product = _product_context(signal, item)
    rag = _retrieve_rag(item, pack, product)
    llm_result = _llm_generate(item, pack, product, rag)
    synthesized = llm_result["output"] if llm_result["validation"].get("valid") else _deterministic_rag_synthesis(item, pack, product, rag)
    validation = _validate(synthesized, product)
    if not validation.get("valid"):
        synthesized = _deterministic_rag_synthesis(item, pack, product, rag)
        validation = _validate(synthesized, product)
    cards = synthesized.get("productActionCards") or []
    affected = list(item.get("affectedProducts") or [])
    base_product = {"productId": product.get("productId"), "productTitle": product.get("productTitle"), "objectId": product.get("objectId"), "storeId": product.get("storeId"), "store": product.get("storeName"), "platform": product.get("platform"), "productLink": product.get("productLink"), "openProductRoute": product.get("openProductRoute"), "openProductState": product.get("openProductState"), "primaryAction": (cards[0] or {}).get("primaryAction") if cards else None, "why": (cards[0] or {}).get("why") if cards else None}
    if product.get("productId") and not any(str(row.get("productId")) == str(product.get("productId")) for row in affected if isinstance(row, dict)):
        affected.insert(0, base_product)
    agent = {**dict(item.get("agentOperatingJudgment") or {}), **synthesized, "version": V1212_RAG_LLM_AGENT_VERSION, "ragUsed": True, "llmStatus": (llm_result.get("llm") or {}).get("status"), "llmFallbackUsed": (llm_result.get("llm") or {}).get("fallbackUsed"), "sopValidation": validation, "ragCardTitles": [card.get("title") for card in rag.get("retrievedCards") or []]}
    title = f"{product.get('productTitle') or item.get('productTitle') or '商品'}｜{synthesized.get('title') or item.get('actionType') or 'Agent SOP'}"
    detail.update({"version": V1212_RAG_LLM_AGENT_VERSION, "title": title, "warningSummary": synthesized.get("judgment"), "agentOperatingJudgment": agent, "operatorSopSteps": synthesized.get("operatorSopSteps") or item.get("sopSteps") or [], "sopSteps": synthesized.get("operatorSopSteps") or item.get("sopSteps") or [], "systemRecapLine": synthesized.get("systemRecapLine") or item.get("systemRecapLine") or [], "ragRetrievedContext": rag, "llmGeneration": llm_result.get("llm"), "llmPromptPayload": llm_result.get("promptPayload"), "sopValidation": validation, "productActionCards": cards, "affectedProducts": affected})
    item.update({"version": V1212_RAG_LLM_AGENT_VERSION, "title": title, "task": (synthesized.get("operatorSopSteps") or [item.get("task") or "执行Agent SOP"])[0], "actionType": synthesized.get("title") or item.get("actionType"), "taskDetailReport": detail, "agentOperatingJudgment": agent, "operatorSopSteps": detail["operatorSopSteps"], "sopSteps": detail["sopSteps"], "systemRecapLine": detail["systemRecapLine"], "ragRetrievedContext": rag, "llmGeneration": llm_result.get("llm"), "llmPromptPayload": llm_result.get("promptPayload"), "sopValidation": validation, "productActionCards": cards, "affectedProducts": affected, "productId": product.get("productId") or item.get("productId"), "productTitle": product.get("productTitle") or item.get("productTitle"), "objectId": product.get("objectId") or item.get("objectId"), "productLink": product.get("productLink") or item.get("productLink") or item.get("link"), "judgmentTags": [*list(item.get("judgmentTags") or []), "V12.12 RAG基础库", "LLM生成增强", "SOP校验器", "商品级动作卡"]})
    return item


def apply_v1212_rag_llm_agent() -> Dict[str, Any]:
    global _PATCHED, _ORIGINAL_TASK_PAYLOAD
    seed = seed_v1212_rag_baseline()
    if _PATCHED:
        return {"version": V1212_RAG_LLM_AGENT_VERSION, "status": "already_applied", "seed": seed}
    from src.services import operating_cadence_task_service as cadence_service

    _ORIGINAL_TASK_PAYLOAD = cadence_service._task_payload

    def _wrapped_task_payload(signal: Dict[str, Any]) -> Dict[str, Any]:
        base = _ORIGINAL_TASK_PAYLOAD(signal)  # type: ignore[misc]
        return _merge(base, signal)

    cadence_service._task_payload = _wrapped_task_payload
    cadence_service.OPERATING_CADENCE_VERSION = V1212_RAG_LLM_AGENT_VERSION
    _PATCHED = True
    return {"version": V1212_RAG_LLM_AGENT_VERSION, "status": "applied", "seed": seed, "llm": llm_status(), "rule": "V12.12：系统变化包 + 商品上下文 + RAG基础库 + LLM生成 + SOP校验器。"}
