"""V13.7 clean business station registry.

Only business mainline stations live here. V13.7 completes the internal task
lifecycle line: acceptance/assignment, submission/review, recap/RAG feedback are
explicit stations instead of hidden todo-only actions.
"""

from __future__ import annotations

from typing import Any, Dict, List

STATION_REGISTRY_VERSION = "13.7.0"


def station(station_id: str, stage: str, title: str, backend: str, prefix: str, next_station: str | None, line: str, domain: str, *, replayable: bool = True) -> Dict[str, Any]:
    return {
        "stationId": station_id,
        "stage": stage,
        "title": title,
        "backendModule": backend,
        "frontendModule": f"web_demo/stations/{station_id.replace('_', '-')}",
        "outputRefPrefix": prefix,
        "nextStation": next_station,
        "stationLine": line,
        "stationDomain": domain,
        "replayable": replayable,
        "diagnosticSupported": True,
    }


STATIONS: List[Dict[str, Any]] = [
    station("import_station", "import_uploaded", "报表接收站", "src.api.routes.data_import", "import", "report_parse_station", "external_data_line", "data_ingestion", replayable=False),
    station("report_parse_station", "report_parsed", "报表解析站", "src.api.routes.data_import", "rows", "metric_fact_station", "external_data_line", "data_ingestion"),
    station("metric_fact_station", "metric_facts_ready", "指标事实站", "src.services.metric_fact_store_service", "metric_facts", "operating_object_station", "external_data_line", "data_fact"),
    station("operating_object_station", "operating_objects_ready", "商品/店铺映射站", "src.services.operating_object_store_service", "operating_objects", "operating_snapshot_station", "external_data_line", "operating_object"),
    station("operating_snapshot_station", "operating_unit_snapshot_ready", "经营页快照站", "src.services.operating_unit_snapshot_service", "operating_unit_snapshot", "task_signal_station", "external_data_line", "operating_snapshot"),
    station("task_signal_station", "task_signal_ready", "任务信号站", "src.services.risk_task_service", "task_signals", "rag_context_station", "agent_task_judgment_line", "task_signal"),
    station("rag_context_station", "rag_context_ready", "RAG参照站", "src.services.rag_feedback_loop_service", "rag_context", "agent_judgment_station", "agent_task_judgment_line", "rag_context"),
    station("agent_judgment_station", "agent_judgment_ready", "Agent判断站", "src.stations.agent_enhance_station.service", "agent_judgment", "task_snapshot_station", "agent_task_judgment_line", "agent_judgment"),
    station("task_snapshot_station", "task_snapshot_ready", "任务快照站", "src.services.task_snapshot_station_service", "task_snapshot", "task_pool_station", "agent_task_judgment_line", "task_snapshot"),
    station("task_pool_station", "task_pool_entered", "任务入池站", "src.services.task_pool_station_service", "task_pool", "task_acceptance_station", "internal_task_lifecycle_line", "task_pool"),
    station("task_acceptance_station", "task_accepted", "任务接收站", "src.services.task_acceptance_assignment_station_service", "task_acceptance", "task_submission_station", "internal_task_lifecycle_line", "task_acceptance"),
    station("task_assignment_station", "task_assigned", "任务派发站", "src.services.task_acceptance_assignment_station_service", "task_assignment", "task_acceptance_station", "internal_task_lifecycle_line", "task_assignment"),
    station("task_submission_station", "operator_evidence_submitted", "运营提交站", "src.services.task_submission_review_station_service", "submission", "task_review_station", "internal_task_lifecycle_line", "task_submission", replayable=False),
    station("task_review_station", "manager_reviewed", "总管复核站", "src.services.task_submission_review_station_service", "review", "recap_schedule_station", "internal_task_lifecycle_line", "task_review", replayable=False),
    station("recap_schedule_station", "recap_scheduled", "复盘排期站", "src.services.task_recap_rag_station_service", "recap_schedule", "recap_complete_station", "internal_task_lifecycle_line", "recap_schedule"),
    station("recap_complete_station", "system_auto_recap_completed", "系统复盘站", "src.services.task_recap_rag_station_service", "recap", "rag_feedback_station", "internal_task_lifecycle_line", "recap_complete"),
    station("rag_feedback_station", "rag_candidate_ready", "RAG回流站", "src.services.task_recap_rag_station_service", "rag_candidate", None, "internal_task_lifecycle_line", "rag_feedback"),
]


def list_stations() -> List[Dict[str, Any]]:
    return [{**item, "version": STATION_REGISTRY_VERSION, "interface": "/api/stations/{stationId}"} for item in STATIONS]


def get_station(station_id: str) -> Dict[str, Any] | None:
    for item in STATIONS:
        if item["stationId"] == station_id or item["stage"] == station_id:
            return {**item, "version": STATION_REGISTRY_VERSION, "interface": f"/api/stations/{item['stationId']}"}
    return None


def station_by_stage(stage: str) -> Dict[str, Any] | None:
    for item in STATIONS:
        if item["stage"] == stage:
            return get_station(item["stationId"])
    return None


def station_order() -> List[str]:
    return [item["stationId"] for item in STATIONS]


def registry_summary() -> Dict[str, Any]:
    return {
        "version": STATION_REGISTRY_VERSION,
        "stationCount": len(STATIONS),
        "stations": list_stations(),
        "lines": {
            "externalDataLine": [item["stationId"] for item in STATIONS if item.get("stationLine") == "external_data_line"],
            "agentTaskJudgmentLine": [item["stationId"] for item in STATIONS if item.get("stationLine") == "agent_task_judgment_line"],
            "internalTaskLifecycleLine": [item["stationId"] for item in STATIONS if item.get("stationLine") == "internal_task_lifecycle_line"],
        },
        "mainlinePurity": "deprecated_files_excluded",
        "rule": "V13.7：外部数据线、Agent判断线、任务生命周期线已经合并为完整站点闭环。",
    }
