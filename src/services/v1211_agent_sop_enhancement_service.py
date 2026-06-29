"""V12.11 system-change-pack + Agent SOP enhancement.

The operating task chain should not ask operators to split traffic sources,
review ROI reasons, or manually recap after a test. The deterministic system
layer extracts metric changes; the Agent layer uses that change package to
produce an executable SOP and a system recap line.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, List

V1211_AGENT_SOP_VERSION = "12.11.0"

_PATCHED = False
_ORIGINAL_TASK_PAYLOAD: Callable[[Dict[str, Any]], Dict[str, Any]] | None = None


def _num(value: Any) -> float | None:
    if value in {None, "", "—", "未识别"}:
        return None
    try:
        return float(str(value).replace("¥", "").replace(",", "").replace("%", ""))
    except (TypeError, ValueError):
        return None


def _fmt_num(value: Any, default: str = "待确认") -> str:
    if value in {None, "", "—"}:
        return default
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _fmt_change(value: float | None) -> str:
    return "无法计算" if value is None else f"{value * 100:+.1f}%"


def _direction(value: float | None) -> str:
    if value is None:
        return "unknown"
    if value >= 0.05:
        return "up"
    if value <= -0.05:
        return "down"
    return "flat"


def _metric_map(signal: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(item.get("metricCode") or ""): item for item in signal.get("metrics") or [] if isinstance(item, dict)}


def _metric_line(metric: Dict[str, Any], role: str) -> Dict[str, Any]:
    name = metric.get("metricName") or metric.get("metricCode") or "指标"
    first_value = metric.get("firstDisplayValue") or _fmt_num(metric.get("firstValue"))
    latest_value = metric.get("latestDisplayValue") or _fmt_num(metric.get("latestValue"))
    change = metric.get("changeRate")
    summary = f"{name}：{first_value} → {latest_value}，环比 {_fmt_change(change)}"
    return {
        "type": "system_metric_change",
        "role": role,
        "metricCode": metric.get("metricCode"),
        "metricName": name,
        "title": name,
        "label": name,
        "firstValue": metric.get("firstValue"),
        "latestValue": metric.get("latestValue"),
        "firstDisplayValue": first_value,
        "latestDisplayValue": latest_value,
        "changeRate": change,
        "direction": _direction(change),
        "summary": summary,
        "reason": summary,
        "firstDate": metric.get("firstDate"),
        "latestDate": metric.get("latestDate"),
        "dataVersion": metric.get("dataVersion"),
        "sourceSheet": metric.get("sourceSheet"),
        "sourceBlockId": metric.get("sourceBlockId"),
    }


def _line_for(metrics: Dict[str, Dict[str, Any]], code: str, role: str) -> Dict[str, Any] | None:
    metric = metrics.get(code)
    if not metric or metric.get("missing"):
        return None
    return _metric_line(metric, role)


def _build_system_change_pack(signal: Dict[str, Any]) -> Dict[str, Any]:
    metrics = _metric_map(signal)
    primary_codes = ["roi", "payment_amount", "ad_spend"]
    driver_codes = ["paid_visitor_count", "organic_visitor_count", "visitor_count", "click_rate", "payment_conversion_rate"]
    risk_codes = ["inventory_qty", "sellable_days", "refund_rate", "gross_margin_rate"]
    lines: List[Dict[str, Any]] = []
    for code in primary_codes:
        line = _line_for(metrics, code, "主指标变化")
        if line:
            lines.append(line)
    for code in driver_codes:
        line = _line_for(metrics, code, "驱动/承接变化")
        if line:
            lines.append(line)
    for code in risk_codes:
        line = _line_for(metrics, code, "风险/承接变化")
        if line:
            lines.append(line)
    missing_hourly = True
    return {
        "version": V1211_AGENT_SOP_VERSION,
        "source": "system_deterministic_metric_change_pack",
        "rule": "系统只拆数据、算环比和趋势方向，不把拆分数据来源作为运营任务。",
        "productId": signal.get("productId"),
        "storeId": signal.get("storeId"),
        "dataVersion": signal.get("dataVersion"),
        "window": signal.get("window"),
        "cadence": signal.get("cadence"),
        "lines": lines,
        "primaryChanges": [item for item in lines if item.get("role") == "主指标变化"],
        "driverChanges": [item for item in lines if item.get("role") == "驱动/承接变化"],
        "riskChanges": [item for item in lines if item.get("role") == "风险/承接变化"],
        "dataGaps": [
            {
                "field": "小时级投放明细",
                "status": "missing",
                "impact": "不生成主投时间从8点切到13点等分时投放动作；已有日级/流量来源数据时只生成标题、素材、ROAS计划、预算节奏动作。",
            }
        ] if missing_hourly else [],
    }


def _metric(metrics: Dict[str, Dict[str, Any]], code: str) -> Dict[str, Any]:
    return metrics.get(code) or {}


def _roi_floor(metrics: Dict[str, Dict[str, Any]]) -> float:
    latest = _num(_metric(metrics, "roi").get("latestValue"))
    if latest is None:
        return 2.0
    return max(round(latest * 0.92, 2), 1.6)


def _conversion_floor(metrics: Dict[str, Dict[str, Any]]) -> float | None:
    latest = _num(_metric(metrics, "payment_conversion_rate").get("latestValue"))
    if latest is None:
        return None
    return round(latest * 0.94, 4)


def _click_drop_line(metrics: Dict[str, Dict[str, Any]]) -> str:
    latest = _num(_metric(metrics, "click_rate").get("latestValue"))
    if latest is None:
        return "点击率继续下降超过 10%"
    return f"点击率低于 {round(latest * 0.90, 4)} 或继续下降超过 10%"


def _agent_output(signal: Dict[str, Any], pack: Dict[str, Any]) -> Dict[str, Any]:
    metrics = _metric_map(signal)
    quadrant = (signal.get("roiGmvQuadrant") or {}).get("quadrant")
    signal_type = signal.get("signalType") or ""
    roi_change = _metric(metrics, "roi").get("changeRate")
    gmv_change = _metric(metrics, "payment_amount").get("changeRate")
    ad_change = _metric(metrics, "ad_spend").get("changeRate")
    conv_change = _metric(metrics, "payment_conversion_rate").get("changeRate")
    click_change = _metric(metrics, "click_rate").get("changeRate")
    refund_change = _metric(metrics, "refund_rate").get("changeRate")
    roi_floor = _roi_floor(metrics)
    conv_floor = _conversion_floor(metrics)
    click_line = _click_drop_line(metrics)

    if signal_type == "redline_inventory_zero":
        title = "库存断点｜暂停放量并切换替代主推"
        judgment = "系统变化包显示库存或可售承接触发红线。Agent判断当前不是继续分析流量，而是先处理断货、下架、补货或替代主推。"
        sop = [
            "6小时内暂停该商品继续加预算或新增推广动作。",
            "6小时内提交库存截图、补货/调拨结论；若无可售库存，切换到同店铺替代主推品。",
            "若商品仍在承接GMV，立即补充客服缺货话术或下架缺货链接，避免售后反噬。",
        ]
        recap = ["系统在后续报表更新后自动比对库存、可售天数、GMV和退款率；若库存仍未恢复且GMV继续承接，自动生成下架/替换主推复核任务。"]
    elif signal_type in {"redline_margin_floor", "redline_refund_floor"}:
        title = "红线反噬｜暂停继续放量并处理承接风险"
        judgment = "系统变化包显示毛利或退款触发红线。Agent判断当前先保底线，不把GMV增长当成有效增长。"
        sop = [
            "6小时内暂停继续加预算和活动加码。",
            "今日提交退款TOP5或毛利异常截图，明确是价格、优惠、客服、质量还是详情承诺问题。",
            "红线未解除前，不生成扩量任务；只允许生成修承接、控预算、改详情页任务。",
        ]
        recap = ["系统在后续报表更新后自动比对退款率、毛利率、GMV和ROI；红线未解除时自动写入日报/周报风险项并生成下一轮承接修复任务。"]
    elif quadrant == "low_roi_high_gmv" and ad_change is not None and ad_change > 0:
        stable_conversion = conv_change is None or conv_change > -0.08
        title = "付费放量ROI回撤｜测试标题与ROAS计划"
        judgment = "系统变化包显示GMV放大与广告消耗变化同步，ROI回撤不能直接判定为商品变差。Agent判断优先控制继续加预算，并通过标题/素材与ROAS计划做低风险测试。" if stable_conversion else "系统变化包显示付费放量伴随转化承接下滑。Agent判断优先修详情页、价格或客服承接，再考虑预算动作。"
        sop = [
            f"今日不继续新增预算，保留当前ROI不低于 {roi_floor} 的ROAS计划稳定观察。",
            "今日新增标题/素材A测试，保留原标题/素材B作为对照，并在提交页上传修改截图与测试范围。",
            "若后台已有ROAS计划明细，只切换到系统标记为高ROI的计划；若没有计划级数据，不生成让运营拆数据的任务。",
        ]
        if not stable_conversion:
            sop.insert(1, "12小时内优先修详情页、价格或评价承接，提交修改截图；不直接扩大投放。")
        recap = [
            f"系统在后续报表更新后自动比对ROI是否低于 {roi_floor}、{click_line}、GMV是否继续增长、广告消耗是否继续快于GMV增长。",
            "若未达系统复盘线，系统自动生成切换素材、降低预算或更换ROAS计划的下一轮任务，并写入日报/周报。",
        ]
    elif quadrant == "high_roi_low_gmv":
        title = "高ROI未放量｜测试标题/素材扩大入口"
        judgment = "系统变化包显示ROI尚可但GMV未放大。Agent判断不是让运营拆流量，而是直接给低风险扩入口动作。"
        sop = [
            "今日新增标题或主图素材测试，保留原版本对照。",
            f"只允许小幅测试预算，系统复盘线要求ROI不低于 {roi_floor}。",
            "提交测试标题/主图截图、测试开始时间和商品范围。",
        ]
        recap = [f"系统在后续报表更新后自动比对GMV、ROI、点击率和转化率；若GMV未增长且ROI稳定，自动生成下一轮入口扩量任务。"]
    elif quadrant == "high_roi_high_gmv":
        title = "高ROI高GMV｜检查库存承接后稳定放量"
        judgment = "系统变化包显示ROI与GMV同时可用。Agent判断先确认库存和可售天数，不让运营继续拆原因。"
        sop = [
            "今日确认库存和可售天数是否能承接未来3天GMV，不足时优先补货或替换主推位。",
            f"库存承接正常时，保留ROI不低于 {roi_floor} 的计划，不做降投。",
            "提交库存截图、主推位截图和是否补货/替换主推的结论。",
        ]
        recap = ["系统在后续报表更新后自动比对ROI、GMV、库存和可售天数；若库存下降快于GMV增长，自动生成补货或主推位替换任务。"]
    else:
        title = "经营波动观察｜执行低风险素材/承接测试"
        judgment = "系统变化包显示当前未形成单一强红线。Agent判断运营不需要拆数据，只执行低风险测试并提交材料，后续由系统自动复盘。"
        sop = [
            "今日选择标题、主图、素材或详情页中的一个低风险动作进行测试，避免多动作同时改动。",
            f"测试期间不新增大额预算，系统复盘线要求ROI不低于 {roi_floor}。",
            "提交修改截图、测试开始时间和影响商品范围。",
        ]
        recap = ["系统在后续报表更新后自动比对ROI、GMV、点击率、转化率和广告消耗；未达标时自动生成下一轮任务。"]

    if conv_floor is not None:
        recap.append(f"支付转化率系统复盘线：不得低于 {conv_floor}，低于该线时优先生成承接修复任务。")

    return {
        "version": V1211_AGENT_SOP_VERSION,
        "status": "agent_generated_from_system_change_pack",
        "title": title,
        "judgment": judgment,
        "operatorSopSteps": sop,
        "systemRecapLine": recap,
        "nextTaskTrigger": [
            "后续报表或接口数据更新后由系统自动计算，不要求运营手动复盘。",
            "系统复盘未达标时自动生成下一轮任务，并写入日报、周报和复盘库。",
        ],
        "forbiddenOperatorActions": ["拆分流量来源", "拆分广告计划", "人工复盘ROI", "人工判断数据原因"],
        "inputChanges": pack.get("lines", []),
        "roiChange": _fmt_change(roi_change),
        "gmvChange": _fmt_change(gmv_change),
        "adSpendChange": _fmt_change(ad_change),
        "clickChange": _fmt_change(click_change),
        "conversionChange": _fmt_change(conv_change),
        "refundChange": _fmt_change(refund_change),
    }


def _enhance_payload(payload: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    task = deepcopy(payload)
    pack = _build_system_change_pack(signal)
    agent = _agent_output(signal, pack)
    product_title = signal.get("productTitle") or task.get("productTitle") or task.get("title") or signal.get("productId") or "经营对象"
    operator_sop = agent["operatorSopSteps"]
    recap_line = agent["systemRecapLine"]
    evidence_pack = pack.get("lines", [])
    evidence_pack.append({
        "type": "agent_operating_judgment",
        "title": "Agent经营判断",
        "label": "Agent经营判断",
        "summary": agent["judgment"],
        "reason": agent["judgment"],
    })
    detail = dict(task.get("taskDetailReport") or {})
    detail.update({
        "version": V1211_AGENT_SOP_VERSION,
        "title": f"{product_title}｜{agent['title']}",
        "warningSummary": agent["judgment"],
        "systemChangePack": pack,
        "agentOperatingJudgment": agent,
        "evidencePack": evidence_pack,
        "sopSteps": operator_sop,
        "operatorSopSteps": operator_sop,
        "systemRecapLine": recap_line,
        "autoRecapRule": "运营提交材料后进入等待系统复盘；后续报表/接口数据更新后系统自动计算复盘，不要求运营人工复盘。",
        "completionGate": ["已执行Agent生成的当前动作", "已上传处理截图或数据凭证", "已填写处理说明", "提交后等待系统自动复盘"],
        "reviewMetrics": {
            "primaryMetrics": ["ROI", "GMV/支付金额", "广告消耗"],
            "explainMetrics": ["付费流量", "自然流量", "点击率", "转化率", "退款率", "毛利率", "库存/可售天数"],
            "systemRecap": True,
            "operatorManualRecap": False,
            "requiredFactTables": ["product_metric_facts"],
        },
    })
    task.update({
        "title": f"{product_title}｜{agent['title']}",
        "task": operator_sop[0] if operator_sop else agent["title"],
        "taskType": "Agent经营执行任务",
        "actionType": agent["title"],
        "taskCard": {**dict(task.get("taskCard") or {}), "title": f"{product_title}｜{agent['title']}", "subtitle": "Agent已生成SOP · 系统自动复盘"},
        "taskDetailReport": detail,
        "evidencePack": evidence_pack,
        "evidence": evidence_pack,
        "sopSteps": operator_sop,
        "executionRequirements": operator_sop,
        "systemChangePack": pack,
        "agentOperatingJudgment": agent,
        "systemRecapLine": recap_line,
        "autoRecapRequired": True,
        "operatorManualRecapRequired": False,
        "completionGate": detail["completionGate"],
        "reviewMetrics": detail["reviewMetrics"],
        "judgmentTags": [*list(task.get("judgmentTags") or []), "V12.11 系统拆数据", "Agent生成SOP", "系统自动复盘"],
    })
    return task


def apply_v1211_agent_sop_enhancement() -> Dict[str, Any]:
    """Patch operating cadence task payloads with V12.11 Agent SOP output."""
    global _PATCHED, _ORIGINAL_TASK_PAYLOAD
    if _PATCHED:
        return {"version": V1211_AGENT_SOP_VERSION, "status": "already_applied"}
    from src.services import operating_cadence_task_service as cadence_service

    _ORIGINAL_TASK_PAYLOAD = cadence_service._task_payload

    def _wrapped_task_payload(signal: Dict[str, Any]) -> Dict[str, Any]:
        base = _ORIGINAL_TASK_PAYLOAD(signal)  # type: ignore[misc]
        return _enhance_payload(base, signal)

    cadence_service._task_payload = _wrapped_task_payload
    cadence_service.OPERATING_CADENCE_VERSION = V1211_AGENT_SOP_VERSION
    _PATCHED = True
    return {
        "version": V1211_AGENT_SOP_VERSION,
        "status": "applied",
        "rule": "系统拆数据生成变化包，Agent基于变化包生成经营判断和SOP，运营只执行，复盘由系统自动计算并写入日报/周报。",
    }
