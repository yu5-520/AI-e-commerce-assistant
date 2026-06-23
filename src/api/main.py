"""FastAPI entrypoint."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import accounts, approvals, architecture, audit, data_import, health, import_jobs, llm, modules, report_task_sync, system, task_persistence, worker_jobs
from src.middleware.api_rate_limit import api_rate_limit_middleware
from src.middleware.security_headers import security_headers_middleware
from src.repositories.task_repository import bootstrap_task_repository
from src.services import module_task_service
from src.services.llm_gateway_service import ensure_llm_gateway_tables
from src.services.system_service import reset_legacy_runtime_once
from src.services.task_state_machine_service import load_task_snapshots
from src.services.tech_log_service import ensure_tech_log_tables
from src.services.trace_audit_service import ensure_trace_audit_tables
from src.services.worker_queue_service import ensure_worker_queue_tables

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"
API_VERSION = "5.2.9"
CORS_ORIGINS = [item.strip() for item in os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000").split(",") if item.strip()]

app = FastAPI(
    title="AI ERP Operating Advisor API",
    version=API_VERSION,
    description="V5.2.9 runtime with Nginx deployment templates, security headers, API rate limit, LLM Gateway controls, JSON TechLog redaction, trace_id audit chain, ARQ dispatch fallback, UserContext, and architecture APIs.",
)

app.middleware("http")(security_headers_middleware)
app.middleware("http")(api_rate_limit_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["Accept", "Content-Type", "X-Mock-User-Id", "X-Tenant-Id", "X-Org-Id", "Authorization"],
)

if WEB_DEMO_DIR.exists():
    app.mount("/web_demo", StaticFiles(directory=WEB_DEMO_DIR), name="web_demo")


@app.on_event("startup")
def apply_v5_runtime_cleanup() -> None:
    """Initialize demo cleanup and hydrate task runtime from persisted snapshots."""
    reset_legacy_runtime_once()
    bootstrap_task_repository()
    ensure_worker_queue_tables()
    ensure_trace_audit_tables()
    ensure_tech_log_tables()
    ensure_llm_gateway_tables()
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
app.include_router(import_jobs.router)
app.include_router(approvals.router)
app.include_router(system.router)
app.include_router(architecture.router)
app.include_router(task_persistence.router)
app.include_router(report_task_sync.router)
app.include_router(worker_jobs.router)
app.include_router(audit.router)
