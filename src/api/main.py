"""FastAPI entrypoint for the AI operating advisor MVP.

Run:
    uvicorn src.api.main:app --reload

The API uses Mock ERP / CRM data in the MVP. It generates business advice,
reports, and confirmation drafts, but does not connect to real shop backends or
execute high-risk actions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import approvals, business, customers, data_import, demo, diagnosis, evals, health, logs, products, reports, system, tasks

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"

app = FastAPI(
    title="AI Operating Advisor API",
    version="1.4.0",
    description="Productized API for ERP-based ecommerce operating unit advice.",
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


@app.get("/")
def index() -> FileResponse | Dict[str, str]:
    """Serve the static demo homepage when available."""
    index_path = WEB_DEMO_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "AI Operating Advisor API is running. Visit /api/business/today or /docs."}


# Productized API used by the current frontend.
app.include_router(business.router)

# Compatibility and internal routes kept for previous demos and debugging.
app.include_router(health.router)
app.include_router(system.router)
app.include_router(data_import.router)
app.include_router(demo.router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(diagnosis.router)
app.include_router(tasks.router)
app.include_router(approvals.router)
app.include_router(reports.router)
app.include_router(evals.router)
app.include_router(logs.router)
