"""Load mock ERP / CRM CSV datasets.

This module intentionally uses only Python standard library so the demo can run
without installing extra dependencies.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = ROOT_DIR / "examples"


def read_csv(filename: str) -> List[Dict[str, str]]:
    """Read a CSV file from examples/ and return rows as dictionaries."""
    path = EXAMPLES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing mock dataset: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def to_number(value: Any, default: float = 0) -> float:
    """Convert CSV string values to float safely."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    """Convert CSV string values to int safely."""
    return int(to_number(value, default))


def load_all() -> Dict[str, List[Dict[str, str]]]:
    """Load all mock ERP / CRM datasets used by the demo workflow."""
    return {
        "products": read_csv("mock_products.csv"),
        "orders": read_csv("mock_orders.csv"),
        "inventory": read_csv("mock_inventory.csv"),
        "refunds": read_csv("mock_refunds.csv"),
        "customers": read_csv("mock_customers.csv"),
        "customer_tags": read_csv("mock_customer_tags.csv"),
        "interactions": read_csv("mock_interactions.csv"),
    }
