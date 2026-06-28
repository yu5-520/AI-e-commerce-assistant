"""Task report service for V12.8.1 lifecycle reports."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from src.services.account_service import get_user
from src.services.module_task_service import find_task, list_tasks
from src.services.task_lifecycle_orchestrator_service import TASK_LIFECYCLE_VERSION, lifecycle_snapshot

REPORT_VERSION = "12.8.1"

ROLE_INSIGHTS = {
    "owner": {"title": "Owner view", "summary": "Focus on budget, margin and accountability.", "focus": ["margin", "budget", "accountability"], "hidden": []},
    "manager": {"title": "Manager view", "summary": "Focus on assignment, progress, recap cycle and RAG candidate quality.", "focus": ["assignment", "progress", "review", "recap", "RAG"], "hidden": []},
    "operator": {"title": "Operator view", "summary": "Focus on what to do, what proof to submit, and what system will recap later.", "focus": ["steps", "evidence", "submission", "recap window"], "hidden": []},
    "finance": {"title": "Finance view", "summary": "Focus on margin, refunds, ad spend and inventory cash.", "focus": ["margin", "refund", "ad spend", "inventory"], "hidden": []},
    "observer": {"title": "Read-only view", "summary": "Focus on status and archive result.", "focus": ["status", "result"], "hidden": []},
}


def _now() -> str:
    return datetime.now().isoformat()


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _apply_role_insight(report: Dict[str, Any], user_id: str | None = None) -> Dict[str, Any]:
    user = get_user(user_id)
    if not user:
        return report
    insight = ROLE_INSIGHTS.get(user.get("roleId"), ROLE_INSIGHTS["observer"])
    report["viewer"] = {"userId": user.get("id"), "name": user.get("name"), "roleName": user.get("roleName"), "insightDepth": user.get("insightDepth"), "permissionNames": user.get("permissionNames", [])}
    report["roleInsight"] = insight
    report["insightDepth"] = user.get("insightDepth")
    return report


def _task_lookup(task_id: str, user_id: str | None = None) -> Dict[str, Any] | None:
    task = next((item for item in list_tasks(active_only=False, viewer_id=user_id) if item.get("id") == task_id), None)
    return task or find_task(task_id)


def _structure_missing_report(task_id: str, user_id: str | None = None, task: Dict[str, Any] | None = None) -> Dict[str, Any]:
    title = (task or {}).get("title") or task_id
    lifecycle = lifecycle_snapshot(task or {"id": task_id, "status": "structure_missing"})
    report = {
        "reportId": f"RPT-STRUCTURE-MISSING-{task_id}",
        "reportType": "structure_missing",
        "version": REPORT_VERSION,
        "lifecycleVersion": TASK_LIFECYCLE_VERSION,
        "module": "task",
        "sourceModule": "task_report_service",
        "sourceRoute": "business-actions",
        "entityId": (task or {}).get("entityId") or (task or {}).get("productId") or task_id,
        "taskId": task_id,
        "taskStatus": (task or {}).get("status") or "structure_missing",
        "generatedAt": _now(),
        "title": f"Task detail pending | {title}",
        "warningSummary": "The task exists but has no complete taskDetailReport. The page returns a structured fallback instead of failing.",
        "riskLevel": (task or {}).get("priority") or "medium",
        "evidence": (task or {}).get("evidencePack") or [],
        "suggestedActions": (task or {}).get("sopSteps") or ["Accept the task", "Submit execution proof", "Wait for system recap"],
        "operationChecklist": (task or {}).get("sopSteps") or ["Check store and product ownership", "Check metric evidence", "Submit execution note"],
        "affectedProducts": (task or {}).get("affectedProducts") or [],
        "affectedProductCount": (task or {}).get("affectedProductCount") or 0,
        "actionAuthorization": (task or {}).get("actionAuthorization"),
        "actionImpactEstimate": (task or {}).get("actionImpactEstimate"),
        "ragBusinessMemory": (task or {}).get("ragBusinessMemory"),
        "taskLifecycle": lifecycle,
        "recapCycles": lifecycle.get("recapCycles") or [],
        "ragCandidate": lifecycle.get("ragCandidate"),
        "nextStep": lifecycle.get("nextExpected") or "Continue from the task queue.",
        "fallbackDetail": True,
        "structureMissing": True,
        "failClosed": False,
        "relatedTask": task,
    }
    return _apply_role_insight(report, user_id)


def _report_from_structured_task(task: Dict[str, Any], task_id: str, user_id: str | None = None) -> Dict[str, Any]:
    detail = dict(task.get("taskDetailReport") or {})
    card = task.get("taskCard") or {}
    title = card.get("title") or task.get("title") or task_id
    lifecycle = lifecycle_snapshot(task)
    detail.setdefault("reportId", f"RPT-TASK-{task_id}")
    detail.setdefault("reportType", "task")
    detail["version"] = REPORT_VERSION
    detail["lifecycleVersion"] = TASK_LIFECYCLE_VERSION
    detail.setdefault("module", "task")
    detail.setdefault("sourceModule", task.get("sourceModule") or "SOP task package")
    detail.setdefault("sourceRoute", task.get("sourceRoute") or "business-actions")
    detail.setdefault("entityId", task.get("entityId") or task.get("productId") or task_id)
    detail.setdefault("taskId", task_id)
    detail["taskStatus"] = task.get("status")
    detail.setdefault("generatedAt", _now())
    detail.setdefault("title", f"Task report | {title}")
    detail.setdefault("warningSummary", task.get("reason") or "Structured task report.")
    detail.setdefault("riskLevel", task.get("priority") or "medium")
    detail["taskCard"] = card
    detail["evidence"] = task.get("evidencePack") or task.get("evidence") or detail.get("evidence") or []
    detail["evidencePack"] = task.get("evidencePack") or detail.get("evidencePack") or []
    detail["sopSteps"] = _as_list(task.get("sopSteps")) or _as_list(detail.get("sopSteps")) or _as_list(detail.get("suggestedActions"))
    detail["suggestedActions"] = _as_list(detail.get("suggestedActions")) or detail["sopSteps"]
    detail["operationChecklist"] = _as_list(detail.get("operationChecklist")) or detail["sopSteps"]
    detail["reviewMetrics"] = task.get("reviewMetrics") or detail.get("reviewMetrics") or {}
    detail["completionGate"] = task.get("completionGate") or detail.get("completionGate") or []
    detail["failureThreshold"] = task.get("failureThreshold") or detail.get("failureThreshold") or {}
    detail["ownership"] = task.get("ownership") or {}
    detail["agentJudgment"] = task.get("agentJudgment") or {}
    detail["actionAuthorization"] = task.get("actionAuthorization") or detail.get("actionAuthorization")
    detail["actionImpactEstimate"] = task.get("actionImpactEstimate") or detail.get("actionImpactEstimate")
    detail["ragBusinessMemory"] = task.get("ragBusinessMemory") or detail.get("ragBusinessMemory")
    detail["affectedProducts"] = task.get("affectedProducts") or detail.get("affectedProducts") or []
    detail["affectedProductCount"] = task.get("affectedProductCount") or len(detail["affectedProducts"])
    detail["batchTask"] = bool(task.get("batchTask"))
    detail["taskClusterVersion"] = task.get("taskClusterVersion") or detail.get("taskClusterVersion")
    detail["taskLifecycle"] = lifecycle
    detail["recapCycles"] = lifecycle.get("recapCycles") or []
    detail["ragCandidate"] = task.get("ragCandidate") or lifecycle.get("ragCandidate")
    detail["autoRecapResult"] = task.get("autoRecapResult")
    detail["relatedTask"] = task
    detail["fallbackDetail"] = False
    detail["structureMissing"] = False
    detail["failClosed"] = False
    return _apply_role_insight(detail, user_id)


def get_candidate_report(module: str, entity_id: str, user_id: str | None = None) -> Dict[str, Any] | None:
    return _structure_missing_report(entity_id, user_id)


def get_task_report(task_id: str, user_id: str | None = None) -> Dict[str, Any] | None:
    task = _task_lookup(task_id, user_id)
    if not task:
        return _structure_missing_report(task_id, user_id)
    if not task.get("taskDetailReport"):
        return _structure_missing_report(task_id, user_id, task)
    return _report_from_structured_task(task, task_id, user_id)
