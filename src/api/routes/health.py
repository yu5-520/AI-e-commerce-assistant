from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "14.8.0"
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
        "frontendReadModelEntry": "/api/view/dashboard",
        "frontendTaskViewEntry": "/api/view/tasks",
        "frontendProductViewEntry": "/api/view/products",
        "taskReportEntry": "/api/modules/task-reports/tasks/{task_id}",
        "runtimeDiagnosticsEntry": "/api/system/runtime-diagnostics",
        "runtimeResetEntry": "/api/system/reset-runtime-data?confirm=true",
        "v148Rule": "frontend_read_model_compute_read_isolation_streaming_task_handoff",
        "permissionEnvelope": "structured_budget_permission_fields",
        "taskOutputContract": "V11.8 SOP package remains formal task output",
    }
