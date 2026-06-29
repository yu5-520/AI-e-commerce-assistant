"""Task report routes with fail-closed fallback."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

from src.services.account_service import user_id_from_headers
from src.services.alert_detail_service import get_alert_detail_report
from src.services.task_report_service import get_candidate_report, get_task_report

router = APIRouter()
TASK_REPORT_ROUTE_VERSION = "12.8.3"


def request_user_id(request: Request) -> str:
    return user_id_from_headers(request.headers)


def _safe_report(kind: str, entity_id: str, exc: Exception) -> Dict[str, Any]:
    return {
        "id": entity_id,
        "title": "详情报告临时兜底",
        "version": TASK_REPORT_ROUTE_VERSION,
        "reportType": kind,
        "taskStatus": "详情生成异常",
        "failClosed": True,
        "summary": "任务本身仍可处理；详情服务返回结构化兜底，避免页面 500。请检查同一个 task_id 是否已经生成聚合详情报告。",
        "error": str(exc),
        "taskLifecycle": {"stage": "generated", "stageLabel": "生成任务", "nextExpected": "返回任务列表继续处理"},
        "sections": [
            {"title": "下一步", "items": ["返回任务列表", "使用任务卡片摘要先接收或处理", "刷新后重试详情页"]},
            {"title": "排障线索", "items": ["检查 task_id 是否存在于 /api/modules/todo", "检查聚合任务是否带 taskDetailReport", "检查 affectedProducts 是否为空"]},
        ],
        "fallbackRule": "safe fallback 只能兜底，不能作为正常详情页。",
    }


@router.get("/task-reports/tasks/{task_id}")
def task_report(request: Request, task_id: str) -> Dict[str, Any]:
    try:
        report = get_task_report(task_id, user_id=request_user_id(request))
    except Exception as exc:
        return _safe_report("task", task_id, exc)
    if not report:
        raise HTTPException(status_code=404, detail="task report not found")
    return report


@router.get("/task-reports/candidates/{module}/{entity_id}")
def candidate_report(request: Request, module: str, entity_id: str) -> Dict[str, Any]:
    try:
        report = get_candidate_report(module, entity_id, user_id=request_user_id(request))
    except Exception as exc:
        return _safe_report("candidate", f"{module}:{entity_id}", exc)
    if not report:
        raise HTTPException(status_code=404, detail="candidate report not found")
    return report


@router.get("/task-reports/alerts/{alert_id}")
def alert_report(request: Request, alert_id: str) -> Dict[str, Any]:
    try:
        report = get_alert_detail_report(alert_id, user_id=request_user_id(request))
    except Exception as exc:
        return _safe_report("alert", alert_id, exc)
    if not report:
        raise HTTPException(status_code=404, detail="alert report not found")
    return report
