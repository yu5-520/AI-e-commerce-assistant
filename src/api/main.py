"""FastAPI entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import accounts, approvals, architecture, audit, data_import, health, import_jobs, llm, modules, report_task_sync, system, task_persistence, trends, v10_product, v9_readiness, worker_jobs
from src.services.v112_task_chain_fix_service import apply_v112_task_chain_fix

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"
API_VERSION = "12.1.2"

app = FastAPI(title="AI ERP Operating Advisor API", version=API_VERSION)
V112_TASK_CHAIN_FIX = apply_v112_task_chain_fix()

if WEB_DEMO_DIR.exists():
    app.mount("/web_demo", StaticFiles(directory=WEB_DEMO_DIR), name="web_demo")


@app.get("/", response_model=None)
def index() -> Any:
    index_path = WEB_DEMO_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI ERP Operating Advisor API is running.", "version": API_VERSION, "v12_1_2": "product_archive_fact_detail"}


app.include_router(modules.router)
app.include_router(accounts.router)
app.include_router(health.router)
app.include_router(llm.router)
app.include_router(data_import.router)
app.include_router(import_jobs.router)
app.include_router(approvals.router)
app.include_router(system.router)
app.include_router(architecture.router)
app.include_router(v9_readiness.router)
app.include_router(v10_product.router)
app.include_router(task_persistence.router)
app.include_router(report_task_sync.router)
app.include_router(trends.router)
app.include_router(worker_jobs.router)
app.include_router(audit.router)
