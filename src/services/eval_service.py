"""Eval service for product-oriented API routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from evals.run_evals import run_crm_segmentation_eval, run_rpa_task_eval

ROOT_DIR = Path(__file__).resolve().parents[2]


def run_minimal_evals() -> Dict[str, Any]:
    results: List[Dict[str, Any]] = [run_crm_segmentation_eval(), run_rpa_task_eval()]
    passed = all(item["passed"] for item in results)
    output_dir = ROOT_DIR / "evals" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "latest_results.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "passed": passed,
        "results": results,
        "output_path": str(output_path),
    }
