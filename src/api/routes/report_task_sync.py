"""V14.1 Report task sync compatibility route."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.core.context import UserContext, get_current_context

router = APIRouter(prefix="/api/data/report-tasks", tags=["report-task-sync"])
REPORT_TASK_SYNC_VERSION = "14.1.0"


@router.post("/sync-current")
def sync_current_report_tasks(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return {
        "version": REPORT_TASK_SYNC_VERSION,
        "mode": "disabled_legacy_report_task_sync",
        "syncedTaskIds": [],
        "syncedTaskCount": 0,
        "ctx": {"tenantId": ctx.tenant_id, "orgId": ctx.org_id, "userId": ctx.user_id},
        "rule": "V14.1：报表任务不再从旧内存任务池同步；可见任务必须来自 task_snapshot_station -> task_pool_station。",
    }
