"""FastAPI entrypoint for the AI ERP operating advisor MVP.

Current runtime chain:
    src.api.main:app
    ↓
    / serves web_demo/index.html
    ↓
    web_demo/app-v2.js calls /api/business/*

The app keeps only the current product-facing API surface plus health,
data-import, approval, and system maintenance routes. Legacy demo/debug route
families are intentionally not mounted to avoid old templates being pulled back
into the main product flow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import approvals, business, data_import, health, system

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"

app = FastAPI(
    title="AI ERP Operating Advisor API",
    version="1.0.14",
    description="Product API for ERP-based ecommerce operating unit advice.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if WEB_DEMO_DIR.exists():
    app.mount("/web_demo", StaticFiles(directory=WEB_DEMO_DIR), name="web_demo")


@app.get("/", response_model=None)
def index() -> Any:
    """Serve the current product homepage when available."""
    index_path = WEB_DEMO_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI ERP Operating Advisor API is running. Visit /api/business/today or /docs."}


# Current product API used by web_demo/app-v2.js.
app.include_router(business.router)

# Supporting routes still used by the product shell and deployment checks.
app.include_router(health.router)
app.include_router(data_import.router)
app.include_router(approvals.router)
app.include_router(system.router)
