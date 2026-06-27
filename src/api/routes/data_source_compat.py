"""V12.2.8 data source connection compatibility routes.

The web demo calls GET /api/data/source-connections.  A previous route cleanup
kept only /api/data/sources and POST /api/data/source-connections/{id}/sync,
which made the Data page fail closed with 404.  This module restores the GET
contract without changing the import pipeline.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from src.services.data_source_connection_service import list_data_source_connections

router = APIRouter(prefix="/api/data", tags=["data-source-compat"])


@router.get("/source-connections")
def source_connections() -> Dict[str, Any]:
    payload = list_data_source_connections()
    payload["version"] = "12.2.8"
    payload["routeContractRestored"] = True
    payload["rule"] = "V12.2.8：前端数据页使用 GET /api/data/source-connections；该接口必须存在，不能让辅助接口404导致整页停摆。"
    return payload
