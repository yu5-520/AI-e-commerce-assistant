"""FastAPI entrypoint for V7 API interactive demo.

Run:
    uvicorn src.api.main:app --reload

This API wraps the existing Mock Workflow. It does not connect to real ERP,
CRM, shop backends, or customer data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from evals.run_evals import run_crm_segmentation_eval, run_rpa_task_eval
from src.workflow.mock_workflow import build_mock_workflow_result

ROOT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT_DIR / "outputs"
WEB_DEMO_DIR = ROOT_DIR / "web_demo"
LOG_DIR = ROOT_DIR / "logs"
APPROVAL_LOG_PATH = LOG_DIR / "approval_records.jsonl"

app = FastAPI(
    title="AI + RPA + ERP + CRM E-commerce Workflow API",
    version="0.7.0",
    description="V7 API wrapper for the mock workflow demo.",
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

# In-memory task status store for MVP demo. Later this can be replaced by SQLite.
TASK_STATUS: Dict[str, Dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _load_latest_tasks() -> List[Dict[str, Any]]:
    result = build_mock_workflow_result(write_outputs=False)
    return result["rpa_tasks"]


def _update_task_status(task_id: str, status: str, operator: str = "demo_user") -> Dict[str, Any]:
    tasks = _load_latest_tasks()
    task = next((item for item in tasks if item.get("task_id") == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    if status not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid task status")

    updated = {
        **task,
        "approval_status": status,
        "status": status,
        "operator": operator,
        "updated_at": _now_iso(),
        "execution_note": "V7 demo only records approval state; it does not execute real RPA actions.",
    }
    TASK_STATUS[task_id] = updated
    _append_jsonl(APPROVAL_LOG_PATH, updated)
    return updated


@app.get("/")
def index() -> FileResponse | Dict[str, str]:
    """Serve the static demo homepage when available."""
    index_path = WEB_DEMO_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "API is running. Visit /api/health or /docs."}


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": "V7 API Demo",
        "mode": "mock_workflow_only",
        "safety": {
            "real_erp_connected": False,
            "real_crm_connected": False,
            "real_shop_backend_connected": False,
            "auto_high_risk_execution": False,
        },
    }


@app.get("/api/demo/run")
def run_demo_api() -> Dict[str, Any]:
    """Run the mock workflow and return structured results for the frontend."""
    result = build_mock_workflow_result(write_outputs=True)
    if TASK_STATUS:
        result["task_status_overrides"] = TASK_STATUS
    return result


@app.get("/api/demo/report", response_class=PlainTextResponse)
def demo_report() -> str:
    """Return the latest generated Markdown demo report."""
    report_path = OUTPUT_DIR / "demo_report.md"
    if not report_path.exists():
        build_mock_workflow_result(write_outputs=True)
    return report_path.read_text(encoding="utf-8")


@app.get("/api/evals/run")
def run_evals_api() -> Dict[str, Any]:
    """Run minimal evals and return pass/fail results."""
    results = [run_crm_segmentation_eval(), run_rpa_task_eval()]
    passed = all(item["passed"] for item in results)
    output_dir = ROOT_DIR / "evals" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "latest_results.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "passed": passed,
        "results": results,
        "output_path": str(output_path),
    }


@app.post("/api/tasks/{task_id}/approve")
def approve_task(task_id: str) -> Dict[str, Any]:
    """Approve a task draft without executing real RPA actions."""
    return _update_task_status(task_id=task_id, status="approved")


@app.post("/api/tasks/{task_id}/reject")
def reject_task(task_id: str) -> Dict[str, Any]:
    """Reject a task draft and record the decision."""
    return _update_task_status(task_id=task_id, status="rejected")


@app.get("/api/tasks/status")
def task_status() -> Dict[str, Dict[str, Any]]:
    """Return in-memory task approval overrides for the demo session."""
    return TASK_STATUS
