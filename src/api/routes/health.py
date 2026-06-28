from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "12.7.2"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "currentEntry": "/",
        "todoEntry": "/api/modules/todo",
        "productEntry": "/api/modules/product?storeId=STORE_ID",
        "taskReportEntry": "/api/modules/task-reports/tasks/{task_id}",
        "runtimeDiagnosticsEntry": "/api/system/runtime-diagnostics",
        "runtimeResetEntry": "/api/system/reset-runtime-data?confirm=true",
        "v1270Rule": "operating_weight_confidence_policy",
        "v1271Rule": "clustered_task_queue_and_safe_reports",
        "v1272Rule": "real_clustered_task_lifecycle_inventory_before_material_tests",
    }
