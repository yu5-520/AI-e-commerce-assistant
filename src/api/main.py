"""FastAPI entrypoint for the product-oriented API MVP.

Run:
    uvicorn src.api.main:app --reload

The API still uses Mock ERP / CRM data and does not connect to real shop
backends or execute high-risk RPA actions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import approvals, customers, demo, diagnosis, evals, health, products, reports, tasks

ROOT_DIR = Path(__file__).resolve().parents[2]
WEB_DEMO_DIR = ROOT_DIR / "web_demo"

app = FastAPI(
    title="AI + RPA + ERP + CRM E-commerce Workflow API",
    version="0.8.0",
    description="Product-oriented API MVP for the AI ecommerce workflow workbench.",
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
    return {"message": "API is running. Visit /api/health or /docs."}


app.include_router(health.router)
app.include_router(demo.router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(diagnosis.router)
app.include_router(tasks.router)
app.include_router(approvals.router)
app.include_router(reports.router)
app.include_router(evals.router)
