# Frontend UI

This folder contains the frontend UI for the AI ecommerce operation console.

## Files
- `index.html`: page structure, product sections, and generation configuration controls
- `styles.css`: cloud-console style UI with light/dark theme variables
- `runtime.css`: configuration controls, productized result cards, copy buttons, feedback button, and debug panel styles
- `app.js`: theme switch, mode selection, generation configuration, backend API calls, product result cleanup, productized rendering, copy actions, and feedback backflow

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

## Generation Configuration
Before generation, users can choose the output range:

```text
membership: free / vip
title_count: 3 / 5 / 10 VIP / 15 VIP
image_plan_count: 1 / 2 / 3 VIP / 5 VIP
image_generate_count: 0 / 1 / 2 / 3 VIP / 5 VIP
```

Free users are limited to:
- title_count: 3 or 5
- image_plan_count: 1 or 2
- image_generate_count: 0, 1, or 2

VIP users can choose:
- title_count: 3, 5, 10, or 15
- image_plan_count: 1, 2, 3, or 5
- image_generate_count: 0, 1, 2, 3, or 5

Image generation is currently only estimated by credits. Real image generation is not connected yet.

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
User selects generation configuration
↓
POST /api/generate
↓
Backend applies free/VIP limits and returns product_result
↓
Frontend normalizes product_result
↓
Frontend renders productized cards according to selected counts
↓
User copies or marks specific items as used
↓
POST /api/feedback
↓
Backend stores item-level feedback under data/runtime_feedback/
```

## Productized Rendering Rules
- Main result area must not expose engineering fields such as `result_id`, `llm_status`, `backflow_status`, `fallback`, or API details.
- Engineering fields may appear only inside the developer debug details panel.
- Titles should be rendered as copyable title cards.
- Image directions should be rendered as main text, sub text, and visual structure cards.
- SKU suggestions should be rendered as table rows with copy and feedback actions.
- Price and activity suggestions should be rendered as direct action items.
- Feedback should be attached to the exact copied/used item when possible.

## Current Status
This is an MVP frontend-backend connection. It can generate and display cleaned product results through the local backend, respect generation count choices, estimate image generation credits, and write item-level feedback backflow records. It is not yet connected to authentication, billing, real image generation, production storage, or VIP user isolation.
