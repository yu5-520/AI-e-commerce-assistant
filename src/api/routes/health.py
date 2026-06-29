from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "14.3.1"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "currentEntry": "/",
        "todoEntry": "/api/modules/todo",
        "todoLifecycleSummaryEntry": "/api/modules/todo/lifecycle/summary",
        "todoRecapCompleteEntry": "/api/modules/todo/{task_id}/recap/complete",
        "productEntry": "/api/modules/product?storeId=STORE_ID",
        "taskReportEntry": "/api/modules/task-reports/tasks/{task_id}",
        "runtimeDiagnosticsEntry": "/api/system/runtime-diagnostics",
        "runtimeResetEntry": "/api/system/reset-runtime-data?confirm=true",
        "v143Rule": "full_signal_package_rag_budget_agent_lifecycle",
        "v1431Fix": "signal_pool_status_handoff_to_pending_rag_agent",
    }
