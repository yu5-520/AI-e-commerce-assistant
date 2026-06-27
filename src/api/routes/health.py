from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "12.1.2"
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "currentEntry": "/",
        "dashboardEntry": "/api/modules/dashboard",
        "operatingUnitEntry": "/api/modules/operating-unit",
        "productEntry": "/api/modules/product?storeId=STORE_ID",
        "productDetailEntry": "/api/modules/product/{product_id}",
        "runtimeDiagnosticsEntry": "/api/system/runtime-diagnostics",
        "runtimeResetEntry": "/api/system/reset-runtime-data?confirm=true",
        "repositoryModeEntry": "/api/system/repositories",
        "readinessEntry": "/api/architecture/v10/readiness",
        "v12ReportGateway": "/api/data/upload/preview",
        "v121MetricFacts": "/api/data/metric-facts/summary",
        "v12Rule": "report_profile_agent_system_code_metric_facts",
        "v121Rule": "independent_metric_fact_tables_no_task_noise",
        "v1211Rule": "sheetRows_routed_by_reportProfile_sheetProfiles",
        "v1212Rule": "product_archive_position_metric_sections_task_summary",
    }
