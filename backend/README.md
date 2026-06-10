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
Frontend product input -> generation configuration -> backend generation -> productized cleanup -> result backflow -> frontend result.

Input example:

```json
{
  "mode": "自然流",
  "product": "防晒衣",
  "detail": "成本19，卖39，库存200，目标清库存",
  "cost": 19,
  "price": 39,
  "stock": 200,
  "membership": "free",
  "title_count": 3,
  "image_plan_count": 1,
  "image_generate_count": 0
}
```

Generation configuration fields:
- `membership`: `free` or `vip`
- `title_count`: number of title options requested
- `image_plan_count`: number of image direction plans requested
- `image_generate_count`: number of real image generations requested; currently only used for credit estimate

Free limits:
- title_count: 3 or 5
- image_plan_count: 1 or 2
- image_generate_count: 0, 1, or 2

VIP limits:
- title_count: 3, 5, 10, or 15
- image_plan_count: 1, 2, 3, or 5
- image_generate_count: 0, 1, 2, 3, or 5

If a free request asks for VIP-only counts, the backend automatically applies the nearest allowed free value and records the adjustment in `generation_config.adjustments`.

Output includes:
- `result_id`
- `product_result`: cleaned user-facing fields for frontend cards
- `product_result.generation_config`: requested/applied generation configuration and adjustments
- `product_result.image_generation_plan`: selected image count and estimated credits
- `markdown`: readable backup version generated from `product_result`
- `debug`: result id, model status, local backflow status, and generation config

`product_result` includes:
- titles
- image_directions
- image_generation_plan
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

If `LLM_ENABLED=true` and provider environment variables are configured, it asks the model to return productized JSON and to respect the applied generation counts.
If the model is not enabled, fails, or returns non-JSON, the backend returns a deterministic productized fallback result so the frontend remains usable.

## Product Cleanup Boundary

User-facing frontend output should use `product_result` only.
Engineering details such as `result_id`, `llm_status`, `backflow_status`, fallback state, and API details belong in `debug` or backend logs, not in the main product result area.

## Current Boundary

This backend is a local MVP API layer. It is not yet a production authentication, billing, real image generation, storage, or multi-user permission system.
