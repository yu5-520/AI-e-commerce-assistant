"""FastAPI entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import accounts, approvals, data_import, health, llm, modules, system
from src.services.system_service import reset_legacy_runtime_once

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"

app = FastAPI(
    title="AI ERP Operating Advisor API",
    version="5.0.8",
    description="V5.0.8 runtime with productized dashboard import summary and priority-sorted operating tasks.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Content-Type", "X-Mock-User-Id"],
)

if WEB_DEMO_DIR.exists():
    app.mount("/web_demo", StaticFiles(directory=WEB_DEMO_DIR), name="web_demo")


@app.on_event("startup")
def apply_v5_runtime_cleanup() -> None:
    """Clear pre-V5 persisted demo rows once so the product starts empty after deploy."""
    reset_legacy_runtime_once()


@app.get("/", response_model=None)
def index() -> Any:
    index_path = WEB_DEMO_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI ERP Operating Advisor API is running.", "version": "5.0.8"}


app.include_router(modules.router)
app.include_router(accounts.router)
app.include_router(health.router)
app.include_router(llm.router)
app.include_router(data_import.router)
app.include_router(approvals.router)
app.include_router(system.router)
