"""V16.5 split station adapter service.

The adapter now routes each Station ID to one narrow station function. It keeps a
small legacy fallback, but the V16.5 registry/queue use the split station IDs.
"""

from __future__ import annotations

from typing import Any, Callable, Dict

STATION_ADAPTER_VERSION = "16.5"
DEFAULT_AGENT_BATCH_SIZE = 160


def _count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ["createdTaskCount", "taskSnapshotCount", "judgmentCount", "rawJudgmentCount", "productJudgmentPackageCount", "identityGapCount", "taskDecisionCount", "matchedContextCount", "productSignalPackageCount", "productSignalCount", "productSnapshotCount", "signalCount", "storeRows", "count", "rowCount"]:
            raw = value.get(key)
            if isinstance(raw, int):
                return raw
            if isinstance(raw, list):
                return len(raw)
    return 0


def _call_alignment(function_name: str, *, data_version: str | None, user_id: str | None, body: Dict[str, Any]) -> Dict[str, Any]:
    import src.services.station_alignment_v165_service as alignment
    fn: Callable[..., Dict[str, Any]] = getattr(alignment, function_name)
    kwargs = dict(body or {})
    kwargs.pop("dataVersion", None)
    kwargs.pop("data_version", None)
    kwargs.pop("userId", None)
    kwargs.pop("user_id", None)
    if "maxSignals" in kwargs and "max_signals" not in kwargs:
        kwargs["max_signals"] = kwargs.pop("maxSignals")
    return fn(data_version=data_version, user_id=user_id, **kwargs)


def _refresh_read_model(station_id: str, data_version: str | None, output: Dict[str, Any]) -> Dict[str, Any] | None:
    if station_id in {"product_signal_snapshot_station", "full_product_bundle_station", "task_pool_admission_station", "frontend_read_model_station"}:
        try:
            from src.services.frontend_read_model_service import refresh_after_station
            return refresh_after_station(station_id=station_id, data_version=data_version, output=output)
        except Exception as exc:
            return {"status": "read_model_refresh_failed", "error": str(exc), "rule": "Read model refresh failure must not fail station compute."}
    return None


def simulated_station_output(station: Dict[str, Any], body: Dict[str, Any] | None = None, *, diagnostic: bool = False) -> Dict[str, Any]:
    body = body or {}
    data_version = body.get("dataVersion") or body.get("data_version") or ("DIAG-V16.5" if diagnostic else None)
    output_ref = f"{station.get('outputRefPrefix')}:{data_version or 'latest'}"
    return {"version": STATION_ADAPTER_VERSION, "adapterMode": "diagnostic_simulated" if diagnostic else "contract_only", "stationId": station.get("stationId"), "stage": station.get("stage"), "dataVersion": data_version, "outputRef": output_ref, "isDiagnostic": diagnostic, "count": 1, "rule": "standard station output"}


ALIGNMENT_FUNCTIONS = {
    "report_receive_station": "report_receive_station",
    "report_schema_station": "report_schema_station",
    "report_fact_station": "report_fact_station",
    "product_master_station": "product_master_station",
    "product_metric_snapshot_station": "product_metric_snapshot_station",
    "full_product_bundle_station": "full_product_bundle_station",
    "bundle_validation_station": "bundle_validation_station",
    "product_judgment_agent_station": "product_judgment_agent_station",
    "product_judgment_package_station": "product_judgment_package_station",
    "rag_permission_context_station": "rag_permission_context_station",
    "task_mapping_agent_station": "task_mapping_agent_station",
    "task_pool_admission_station": "task_pool_admission_station",
    "frontend_read_model_station": "frontend_read_model_station",
    "task_pool_acceptance_station": "task_pool_acceptance_station",
}


def run_station_adapter(station: Dict[str, Any], body: Dict[str, Any] | None = None, *, diagnostic: bool = False) -> Dict[str, Any]:
    body = body or {}
    station_id = station.get("stationId")
    if diagnostic:
        return simulated_station_output(station, body, diagnostic=True)

    data_version = body.get("dataVersion") or body.get("data_version")
    user_id = body.get("userId") or body.get("user_id")

    if station_id in ALIGNMENT_FUNCTIONS:
        result = _call_alignment(ALIGNMENT_FUNCTIONS[station_id], data_version=data_version, user_id=user_id, body=body)
        result.setdefault("version", STATION_ADAPTER_VERSION)
        result["adapterMode"] = f"real_v165_split_{station_id}"
        result.setdefault("stationId", station_id)
        result.setdefault("stage", station.get("stage"))
        result.setdefault("dataVersion", data_version)
        result.setdefault("outputRef", f"{station.get('outputRefPrefix')}:{data_version or 'latest'}")
        refresh = _refresh_read_model(station_id, data_version, result)
        if refresh is not None:
            result["readModelRefresh"] = refresh
        return result

    if station_id == "task_acceptance_station":
        from src.services.task_acceptance_assignment_station_service import accept_task
        task_id = body.get("taskId") or body.get("task_id")
        return accept_task(str(task_id), user_id=user_id) if task_id else simulated_station_output(station, body)

    if station_id == "task_assignment_station":
        from src.services.task_acceptance_assignment_station_service import assign_task
        task_id = body.get("taskId") or body.get("task_id")
        assignee_id = body.get("assigneeId") or body.get("assignee_id")
        return assign_task(str(task_id), str(assignee_id), user_id=user_id) if task_id and assignee_id else simulated_station_output(station, body)

    if station_id in {"task_submission_station", "task_review_station", "recap_schedule_station", "recap_complete_station", "rag_feedback_station"}:
        output = simulated_station_output(station, body, diagnostic=False)
        output["adapterMode"] = "lifecycle_station_contract_placeholder"
        output["rule"] = "Lifecycle stations remain isolated from task-generation station alignment."
        output["count"] = _count(body)
        return output

    output = simulated_station_output(station, body, diagnostic=False)
    output["adapterMode"] = "contract_only_no_real_adapter"
    output["warning"] = "station is registered but not connected to a real adapter"
    output["count"] = _count(body)
    return output
