"""V12.8.2 operating action authorization gate.

Authorization must not jump from action type directly to manager approval. Budget
and activity actions pass through: operator budget range, system conservative
impact floor, company baseline, and confirmed governance weight.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from src.services.operating_weight_policy_service import OPERATING_WEIGHT_POLICY_VERSION, infer_operating_weight, is_governance_high_weight

ACTION_AUTHORIZATION_VERSION = "12.8.2"

ACTION_LABELS = {
    "activity_participation": "活动报名 / 活动承接",
    "inventory_restock": "库存警告 / 补货承接",
    "title_test": "标题测试",
    "main_image_test": "主图测试",
    "creative_material_test": "素材测试",
    "traffic_expansion": "扩流测试",
    "price_adjustment": "价格调整",
    "ad_budget_adjustment": "投放预算调整",
    "homepage_position": "主推位调整",
    "product_demotion": "下架 / 降权处理",
    "generic_operation": "经营处理",
}

HARD_APPROVAL_ACTIONS = {"price_adjustment", "homepage_position", "product_demotion"}
BUDGET_GATED_ACTIONS = {"ad_budget_adjustment", "activity_participation", "traffic_expansion"}
APPROVAL_ACTIONS_ON_CONFIRMED_HIGH_WEIGHT = HARD_APPROVAL_ACTIONS | BUDGET_GATED_ACTIONS | {"title_test", "main_image_test"}


def _join_text(task: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("title", "task", "taskType", "actionType", "riskDomain", "sourceModule", "reason", "submissionNote"):
        if task.get(key):
            parts.append(str(task.get(key)))
    parts.extend(str(item) for item in task.get("judgmentTags") or [])
    parts.extend(str(item) for item in task.get("sopSteps") or [])
    card = task.get("taskCard") or {}
    detail = task.get("taskDetailReport") or {}
    parts.extend([str(card.get("title") or ""), str(card.get("subtitle") or ""), str(detail.get("warningSummary") or "")])
    return " ".join(parts)


def _as_float(value: Any) -> float | None:
    if value in {None, "", "—", "未识别"}:
        return None
    try:
        return float(str(value).replace("¥", "").replace(",", "").replace("元", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _first_number(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:元|预算|预算金额)?", text or "")
    return _as_float(match.group(1)) if match else None


def infer_action_type(task: Dict[str, Any]) -> str:
    text = _join_text(task)
    explicit = str(task.get("actionType") or "")
    if explicit in ACTION_LABELS and explicit != "generic_operation":
        return explicit
    if any(token in text for token in ("库存归零", "库存", "补货", "调拨", "可售天数", "断货", "缺货")):
        return "inventory_restock"
    if any(token in text for token in ("活动", "报名", "平台补贴", "商家让利", "活动价")):
        return "activity_participation"
    if any(token in text for token in ("改价", "价格", "让利")):
        return "price_adjustment"
    if any(token in text for token in ("预算", "广告消耗", "加投", "降预算", "投放")):
        return "ad_budget_adjustment"
    if any(token in text for token in ("主推位", "首页", "资源位")):
        return "homepage_position"
    if any(token in text for token in ("下架", "降权", "暂停销售")):
        return "product_demotion"
    if any(token in text for token in ("标题", "关键词", "搜索词")):
        return "title_test"
    if any(token in text for token in ("主图", "首图", "图片")):
        return "main_image_test"
    if any(token in text for token in ("素材", "创意")):
        return "creative_material_test"
    if any(token in text for token in ("扩流", "流量入口", "曝光", "渠道覆盖")):
        return "traffic_expansion"
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


def _company_baseline(task: Dict[str, Any]) -> Dict[str, Any]:
    rag = task.get("ragBusinessMemory") or task.get("v126RagMemory") or {}
    baseline = rag.get("companyBaseline") if isinstance(rag.get("companyBaseline"), dict) else {}
    return baseline or {"minRoi": 2.0, "minGrossMarginRate": 0.28, "operatorActivityBudgetRange": [3000, 8000]}


def _operator_budget_range(task: Dict[str, Any]) -> tuple[float, float]:
    baseline = _company_baseline(task)
    raw = baseline.get("operatorActivityBudgetRange") or baseline.get("operatorBudgetRange") or [3000, 8000]
    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        low = _as_float(raw[0]) or 0
        high = _as_float(raw[1]) or 0
        return low, high
    return 3000.0, 8000.0


def _requested_budget(task: Dict[str, Any]) -> float | None:
    for key in ("requestedBudget", "budgetAmount", "activityBudget", "adBudget", "plannedBudget"):
        parsed = _as_float(task.get(key))
        if parsed is not None:
            return parsed
    detail = task.get("taskDetailReport") or {}
    for source in (task.get("actionAuthorization") or {}, task.get("actionImpactEstimate") or {}, detail):
        for key in ("requestedBudget", "budgetAmount", "activityBudget", "adBudget", "plannedBudget"):
            parsed = _as_float(source.get(key) if isinstance(source, dict) else None)
            if parsed is not None:
                return parsed
    return _first_number(_join_text(task))


def _conservative_floor(task: Dict[str, Any], metric: str) -> float | None:
    estimate = task.get("actionImpactEstimate") or task.get("v126ImpactEstimate") or {}
    bands = estimate.get("scenarioBands") if isinstance(estimate.get("scenarioBands"), dict) else {}
    target = bands.get(metric) if isinstance(bands.get(metric), dict) else {}
    return _as_float(target.get("conservative"))


def _below_company_floor(task: Dict[str, Any]) -> bool:
    baseline = _company_baseline(task)
    roi_floor = _conservative_floor(task, "roi")
    margin_floor = _conservative_floor(task, "grossMarginRate")
    min_roi = _as_float(baseline.get("minRoi"))
    min_margin = _as_float(baseline.get("minGrossMarginRate"))
    return bool((roi_floor is not None and min_roi is not None and roi_floor < min_roi) or (margin_floor is not None and min_margin is not None and margin_floor < min_margin))


def _operator_fields(action_type: str) -> List[str]:
    return {
        "activity_participation": ["活动入口", "活动价", "平台补贴", "商家让利", "报名门槛", "资源位", "竞品价格", "竞品销量截图"],
        "inventory_restock": ["当前库存截图", "可售天数", "预计到货时间", "可调拨库存", "活动或投放承接计划"],
        "ad_budget_adjustment": ["当前广告计划截图", "拟调整预算金额", "投放时段", "人群/关键词/素材范围", "调整原因"],
        "title_test": ["原标题截图", "新标题方案", "测试开始时间", "测试范围"],
        "main_image_test": ["原主图截图", "新主图方案", "测试开始时间", "测试范围"],
        "creative_material_test": ["原素材截图", "新素材方案", "投放位置", "测试开始时间"],
    }.get(action_type, ["执行截图", "处理记录", "复核说明"])


def authorize_action(task: Dict[str, Any]) -> Dict[str, Any]:
    action_type = infer_action_type(task)
    object_weight = infer_object_weight(task)
    operator_level = _operator_permission_level(task)
    confirmed_high_weight = is_governance_high_weight(object_weight)
    hard_action = action_type in HARD_APPROVAL_ACTIONS
    budget_action = action_type in BUDGET_GATED_ACTIONS
    budget = _requested_budget(task)
    budget_min, budget_max = _operator_budget_range(task)
    budget_over_limit = bool(budget is not None and budget_max and budget > budget_max)
    below_floor = _below_company_floor(task)
    needs_weight_approval = confirmed_high_weight and operator_level != "high" and action_type in APPROVAL_ACTIONS_ON_CONFIRMED_HIGH_WEIGHT
    if hard_action and confirmed_high_weight and task.get("priority") == "高":
        decision = "owner_approval_required"
        layer = "manager_approval"
        reason = "硬风险动作作用于已确认治理高权重/战略对象，需要老板或总管确认。"
    elif hard_action or budget_over_limit or below_floor or needs_weight_approval:
        decision = "manager_approval_required"
        layer = "manager_approval"
        reason = "动作超过运营权限、保守估算低于公司基线、或作用于已确认治理高权重对象，需要主管确认。"
    else:
        decision = "auto_execute"
        layer = "operator_execution"
        reason = "动作在当前账号权限和公司基线内；投放/活动类任务未因动作类型一刀切升级审批。"
    return {
        "version": ACTION_AUTHORIZATION_VERSION,
        "mode": "main_architecture_forced_permission_gate_v12_8_2",
        "actionType": action_type,
        "actionLabel": ACTION_LABELS.get(action_type, "经营处理"),
        "operatorPermissionLevel": operator_level,
        "objectWeight": object_weight,
        "operatingWeightPolicyVersion": OPERATING_WEIGHT_POLICY_VERSION,
        "decision": decision,
        "taskLayer": layer,
        "approvalReason": reason,
        "operatorFactFields": _operator_fields(action_type),
        "budgetGate": {"isBudgetAction": budget_action, "requestedBudget": budget, "operatorBudgetMin": budget_min, "operatorBudgetMax": budget_max, "budgetOverLimit": budget_over_limit},
        "impactGate": {"usesSystemEstimate": True, "belowCompanyFloor": below_floor, "roiConservativeFloor": _conservative_floor(task, "roi"), "marginConservativeFloor": _conservative_floor(task, "grossMarginRate"), "companyBaseline": _company_baseline(task)},
        "policy": {
            "operatorProvidesFactsOnly": True,
            "systemEstimatesImpact": True,
            "approvalUsesConservativeFloor": True,
            "reportPerformanceIsNotGovernanceWeight": True,
            "inventorySignalsBeforeCreativeWords": True,
            "budgetActionIsNotAutomaticManagerApproval": True,
            "rule": "V12.8.2：审批必须经过预算权限、系统保守估算、公司基线和已确认治理权重，不能只靠actionType短路。",
        },
    }


def apply_action_authorization(task: Dict[str, Any]) -> Dict[str, Any]:
    gate = authorize_action(task)
    next_task = {**task, "actionAuthorization": gate, "v1282ActionGate": gate, "v127ActionGate": gate, "v126ActionGate": gate}
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
