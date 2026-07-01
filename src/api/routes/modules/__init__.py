"""V16.20 modular product API router package.

Legacy module Agent route is removed from the active module router. Current V16
Agent execution is owned by the product judgment and task mapping mainline, not
by old module-level candidate/playbook endpoints.
"""

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
router.include_router(rag_memory.router)
router.include_router(feedback_flywheel.router)
router.include_router(todo.router)
router.include_router(log.router)
