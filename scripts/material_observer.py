from __future__ import annotations

import re
from collections import Counter
from typing import Any

AGENT_ID = "material-observer"
AGENT_NAME = "素材观察 Agent"
AGENT_VERSION = "0.9.2"
AGENT_STAGE = "pre_generation"

SCENE_WORDS = ["通勤", "骑行", "户外", "旅游", "防晒", "出游", "上班", "学生", "宝妈", "露营", "跑步"]
FUNCTION_WORDS = ["轻薄", "透气", "冰丝", "凉感", "速干", "防晒", "显瘦", "宽松", "不闷", "防紫外线", "收纳"]
PRICE_WORDS = ["低价", "券后", "活动价", "清仓", "高性价比", "限时", "多件装"]
GENERIC_BANNED_WORDS = ["2024", "2025", "过季", "去年", "全网爆款", "全网热卖", "官方正品", "永久", "第一", "最强"]
SOURCE_POLICY = {
    "allowed_sources": ["user_provided_text", "merchant_owned_data", "uploaded_screenshot_text", "legal_search_api"],
    "disallowed_sources": ["unauthorized_platform_scraping", "copying_competitor_titles_verbatim"],
    "copy_rule": "只提取词感、词频、结构和风险，不直接复制竞品标题。",
}


def _unique(items: list[str], limit: int = 12) -> list[str]:
    result = []
    for item in items:
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", text or "")


def _pick_terms(samples: list[str], product: str) -> dict[str, list[str]]:
    joined = " ".join(samples)
    token_counts = Counter(_tokens(joined))
    banned = {product, "拼多多", "商品", "标题", "新款", "爆款", "正品", "旗舰", "包邮", "现货"}
    dynamic_terms = [word for word, _ in token_counts.most_common(40) if word not in banned and not re.fullmatch(r"20\d{2}", word)]
    return {
        "dynamic_terms": _unique(dynamic_terms, 12),
        "scene_terms": _unique([word for word in SCENE_WORDS if word in joined], 8),
        "function_terms": _unique([word for word in FUNCTION_WORDS if word in joined], 8),
        "price_terms": _unique([word for word in PRICE_WORDS if word in joined], 6),
    }


def _risk_flags(samples: list[str]) -> list[str]:
    joined = " ".join(samples)
    flags = []
    if re.search(r"\b202[0-5]\b", joined):
        flags.append("stale_year_detected")
    if any(word in joined for word in ["全网爆款", "全网热卖", "最强", "永久", "第一"]):
        flags.append("overclaim_word_detected")
    if not samples:
        flags.append("no_market_material")
    if len(samples) < 3:
        flags.append("low_sample_count")
    return flags


def _confidence(samples: list[str], usable_terms: list[str]) -> dict[str, Any]:
    score = 0.35
    if len(samples) >= 3:
        score += 0.25
    elif len(samples) >= 1:
        score += 0.12
    if len(usable_terms) >= 6:
        score += 0.25
    elif len(usable_terms) >= 3:
        score += 0.14
    score = min(round(score, 2), 0.9)
    if score >= 0.75:
        label = "high"
    elif score >= 0.5:
        label = "medium"
    else:
        label = "low"
    return {"score": score, "label": label}


def agent_contract() -> dict[str, Any]:
    return {
        "agent_id": AGENT_ID,
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "stage": AGENT_STAGE,
        "input_schema": {
            "product": "string",
            "mode_name": "string",
            "market_context": {"current_year": "int", "season": "string"},
            "material_pack": {"samples": "list[string]", "terms": "list[string]"},
        },
        "output_schema": {
            "search_tasks": "list[string]",
            "usable_terms": "list[string]",
            "title_structures": "list[string]",
            "banned_terms": "list[string]",
            "risk_flags": "list[string]",
            "confidence": {"score": "float", "label": "low|medium|high"},
            "next_sampling": "list[string]",
        },
        "source_policy": SOURCE_POLICY,
    }


def build_material_observation(product: str, mode_name: str, market_context: dict[str, Any], material_pack: dict[str, Any]) -> dict[str, Any]:
    """Build a bounded material-observation pack before title generation.

    This is a governed Agent layer: it plans what to observe, extracts wording
    signals from user-provided or legal material, returns confidence/risk
    metadata, and avoids unauthorized scraping or direct title copying.
    """
    product = (product or "商品").strip() or "商品"
    season = market_context.get("season") or "当季"
    current_year = market_context.get("current_year")
    samples = material_pack.get("samples") or []
    extracted = _pick_terms(samples, product)
    has_material = bool(samples)

    search_tasks = [
        f"拼多多 {product} {season} 热门标题",
        f"{product} {season} 主图卖点",
        f"{product} 价格带 SKU 组合",
    ]
    if mode_name == "强付费":
        search_tasks.append(f"{product} 投放素材 点击率 卖点")
    elif mode_name == "爆品打造":
        search_tasks.append(f"{product} 爆品 对标 价格带")
    else:
        search_tasks.append(f"{product} 自然搜索 长尾词")

    title_structures = [
        "商品词 + 当季词 + 功能词 + 场景词",
        "商品词 + 人群词 + 功能词 + 价格感",
        "商品词 + 材质/体验词 + 痛点词 + 场景词",
    ]

    next_sampling = [] if has_material else [
        "补充 3-5 条当前竞品标题",
        "补充 1-2 个主图大字或卖点词",
        "补充同价位商品的价格表达",
    ]

    usable_terms = _unique(
        extracted["dynamic_terms"] + extracted["scene_terms"] + extracted["function_terms"] + extracted["price_terms"],
        18,
    )
    risk_flags = _risk_flags(samples)
    confidence = _confidence(samples, usable_terms)

    return {
        "agent_id": AGENT_ID,
        "agent_name": AGENT_NAME,
        "agent_version": AGENT_VERSION,
        "stage": AGENT_STAGE,
        "status": "素材已提取" if has_material else "等待素材补充",
        "market_time": {"current_year": current_year, "season": season},
        "search_tasks": _unique(search_tasks, 8),
        "usable_terms": usable_terms,
        "title_structures": title_structures,
        "banned_terms": GENERIC_BANNED_WORDS,
        "risk_flags": risk_flags,
        "confidence": confidence,
        "sample_count": len(samples),
        "next_sampling": next_sampling,
        "source_policy": SOURCE_POLICY,
        "agent_trace": [
            "read_market_context",
            "clean_user_material",
            "extract_terms",
            "build_title_structures",
            "mark_risks",
            "return_observation_pack",
        ],
        "rule": SOURCE_POLICY["copy_rule"],
    }
