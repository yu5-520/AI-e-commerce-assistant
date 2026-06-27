from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "12.4.0"
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
        "v1213DataGaps": "/api/data/data-gaps/summary",
        "v1215ImportDiagnostics": "/api/data/import-diagnostics",
        "v1228SourceConnections": "/api/data/source-connections",
        "v12Rule": "report_profile_agent_system_code_metric_facts",
        "v121Rule": "independent_metric_fact_tables_no_task_noise",
        "v1211Rule": "sheetRows_routed_by_reportProfile_sheetProfiles",
        "v1212Rule": "product_archive_position_metric_sections_task_summary",
        "v1213Rule": "data_gap_events_logged_without_task_creation",
        "v1214Rule": "task_generation_from_operating_judgment_then_evidence_gate",
        "v1215Rule": "import_diagnostics_acceptance_report",
        "v1216Rule": "productized_frontend_format_and_task_min_identity",
        "v1220Rule": "report_layout_agent_sheet_profile_to_block_profile",
        "v1221Rule": "row_coordinates_source_block_id_metric_scope_preserved",
        "v1222Rule": "metric_facts_written_by_layout_blocks",
        "v1223Rule": "operating_products_identity_only_no_metric_cache",
        "v1224Rule": "product_page_fail_closed_no_cache_no_zero",
        "v1225Rule": "roi_scope_isolation_product_traffic_store",
        "v1226Rule": "import_diagnostics_sheet_block_fact_gap_staging",
        "v1227Rule": "task_evidence_gate_strict_metric_scope_no_cross_roi",
        "v1228Rule": "api_contract_patch_source_connections_and_demo_account_switch",
        "v1230Rule": "document_governance_current_docs_archive_deprecated_frontend_hygiene_gate",
        "v1240Rule": "operating_cadence_upload_frequency_trend_windows_agent_tasks_report_seeds",
    }
