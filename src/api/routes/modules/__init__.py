"""Modular product API router package."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.routes.modules import dashboard
from src.api.routes.modules import operating_unit
from src.api.routes.modules import product
from src.api.routes.modules import competitor
from src.api.routes.modules import listing
from src.api.routes.modules import traffic
from src.api.routes.modules import inventory
from src.api.routes.modules import aftersales
from src.api.routes.modules import report_v5 as report
from src.api.routes.modules import task_report
from src.api.routes.modules import agents
from src.api.routes.modules import rag_memory
from src.api.routes.modules import feedback_flywheel
from src.api.routes.modules import todo
from src.api.routes.modules import log

router = APIRouter(prefix="/api/modules", tags=["modules"])
router.include_router(dashboard.router)
router.include_router(operating_unit.router)
router.include_router(product.router)
router.include_router(competitor.router)
router.include_router(listing.router)
router.include_router(traffic.router)
router.include_router(inventory.router)
router.include_router(aftersales.router)
router.include_router(report.router)
router.include_router(task_report.router)
router.include_router(agents.router)
router.include_router(rag_memory.router)
router.include_router(feedback_flywheel.router)
router.include_router(todo.router)
router.include_router(log.router)
