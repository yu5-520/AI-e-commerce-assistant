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
Frontend product input -> backend generation -> result backflow -> frontend result.

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
- result_id
- markdown result
- llm_status
- backflow_status

### POST /api/feedback
Frontend feedback button -> feedback record.

Input example:

```json
{
  "result_id": "res_xxx",
  "action": "used_title",
  "section": "frontend_result_card"
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

If `LLM_ENABLED=true` and provider environment variables are configured, it calls the configured OpenAI-compatible model.
If the model is not enabled or fails, the backend returns a deterministic fallback result so the frontend remains usable.

## Current Boundary

This backend is a local MVP API layer. It is not yet a production authentication, billing, storage, or multi-user permission system.
