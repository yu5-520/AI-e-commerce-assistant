"""V16.5 split station registry.

Registry is now the source of truth for the MVP-real chain. Each station has one
core responsibility, one output contract and one acceptance boundary.
"""

from __future__ import annotations

from typing import Any, Dict, List

STATION_REGISTRY_VERSION = "16.5"


def station(station_id: str, stage: str, title: str, backend: str, prefix: str, next_station: str | None, line: str, domain: str, *, replayable: bool = True, acceptance: str = "count") -> Dict[str, Any]:
    return {"stationId": station_id, "stage": stage, "title": title, "backendModule": backend, "frontendModule": f"web_demo/stations/{station_id.replace('_', '-')}", "outputRefPrefix": prefix, "nextStation": next_station, "stationLine": line, "stationDomain": domain, "replayable": replayable, "diagnosticSupported": True, "acceptance": acceptance, "version": STATION_REGISTRY_VERSION}


STATIONS: List[Dict[str, Any]] = [
    station("report_receive_station", "report_received", "报表接收站", "src.services.station_alignment_v165_service", "raw_report", "report_schema_station", "real_report_fact_line", "report_receive", replayable=False, acceptance="dataVersion"),
    station("report_schema_station", "report_schema_mapped", "报表结构映射站", "src.services.station_alignment_v165_service", "report_schema_mapping", "report_fact_station", "real_report_fact_line", "report_schema", acceptance="header/date mapping"),
    station("report_fact_station", "report_facts_ready", "报表事实分层站", "src.services.station_alignment_v165_service", "report_fact_namespace", "product_master_station", "real_report_fact_line", "report_fact", acceptance="product/store/traffic namespace"),
    station("product_master_station", "product_master_ready", "商品主档去重站", "src.services.station_alignment_v165_service", "product_master", "product_metric_snapshot_station", "real_report_fact_line", "product_master", acceptance="distinct platform+store+product+sku"),
    station("product_metric_snapshot_station", "product_metric_snapshot_ready", "商品指标快照站", "src.services.station_alignment_v165_service", "product_metric_snapshot", "full_product_bundle_station", "snapshot_bundle_line", "product_metric_snapshot", acceptance="ROI/date/traffic child facts"),
    station("full_product_bundle_station", "full_product_bundle_ready", "商品全量包整合站", "src.services.station_alignment_v165_service", "full_product_bundle", "bundle_validation_station", "snapshot_bundle_line", "full_product_bundle", acceptance="bundleCount = productMasterCount"),
    station("bundle_validation_station", "bundle_validation_ready", "全量包事实验收站", "src.services.station_alignment_v165_service", "validated_full_product_bundle", "product_judgment_agent_station", "snapshot_bundle_line", "bundle_validation", acceptance="factLayerValidation"),
    station("product_judgment_agent_station", "product_judgment_ready", "真实商品判断Agent站", "src.services.station_alignment_v165_service", "product_judgment", "product_judgment_package_station", "agent_judgment_line", "product_judgment_agent", acceptance="coverageRate >= 90%"),
    station("product_judgment_package_station", "product_judgment_package_ready", "商品判断包合并站", "src.services.station_alignment_v165_service", "product_judgment_package", "rag_permission_context_station", "agent_judgment_line", "product_judgment_package", acceptance="package coverage + 70% confidence gate"),
    station("rag_permission_context_station", "rag_permission_context_ready", "RAG权限上下文站", "src.services.station_alignment_v165_service", "rag_permission_context", "task_mapping_agent_station", "task_mapping_line", "rag_permission_context", acceptance="permission/SOP/approval context"),
    station("task_mapping_agent_station", "task_mapping_ready", "真实任务映射Agent站", "src.services.station_alignment_v165_service", "task_generation_decision", "task_pool_admission_station", "task_mapping_line", "task_mapping_agent", acceptance="strict JSON tasks + permission boundary"),
    station("task_pool_admission_station", "task_pool_admitted", "任务池准入站", "src.services.station_alignment_v165_service", "task_pool", "frontend_read_model_station", "task_delivery_line", "task_pool_admission", acceptance="dedupe/limit/current dataVersion"),
    station("frontend_read_model_station", "frontend_read_model_ready", "前端读模型站", "src.services.station_alignment_v165_service", "frontend_read_model", "task_pool_acceptance_station", "task_delivery_line", "frontend_read_model", acceptance="current-run isolated projections"),
    station("task_pool_acceptance_station", "task_pool_acceptance_ready", "本轮任务池验收站", "src.services.station_alignment_v165_service", "task_pool_acceptance", None, "task_delivery_line", "task_pool_acceptance", acceptance="data-line = task_pool = frontend views"),
    station("task_acceptance_station", "task_accepted", "任务接收站", "src.services.task_acceptance_assignment_station_service", "task_acceptance", "task_submission_station", "internal_task_lifecycle_line", "task_acceptance", replayable=False, acceptance="lifecycle transition"),
    station("task_assignment_station", "task_assigned", "任务派发站", "src.services.task_acceptance_assignment_station_service", "task_assignment", "task_acceptance_station", "internal_task_lifecycle_line", "task_assignment", acceptance="assignee permission"),
    station("task_submission_station", "operator_evidence_submitted", "运营提交站", "src.services.task_submission_review_station_service", "submission", "task_review_station", "internal_task_lifecycle_line", "task_submission", replayable=False, acceptance="evidence submitted"),
    station("task_review_station", "manager_reviewed", "总管复核站", "src.services.task_submission_review_station_service", "review", "recap_schedule_station", "internal_task_lifecycle_line", "task_review", replayable=False, acceptance="manager decision"),
    station("recap_schedule_station", "recap_scheduled", "复盘排期站", "src.services.task_recap_rag_station_service", "recap_schedule", "recap_complete_station", "internal_task_lifecycle_line", "recap_schedule", acceptance="recap scheduled"),
    station("recap_complete_station", "system_auto_recap_completed", "系统复盘站", "src.services.task_recap_rag_station_service", "recap", "rag_feedback_station", "internal_task_lifecycle_line", "recap_complete", acceptance="after metrics collected"),
    station("rag_feedback_station", "rag_candidate_ready", "RAG回流站", "src.services.task_recap_rag_station_service", "rag_candidate", None, "internal_task_lifecycle_line", "rag_feedback", acceptance="feedback candidate"),
]

