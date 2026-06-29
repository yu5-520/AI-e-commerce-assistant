"""V12.14 station registry.

A station is an independently addressable pipeline module. External callers must
use the Station Interface instead of importing station internals. The current
release keeps the implementation in a modular monolith, but standardizes station
identity, stage mapping, order, health and replay metadata.
"""

from __future__ import annotations

from typing import Any, Dict, List

STATION_REGISTRY_VERSION = "12.14.0"

STATIONS: List[Dict[str, Any]] = [
    {
        "stationId": "import_station",
        "stage": "import_uploaded",
        "title": "报表接收站",
        "backendModule": "src.api.routes.data_import",
        "frontendModule": "web_demo/stations/import-station",
        "outputRefPrefix": "import",
        "nextStation": "report_parse_station",
        "replayable": False,
        "diagnosticSupported": True,
    },
    {
        "stationId": "report_parse_station",
        "stage": "report_parsed",
        "title": "报表解析站",
        "backendModule": "src.api.routes.data_import",
        "frontendModule": "web_demo/stations/report-parse-station",
        "outputRefPrefix": "rows",
        "nextStation": "metric_fact_station",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "metric_fact_station",
        "stage": "metric_facts_ready",
        "title": "指标事实站",
        "backendModule": "src.services.metric_fact_store_service",
        "frontendModule": "web_demo/stations/metric-fact-station",
        "outputRefPrefix": "metric_facts",
        "nextStation": "operating_object_station",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "operating_object_station",
        "stage": "operating_objects_ready",
        "title": "商品/店铺映射站",
        "backendModule": "src.services.operating_object_store_service",
        "frontendModule": "web_demo/stations/operating-object-station",
        "outputRefPrefix": "operating_objects",
        "nextStation": "operating_snapshot_station",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "operating_snapshot_station",
        "stage": "operating_unit_snapshot_ready",
        "title": "经营页快照站",
        "backendModule": "src.services.operating_unit_snapshot_service",
        "frontendModule": "web_demo/stations/snapshot-station",
        "outputRefPrefix": "operating_unit_snapshot",
        "nextStation": "task_signal_station",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "task_signal_station",
        "stage": "task_signal_ready",
        "title": "任务信号站",
        "backendModule": "src.services.risk_task_service",
        "frontendModule": "web_demo/stations/task-signal-station",
        "outputRefPrefix": "tasks",
        "nextStation": "agent_enhance_station",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "agent_enhance_station",
        "stage": "task_agent_enhanced",
        "title": "Agent增强站",
        "backendModule": "src.services.v1212_rag_llm_agent_service",
        "frontendModule": "web_demo/stations/agent-enhance-station",
        "outputRefPrefix": "task_packages",
        "nextStation": "evidence_station",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "evidence_station",
        "stage": "operator_evidence_submitted",
        "title": "运营提交站",
        "backendModule": "src.services.task_evidence_service",
        "frontendModule": "web_demo/stations/evidence-station",
        "outputRefPrefix": "evidence",
        "nextStation": "auto_recap_station",
        "replayable": False,
        "diagnosticSupported": True,
    },
    {
        "stationId": "auto_recap_station",
        "stage": "system_auto_recap_completed",
        "title": "系统复盘站",
        "backendModule": "src.services.task_recap_scheduler_service",
        "frontendModule": "web_demo/stations/auto-recap-station",
        "outputRefPrefix": "recap",
        "nextStation": "rag_feedback_station",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "rag_feedback_station",
        "stage": "rag_candidate_ready",
        "title": "RAG回流站",
        "backendModule": "src.services.rag_feedback_loop_service",
        "frontendModule": "web_demo/stations/rag-feedback-station",
        "outputRefPrefix": "rag_candidate",
        "nextStation": None,
        "replayable": True,
        "diagnosticSupported": True,
    },
]


def list_stations() -> List[Dict[str, Any]]:
    return [{**station, "version": STATION_REGISTRY_VERSION, "interface": "/api/stations/{stationId}"} for station in STATIONS]


def get_station(station_id: str) -> Dict[str, Any] | None:
    for station in STATIONS:
        if station["stationId"] == station_id or station["stage"] == station_id:
            return {**station, "version": STATION_REGISTRY_VERSION, "interface": f"/api/stations/{station['stationId']}"}
    return None


def station_by_stage(stage: str) -> Dict[str, Any] | None:
    for station in STATIONS:
        if station["stage"] == stage:
            return get_station(station["stationId"])
    return None


def station_order() -> List[str]:
    return [station["stationId"] for station in STATIONS]


def registry_summary() -> Dict[str, Any]:
    return {
        "version": STATION_REGISTRY_VERSION,
        "stationCount": len(STATIONS),
        "stations": list_stations(),
        "rule": "每个站点独立注册，前后端只通过标准 Station Interface 和 pipeline gate 交接。",
    }
