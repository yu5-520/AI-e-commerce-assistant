"""V13.4 station adapter service.

Station Contract is the public interface. Adapters are the narrow bridge from a
standard station run to existing internal services. V13.4 adds a real adapter for
Task Pool Station so task snapshots can enter the visible task pool without
skipping acceptance, assignment, submission or review stations.
"""

from __future__ import annotations

from typing import Any, Dict

STATION_ADAPTER_VERSION = "13.4.0"


def _count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ["createdTaskCount", "storeCount", "productCount", "storeRows", "count", "rowCount", "entryCount"]:
            raw = value.get(key)
            if isinstance(raw, int):
                return raw
            if isinstance(raw, list):
                return len(raw)
    return 0


def simulated_station_output(station: Dict[str, Any], body: Dict[str, Any] | None = None, *, diagnostic: bool = False) -> Dict[str, Any]:
    body = body or {}
    data_version = body.get("dataVersion") or body.get("data_version") or ("DIAG-V13-4" if diagnostic else None)
    output_ref = f"{station.get('outputRefPrefix')}:{data_version or 'latest'}"
    return {
        "version": STATION_ADAPTER_VERSION,
        "adapterMode": "diagnostic_simulated" if diagnostic else "contract_only",
        "stationId": station.get("stationId"),
        "stage": station.get("stage"),
        "dataVersion": data_version,
        "outputRef": output_ref,
        "isDiagnostic": diagnostic,
        "count": 1,
        "rule": "标准站点输出；未接真实adapter时只写契约输出和阀门。",
    }


def run_station_adapter(station: Dict[str, Any], body: Dict[str, Any] | None = None, *, diagnostic: bool = False) -> Dict[str, Any]:
    body = body or {}
    station_id = station.get("stationId")
    if diagnostic:
        return simulated_station_output(station, body, diagnostic=True)

    data_version = body.get("dataVersion") or body.get("data_version")

    if station_id == "operating_snapshot_station":
        from src.services.operating_unit_snapshot_service import materialize_operating_unit_snapshot

        snapshot = materialize_operating_unit_snapshot(user_id=body.get("userId") or body.get("user_id"), data_version=data_version, force=bool(body.get("force", True)))
        return {
            "version": STATION_ADAPTER_VERSION,
            "adapterMode": "real_operating_snapshot",
            "stationId": station_id,
            "stage": station.get("stage"),
            "dataVersion": data_version or (snapshot.get("syncState") or {}).get("latestDataVersion"),
            "snapshotKey": snapshot.get("snapshotKey"),
            "storeRows": len(snapshot.get("storeRows") or []),
            "outputRef": snapshot.get("snapshotKey") or f"operating_unit_snapshot:{data_version or 'latest'}",
            "snapshot": snapshot,
            "isDiagnostic": False,
        }

    if station_id == "task_signal_station":
        from src.services.risk_task_service import generate_risk_tasks_for_signals

        result = generate_risk_tasks_for_signals(data_version=data_version, requester_role_id=body.get("requesterRoleId") or "operator")
        return {
            "version": STATION_ADAPTER_VERSION,
            "adapterMode": "real_task_signal",
            "stationId": station_id,
            "stage": station.get("stage"),
            "dataVersion": data_version,
            "createdTaskCount": result.get("createdTaskCount", 0),
            "strictRiskCreatedTaskCount": result.get("strictRiskCreatedTaskCount", 0),
            "operatingCadenceCreatedTaskCount": result.get("operatingCadenceCreatedTaskCount", 0),
            "outputRef": f"tasks:{data_version or 'latest'}",
            "taskGeneration": result,
            "isDiagnostic": False,
        }

    if station_id == "task_pool_station":
        from src.services.task_pool_station_service import enter_task_pool_from_snapshot, sync_ready_task_snapshots

        task_snapshot_id = body.get("taskSnapshotId") or body.get("task_snapshot_id")
        if task_snapshot_id:
            result = enter_task_pool_from_snapshot(str(task_snapshot_id), created_by=body.get("userId") or body.get("user_id"), force=bool(body.get("force")))
        else:
            result = sync_ready_task_snapshots(data_version=data_version, limit=int(body.get("limit") or 50), created_by=body.get("userId") or body.get("user_id"))
        latest_entry = (result.get("poolEntry") or {}) if isinstance(result.get("poolEntry"), dict) else ((result.get("results") or [{}])[0].get("poolEntry") if result.get("results") else {})
        return {
            "version": STATION_ADAPTER_VERSION,
            "adapterMode": "real_task_pool",
            "stationId": station_id,
            "stage": station.get("stage"),
            "dataVersion": data_version or result.get("dataVersion"),
            "poolEntryId": latest_entry.get("poolEntryId"),
            "taskId": latest_entry.get("taskId"),
            "createdTaskCount": result.get("createdTaskCount", 0),
            "outputRef": f"task_pool:{latest_entry.get('poolEntryId') or data_version or 'latest'}",
            "taskPool": result,
            "isDiagnostic": False,
        }

    output = simulated_station_output(station, body, diagnostic=False)
    output["adapterMode"] = "contract_only_no_real_adapter"
    output["warning"] = "该站点已纳入Station Interface，但真实业务adapter尚未接管。"
    output["count"] = _count(body)
    return output
