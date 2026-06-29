"""V14.4.2 task generation mainline orchestrator.

Compatibility functions keep older imports working, but the returned contract is
V14.4.2: full product signal packages -> RAG -> Agent -> TaskIntent ->
PermissionEnvelope -> task snapshots -> task pool.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.station_contract_service import run_station_contract

V142_TASK_MAINLINE_VERSION = "14.4.2"
V143_TASK_MAINLINE_VERSION = "14.4.2"
V144_TASK_MAINLINE_VERSION = "14.4.2"
DEFAULT_AGENT_BATCH_SIZE = 20


def _count(output: Dict[str, Any], key: str) -> int:
    value = output.get(key)
    try:
        return int(value or 0)
    except Exception:
        return 0


def _batch_size(max_signals: int | None) -> int:
    requested = int(max_signals or DEFAULT_AGENT_BATCH_SIZE)
    return max(1, min(requested, DEFAULT_AGENT_BATCH_SIZE))


def run_v142_task_mainline(data_version: str, *, user_id: str | None = None, max_signals: int = DEFAULT_AGENT_BATCH_SIZE, force: bool = True, source: str = "v1442_mainline") -> Dict[str, Any]:
    batch_size = _batch_size(max_signals)
    base = {"dataVersion": data_version, "userId": user_id, "maxSignals": batch_size, "force": force, "source": source, "agentBatchSize": batch_size}
    operating = run_station_contract("operating_snapshot_station", {**base, "operatingObjectRef": f"operating_objects:{data_version}", "upstreamStage": "operating_objects_ready"})
    product_snapshot = run_station_contract("system_product_snapshot_station", {**base, "upstreamStage": "operating_unit_snapshot_ready"})
    product_signal = run_station_contract("product_signal_snapshot_station", {**base, "productSnapshotRef": (product_snapshot.get("output") or {}).get("productSnapshotRef"), "upstreamStage": "system_product_snapshot_ready"})
    signal = run_station_contract("task_signal_station", {**base, "productSignalSnapshotRef": (product_signal.get("output") or {}).get("productSignalSnapshotRef"), "upstreamStage": "product_signal_snapshot_ready"})
    rag = run_station_contract("rag_context_station", {**base, "taskSignalRef": (signal.get("output") or {}).get("taskSignalRef"), "limit": batch_size, "upstreamStage": "task_signal_ready"})
    agent = run_station_contract("agent_judgment_station", {**base, "ragContextRef": (rag.get("output") or {}).get("ragContextRef"), "upstreamStage": "rag_context_ready"})
    task_snapshot = run_station_contract("task_snapshot_station", {**base, "limit": batch_size, "upstreamStage": "agent_judgment_ready"})
    pool = run_station_contract("task_pool_station", {**base, "limit": batch_size, "upstreamStage": "task_snapshot_ready"})
    outputs = {"operatingSnapshot": operating.get("output") or {}, "productSnapshot": product_snapshot.get("output") or {}, "productSignalSnapshot": product_signal.get("output") or {}, "signalPool": signal.get("output") or {}, "ragContext": rag.get("output") or {}, "agentJudgment": agent.get("output") or {}, "taskSnapshot": task_snapshot.get("output") or {}, "taskPool": pool.get("output") or {}}
    product_snapshot_count = _count(outputs["productSnapshot"], "productSnapshotCount")
    product_signal_count = _count(outputs["productSignalSnapshot"], "productSignalCount")
    product_signal_package_count = _count(outputs["productSignalSnapshot"], "productSignalPackageCount") or product_signal_count
    signal_count = _count(outputs["signalPool"], "signalCount")
    judgment_count = _count(outputs["agentJudgment"], "judgmentCount")
    task_snapshot_count = _count(outputs["taskSnapshot"], "taskSnapshotCount")
    created_count = _count(outputs["taskPool"], "createdTaskCount")
    return {"version": V144_TASK_MAINLINE_VERSION, "mode": "v1442_task_intent_permission_mainline", "dataVersion": data_version, "source": source, "agentBatchSize": batch_size, "compatibilityFunction": "run_v142_task_mainline", "stationRuns": {"operatingSnapshot": operating, "productSnapshot": product_snapshot, "productSignalSnapshot": product_signal, "signal": signal, "rag": rag, "agent": agent, "taskSnapshot": task_snapshot, "taskPool": pool}, "taskGeneration": {"version": V144_TASK_MAINLINE_VERSION, "mode": "full_signal_package_to_task_intent_permission_task_pool", "productSnapshotCount": product_snapshot_count, "productSignalPackageCount": product_signal_package_count, "productSignalCount": product_signal_count, "signalCount": signal_count, "judgmentCount": judgment_count, "taskSnapshotCount": task_snapshot_count, "createdTaskCount": created_count, "observeOrNoiseCount": max(judgment_count - task_snapshot_count, 0), "outputs": outputs}, "rule": "V14.4.2：导入后主链生成全量信号包，RAG与Agent判断后统一进入TaskIntent和PermissionEnvelope，再生成任务快照与任务池。"}


def run_v143_task_mainline(data_version: str, *, user_id: str | None = None, max_signals: int = DEFAULT_AGENT_BATCH_SIZE, force: bool = True, source: str = "v1442_mainline") -> Dict[str, Any]:
    return run_v142_task_mainline(data_version, user_id=user_id, max_signals=max_signals, force=force, source=source)


def run_v144_task_mainline(data_version: str, *, user_id: str | None = None, max_signals: int = DEFAULT_AGENT_BATCH_SIZE, force: bool = True, source: str = "v1442_mainline") -> Dict[str, Any]:
    return run_v142_task_mainline(data_version, user_id=user_id, max_signals=max_signals, force=force, source=source)
