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
API_VERSION = "16.2"

app = FastAPI(title="AI ERP Operating Advisor API", version=API_VERSION)
STATION_MAINLINE = {
    "version": API_VERSION,
    "legacyStartupHooks": [],
    "mode": "v162_real_product_and_task_agents_mvp",
    "mainline": [
        "report_schema_agent_mapping_cache",
        "system_cleaning_import",
        "full_product_bundle",
        "real_product_judgment_agent_batch_json",
        "product_judgment_package_confidence_gate_70",
        "real_task_mapping_agent_rag_permission_json",
        "task_pool_admission_current_data_version",
        "frontend_read_model_current_run_only",
        "data_metro_line_real_agent_status",
    ],
    "rule": "V16.2：商品判断与任务映射都切到真实批量Agent JSON。任务映射Agent只处理70%+商品判断包，并结合RAG权限/SOP/审批规则生成任务；API未配置、JSON无效或无有效任务时，不回退模板任务、不生成假任务。",
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
    return {"message": "AI ERP Operating Advisor API is running.", "version": API_VERSION, "v162": "real_product_and_task_agents_mvp", "stationMainline": STATION_MAINLINE}


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
