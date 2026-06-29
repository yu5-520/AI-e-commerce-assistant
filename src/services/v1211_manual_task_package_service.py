"""V12.11.1 manual module task package wrapper.

Module pages may still create tasks from product / competitor / listing / traffic /
report cards. Those entry points used old flat payloads, while the task runtime
requires the V11.8+ SOP package contract. This wrapper converts any legacy flat
module payload into the same V12.11 shape used by generated operating tasks.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

V1211_MANUAL_TASK_PACKAGE_VERSION = "12.11.1"


def _arr(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _priority(payload: Dict[str, Any]) -> str:
    return _text(payload.get("priority"), "中")


def _risk_domain(payload: Dict[str, Any]) -> str:
    return _text(payload.get("riskDomain") or payload.get("taskType"), "经营")


def _title(payload: Dict[str, Any]) -> str:
    base = _text(payload.get("title") or payload.get("productTitle") or payload.get("productShort") or payload.get("entityId") or payload.get("productId"), "经营任务")
    action = _text(payload.get("actionType") or payload.get("taskType"), "执行SOP")
    if action and action not in base:
        return f"{base}｜{action}"
    return base


def _operator_sop(payload: Dict[str, Any]) -> List[str]:
    risk = _risk_domain(payload)
    task_text = _text(payload.get("task") or payload.get("reason") or payload.get("taskSignal"), "按系统判断执行当前动作。")
    if "库存" in risk:
        return [
            "6小时内提交库存截图、可售天数或补货/调拨结论。",
            "库存无法承接时，暂停继续加预算，并切换到同店铺替代主推品。",
            "提交处理说明和影响商品范围，后续由系统自动复盘库存、GMV和退款变化。",
        ]
    if "售后" in risk or "退款" in risk:
        return [
            "6小时内提交退款/售后原因截图或客服核实结论。",
            "优先处理退款TOP原因，不继续放大该商品投放。",
            "提交处理截图和说明，后续由系统自动复盘退款率、转化率和GMV变化。",
        ]
    if "竞品" in risk or "上新" in risk:
        return [
            "今日完成标题、主图、素材或对标版本中的一个低风险测试动作，避免多项同时改动。",
            "保留原版本作为对照，提交修改截图、测试开始时间和影响范围。",
            "后续由系统自动复盘点击率、转化率、ROI和GMV，不要求运营人工复盘。",
        ]
    if "流量" in risk:
        return [
            "今日优先执行系统给出的标题/素材/ROAS计划动作，不要求运营拆分流量来源。",
            "提交处理截图、测试范围和当前预算节奏说明。",
            "后续由系统自动复盘ROI、GMV、点击率、转化率和广告消耗变化。",
        ]
    if "报表" in risk:
        return [
            "确认本次报表已完成入库和经营对象同步。",
            "只提交异常字段或缺口说明；不要求运营人工复盘整份报表。",
            "后续由系统根据新报表自动生成日报、周报、复盘库和下一轮任务。",
        ]
    return [
        task_text,
        "提交执行截图、处理说明和影响范围。",
        "后续由系统自动复盘相关指标变化，不要求运营人工复盘。",
    ]


def _system_change_pack(payload: Dict[str, Any]) -> Dict[str, Any]:
    tags = [str(item) for item in _arr(payload.get("judgmentTags")) if item]
    lines = []
    for index, tag in enumerate(tags[:8], start=1):
        lines.append({
            "type": "system_metric_change",
            "role": "模块事实/标签",
            "metricName": f"模块证据 {index}",
            "label": f"模块证据 {index}",
            "summary": tag,
            "reason": tag,
            "direction": "unknown",
            "sourceModule": payload.get("sourceModule") or payload.get("source") or "模块手动任务",
            "dataVersion": payload.get("sourceDataVersion") or (payload.get("sourceDataVersions") or [None])[0],
        })
    if not lines:
        reason = _text(payload.get("reason") or payload.get("taskSignal"), "模块手动加入任务，缺少结构化指标变化。")
        lines.append({"type": "system_metric_change", "role": "模块事实", "metricName": "模块触发原因", "label": "模块触发原因", "summary": reason, "reason": reason, "direction": "unknown"})
    return {
        "version": V1211_MANUAL_TASK_PACKAGE_VERSION,
        "source": "manual_module_task_wrapped_to_v1211",
        "rule": "模块手动建任务不再使用旧扁平payload，统一包装为V12.11 SOP任务包。",
        "entityType": payload.get("entityType"),
        "entityId": payload.get("entityId"),
        "productId": payload.get("productId"),
        "storeIds": payload.get("storeIds") or payload.get("visibleStoreIds") or [],
        "lines": lines,
        "dataGaps": [{"field": "完整趋势变化包", "status": "manual_entry", "impact": "该任务来自模块手动入口；若需要完整环比/趋势链，请以报表导入生成的V12.11任务为准。"}],
    }


def _agent(payload: Dict[str, Any], sop: List[str], pack: Dict[str, Any]) -> Dict[str, Any]:
    risk = _risk_domain(payload)
    title = _title(payload)
    judgment = _text(payload.get("reason") or payload.get("taskSignal"), "Agent基于模块事实生成执行SOP，运营只提交处理材料，后续系统自动复盘。")
    return {
        "version": V1211_MANUAL_TASK_PACKAGE_VERSION,
        "status": "manual_task_wrapped_agent_sop",
        "title": title,
        "judgment": judgment,
        "operatorSopSteps": sop,
        "systemRecapLine": [
            "系统在后续报表或接口数据更新后自动比对相关指标变化，不要求运营人工复盘。",
            "若未达复盘线，系统自动生成下一轮任务，并写入日报、周报和复盘库。",
        ],
        "nextTaskTrigger": ["后续数据更新触发系统自动复盘", "复盘未达标自动生成下一轮任务"],
        "forbiddenOperatorActions": ["拆分流量来源", "拆分广告计划", "人工复盘ROI", "人工判断数据原因"],
        "inputChanges": pack.get("lines", []),
        "riskDomain": risk,
    }


def wrap_manual_task_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    item = deepcopy(payload or {})
    if item.get("taskGenerationMode") == "v11_8_sop_package" and item.get("taskDetailReport"):
        return item
    sop = _operator_sop(item)
    pack = _system_change_pack(item)
    agent = _agent(item, sop, pack)
    title = agent["title"]
    priority = _priority(item)
    store_ids = item.get("storeIds") or item.get("visibleStoreIds") or []
    assignee_id = item.get("assigneeId") or item.get("ownerUserId")
    reviewer_id = item.get("reviewerId")
    visible_roles = item.get("visibleRoleIds") or ["owner", "manager", "operator"]
    visible_users = list(dict.fromkeys([value for value in [assignee_id, reviewer_id, *(_arr(item.get("visibleUserIds")))] if value]))
    ownership = {
        "ownerUserId": assignee_id,
        "assignedOperatorId": assignee_id,
        "reviewerId": reviewer_id,
        "visibleUserIds": visible_users,
        "visibleRoleIds": visible_roles,
        "storeIds": store_ids,
    }
    detail = {
        "version": V1211_MANUAL_TASK_PACKAGE_VERSION,
        "title": title,
        "warningSummary": agent["judgment"],
        "systemChangePack": pack,
        "agentOperatingJudgment": agent,
        "evidencePack": [*pack.get("lines", []), {"type": "agent_operating_judgment", "title": "Agent经营判断", "label": "Agent经营判断", "summary": agent["judgment"], "reason": agent["judgment"]}],
        "sopSteps": sop,
        "operatorSopSteps": sop,
        "systemRecapLine": agent["systemRecapLine"],
        "autoRecapRule": "运营提交材料后进入等待系统复盘；后续报表/接口数据更新后系统自动计算复盘，不要求运营人工复盘。",
        "completionGate": ["已执行Agent生成的当前动作", "已上传处理截图或数据凭证", "已填写处理说明", "提交后等待系统自动复盘"],
        "reviewMetrics": {"systemRecap": True, "operatorManualRecap": False, "source": "manual_module_task"},
    }
    item.update({
        "taskGenerationMode": "v11_8_sop_package",
        "taskPackageVersion": V1211_MANUAL_TASK_PACKAGE_VERSION,
        "title": title,
        "productTitle": item.get("productTitle") or title,
        "task": sop[0],
        "taskType": item.get("taskType") or "Agent经营执行任务",
        "actionType": item.get("actionType") or "Agent执行SOP",
        "taskCard": {"title": title, "subtitle": "Agent已生成SOP · 系统自动复盘", "priority": priority, "deadline": item.get("deadline") or "今日内", "ownerRole": "operator"},
        "taskDetailReport": detail,
        "evidencePack": detail["evidencePack"],
        "evidence": detail["evidencePack"],
        "sopSteps": sop,
        "executionRequirements": sop,
        "systemChangePack": pack,
        "agentOperatingJudgment": agent,
        "systemRecapLine": agent["systemRecapLine"],
        "autoRecapRequired": True,
        "operatorManualRecapRequired": False,
        "completionGate": detail["completionGate"],
        "failureThreshold": {"systemAutoRecap": True, "manualTaskFallback": True},
        "reviewMetrics": detail["reviewMetrics"],
        "agentJudgment": agent,
        "ownership": {**ownership, **dict(item.get("ownership") or {})},
        "judgmentTags": [*list(item.get("judgmentTags") or []), "V12.11.1 手动任务包装", "Agent生成SOP", "系统自动复盘"],
    })
    return item