LEGACY_STATION_ALIASES = {
    "import_station": "report_receive_station",
    "report_parse_station": "report_schema_station",
    "metric_fact_station": "report_fact_station",
    "operating_object_station": "product_master_station",
    "operating_snapshot_station": "product_metric_snapshot_station",
    "system_product_snapshot_station": "product_metric_snapshot_station",
    "product_signal_snapshot_station": "full_product_bundle_station",
    "task_signal_station": "full_product_bundle_station",
    "rag_context_station": "rag_permission_context_station",
    "agent_judgment_station": "product_judgment_agent_station",
    "task_snapshot_station": "task_mapping_agent_station",
    "task_pool_station": "task_pool_admission_station",
}


def list_stations() -> List[Dict[str, Any]]:
    return [{**item, "interface": f"/api/stations/{item['stationId']}"} for item in STATIONS]


def get_station(station_id: str) -> Dict[str, Any] | None:
    resolved = LEGACY_STATION_ALIASES.get(station_id, station_id)
    for item in STATIONS:
        if item["stationId"] == resolved or item["stage"] == resolved:
            result = {**item, "interface": f"/api/stations/{item['stationId']}"}
            if resolved != station_id:
                result["legacyAliasFor"] = station_id
            return result
    return None


def station_by_stage(stage: str) -> Dict[str, Any] | None:
    for item in STATIONS:
        if item["stage"] == stage:
            return get_station(item["stationId"])
    return None


def station_order() -> List[str]:
    return [item["stationId"] for item in STATIONS]


def registry_summary() -> Dict[str, Any]:
    return {"version": STATION_REGISTRY_VERSION, "stationCount": len(STATIONS), "stations": list_stations(), "legacyAliases": LEGACY_STATION_ALIASES, "lines": {"realReportFactLine": [item["stationId"] for item in STATIONS if item.get("stationLine") == "real_report_fact_line"], "snapshotBundleLine": [item["stationId"] for item in STATIONS if item.get("stationLine") == "snapshot_bundle_line"], "agentJudgmentLine": [item["stationId"] for item in STATIONS if item.get("stationLine") == "agent_judgment_line"], "taskMappingLine": [item["stationId"] for item in STATIONS if item.get("stationLine") == "task_mapping_line"], "taskDeliveryLine": [item["stationId"] for item in STATIONS if item.get("stationLine") == "task_delivery_line"], "internalTaskLifecycleLine": [item["stationId"] for item in STATIONS if item.get("stationLine") == "internal_task_lifecycle_line"]}, "mainlinePurity": "v16_5_one_station_one_responsibility", "rule": "V16.5：Registry/Contract/Queue/Adapter/Data-line统一；Agent站只做Agent，系统站负责事实、合包、入池、读模型和验收。"}
