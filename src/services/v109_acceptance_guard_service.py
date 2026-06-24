"""V10.9 task-driven acceptance guard contract.

V10.9 is a closure release: no new daily workflow is added. It defines the
end-to-end acceptance chain that must remain true after future changes.
"""

from __future__ import annotations

from typing import Any, Dict, List

V109_ACCEPTANCE_GUARD_VERSION = "10.9.0"

V109_ACCEPTANCE_CHAIN = [
    "report_imported",
    "v104_modules_refreshed",
    "v107_operating_profile_created",
    "agent_tags_created_without_user_confirmation",
    "v108_tag_change_tasks_created",
    "task_pool_visible",
    "v105_role_views_synced",
    "v106_minimal_actions_enforced",
    "task_events_and_logs_written",
    "rag_memory_candidate_after_review",
]

V109_ACCEPTANCE_RULES = [
    "all_user_intervention_must_be_task",
    "no_manual_tag_confirmation_in_default_flow",
    "tag_change_must_enter_task_pool",
    "one_task_id_multiple_role_views",
    "task_card_max_two_visible_actions",
    "system_complexity_stays_in_status_and_logs",
    "import_result_must_report_next_action",
    "task_result_can_become_rag_memory_candidate_after_review",
]

V109_BLOCKING_FAILURES = [
    "import_success_without_task_sync",
    "agent_tags_require_user_confirmation",
    "tag_change_only_candidate_not_task",
    "todo_task_without_role_projection",
    "task_card_exposes_more_than_two_workflow_actions",
    "task_without_event_or_log_trace",
]


def v109_acceptance_summary() -> Dict[str, Any]:
    return {
        "version": V109_ACCEPTANCE_GUARD_VERSION,
        "mode": "task_driven_product_acceptance_guard",
        "acceptanceChain": V109_ACCEPTANCE_CHAIN,
        "acceptanceRules": V109_ACCEPTANCE_RULES,
        "blockingFailures": V109_BLOCKING_FAILURES,
        "passCriteria": [
            "导入后返回 v104ImportTaskSync、v107OperatingProfile、v108TagChangeTaskSync。",
            "v107OperatingProfile.userConfirmationRequired 必须为 false。",
            "标签变化必须进入任务池，并带 profileSnapshot。",
            "任务池返回跨账号视图和极简动作。",
            "每张任务卡最多两个前台流程动作。",
            "复核通过后必须能生成 RAG 记忆候选草案。",
        ],
    }


def summarize_runtime_acceptance(import_payload: Dict[str, Any], owner_todo: Dict[str, Any], manager_todo: Dict[str, Any], operator_todo: Dict[str, Any]) -> Dict[str, Any]:
    profile = import_payload.get("v107OperatingProfile") or {}
    tag_sync = import_payload.get("v108TagChangeTaskSync") or {}
    todos = [owner_todo, manager_todo, operator_todo]
    visible_action_counts: List[int] = []
    projected_task_count = 0
    for todo in todos:
        for task in todo.get("activeTasks", []):
            if task.get("taskActionVersion") == "10.6.0":
                visible_action_counts.append(len(task.get("visibleTaskActions") or []))
            if task.get("crossAccountFlowVersion") == "10.5.0":
                projected_task_count += 1
    checks = {
        "v104ImportSync": (import_payload.get("v104ImportTaskSync") or {}).get("version") == "10.4.0",
        "v107OperatingProfile": profile.get("version") == "10.7.0" and profile.get("userConfirmationRequired") is False,
        "v108TagTasks": tag_sync.get("version") == "10.8.0" and tag_sync.get("createdTaskCount", 0) >= 1,
        "roleProjection": projected_task_count >= 1,
        "minimalActions": bool(visible_action_counts) and max(visible_action_counts) <= 2,
    }
    return {"version": V109_ACCEPTANCE_GUARD_VERSION, "checks": checks, "passed": all(checks.values()), "acceptanceChain": V109_ACCEPTANCE_CHAIN}
