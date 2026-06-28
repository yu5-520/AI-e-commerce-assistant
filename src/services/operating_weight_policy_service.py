"""V12.7 operating weight policy.

High-weight store/product status is a governance label, not a one-day report
performance label. ROI, GMV, click rate, conversion rate, and task priority can
explain business opportunity/risk, but they cannot by themselves create approval
protection.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable

OPERATING_WEIGHT_POLICY_VERSION = "12.7.0"

EXPLICIT_HIGH_MARKERS = ("高权重", "主推商品", "核心商品", "核心SKU", "战略店铺", "品牌主店", "老板关注", "审批保护", "不可直接改价", "不可直接改主图", "不可直接改标题")
EXPLICIT_STRATEGIC_MARKERS = ("战略", "老板指定", "品牌主店", "核心店铺", "核心商品", "核心SKU")
REPORT_ONLY_MARKERS = ("高ROI", "高GMV", "低库存", "点击率", "转化率", "活动流量", "春夏新品", "常规款", "季节款", "已入库")


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _collect_explicit_text(task: Dict[str, Any]) -> str:
    """Only collect governance fields; do not read broad business tags."""
    ownership = task.get("ownership") or {}
    detail = task.get("taskDetailReport") or {}
    rag = task.get("ragBusinessMemory") or task.get("v126RagMemory") or {}
    policy = rag.get("companyBaseline") if isinstance(rag.get("companyBaseline"), dict) else {}
    allowed_keys = (
        "storeWeightTag",
        "productWeightTag",
        "storeWeightLevel",
        "productWeightLevel",
        "governanceWeightTag",
        "governanceWeightLevel",
        "weightSource",
        "weightLevel",
    )
    parts: list[str] = []
    for source in (task, ownership, detail, policy):
        for key in allowed_keys:
            if isinstance(source, dict) and source.get(key):
                parts.append(_clean(source.get(key)))
    explicit = task.get("explicitWeightTags") or task.get("governanceTags") or []
    if isinstance(explicit, list):
        parts.extend(_clean(item) for item in explicit)
    return " ".join(part for part in parts if part)


def _declared_source(task: Dict[str, Any]) -> str:
    text = _collect_explicit_text(task)
    if "owner_marked" in text or "老板" in text:
        return "owner_marked"
    if "manager_marked" in text or "主管" in text or "总管" in text:
        return "manager_marked"
    if "rag_declared" in text or "RAG" in text or "配置" in text:
        return "rag_declared"
    if "historical_contribution" in text or "90" in text or "长期贡献" in text:
        return "historical_contribution"
    if text:
        return "explicit_governance_tag"
    return "first_report_baseline"


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    return any(marker in text for marker in markers)


def infer_operating_weight(task: Dict[str, Any]) -> Dict[str, Any]:
    explicit_text = _collect_explicit_text(task)
    source = _declared_source(task)
    strategic = _contains_any(explicit_text, EXPLICIT_STRATEGIC_MARKERS)
    high = strategic or _contains_any(explicit_text, EXPLICIT_HIGH_MARKERS) or "high" in explicit_text.lower() or "strategic" in explicit_text.lower()
    if strategic:
        level = "strategic"
        confidence = "high"
    elif high:
        level = "high"
        confidence = "high" if source in {"owner_marked", "manager_marked", "rag_declared", "historical_contribution"} else "medium"
    else:
        level = "middle"
        confidence = "low" if source == "first_report_baseline" else "medium"
    can_trigger_approval = level in {"high", "strategic"} and source != "first_report_baseline" and confidence in {"medium", "high"}
    return {
        "version": OPERATING_WEIGHT_POLICY_VERSION,
        "mode": "governance_weight_not_report_performance",
        "storeWeight": level,
        "productWeight": level,
        "combinedWeight": level,
        "weightLevel": level,
        "weightConfidence": confidence,
        "weightSource": source,
        "canTriggerApproval": can_trigger_approval,
        "explicitWeightText": explicit_text,
        "reportOnlyMarkersIgnored": list(REPORT_ONLY_MARKERS),
        "rule": "高权重必须来自RAG配置、主管/老板标记或多期历史贡献；高ROI、高GMV、任务优先级和首份报表标签不能触发高权重审批。",
    }


def is_governance_high_weight(weight: Dict[str, Any]) -> bool:
    return bool(weight.get("canTriggerApproval") and weight.get("combinedWeight") in {"high", "strategic"})
