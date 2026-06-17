"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "3.1.2"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "v312_rollback_task_strategy_runtime",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "safety": {
            "auto_scheduled_platform_action": False,
            "auto_ad_account_operation": False,
            "auto_product_publish": False,
            "auto_price_change": False,
            "auto_inventory_change": False,
            "auto_customer_message_blast": False,
            "marketplace_api_connected": False,
        },
        "import_records_endpoint": "/api/data/import-records",
        "data_version_rollback_endpoint": "/api/data/versions/{data_version}/rollback",
        "data_version_soft_rollback": True,
        "rollback_audit_record": True,
        "rollback_keeps_task_audit": True,
        "rollback_task_strategy": True,
        "rollback_task_strategy_review": True,
        "rollback_task_strategy_archive": True,
        "rollback_task_strategy_keep": True,
        "rollback_task_strategy_default": "review",
        "report_page_import_records": True,
        "report_page_rollback_task_strategy_select": True,
        "inventory_center_endpoint": "/api/modules/inventory",
        "inventory_task_endpoint": "/api/modules/inventory/{product_id}/tasks",
        "customer_service_center_endpoint": "/api/modules/aftersales",
        "customer_service_task_endpoint": "/api/modules/aftersales/{product_id}/tasks",
        "manager_inventory_card_route": "inventory-center",
        "manager_service_card_route": "service-center",
        "operation_center_store_scope": True,
        "operation_center_task_store_owner": True,
        "recap_candidates_endpoint": "/api/modules/recap-candidates",
        "task_approval_to_recap_candidate": True,
        "task_evidence_endpoint": "/api/modules/todo/{task_id}/evidence",
        "task_submit_evidence_endpoint": "/api/modules/todo/{task_id}/submit-evidence",
        "task_review_evidence_endpoint": "/api/modules/todo/{task_id}/review-evidence",
        "alert_evidence_report_endpoint": "/api/modules/task-reports/alerts/{alert_id}",
        "report_row_store_scope": True,
        "report_alerts_scoped_by_account": True,
        "report_preview_store_aliases": True,
        "alert_task_routes_to_store_operator": True,
        "manager_navigation_compacted": True,
        "manager_business_modules_nested": True,
        "minimal_ui_microcopy_removed": True,
        "owner_store_migration_confirm": True,
        "store_permission_next_day_effective": True,
        "role_scoped_task_flow": True,
        "warning_to_operator_todo": True,
        "cross_account_lifecycle_sync": True,
        "v3_data_snapshot": True,
        "v3_report_alert_event": True,
        "v3_alert_to_task_bridge": True,
        "v3_file_first_report_upload": True,
        "v3_report_schema_preview": True,
        "v3_confirm_before_alert": True,
        "v3_templates_endpoint": "/api/data/templates",
        "v3_preview_endpoint": "/api/data/preview",
        "v3_confirm_import_endpoint": "/api/data/import/confirm",
        "v3_alerts_endpoint": "/api/data/alerts",
        "v3_versions_endpoint": "/api/data/versions",
        "v3_summary_endpoint": "/api/data/v3-summary",
    }
