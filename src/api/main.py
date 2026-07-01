"""V16.21 FastAPI entrypoint.

MVP runtime only. Legacy routes, worker scaffold routes, deleted source-core
modules, old mock workflow dependencies, syntax leftovers, old audit/data-import
context imports, old V11 report-governance dependencies, legacy ImportJob wrapper
routes, legacy LLM debug gateway routes, legacy module task-report routes,
legacy module Agent candidate/playbook routes, and legacy module Todo routes are
removed from the active app; Git history remains the archive.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import accounts, approvals, audit, data_import, frontend_views, health, modules, ops, pipeline, stations, system, task_lifecycle_stations, task_persistence, task_pool, task_snapshots
from src.services.station_queue_worker_service import start_station_queue_worker, stop_station_queue_worker

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"
API_VERSION = "16.21"

app = FastAPI(title="AI ERP Operating Advisor API", version=API_VERSION)
STATION_MAINLINE = {
    "version": API_VERSION,
    "legacyStartupHooks": [],
    "mode": "v1621_module_todo_route_pruned",
    "mainline": [
        "report_receive_station",
        "report_schema_station",
        "report_fact_station",
        "product_master_station",
        "product_metric_snapshot_station",
        "full_product_bundle_station",
        "bundle_validation_station",
        "product_judgment_agent_station",
        "product_judgment_package_station",
        "rag_permission_context_station",
        "task_mapping_agent_station",
        "task_pool_admission_station",
        "frontend_read_model_station",
        "task_pool_acceptance_station",
    ],
    "rule": "V16.21：modules内部旧todo子路由从active app移除。任务列表、详情和生命周期动作由V16 task_pool/task_persistence/task_lifecycle/frontend read model主链路承接。",
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
    return {"message": "AI ERP Operating Advisor API is running.", "version": API_VERSION, "v1621": "module_todo_route_pruned", "stationMainline": STATION_MAINLINE}


app.include_router(modules.router)
app.include_router(pipeline.router)
app.include_router(stations.router)
app.include_router(task_snapshots.router)
app.include_router(task_pool.router)
app.include_router(task_lifecycle_stations.router)
app.include_router(frontend_views.router)
app.include_router(ops.router)
app.include_router(accounts.router)
app.include_router(health.router)
app.include_router(data_import.router)
app.include_router(approvals.router)
app.include_router(system.router)
app.include_router(task_persistence.router)
app.include_router(audit.router)
