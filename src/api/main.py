"""FastAPI entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import accounts, approvals, architecture, data_import, health, llm, modules, report_task_sync, system, task_persistence
from src.repositories.task_repository import bootstrap_task_repository
from src.services import module_task_service
from src.services.system_service import reset_legacy_runtime_once
from src.services.task_state_machine_service import load_task_snapshots

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"
API_VERSION = "5.1.8"

app = FastAPI(
    title="AI ERP Operating Advisor API",
    version=API_VERSION,
    description="V5.1.8 runtime with task evidence audit persistence, creative Agent task sync, frontend report import auto-sync, official task write path, scoped reads, startup hydration, UserContext, and architecture APIs.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["Accept", "Content-Type", "X-Mock-User-Id", "X-Tenant-Id", "X-Org-Id"],
)

if WEB_DEMO_DIR.exists():
    app.mount("/web_demo", StaticFiles(directory=WEB_DEMO_DIR), name="web_demo")


@app.on_event("startup")
def apply_v5_runtime_cleanup() -> None:
    """Initialize demo cleanup and hydrate task runtime from persisted snapshots."""
    reset_legacy_runtime_once()
    bootstrap_task_repository()
    if not module_task_service.TASKS:
        snapshots = load_task_snapshots()
        if snapshots:
            module_task_service.TASKS[:] = snapshots


@app.get("/", response_model=None)
def index() -> Any:
    index_path = WEB_DEMO_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI ERP Operating Advisor API is running.", "version": API_VERSION}


app.include_router(modules.router)
app.include_router(accounts.router)
app.include_router(health.router)
app.include_router(llm.router)
app.include_router(data_import.router)
app.include_router(approvals.router)
app.include_router(system.router)
app.include_router(architecture.router)
app.include_router(task_persistence.router)
app.include_router(report_task_sync.router)
