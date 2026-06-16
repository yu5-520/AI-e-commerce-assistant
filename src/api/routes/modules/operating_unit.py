"""Operating unit module route."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/operating-unit")
def operating_unit() -> Dict[str, Any]:
    return {
        "unitName": "家居生活店铺组",
        "platforms": ["淘宝", "拼多多", "抖音小店"],
        "storeCount": 4,
        "dataSources": ["ERP", "CRM"],
        "pendingSources": ["聚水潭", "广告后台"],
    }
