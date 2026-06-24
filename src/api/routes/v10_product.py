"""V10 task-driven product routes."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.core.context import UserContext, get_current_context
from src.services.v100_task_driven_product_service import task_driven_product_summary

router = APIRouter(prefix="/api/architecture", tags=["architecture-v10-product"])


@router.get("/v10/task-driven-product")
async def v100_task_driven_product(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    return task_driven_product_summary(ctx)


@router.get("/v10/readiness")
async def v100_readiness_index(ctx: UserContext = Depends(get_current_context)) -> Dict[str, Any]:
    product = task_driven_product_summary(ctx)
    return {
        "version": "10.9.0",
        "status": "v10_9_task_driven_acceptance_guard_ready",
        "entries": {"taskDrivenProduct": "/api/architecture/v10/task-driven-product", "health": "/api/health", "modules": "/api/modules", "accounts": "/api/accounts"},
        "principle": "用户只完成任务，系统和 Agent 自动完成理解、分类、标签、流转、同步和留痕。",
        "minimalNavigation": product["minimalNavigation"],
        "navigationRouteMap": product["navigationRouteMap"],
        "collapsedOperationRoutes": product["collapsedOperationRoutes"],
        "frontendLayoutRules": product["frontendLayoutRules"],
        "uiProductizationRules": product["uiProductizationRules"],
        "dashboardWorkbenchSections": product["dashboardWorkbenchSections"],
        "dashboardRules": product["dashboardRules"],
        "importTaskFlow": product["importTaskFlow"],
        "importRefreshContract": product["importRefreshContract"],
        "crossAccountFlow": product["crossAccountFlow"],
        "roleViewRules": product["roleViewRules"],
        "taskActionRules": product["taskActionRules"],
        "operatingProfileRules": product["operatingProfileRules"],
        "operatingProfileTagTypes": product["operatingProfileTagTypes"],
        "operatingProfileSurfaces": product["operatingProfileSurfaces"],
        "tagChangeTaskRules": product["tagChangeTaskRules"],
        "tagChangeTaskFlow": product["tagChangeTaskFlow"],
        "acceptanceGuard": product["acceptanceGuard"],
        "acceptanceChain": product["acceptanceChain"],
        "acceptanceRules": product["acceptanceRules"],
        "blockingFailures": product["blockingFailures"],
        "taskTypes": product["taskTypes"],
        "auditMeta": ctx.audit_meta(),
    }
