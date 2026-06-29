"""V12.10 task-chain consistency guards.

This service keeps the stable active-task dedupe fix from V11.2, but it no
longer monkey-patches the task detail report service. V12.9+ owns task detail
through the Repository-aware lifecycle report service, and overriding it with
the old V11.2 signature caused `/api/modules/task-reports/tasks/{task_id}` to
fall into the temporary safe fallback when the route passed `ctx=`.
"""

from __future__ import annotations

from typing import Any, Dict

V112_TASK_CHAIN_FIX_VERSION = "12.10.0"


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

    sourceEvent / alertId / dataVersion are evidence for an existing active
    task, not part of the active task identity. Keeping them out prevents the
    same product/risk/action from creating repeated visible tasks after each
    import.
    """
    from src.services import module_task_service

    entity_type = task.get("entityType") or ("报表" if str(task.get("productId", "")).startswith("R") else "商品")
    entity_id = task.get("entityId") or task.get("productId") or task.get("sourceEntityId") or task.get("id") or "unknown"
    risk_domain = task.get("riskDomain") or module_task_service.infer_domain(task)
    action_type = task.get("actionType") or module_task_service.infer_action(task)
    store_ids = "+".join(task.get("storeIds") or module_task_service.infer_store_ids(task) or ["global"])
    source_family = _stable_task_source(task)
    return ":".join(_stable_text(item) for item in [store_ids, source_family, entity_type, entity_id, risk_domain, action_type])


def apply_v112_task_chain_fix() -> Dict[str, Any]:
    """Patch only stable task dedupe; leave V12.9+ detail reports untouched."""
    from src.services import module_task_service

    module_task_service.build_dedupe_key = stable_build_dedupe_key

    return {
        "version": V112_TASK_CHAIN_FIX_VERSION,
        "taskDedupeKey": "stable_business_identity",
        "taskDetailLookup": "owned_by_v12_9_repository_aware_report_service",
        "routePatch": "disabled_legacy_detail_override",
        "rule": "V12.10：旧 V11.2 详情补丁不再覆盖 get_task_report，避免 ctx 参数不兼容导致详情页兜底。",
    }
