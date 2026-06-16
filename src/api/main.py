"""FastAPI entrypoint for the AI ERP operating advisor MVP.

Current runtime chain:
    src.api.main:app
    ↓
    / serves web_demo/index.html
    ↓
    modular frontend: core/router.js registers modules/*/page.js
    ↓
    /api/modules/* maps one backend module to one frontend module

The app mounts only the current modular product API plus health, data-import,
approval, and system maintenance routes. The old `/api/business/*` compatibility
router is intentionally removed from the active product path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import approvals, data_import, health, modules, system

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"

app = FastAPI(
    title="AI ERP Operating Advisor API",
    version="1.5.2",
    description="Modular product API for ERP-based ecommerce operating unit advice.",
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
    """Serve the current modular product homepage when available."""
    index_path = WEB_DEMO_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI ERP Operating Advisor API is running. Visit /api/modules/dashboard or /docs."}


# Current modular product API used by the frontend route registry.
app.include_router(modules.router)

# Supporting routes still used by product operations and deployment checks.
app.include_router(health.router)
app.include_router(data_import.router)
app.include_router(approvals.router)
app.include_router(system.router)
