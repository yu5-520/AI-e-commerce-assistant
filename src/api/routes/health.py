"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "3.0.2"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "v3_report_schema_preview_runtime",
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
        "owner_business_overview": True,
        "manager_execution_dashboard": True,
        "operator_store_scope": True,
        "role_scoped_task_flow": True,
        "task_store_permission_filtering": True,
        "task_visible_roles": True,
        "task_visible_users": True,
        "task_visible_stores": True,
        "task_parent_child_split": True,
        "warning_to_operator_todo": True,
        "cross_account_lifecycle_sync": True,
        "task_event_stream": True,
        "task_counters_by_user": True,
        "task_transition_function": True,
        "operator_accept_action": True,
        "operator_submit_sync_to_manager": True,
        "manager_review_sync_to_operator": True,
        "recap_handoff_to_owner": True,
        "v3_data_snapshot": True,
        "v3_metric_snapshot": True,
        "v3_report_alert_event": True,
        "v3_alert_to_task_bridge": True,
        "v3_global_data_refresh": True,
        "v3_file_first_report_upload": True,
        "v3_report_schema_preview": True,
        "v3_field_alias_mapping": True,
        "v3_confirm_before_alert": True,
        "v3_mock_report_import": True,
        "v3_upload_payload_import": True,
        "task_events_endpoint": "/api/modules/todo/events",
        "task_counters_endpoint": "/api/modules/todo/counters",
        "operator_accept_endpoint": "/api/modules/todo/{task_id}/accept",
        "manager_split_endpoint": "/api/modules/todo/{task_id}/split",
        "manager_assign_endpoint": "/api/modules/todo/{task_id}/assign",
        "operator_submit_endpoint": "/api/modules/todo/{task_id}/submit",
        "manager_review_endpoint": "/api/modules/todo/{task_id}/review",
        "recap_endpoint": "/api/modules/todo/{task_id}/recap",
        "v3_templates_endpoint": "/api/data/templates",
        "v3_preview_endpoint": "/api/data/preview",
        "v3_confirm_import_endpoint": "/api/data/import/confirm",
        "v3_report_import_endpoint": "/api/data/import/report",
        "v3_mock_alert_endpoint": "/api/data/import/mock-alerts",
        "v3_alerts_endpoint": "/api/data/alerts",
        "v3_versions_endpoint": "/api/data/versions",
        "v3_summary_endpoint": "/api/data/v3-summary",
    }
