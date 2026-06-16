"""Modular product API router package.

Each product module owns its own route file. This package only aggregates those
routers under the shared `/api/modules` prefix so one module can be changed
without editing every other module endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.api.routes.modules import (
    competitor,
    dashboard,
    listing,
    log,
    operating_unit,
    product,
    report,
    todo,
    traffic,
)

router = APIRouter(prefix="/api/modules", tags=["modules"])
router.include_router(dashboard.router)
router.include_router(operating_unit.router)
router.include_router(product.router)
router.include_router(competitor.router)
router.include_router(listing.router)
router.include_router(traffic.router)
router.include_router(report.router)
router.include_router(todo.router)
router.include_router(log.router)
