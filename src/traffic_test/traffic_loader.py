from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
CATEGORY_EXAMPLES_DIR = ROOT_DIR / "examples" / "category_sun_protection"


def load_mock_traffic_tests() -> List[Dict[str, str]]:
    """Load same-category traffic test mock data.

    MVP boundary: this reads manually prepared / mock traffic experiment rows. It
    does not connect to real ad accounts, platform APIs, or modify campaigns.
    """
    path = CATEGORY_EXAMPLES_DIR / "mock_traffic_tests.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing mock traffic test dataset: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))
