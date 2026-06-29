"""V14 station adapter service.

Station Contract is the public interface. Adapters are the narrow bridge from a
standard station run to internal services. V14 turns the task generation mainline
from rule-direct task creation into Signal Pool -> RAG Context -> Agent Judgment ->
Task Snapshot -> Task Pool.
"""

from __future__ import annotations

from typing import Any, Dict

STATION_ADAPTER_VERSION = "14.0.0"


def _count(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in [
            "createdTaskCount",
            "taskSnapshotCount",
            "judgmentCount",
            "matchedContextCount",
            "signalCount",
            "storeCount",
            "productCount",
            "storeRows",
            "count",
            "rowCount",
            "entryCount",
        ]:
            raw = value.get(key)
            if isinstance(raw, int):
                return raw
            if isinstance(raw, list):
                return len(raw)
    return 0


def simulated_station_output(station: Dict[str, Any], body: Dict[str, Any] | None = None, *, diagnostic: bool = False) -> Dict[str, Any]:
    body = body or {}
    data_version = body.get("dataVersion") or body.get("data_version") or ("DIAG-V14" if diagnostic else None)
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
        from src.services.signal_pool_service import generate_signal_pool

        result = generate_signal_pool(data_version=data_version, max_signals=int(body.get("maxSignals") or 200))
        return {
            "version": STATION_ADAPTER_VERSION,
            "adapterMode": "real_signal_pool_no_task_creation",
            "stationId": station_id,
            "stage": station.get("stage"),
            "dataVersion": data_version,
            "signalCount": result.get("signalCount", 0),
            "taskSignalRef": result.get("taskSignalRef"),
            "createdTaskCount": 0,
            "outputRef": result.get("outputRef") or f"signal_pool:{data_version or 'latest'}",
            "signalPool": result,
            "isDiagnostic": False,
            "rule": "V14：信号站只生成signal_pool，不再直接生成任务。",
        }

    if station_id == "rag_context_station":
        from src.services.rag_context_station_service import build_rag_context_snapshot

        result = build_rag_context_snapshot(data_version=data_version, signal_ref=body.get("taskSignalRef") or body.get("signalRef"), limit=int(body.get("limit") or 200))
        return {
            "version": STATION_ADAPTER_VERSION,
            "adapterMode": "real_rag_context",
            "stationId": station_id,
            "stage": station.get("stage"),
            "dataVersion": data_version,
            "matchedContextCount": result.get("matchedContextCount", 0),
            "ragContextRef": result.get("ragContextRef"),
            "outputRef": result.get("outputRef") or f"rag_context:{data_version or 'latest'}",
            "ragContext": result,
            "isDiagnostic": False,
        }

    if station_id == "agent_judgment_station":
        from src.services.agent_judgment_station_service import run_agent_judgment_station

        result = run_agent_judgment_station(data_version=data_version, rag_context_ref=body.get("ragContextRef"), max_signals=int(body.get("maxSignals") or 32))
        return {
            "version": STATION_ADAPTER_VERSION,
            "adapterMode": "real_agent_judgment",
            "stationId": station_id,
            "stage": station.get("stage"),
            "dataVersion": data_version,
            "decision": "mixed" if result.get("judgmentCount") else "no_signals",
            "confidence": max([float(item.get("confidence") or 0) for item in result.get("judgments") or []], default=0),
            "judgmentCount": result.get("judgmentCount", 0),
            "pendingTaskSnapshotCount": result.get("pendingTaskSnapshotCount", 0),
            "agentJudgmentRef": result.get("agentJudgmentRef"),
            "outputRef": result.get("outputRef") or f"agent_judgment:{data_version or 'latest'}",
            "agentJudgment": result,
            "isDiagnostic": False,
        }

    if station_id == "task_snapshot_station":
        from src.services.agent_judgment_station_service import materialize_task_snapshots_from_judgments
        from src.services.task_snapshot_station_service import create_task_snapshot

        if body.get("agentJudgment") or body.get("taskPlan"):
            snapshot = create_task_snapshot(body, created_by=body.get("userId") or body.get("user_id"))
            result = {"taskSnapshotCount": 1, "snapshots": [snapshot], "outputRef": f"task_snapshot:{snapshot.get('taskSnapshotId')}"}
        else:
            result = materialize_task_snapshots_from_judgments(data_version=data_version, created_by=body.get("userId") or body.get("user_id"), limit=int(body.get("limit") or 50))
        latest_snapshot = (result.get("snapshots") or [{}])[0]
        return {
            "version": STATION_ADAPTER_VERSION,
            "adapterMode": "real_task_snapshot",
            "stationId": station_id,
            "stage": station.get("stage"),
            "dataVersion": data_version,
            "taskSnapshotId": latest_snapshot.get("taskSnapshotId"),
            "decision": latest_snapshot.get("decision") or "none",
            "status": latest_snapshot.get("status") or "empty",
            "taskSnapshotCount": result.get("taskSnapshotCount", 0),
            "outputRef": result.get("outputRef") or f"task_snapshot:{data_version or 'latest'}",
            "taskSnapshot": result,
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
            "adapterMode": "real_task_pool_from_snapshots_only",
            "stationId": station_id,
            "stage": station.get("stage"),
            "dataVersion": data_version or result.get("dataVersion"),
            "poolEntryId": latest_entry.get("poolEntryId"),
            "taskId": latest_entry.get("taskId"),
            "createdTaskCount": result.get("createdTaskCount", 0),
            "outputRef": f"task_pool:{latest_entry.get('poolEntryId') or data_version or 'latest'}",
            "taskPool": result,
            "isDiagnostic": False,
            "rule": "V14：任务池只消费任务快照，不接受旧规则直出任务。",
        }

    output = simulated_station_output(station, body, diagnostic=False)
    output["adapterMode"] = "contract_only_no_real_adapter"
    output["warning"] = "该站点已纳入Station Interface，但真实业务adapter尚未接管。"
    output["count"] = _count(body)
    return output
