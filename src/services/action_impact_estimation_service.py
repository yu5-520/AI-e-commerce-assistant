"""V12.6 system-side operating action impact estimation.

Operators do not provide ROI/GMV/sales/margin forecasts. They provide objective
facts such as activity price, platform subsidy, competitor price, or before/after
creative screenshots. The system owns conservative / normal / optimistic impact
estimation and uses the conservative floor for authorization.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from src.services.action_authorization_gate_service import infer_action_type

ACTION_IMPACT_ESTIMATION_VERSION = "12.6.0"


def _as_float(value: Any) -> float | None:
    if value in {None, "", "—", "未识别"}:
        return None
    try:
        return float(str(value).replace("¥", "").replace(",", "").replace("%", ""))
    except (TypeError, ValueError):
        return None


def _metric_value(task: Dict[str, Any], names: Iterable[str]) -> float | None:
    wanted = set(names)
    packs = []
    packs.extend(task.get("evidencePack") or [])
    packs.extend(task.get("evidence") or [])
    packs.extend((task.get("taskDetailReport") or {}).get("evidencePack") or [])
    for item in packs:
        title = str(item.get("title") or item.get("label") or "")
        if title in wanted or any(name in title for name in wanted):
            value = item.get("metric") if item.get("metric") is not None else item.get("value")
            parsed = _as_float(value)
            if parsed is not None:
                return parsed
    return None


def _band(base: float | None, conservative_delta: float, normal_delta: float, optimistic_delta: float) -> Dict[str, Any]:
    if base is None:
        return {"basis": "pending_fact", "conservative": None, "normal": None, "optimistic": None}
    return {
        "basis": base,
        "conservative": round(base * (1 + conservative_delta), 4),
        "normal": round(base * (1 + normal_delta), 4),
        "optimistic": round(base * (1 + optimistic_delta), 4),
    }


def estimate_action_impact(task: Dict[str, Any], memory_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    action_type = infer_action_type(task)
    roi = _metric_value(task, ["ROI"])
    gmv = _metric_value(task, ["GMV", "支付金额"])
    click_rate = _metric_value(task, ["点击率"])
    conversion = _metric_value(task, ["支付转化率", "转化率"])
    margin = _metric_value(task, ["毛利率"])
    inventory = _metric_value(task, ["库存数量", "库存"])
    if action_type == "activity_participation":
        effect = {
            "trafficMultiplier": {"conservative": 1.15, "normal": 1.45, "optimistic": 1.9},
            "roi": _band(roi, -0.08, 0.02, 0.12),
            "gmv": _band(gmv, 0.12, 0.35, 0.7),
            "grossMarginRate": _band(margin, -0.08, -0.03, 0.0),
            "inventoryConsumption": _band(inventory, -0.3, -0.5, -0.75),
            "refundRisk": "活动价和竞品价进入后由系统重算，保守下限用于过审。",
        }
    elif action_type in {"title_test", "main_image_test", "creative_material_test"}:
        effect = {
            "clickRate": _band(click_rate, 0.03, 0.08, 0.15),
            "conversionRate": _band(conversion, -0.02, 0.0, 0.05),
            "roi": _band(roi, -0.03, 0.02, 0.08),
            "gmv": _band(gmv, 0.02, 0.08, 0.18),
            "testWindowDays": 3,
        }
    elif action_type == "traffic_expansion":
        effect = {
            "roi": _band(roi, -0.1, -0.03, 0.05),
            "gmv": _band(gmv, 0.08, 0.22, 0.42),
            "clickRate": _band(click_rate, -0.02, 0.0, 0.05),
            "conversionRate": _band(conversion, -0.03, 0.0, 0.03),
        }
    else:
        effect = {
            "roi": _band(roi, -0.05, 0.0, 0.05),
            "gmv": _band(gmv, 0.0, 0.08, 0.2),
            "grossMarginRate": _band(margin, -0.03, 0.0, 0.02),
        }
    return {
        "version": ACTION_IMPACT_ESTIMATION_VERSION,
        "mode": "system_estimates_operator_does_not_forecast",
        "actionType": action_type,
        "scenarioBands": effect,
        "conservativeFloorRule": "自动确认只看保守估算下限；运营不提交 ROI、GMV、销量、库存消耗、毛利率等预测值。",
        "operatorInputBoundary": "运营只补充活动、竞品、素材、标题、主图等客观事实。",
        "memoryContext": memory_context or {},
    }


def apply_action_impact_estimation(task: Dict[str, Any], memory_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    estimate = estimate_action_impact(task, memory_context=memory_context)
    return {**task, "actionImpactEstimate": estimate, "v126ImpactEstimate": estimate}
