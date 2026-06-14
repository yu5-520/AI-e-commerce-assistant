from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
CATEGORY_EXAMPLES_DIR = ROOT_DIR / "examples" / "category_sun_protection"


def load_mock_competitors() -> List[Dict[str, str]]:
    """Load same-category competitor mock data.

    MVP boundary: this reads manually prepared / mock competitor rows. It does
    not crawl real platform pages or bypass any platform controls.
    """
    path = CATEGORY_EXAMPLES_DIR / "mock_competitors.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing mock competitor dataset: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))
