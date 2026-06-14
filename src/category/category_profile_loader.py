from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
CATEGORY_PROFILE_DIR = ROOT_DIR / "knowledge_base" / "category_profiles"

CATEGORY_PROFILE_FILES = {
    "sun_protection_clothing": "sun_protection_clothing.md",
    "防晒服": "sun_protection_clothing.md",
}


def _extract_heading_section(content: str, heading: str) -> str:
    """Extract a markdown section by heading text.

    This deliberately stays lightweight. The category profile is still a human
    readable markdown file; this helper only extracts enough structure for MVP
    workflow context and smoke tests.
    """
    pattern = rf"^##\s+\d+\.\s+{re.escape(heading)}\s*$"
    match = re.search(pattern, content, flags=re.MULTILINE)
    if not match:
        return ""

    start = match.end()
    next_heading = re.search(r"^##\s+\d+\.\s+", content[start:], flags=re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(content)
    return content[start:end].strip()


def _extract_bullets(section: str) -> List[str]:
    values: List[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            values.append(stripped[2:].strip("。 "))
    return values


def _extract_text_block(section: str) -> List[str]:
    blocks = re.findall(r"```text\n(.*?)\n```", section, flags=re.DOTALL)
    values: List[str] = []
    for block in blocks:
        for line in block.splitlines():
            stripped = line.strip()
            if stripped:
                values.append(stripped)
    return values


def load_category_profile(category_id: str = "sun_protection_clothing") -> Dict[str, Any]:
    """Load one vertical category profile from knowledge_base/category_profiles."""
    filename = CATEGORY_PROFILE_FILES.get(category_id, CATEGORY_PROFILE_FILES["sun_protection_clothing"])
    path = CATEGORY_PROFILE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Category profile not found: {path}")

    content = path.read_text(encoding="utf-8")
    category_name = "防晒服" if "防晒服" in content[:120] else category_id

    seasonality_section = _extract_heading_section(content, "核心经营周期")
    price_section = _extract_heading_section(content, "常见价格带")
    selling_points_section = _extract_heading_section(content, "核心卖点")
    image_section = _extract_heading_section(content, "主图表达方向")
    sku_section = _extract_heading_section(content, "SKU 结构建议")
    review_section = _extract_heading_section(content, "高频差评与售后风险")
    competitor_section = _extract_heading_section(content, "竞品比对维度")
    traffic_section = _extract_heading_section(content, "流量测试指标")

    return {
        "category_id": "sun_protection_clothing",
        "category_name": category_name,
        "source": str(path.relative_to(ROOT_DIR)),
        "summary": "季节性强、价格带明显、退换货和尺码问题较高的服饰类目。",
        "seasonality": _extract_text_block(seasonality_section),
        "price_bands": _extract_text_block(price_section),
        "selling_points": _extract_bullets(selling_points_section),
        "image_expression_rules": _extract_bullets(image_section),
        "sku_structure_rules": _extract_bullets(sku_section),
        "common_return_reasons": _extract_bullets(review_section),
        "competitor_compare_dimensions": _extract_text_block(competitor_section),
        "traffic_test_metrics": _extract_text_block(traffic_section),
        "raw_excerpt": content[:600].replace("\n", " "),
    }
