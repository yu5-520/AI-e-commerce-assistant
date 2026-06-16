"""Health routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

API_VERSION = "2.5.1"

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": API_VERSION,
        "product": "AI ERP Operating Advisor",
        "mode": "cross_account_task_lifecycle_sync",
        "api_entry": "/api/modules/*",
        "account_entry": "/api/accounts",
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
        "task_events_endpoint": "/api/modules/todo/events",
        "task_counters_endpoint": "/api/modules/todo/counters",
        "operator_accept_endpoint": "/api/modules/todo/{task_id}/accept",
        "manager_split_endpoint": "/api/modules/todo/{task_id}/split",
        "manager_assign_endpoint": "/api/modules/todo/{task_id}/assign",
        "operator_submit_endpoint": "/api/modules/todo/{task_id}/submit",
        "manager_review_endpoint": "/api/modules/todo/{task_id}/review",
        "recap_endpoint": "/api/modules/todo/{task_id}/recap",
    }
