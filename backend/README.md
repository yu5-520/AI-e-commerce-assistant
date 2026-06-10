# Backend API Server

This backend connects the frontend UI to AI generation and feedback backflow.

## Run

```bash
python backend/server.py
```

Default server:

```text
http://localhost:3000
```

## APIs

### GET /api/health
Health check.

### POST /api/generate
Frontend product input -> backend generation -> productized cleanup -> result backflow -> frontend result.

Input example:

```json
{
  "mode": "自然流",
  "product": "防晒衣",
  "detail": "成本19，卖39，库存200，目标清库存",
  "cost": 19,
  "price": 39,
  "stock": 200
}
```

Output includes:
- `result_id`
- `product_result`: cleaned user-facing fields for frontend cards
- `markdown`: readable backup version generated from `product_result`
- `debug`: result id, model status, and local backflow status

`product_result` includes:
- titles
- image_directions
- sku_plans
- price_advice
- activity_suggestions
- next_actions
- precision_tips

### POST /api/feedback
Frontend copy/use/action button -> item-level feedback record.

Input example:

```json
{
  "result_id": "res_xxx",
  "action": "used_title",
  "section": "product_result_card",
  "item_text": "夏季轻薄防晒衣女外套透气防晒服"
}
```

## Backflow Storage

Generation results are stored under:

```text
data/runtime_results/
```

Feedback records are stored under:

```text
data/runtime_feedback/
```

## LLM Behavior

The backend reuses `scripts/llm_client.py`.

If `LLM_ENABLED=true` and provider environment variables are configured, it asks the model to return productized JSON.
If the model is not enabled, fails, or returns non-JSON, the backend returns a deterministic productized fallback result so the frontend remains usable.

## Product Cleanup Boundary

User-facing frontend output should use `product_result` only.
Engineering details such as `result_id`, `llm_status`, `backflow_status`, fallback state, and API details belong in `debug` or backend logs, not in the main product result area.

## Current Boundary

This backend is a local MVP API layer. It is not yet a production authentication, billing, storage, or multi-user permission system.
