"""FastAPI entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import accounts, approvals, architecture, audit, data_import, data_source_compat, deprecated_stations, health, import_jobs, llm, modules, ops, pipeline, report_task_sync, station_handoffs, stations, system, task_lifecycle_stations, task_persistence, task_pool, task_snapshots, trends, v10_product, v9_readiness, worker_jobs

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"
API_VERSION = "14.4.0"

app = FastAPI(title="AI ERP Operating Advisor API", version=API_VERSION)
STATION_MAINLINE = {
    "version": API_VERSION,
    "legacyStartupHooks": [],
    "mode": "task_intent_contract_lifecycle",
    "mainline": ["operating_snapshot_station", "system_product_snapshot_station", "product_signal_snapshot_station", "task_signal_station", "rag_context_station", "agent_judgment_station", "task_snapshot_station", "task_pool_station", "task_lifecycle_stations"],
    "rule": "V14.4：任务链路新增TaskIntent契约层。Agent输出、任务快照、任务池和旧任务系统之间不再互相读取内部字段，统一先归一成标准任务意图，再进入可见任务与生命周期。",
}

if WEB_DEMO_DIR.exists():
    app.mount("/web_demo", StaticFiles(directory=WEB_DEMO_DIR), name="web_demo")


@app.get("/", response_model=None)
def index() -> Any:
    index_path = WEB_DEMO_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI ERP Operating Advisor API is running.", "version": API_VERSION, "v14": "task_intent_contract_lifecycle", "stationMainline": STATION_MAINLINE}


app.include_router(modules.router)
app.include_router(pipeline.router)
app.include_router(stations.router)
app.include_router(station_handoffs.router)
app.include_router(task_snapshots.router)
app.include_router(task_pool.router)
app.include_router(task_lifecycle_stations.router)
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
