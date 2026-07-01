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
API_VERSION = "16.4"

app = FastAPI(title="AI ERP Operating Advisor API", version=API_VERSION)
STATION_MAINLINE = {
    "version": API_VERSION,
    "legacyStartupHooks": [],
    "mode": "v164_real_report_fact_layer_before_agent",
    "mainline": [
        "report_schema_agent_mapping_cache",
        "system_cleaning_import",
        "real_report_fact_namespace_product_store_traffic",
        "report_date_metric_date_priority",
        "product_master_dedupe_platform_store_product_sku",
        "full_product_bundle_fact_layer_validation",
        "real_product_judgment_agent_batch_json",
        "product_judgment_package_confidence_gate_70",
        "real_task_mapping_agent_rag_permission_json",
        "task_pool_admission_current_data_version",
        "frontend_read_model_current_run_only",
        "task_pool_acceptance_data_line_equals_pool_equals_frontend",
    ],
    "rule": "V16.4：先修真实报表事实层，再给Agent判断。商品经营明细建商品主档，流量来源只作为子事实；商品ROI、店铺ROI、流量ROI分命名空间；指标日期优先读统计日期/更新时间，不用今日时间；商品主键按平台+店铺+商品ID+SKU去重。",
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
    return {"message": "AI ERP Operating Advisor API is running.", "version": API_VERSION, "v164": "real_report_fact_layer_before_agent", "stationMainline": STATION_MAINLINE}


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
