"""FastAPI entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import accounts, approvals, data_import, health, modules, system

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"

app = FastAPI(
    title="AI ERP Operating Advisor API",
    version="3.0.8",
    description="V3 task evidence workflow runtime with structured operator submission, manager evidence review, audit logs, alert evidence reports, scoped dashboard/report alerts, and cross-account task lifecycle sync.",
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
    index_path = WEB_DEMO_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI ERP Operating Advisor API is running.", "version": "3.0.8"}


app.include_router(modules.router)
app.include_router(accounts.router)
app.include_router(health.router)
app.include_router(data_import.router)
app.include_router(approvals.router)
app.include_router(system.router)
