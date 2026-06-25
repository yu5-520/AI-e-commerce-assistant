"""V11.2 task-chain consistency fix.

This service fixes two V11.1 runtime inconsistencies without changing the public API:

1. Todo and task detail must use the same owner/global visibility rule. The owner
   can see all execution tasks in /todo, so opening the same task detail must not
   fall through to the basic fallback report.
2. Active task dedupe must be based on the stable business object and risk domain,
   not on volatile alert_id/data_version/sourceEvent values. New alert/data versions
   are evidence for the existing active task, not separate tasks.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

V112_TASK_CHAIN_FIX_VERSION = "11.2.0"


def _viewer_query_user_id(user_id: str | None) -> str | None:
    """Match /todo owner behavior: owner reads the global queue, others are scoped."""
    if not user_id:
        return None
    from src.services.account_service import get_user

    user = get_user(user_id)
    return None if user and user.get("roleId") == "owner" else user_id


def _stable_text(value: Any, fallback: str = "unknown") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _stable_task_source(task: Dict[str, Any]) -> str:
    """Return a stable source family; never use alertId/dataVersion/sourceEvent."""
    from src.services import module_task_service

    return _stable_text(
        task.get("sourceFamily")
        or task.get("sourceModule")
        or task.get("source")
        or task.get("sourceType")
        or task.get("sourceRoute")
        or module_task_service.infer_source_type(task),
        "task_source",
    )


def stable_build_dedupe_key(task: Dict[str, Any]) -> str:
    """Build a dedupe key from stable business identity instead of volatile events.

    Before V11.2, sourceEvent was often alertId or dataVersion. That made the same
    product/risk/action generate a new task after every import. V11.2 keeps those
    values in evidence/sourceTrail, but excludes them from the active task key.
    """
    from src.services import module_task_service

    entity_type = task.get("entityType") or ("报表" if str(task.get("productId", "")).startswith("R") else "商品")
    entity_id = task.get("entityId") or task.get("productId") or task.get("sourceEntityId") or task.get("id") or "unknown"
    risk_domain = task.get("riskDomain") or module_task_service.infer_domain(task)
    action_type = task.get("actionType") or module_task_service.infer_action(task)
    store_ids = "+".join(task.get("storeIds") or module_task_service.infer_store_ids(task) or ["global"])
    source_family = _stable_task_source(task)
    return ":".join(
        _stable_text(item)
        for item in [store_ids, source_family, entity_type, entity_id, risk_domain, action_type]
    )


def _task_visible_for_detail(task: Dict[str, Any], user_id: str | None) -> bool:
    if not user_id:
        return True
    from src.services.account_service import get_user
    from src.services import module_task_service

    user = get_user(user_id)
    if not user:
        return True
    if user.get("roleId") == "owner":
        return True
    return module_task_service.task_visible_to_viewer(task, user_id)


def _find_task_for_detail(task_id: str, user_id: str | None) -> Dict[str, Any] | None:
    """Find by task id after applying the same query scope used by /todo."""
    from src.services import module_task_service

    query_user_id = _viewer_query_user_id(user_id)
    task = next(
        (item for item in module_task_service.list_tasks(active_only=False, viewer_id=query_user_id) if item.get("id") == task_id),
        None,
    )
    if task:
        return task

    raw_task = module_task_service.find_task(task_id)
    if raw_task and _task_visible_for_detail(raw_task, user_id):
        return deepcopy(raw_task)
    return None


def get_task_report_v112(task_id: str, user_id: str | None = None) -> Dict[str, Any] | None:
    """Task report reader that cannot disagree with /todo visibility."""
    from src.services import task_report_service

    task = _find_task_for_detail(task_id, user_id)
    if not task:
        report = task_report_service._missing_task_report(task_id, user_id)
        report["detailLookup"] = {
            "version": V112_TASK_CHAIN_FIX_VERSION,
            "status": "task_not_visible_or_missing",
            "rule": "任务详情已按 /todo 同口径查询；仍找不到任务时才返回基础兜底。",
        }
        return report

    module = task_report_service._module_from_task(task)
    entity_id = task.get("entityId") or task.get("productId") or task_id
    if module == "report" and str(task.get("productId", "")).startswith("R-"):
        entity_id = str(task["productId"])[2:]

    candidate = task_report_service.get_candidate_report(module, entity_id, user_id=user_id)
    if candidate:
        candidate["reportType"] = "task"
        candidate["taskId"] = task_id
        candidate["taskStatus"] = task.get("status")
        candidate["relatedTask"] = task
        candidate["sourceModule"] = task.get("sourceModule") or candidate["sourceModule"]
        candidate["sourceRoute"] = task.get("sourceRoute") or candidate["sourceRoute"]
        candidate["title"] = f"任务详情报告｜{task.get('productShort') or task.get('title') or task_id}"
        candidate["warningSummary"] = task.get("reason") or candidate["warningSummary"]
        candidate["riskLevel"] = task.get("priority") or candidate["riskLevel"]
        candidate["detailLookup"] = {"version": V112_TASK_CHAIN_FIX_VERSION, "status": "matched_candidate_report"}
        return task_report_service._apply_role_insight(task_report_service._apply_alert_to_report(candidate, task), user_id)

    fallback = task_report_service._fallback_report_from_task(task, task_id, user_id)
    fallback["detailLookup"] = {"version": V112_TASK_CHAIN_FIX_VERSION, "status": "matched_task_fallback"}
    return fallback


def apply_v112_task_chain_fix() -> Dict[str, Any]:
    """Patch the imported service functions used by routes and task creation."""
    from src.services import module_task_service, task_report_service

    module_task_service.build_dedupe_key = stable_build_dedupe_key
    task_report_service.get_task_report = get_task_report_v112

    route_patch = "not_loaded"
    try:
        from src.api.routes.modules import task_report as task_report_route

        task_report_route.get_task_report = get_task_report_v112
        route_patch = "patched"
    except Exception as exc:  # pragma: no cover - defensive startup guard
        route_patch = f"skipped:{type(exc).__name__}"

    return {
        "version": V112_TASK_CHAIN_FIX_VERSION,
        "taskDetailLookup": "todo_visibility_aligned",
        "taskDedupeKey": "stable_business_identity",
        "routePatch": route_patch,
    }
