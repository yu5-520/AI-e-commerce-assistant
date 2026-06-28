from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "12.8.1"
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
        "v1270Rule": "operating_weight_confidence_policy",
        "v1271Rule": "clustered_task_queue_and_safe_reports",
        "v1272Rule": "real_clustered_task_lifecycle_inventory_before_material_tests",
        "v1280Rule": "task_lifecycle_closed_loop_recap_to_rag_feedback",
        "v1281Rule": "frontend_backend_lifecycle_contract_alignment",
    }
