"""V12.7 operating action authorization gate.

The gate separates business performance from governance weight:

- high ROI / high GMV / task priority can create urgency;
- only explicit RAG/company/manager/owner/historical-contribution weight can
  create approval protection.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.services.operating_weight_policy_service import OPERATING_WEIGHT_POLICY_VERSION, infer_operating_weight, is_governance_high_weight

ACTION_AUTHORIZATION_VERSION = "12.7.0"

ACTION_LABELS = {
    "activity_participation": "活动报名 / 活动承接",
    "title_test": "标题测试",
    "main_image_test": "主图测试",
    "creative_material_test": "素材测试",
    "traffic_expansion": "扩流测试",
    "inventory_restock": "补货 / 调拨承接",
    "price_adjustment": "价格调整",
    "ad_budget_adjustment": "投放预算调整",
    "homepage_position": "主推位调整",
    "product_demotion": "下架 / 降权处理",
    "generic_operation": "经营处理",
}

HIGH_RISK_ACTIONS = {"price_adjustment", "ad_budget_adjustment", "homepage_position", "product_demotion"}
APPROVAL_ACTIONS_ON_CONFIRMED_HIGH_WEIGHT = HIGH_RISK_ACTIONS | {"title_test", "main_image_test"}


def _join_text(task: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("title", "task", "taskType", "actionType", "riskDomain", "sourceModule", "reason"):
        if task.get(key):
            parts.append(str(task.get(key)))
    parts.extend(str(item) for item in task.get("judgmentTags") or [])
    parts.extend(str(item) for item in task.get("sopSteps") or [])
    card = task.get("taskCard") or {}
    detail = task.get("taskDetailReport") or {}
    parts.extend([str(card.get("subtitle") or ""), str(detail.get("warningSummary") or "")])
    return " ".join(parts)


def infer_action_type(task: Dict[str, Any]) -> str:
    text = _join_text(task)
    if any(token in text for token in ("活动", "报名", "平台补贴", "商家让利", "活动价")):
        return "activity_participation"
    if any(token in text for token in ("标题", "关键词", "搜索词")):
        return "title_test"
    if any(token in text for token in ("主图", "首图", "图片")):
        return "main_image_test"
    if any(token in text for token in ("素材", "创意")):
        return "creative_material_test"
    if any(token in text for token in ("扩流", "流量入口", "曝光", "渠道覆盖")):
        return "traffic_expansion"
    if any(token in text for token in ("补货", "调拨", "库存", "可售天数")):
        return "inventory_restock"
    if any(token in text for token in ("改价", "价格", "让利")):
        return "price_adjustment"
    if any(token in text for token in ("预算", "广告消耗", "加投", "降预算", "投放")):
        return "ad_budget_adjustment"
    if any(token in text for token in ("主推位", "首页", "资源位")):
        return "homepage_position"
    if any(token in text for token in ("下架", "降权", "暂停销售")):
        return "product_demotion"
    return "generic_operation"


def infer_object_weight(task: Dict[str, Any]) -> Dict[str, Any]:
    return infer_operating_weight(task)


def _operator_permission_level(task: Dict[str, Any]) -> str:
    ownership = task.get("ownership") or {}
    text = " ".join([str(task.get("operatorPermissionLevel") or ""), str(ownership.get("permissionLevel") or "")])
    if "高" in text or "high" in text:
        return "high"
    if "低" in text or "low" in text:
        return "low"
    return "middle"


def _operator_fields(action_type: str) -> List[str]:
    return {
        "activity_participation": ["活动入口", "活动价", "平台补贴", "商家让利", "报名门槛", "资源位", "竞品价格", "竞品销量截图"],
        "title_test": ["原标题截图", "新标题方案", "测试开始时间", "测试范围"],
        "main_image_test": ["原主图截图", "新主图方案", "测试开始时间", "测试范围"],
        "creative_material_test": ["原素材截图", "新素材方案", "投放位置", "测试开始时间"],
    }.get(action_type, ["执行截图", "处理记录", "复核说明"])


def authorize_action(task: Dict[str, Any]) -> Dict[str, Any]:
    action_type = infer_action_type(task)
    object_weight = infer_object_weight(task)
    operator_level = _operator_permission_level(task)
    high_risk = action_type in HIGH_RISK_ACTIONS
    confirmed_high_weight = is_governance_high_weight(object_weight)
    needs_weight_approval = confirmed_high_weight and operator_level != "high" and action_type in APPROVAL_ACTIONS_ON_CONFIRMED_HIGH_WEIGHT
    if high_risk and confirmed_high_weight and task.get("priority") == "高":
        decision = "owner_approval_required"
        layer = "manager_approval"
        reason = "高风险动作作用于已确认高权重/战略对象，需要老板或总管确认。"
    elif high_risk or needs_weight_approval:
        decision = "manager_approval_required"
        layer = "manager_approval"
        reason = "动作风险或已确认权重超过当前账号可直接执行权限，需要主管确认。"
    else:
        decision = "auto_execute"
        layer = "operator_execution"
        reason = "动作在当前账号权限范围内；经营表现标签不会被当作高权重审批依据。"
    return {
        "version": ACTION_AUTHORIZATION_VERSION,
        "mode": "rag_operating_action_permission_gate_v12_7_weight_confidence",
        "actionType": action_type,
        "actionLabel": ACTION_LABELS.get(action_type, "经营处理"),
        "operatorPermissionLevel": operator_level,
        "objectWeight": object_weight,
        "operatingWeightPolicyVersion": OPERATING_WEIGHT_POLICY_VERSION,
        "decision": decision,
        "taskLayer": layer,
        "approvalReason": reason,
        "operatorFactFields": _operator_fields(action_type),
        "policy": {
            "operatorProvidesFactsOnly": True,
            "systemEstimatesImpact": True,
            "approvalUsesConservativeFloor": True,
            "reportPerformanceIsNotGovernanceWeight": True,
            "rule": "V12.7：高权重必须来自RAG配置、主管/老板标记或多期历史贡献；高ROI、高GMV、任务优先级和首份报表标签不能触发高权重审批。",
        },
    }


def apply_action_authorization(task: Dict[str, Any]) -> Dict[str, Any]:
    gate = authorize_action(task)
    next_task = {**task, "actionAuthorization": gate, "v127ActionGate": gate, "v126ActionGate": gate}
    if gate["decision"] in {"manager_approval_required", "owner_approval_required"}:
        next_task["taskLayer"] = gate.get("taskLayer") or "manager_approval"
        next_task["assigneeId"] = None
        next_task["status"] = "待复核"
        next_task["workflowStatus"] = "待审批" if gate["decision"] == "manager_approval_required" else "待老板确认"
        next_task["displayStatus"] = next_task["workflowStatus"]
        next_task["visibleRoleIds"] = list(dict.fromkeys([*(next_task.get("visibleRoleIds") or []), "owner", "manager"]))
        card = dict(next_task.get("taskCard") or {})
        card["subtitle"] = "主管审批｜" + gate.get("actionLabel", "经营动作") if gate["decision"] == "manager_approval_required" else "老板确认｜" + gate.get("actionLabel", "经营动作")
        next_task["taskCard"] = card
        next_task["taskType"] = "主管审批任务" if gate["decision"] == "manager_approval_required" else "老板确认任务"
        next_task["priority"] = "高" if gate["decision"] == "owner_approval_required" else next_task.get("priority", "中")
    else:
        next_task.setdefault("taskLayer", "operator_execution")
    return next_task
