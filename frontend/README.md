# Frontend UI

This folder contains the frontend UI for the AI ecommerce operation console.

## Files
- `index.html`: page structure and product sections
- `styles.css`: cloud-console style UI with light/dark theme variables
- `runtime.css`: runtime result, feedback button, and markdown result styles
- `app.js`: theme switch, mode selection, backend API calls, result rendering, and feedback backflow

## Design Direction
- white / black theme switch
- cloud console layout
- top navigation + left sidebar + card workspace
- orange accent color inspired by cloud product dashboards
- no third-party logo or copied vendor assets

## Product Sections
- operation generation workspace
- VIP product tracking
- credit wallet for image generation
- private knowledge base

## Backend Connection
The frontend calls the local backend APIs:

```text
POST /api/generate
POST /api/feedback
GET /api/health
```

## Runtime Flow

```text
Frontend product input
↓
POST /api/generate
↓
Backend reads mode, product, detail, cost, price, stock
↓
Backend calls LLM if enabled, otherwise deterministic fallback
↓
Backend stores result under data/runtime_results/
↓
Frontend displays generated title/image/SKU/price operation result
↓
User clicks feedback buttons
↓
POST /api/feedback
↓
Backend stores feedback under data/runtime_feedback/
```

## Current Status
This is an MVP frontend-backend connection. It can generate and display operation results through the local backend, and it can write feedback backflow records. It is not yet connected to authentication, billing, production storage, or VIP user isolation.
