"""FastAPI entrypoint."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import accounts, approvals, architecture, audit, data_import, health, import_jobs, llm, modules, report_task_sync, system, task_persistence, trends, worker_jobs
from src.middleware.api_rate_limit import api_rate_limit_middleware
from src.middleware.security_headers import security_headers_middleware
from src.repositories.task_repository import bootstrap_task_repository
from src.services import module_task_service
from src.services.approval_lifecycle_service import ensure_approval_lifecycle_tables
from src.services.execution_feedback_service import ensure_execution_feedback_tables
from src.services.execution_review_service import ensure_execution_review_tables
from src.services.high_risk_trend_gate_service import ensure_high_risk_gate_tables
from src.services.indicator_rag_service import ensure_indicator_rag_tables
from src.services.llm_gateway_service import ensure_llm_gateway_tables
from src.services.permission_budget_service import ensure_permission_budget_tables
from src.services.risk_task_service import ensure_risk_task_tables
from src.services.system_service import reset_legacy_runtime_once
from src.services.task_state_machine_service import load_task_snapshots
from src.services.tech_log_service import ensure_tech_log_tables
from src.services.trace_audit_service import ensure_trace_audit_tables
from src.services.trend_signal_service import ensure_trend_tables
from src.services.v7_saas_control_plane_service import ensure_v7_saas_control_plane_tables
from src.services.v71_tenant_config_service import ensure_v71_tenant_config_tables
from src.services.v75_release_alert_service import ensure_release_alert_tables
from src.services.v80_weight_snapshot_service import ensure_weight_snapshot_tables
from src.services.v81_weight_comparison_service import ensure_weight_comparison_tables
from src.services.v82_weight_rag_gate_service import ensure_weight_rag_tables
from src.services.v83_linked_metric_relation_service import ensure_linked_relation_tables
from src.services.v84_weight_score_service import ensure_weight_score_tables
from src.services.v85_context_weight_adjustment_service import ensure_context_weight_tables
from src.services.v86_cross_validation_service import ensure_cross_validation_tables
from src.services.v87_weight_task_group_service import ensure_weight_task_group_tables
from src.services.v88_weight_approval_service import ensure_weight_approval_tables
from src.services.v89_weight_execution_review_service import ensure_weight_execution_tables
from src.services.worker_queue_service import ensure_worker_queue_tables

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"
API_VERSION = "9.0.0"
CORS_ORIGINS = [item.strip() for item in os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000").split(",") if item.strip()]

app = FastAPI(title="AI ERP Operating Advisor API", version=API_VERSION, description="V9 runtime: SaaS enterprise consistency baseline for repository, frontend, backend, tier isolation, RAG isolation, permissions, audit, and deployment governance.")
app.middleware("http")(security_headers_middleware)
app.middleware("http")(api_rate_limit_middleware)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS", "DELETE"], allow_headers=["Accept", "Content-Type", "X-Mock-User-Id", "X-Tenant-Id", "X-Org-Id", "Authorization"])

if WEB_DEMO_DIR.exists():
    app.mount("/web_demo", StaticFiles(directory=WEB_DEMO_DIR), name="web_demo")


@app.on_event("startup")
def apply_v90_runtime_bootstrap() -> None:
    reset_legacy_runtime_once()
    bootstrap_task_repository()
    ensure_worker_queue_tables()
    ensure_trace_audit_tables()
    ensure_tech_log_tables()
    ensure_llm_gateway_tables()
    ensure_trend_tables()
    ensure_indicator_rag_tables()
    ensure_high_risk_gate_tables()
    ensure_permission_budget_tables()
    ensure_approval_lifecycle_tables()
    ensure_execution_feedback_tables()
    ensure_execution_review_tables()
    ensure_v7_saas_control_plane_tables()
    ensure_v71_tenant_config_tables()
    ensure_release_alert_tables()
    ensure_weight_snapshot_tables()
    ensure_weight_comparison_tables()
    ensure_weight_rag_tables()
    ensure_linked_relation_tables()
    ensure_weight_score_tables()
    ensure_context_weight_tables()
    ensure_cross_validation_tables()
    ensure_weight_task_group_tables()
    ensure_weight_approval_tables()
    ensure_weight_execution_tables()
    ensure_risk_task_tables()
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
app.include_router(trends.router)
app.include_router(worker_jobs.router)
app.include_router(audit.router)
