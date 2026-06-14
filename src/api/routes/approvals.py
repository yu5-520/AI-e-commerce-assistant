"""Approval Center routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from src.services.approval_service import get_task_status_overrides, list_approval_records, update_task_status

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("")
def list_approval_status() -> Dict[str, Dict[str, Any]]:
    return get_task_status_overrides()


@router.get("/records")
def approval_records() -> List[Dict[str, Any]]:
    return list_approval_records()


@router.post("/{task_id}/approve")
def approve_task(task_id: str) -> Dict[str, Any]:
    return update_task_status(task_id=task_id, status="approved")


@router.post("/{task_id}/reject")
def reject_task(task_id: str) -> Dict[str, Any]:
    return update_task_status(task_id=task_id, status="rejected")
