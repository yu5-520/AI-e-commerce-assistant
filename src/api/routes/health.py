"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "3.0.6"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "v3_store_scoped_report_alert_runtime",
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
        "report_row_store_scope": True,
        "report_alert_store_id": True,
        "report_alert_visible_store_ids": True,
        "report_alerts_scoped_by_account": True,
        "dashboard_data_refresh_scoped_by_account": True,
        "report_module_scoped_by_account": True,
        "report_preview_store_aliases": True,
        "alert_task_routes_to_store_operator": True,
        "manager_navigation_compacted": True,
        "manager_business_modules_nested": True,
        "manager_module_cards_clickable": True,
        "manager_module_hub_css": "/web_demo/manager-module-hub.css",
        "minimal_ui_microcopy_removed": True,
        "owner_store_migration_confirm": True,
        "store_permission_next_day_effective": True,
        "pending_store_migrations": True,
        "store_migration_endpoint": "/api/accounts/store-assignments/{store_id}",
        "store_migrations_endpoint": "/api/accounts/store-migrations",
        "manager_operating_unit_full_scope": True,
        "operator_operating_unit_store_slice": True,
        "store_responsibility_assignment": True,
        "operating_unit_viewer_scope": True,
        "product_store_permission_filtering": True,
        "traffic_store_permission_filtering": True,
        "listing_store_permission_filtering": True,
        "role_scoped_task_flow": True,
        "task_store_permission_filtering": True,
        "warning_to_operator_todo": True,
        "cross_account_lifecycle_sync": True,
        "v3_data_snapshot": True,
        "v3_metric_snapshot": True,
        "v3_report_alert_event": True,
        "v3_alert_to_task_bridge": True,
        "v3_global_data_refresh": True,
        "v3_file_first_report_upload": True,
        "v3_report_schema_preview": True,
        "v3_field_alias_mapping": True,
        "v3_confirm_before_alert": True,
        "task_events_endpoint": "/api/modules/todo/events",
        "task_counters_endpoint": "/api/modules/todo/counters",
        "operator_accept_endpoint": "/api/modules/todo/{task_id}/accept",
        "manager_split_endpoint": "/api/modules/todo/{task_id}/split",
        "manager_assign_endpoint": "/api/modules/todo/{task_id}/assign",
        "operator_submit_endpoint": "/api/modules/todo/{task_id}/submit",
        "manager_review_endpoint": "/api/modules/todo/{task_id}/review",
        "v3_templates_endpoint": "/api/data/templates",
        "v3_preview_endpoint": "/api/data/preview",
        "v3_confirm_import_endpoint": "/api/data/import/confirm",
        "v3_alerts_endpoint": "/api/data/alerts",
        "v3_versions_endpoint": "/api/data/versions",
        "v3_summary_endpoint": "/api/data/v3-summary",
    }
