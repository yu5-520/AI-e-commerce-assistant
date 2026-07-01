"""FastAPI entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import accounts, approvals, architecture, audit, data_import, data_source_compat, deprecated_stations, frontend_views, health, import_jobs, llm, modules, ops, pipeline, report_task_sync, station_handoffs, stations, system, task_lifecycle_stations, task_persistence, task_pool, task_snapshots, trends, v10_product, v9_readiness, worker_jobs
from src.services.station_queue_worker_service import start_station_queue_worker, stop_station_queue_worker

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"
API_VERSION = "15.0"

app = FastAPI(title="AI ERP Operating Advisor API", version=API_VERSION)
STATION_MAINLINE = {
    "version": API_VERSION,
    "legacyStartupHooks": [],
    "mode": "v15_agent_budget_ledger_llm_gateway_three_agent_mainline",
    "mainline": [
        "report_schema_agent_mapping_cache",
        "system_cleaning_import",
        "full_product_bundle",
        "product_judgment_agent_budgeted_batch",
        "product_judgment_package_confidence_gate_70",
        "task_mapping_agent_permission_rag_budgeted_batch",
        "task_pool_admission",
        "frontend_read_model",
        "data_metro_line_agent_budget_status",
    ],
    "rule": "V15：报表Agent只做schema mapping；商品判断Agent只做全量包判断和置信值；任务映射Agent只做RAG权限/SOP映射；三类Agent统一走预算账本和网关，禁止按行、按指标、按任务散打API。",
}


@app.on_event("startup")
def startup_station_queue_worker() -> None:
    start_station_queue_worker(worker_id="fastapi-auto-worker")


@app.on_event("shutdown")
def shutdown_station_queue_worker() -> None:
    stop_station_queue_worker()


if WEB_DEMO_DIR.exists():
    app.mount("/web_demo", StaticFiles(directory=WEB_DEMO_DIR), name="web_demo")


@app.get("/", response_model=None)
def index() -> Any:
    index_path = WEB_DEMO_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI ERP Operating Advisor API is running.", "version": API_VERSION, "v15": "agent_budget_ledger_llm_gateway_three_agent_mainline", "stationMainline": STATION_MAINLINE}


app.include_router(modules.router)
app.include_router(pipeline.router)
app.include_router(stations.router)
app.include_router(station_handoffs.router)
app.include_router(task_snapshots.router)
app.include_router(task_pool.router)
app.include_router(task_lifecycle_stations.router)
app.include_router(frontend_views.router)
app.include_router(ops.router)
app.include_router(deprecated_stations.router)
app.include_router(accounts.router)
app.include_router(health.router)
app.include_router(llm.router)
app.include_router(data_import.router)
app.include_router(data_source_compat.router)
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
