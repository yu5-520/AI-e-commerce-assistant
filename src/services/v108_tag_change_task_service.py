"""V10.8 tag-change task sync service.

V10.7 builds Agent operating profiles and tag-change candidates. V10.8 turns
those candidates into real task-pool items so users handle tag drift only
through tasks, not manual classification pages.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from src.core.context import UserContext
from src.services.task_repository_write_service import create_task_with_repository

V108_TAG_CHANGE_TASK_VERSION = "10.8.0"
V108_TAG_CHANGE_RULES = [
    "tag_change_candidates_become_tasks",
    "user_intervention_only_through_tasks",
    "agent_profile_snapshot_is_attached_to_task",
    "manager_operator_owner_views_reuse_v10_5_and_v10_6",
    "task_result_can_enter_logs_and_rag_memory_candidate",
]


def _priority(tags: List[str]) -> str:
    if any(tag in tags for tag in ["ROI偏低", "退款风险"]):
        return "高"
    if "高库存低动销" in tags:
        return "中"
    return "低"


def _task_title(candidate: Dict[str, Any]) -> str:
    entity_id = candidate.get("entityId") or "经营对象"
    tags = " / ".join(candidate.get("tags") or [])
    return f"标签变化：{entity_id} · {tags or '经营标签'}"


def _build_task_payload(candidate: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    tags = list(candidate.get("tags") or [])
    product = next((item for item in profile.get("products", []) if item.get("productId") == candidate.get("entityId")), {})
    store_id = product.get("storeId") or candidate.get("storeId") or "S001"
    priority = _priority(tags)
    return {
        "title": _task_title(candidate),
        "productTitle": _task_title(candidate),
        "productId": candidate.get("entityId") or "TAG",
        "entityType": candidate.get("entityType") or "product",
        "entityId": candidate.get("entityId") or "TAG",
        "source": "Agent 经营档案",
        "sourceModule": "Agent 经营档案",
        "sourceRoute": "operating-unit",
        "taskType": "标签变化任务",
        "task": "复核标签变化并处理经营异常",
        "reason": candidate.get("reason") or "经营档案标签发生变化，系统以任务形式提醒处理。",
        "riskDomain": "标签",
        "actionType": "复核",
        "priority": priority,
        "priorityLevel": "danger" if priority == "高" else "warning" if priority == "中" else "good",
        "deadline": "今天" if priority == "高" else "本周内",
        "storeIds": [store_id] if store_id else [],
        "visibleStoreIds": [store_id] if store_id else [],
        "taskLayer": "operator_execution",
        "visibleRoleIds": ["owner", "manager", "operator"],
        "judgmentTags": tags,
        "profileSnapshot": {
            "version": profile.get("version"),
            "tagTypes": profile.get("tagTypes"),
            "product": product,
            "agentContextRule": profile.get("agentContextRule"),
        },
        "agentJudgment": {
            "version": V108_TAG_CHANGE_TASK_VERSION,
            "status": "tag_change_task_generated",
            "summary": "Agent 已将经营档案中的标签变化转成任务，用户只需要按任务处理。",
        },
        "sourceEvent": f"v108:{candidate.get('entityType')}:{candidate.get('entityId')}:{','.join(tags)}",
    }


def sync_tag_change_tasks(result: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    profile = result.get("v107OperatingProfile") or {}
    candidates = list(profile.get("tagChangeTaskCandidates") or [])
    created: List[Dict[str, Any]] = []
    for candidate in candidates[:10]:
        payload = _build_task_payload(candidate, profile)
        write_result = create_task_with_repository(payload, ctx)
        task = write_result.get("task") or {}
        created.append(
            {
                "candidate": candidate,
                "taskId": task.get("id"),
                "status": task.get("status"),
                "workflowStatus": task.get("workflowStatus"),
                "assigneeId": task.get("assigneeId"),
                "reviewerId": task.get("reviewerId"),
                "dedupeHit": bool(task.get("dedupeHit")),
            }
        )
    return {
        "version": V108_TAG_CHANGE_TASK_VERSION,
        "mode": "tag_change_candidates_to_tasks",
        "rules": V108_TAG_CHANGE_RULES,
        "candidateCount": len(candidates),
        "createdTaskCount": len(created),
        "tasks": created,
        "userMessage": f"标签变化已生成 {len(created)} 个任务",
        "nextAction": "前往任务页处理标签变化任务。" if created else "暂无标签变化任务。",
    }


def attach_v108_tag_change_tasks(result: Dict[str, Any], ctx: UserContext) -> Dict[str, Any]:
    payload = deepcopy(result)
    payload["v108TagChangeTaskSync"] = sync_tag_change_tasks(payload, ctx)
    payload["tagChangeTaskSyncVersion"] = V108_TAG_CHANGE_TASK_VERSION
    return payload
