"""Clean Agent Enhance Station module.

This module is intentionally small in V12.14.2. It gives the main Station
Registry a clean backend module so deprecated V12.11/V12.12 monkey-patch files no
longer sit inside the business station list. Real RAG/LLM enhancement logic will
be migrated here behind an explicit station adapter in a later release.
"""

from __future__ import annotations

from typing import Any, Dict

AGENT_ENHANCE_STATION_VERSION = "12.14.2"


def health() -> Dict[str, Any]:
    return {
        "version": AGENT_ENHANCE_STATION_VERSION,
        "stationId": "agent_enhance_station",
        "status": "healthy",
        "mode": "clean_station_shell",
        "rule": "旧 RAG/LLM monkey-patch 文件已进入 Deprecated Station Archive；本站仅保留干净站点壳。",
    }


def run(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = payload or {}
    data_version = payload.get("dataVersion") or payload.get("data_version")
    return {
        "version": AGENT_ENHANCE_STATION_VERSION,
        "stationId": "agent_enhance_station",
        "dataVersion": data_version,
        "enhancedTaskCount": 0,
        "outputRef": f"task_packages:{data_version or 'latest'}",
        "mode": "contract_only_pending_real_adapter",
        "rule": "Agent增强真实逻辑后续迁移到本站 adapter；当前不允许通过旧全局补丁进入主路。",
    }
