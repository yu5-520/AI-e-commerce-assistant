"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "2.5.0"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "role_scoped_task_flow_system",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
        "owner_business_overview": True,
        "owner_dashboard_not_task_list": True,
        "manager_execution_dashboard": True,
        "manager_dispatch_queue_layout": True,
        "operator_store_scope": True,
        "operator_operation_modules": True,
        "role_scoped_task_flow": True,
        "task_store_permission_filtering": True,
        "task_visible_roles": True,
        "task_visible_users": True,
        "task_visible_stores": True,
        "task_parent_child_split": True,
        "task_source_type": True,
        "task_layer_owner_manager_operator": True,
        "warning_to_operator_todo": True,
        "manager_split_endpoint": "/api/modules/todo/{task_id}/split",
        "manager_assign_endpoint": "/api/modules/todo/{task_id}/assign",
        "operator_submit_endpoint": "/api/modules/todo/{task_id}/submit",
        "manager_review_endpoint": "/api/modules/todo/{task_id}/review",
    }
