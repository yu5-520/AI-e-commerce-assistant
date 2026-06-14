from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
CATEGORY_EXAMPLES_DIR = ROOT_DIR / "examples" / "category_sun_protection"


def load_mock_supplier_products() -> List[Dict[str, str]]:
    """Load same-category supplier product mock data.

    MVP boundary: this reads manually prepared / mock supplier rows. It does not
    connect to real supplier systems or publish products to any platform.
    """
    path = CATEGORY_EXAMPLES_DIR / "mock_supplier_products.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing mock supplier product dataset: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))
