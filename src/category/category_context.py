from __future__ import annotations

from typing import Any, Dict

from src.category.category_profile_loader import load_category_profile
from src.category.category_rules import build_category_risk_rules, suggest_category_next_steps


def build_category_context(category_id: str = "sun_protection_clothing") -> Dict[str, Any]:
    """Build the category context injected into the main workflow.

    The context is intentionally compact: enough for API output, report output,
    smoke tests, and the next V0.9 integration step.
    """
    profile = load_category_profile(category_id)
    return {
        "category_profile": profile,
        "category_rules": build_category_risk_rules(profile),
        "next_steps": suggest_category_next_steps(profile),
        "integration_status": "V0.9 category profile loaded; diagnosis rules not yet category-specialized.",
    }
