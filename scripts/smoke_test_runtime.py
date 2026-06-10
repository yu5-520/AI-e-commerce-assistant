from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# Keep the smoke test deterministic and offline.
os.environ["LLM_ENABLED"] = "false"

from backend.server import generate_operation  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    payload = {
        "mode": "自然流",
        "product": "防晒衣",
        "detail": "成本19，卖39，库存200，卖点轻薄透气。",
        "cost": 19,
        "price": 39,
        "stock": 200,
        "membership": "free",
        "title_count": 3,
        "image_plan_count": 1,
        "image_generate_count": 0,
    }
    result = generate_operation(payload)
    assert_true(result.get("ok") is True, "generate_operation should return ok=True")
    product_result = result.get("product_result") or {}
    assert_true(len(product_result.get("titles", [])) == 3, "free title_count=3 should return 3 titles")
    assert_true(len(product_result.get("image_directions", [])) == 1, "free image_plan_count=1 should return 1 image direction")
    assert_true("generation_config" in product_result, "product_result should include generation_config")
    assert_true("image_generation_plan" in product_result, "product_result should include image_generation_plan")
    print(json.dumps({"ok": True, "result_id": result.get("result_id")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
