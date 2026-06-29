"""V13.3 clean business station registry.

Only business mainline stations live here. Deprecated files, old hooks and legacy
compatibility routes are registered in Deprecated Station Archive, not in the
main Station Registry.

V13.3 adds Agent-guided task judgment stations. Task snapshots are the formal
entry package before task pool and lifecycle stations.
"""

from __future__ import annotations

from typing import Any, Dict, List

STATION_REGISTRY_VERSION = "13.3.0"

STATIONS: List[Dict[str, Any]] = [
    {
        "stationId": "import_station",
        "stage": "import_uploaded",
        "title": "报表接收站",
        "backendModule": "src.api.routes.data_import",
        "frontendModule": "web_demo/stations/import-station",
        "outputRefPrefix": "import",
        "nextStation": "report_parse_station",
        "stationLine": "external_data_line",
        "stationDomain": "data_ingestion",
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
        "stationLine": "external_data_line",
        "stationDomain": "data_ingestion",
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
        "stationLine": "external_data_line",
        "stationDomain": "data_fact",
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
        "stationLine": "external_data_line",
        "stationDomain": "operating_object",
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
        "stationLine": "external_data_line",
        "stationDomain": "operating_snapshot",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "task_signal_station",
        "stage": "task_signal_ready",
        "title": "任务信号站",
        "backendModule": "src.services.risk_task_service",
        "frontendModule": "web_demo/stations/task-signal-station",
        "outputRefPrefix": "task_signals",
        "nextStation": "rag_context_station",
        "stationLine": "agent_task_judgment_line",
        "stationDomain": "task_signal",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "rag_context_station",
        "stage": "rag_context_ready",
        "title": "RAG参照站",
        "backendModule": "src.services.rag_feedback_loop_service",
        "frontendModule": "web_demo/stations/rag-context-station",
        "outputRefPrefix": "rag_context",
        "nextStation": "agent_judgment_station",
        "stationLine": "agent_task_judgment_line",
        "stationDomain": "rag_context",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "agent_judgment_station",
        "stage": "agent_judgment_ready",
        "title": "Agent判断站",
        "backendModule": "src.stations.agent_enhance_station.service",
        "frontendModule": "web_demo/stations/agent-judgment-station",
        "outputRefPrefix": "agent_judgment",
        "nextStation": "task_snapshot_station",
        "stationLine": "agent_task_judgment_line",
        "stationDomain": "agent_judgment",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "task_snapshot_station",
        "stage": "task_snapshot_ready",
        "title": "任务快照站",
        "backendModule": "src.services.task_snapshot_station_service",
        "frontendModule": "web_demo/stations/task-snapshot-station",
        "outputRefPrefix": "task_snapshot",
        "nextStation": "agent_enhance_station",
        "stationLine": "agent_task_judgment_line",
        "stationDomain": "task_snapshot",
        "replayable": True,
        "diagnosticSupported": True,
    },
    {
        "stationId": "agent_enhance_station",
        "stage": "task_agent_enhanced",
        "title": "Agent增强站",
        "backendModule": "src.stations.agent_enhance_station.service",
        "frontendModule": "web_demo/stations/agent-enhance-station",
        "outputRefPrefix": "task_packages",
        "nextStation": "evidence_station",
        "stationLine": "internal_task_lifecycle_line",
        "stationDomain": "agent_enhance",
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
        "stationLine": "internal_task_lifecycle_line",
        "stationDomain": "task_submission",
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
        "stationLine": "internal_task_lifecycle_line",
        "stationDomain": "auto_recap",
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
        "stationLine": "internal_task_lifecycle_line",
        "stationDomain": "rag_feedback",
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
        "lines": {
            "externalDataLine": [station["stationId"] for station in STATIONS if station.get("stationLine") == "external_data_line"],
            "agentTaskJudgmentLine": [station["stationId"] for station in STATIONS if station.get("stationLine") == "agent_task_judgment_line"],
            "internalTaskLifecycleLine": [station["stationId"] for station in STATIONS if station.get("stationLine") == "internal_task_lifecycle_line"],
        },
        "mainlinePurity": "deprecated_files_excluded",
        "rule": "V13.3：外部数据线到经营快照；任务判断线经RAG、Agent和任务快照；任务生命周期线后续继续拆分。",
    }
