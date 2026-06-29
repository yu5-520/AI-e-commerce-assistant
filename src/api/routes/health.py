from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "12.9.0"
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
        "v1282Rule": "main_architecture_forced_gates",
        "v1283Rule": "task_card_single_action_and_aggregate_detail_report",
        "v1290Rule": "task_lifecycle_state_machine_unified_write_entrance",
    }
