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

from backend.server import generate_operation, list_recent_results  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    client_id = "smoke_client_memory"
    payload = {
        "client_id": client_id,
        "mode": "自然流",
        "product": "2024防晒衣",
        "detail": "成本19，卖39，库存200，卖点轻薄透气。参考词：2024新款，夏季骑行，冰丝透气。",
        "market_material": "2024新款防晒衣女夏季冰丝透气\n2024爆款户外骑行防晒服",
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
    assert_true(result.get("client_id") == client_id, "generate_operation should preserve client_id")
    product_result = result.get("product_result") or {}
    assert_true(len(product_result.get("titles", [])) == 3, "free title_count=3 should return 3 titles")
    assert_true(len(product_result.get("image_directions", [])) == 1, "free image_plan_count=1 should return 1 image direction")
    assert_true("generation_config" in product_result, "product_result should include generation_config")
    assert_true("image_generation_plan" in product_result, "product_result should include image_generation_plan")
    assert_true("market_context" in product_result, "product_result should include market_context")
    observation = product_result.get("material_observation") or {}
    assert_true(observation.get("agent_name") == "素材观察 Agent", "product_result should include material observer output")
    assert_true(observation.get("search_tasks"), "material observer should provide search tasks")
    assert_true(observation.get("title_structures"), "material observer should provide title structures")
    serialized = json.dumps(product_result, ensure_ascii=False)
    assert_true("2024" not in serialized, "stale year 2024 should be removed from product result")
    recent = list_recent_results(client_id)
    assert_true(any(item.get("result_id") == result.get("result_id") for item in recent), "recent results should include the generated result for the same client")
    assert_true(not list_recent_results("another_client_should_not_see_this"), "another client should not see this smoke result")
    print(json.dumps({"ok": True, "result_id": result.get("result_id"), "recent_count": len(recent), "observer": observation.get("status")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
