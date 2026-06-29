"""V12.14.1 station adapter service.

Station Contract is the public interface. Adapters are the narrow bridge from a
standard station run to existing internal services. This prevents old routes from
calling business services directly and lets the pipeline become a compatibility
layer around Station Interface.
"""

from __future__ import annotations

from typing import Any, Dict

STATION_ADAPTER_VERSION = "12.14.1"


def _count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ["createdTaskCount", "storeCount", "productCount", "storeRows", "count", "rowCount"]:
            raw = value.get(key)
            if isinstance(raw, int):
                return raw
            if isinstance(raw, list):
                return len(raw)
    return 0


def simulated_station_output(station: Dict[str, Any], body: Dict[str, Any] | None = None, *, diagnostic: bool = False) -> Dict[str, Any]:
    body = body or {}
    data_version = body.get("dataVersion") or body.get("data_version") or ("DIAG-V12-14" if diagnostic else None)
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

    output = simulated_station_output(station, body, diagnostic=False)
    output["adapterMode"] = "contract_only_no_real_adapter"
    output["warning"] = "该站点已纳入Station Interface，但真实业务adapter尚未接管。"
    output["count"] = _count(body)
    return output
