"""V14.5.1 compact task generation mainline orchestrator.

The mainline still runs all stations, but it returns only counters and refs to API
callers. Heavy station payloads stay in storage and station tables.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.station_contract_service import run_station_contract

V142_TASK_MAINLINE_VERSION = "14.5.1"
V143_TASK_MAINLINE_VERSION = "14.5.1"
V144_TASK_MAINLINE_VERSION = "14.5.1"
DEFAULT_AGENT_BATCH_SIZE = 20


def _count(output: Dict[str, Any], key: str) -> int:
    try:
        return int(output.get(key) or 0)
    except Exception:
        return 0


def _ref(output: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = output.get(key)
        if value:
            return value
    return None


def _batch_size(max_signals: int | None) -> int:
    requested = int(max_signals or DEFAULT_AGENT_BATCH_SIZE)
    return max(1, min(requested, DEFAULT_AGENT_BATCH_SIZE))


def _station_summary(run: Dict[str, Any], *, keys: list[str]) -> Dict[str, Any]:
    output = run.get("output") or {}
    summary = {"status": run.get("status") or run.get("handoffStatus") or "completed"}
    for key in keys:
        if key in output:
            summary[key] = output.get(key)
    for key in ["outputRef", "productSnapshotRef", "productSignalSnapshotRef", "taskSignalRef", "ragContextRef", "agentJudgmentRef"]:
        if output.get(key):
            summary[key] = output.get(key)
    return summary


def run_v142_task_mainline(data_version: str, *, user_id: str | None = None, max_signals: int = DEFAULT_AGENT_BATCH_SIZE, force: bool = True, source: str = "v1451_mainline") -> Dict[str, Any]:
    batch_size = _batch_size(max_signals)
    base = {"dataVersion": data_version, "userId": user_id, "maxSignals": batch_size, "force": force, "source": source, "agentBatchSize": batch_size}
    operating = run_station_contract("operating_snapshot_station", {**base, "operatingObjectRef": f"operating_objects:{data_version}", "upstreamStage": "operating_objects_ready"})
    product_snapshot = run_station_contract("system_product_snapshot_station", {**base, "upstreamStage": "operating_unit_snapshot_ready"})
    product_snapshot_output = product_snapshot.get("output") or {}
    product_signal = run_station_contract("product_signal_snapshot_station", {**base, "productSnapshotRef": product_snapshot_output.get("productSnapshotRef"), "upstreamStage": "system_product_snapshot_ready"})
    product_signal_output = product_signal.get("output") or {}
    signal = run_station_contract("task_signal_station", {**base, "productSignalSnapshotRef": product_signal_output.get("productSignalSnapshotRef"), "upstreamStage": "product_signal_snapshot_ready"})
    signal_output = signal.get("output") or {}
    rag = run_station_contract("rag_context_station", {**base, "taskSignalRef": signal_output.get("taskSignalRef"), "limit": batch_size, "upstreamStage": "task_signal_ready"})
    rag_output = rag.get("output") or {}
    agent = run_station_contract("agent_judgment_station", {**base, "ragContextRef": rag_output.get("ragContextRef") or rag_output.get("outputRef"), "upstreamStage": "rag_context_ready"})
    task_snapshot = run_station_contract("task_snapshot_station", {**base, "limit": batch_size, "upstreamStage": "agent_judgment_ready"})
    pool = run_station_contract("task_pool_station", {**base, "limit": batch_size, "upstreamStage": "task_snapshot_ready"})
    outputs = {
        "productSnapshot": product_snapshot_output,
        "productSignalSnapshot": product_signal_output,
        "signalPool": signal_output,
        "ragContext": rag_output,
        "agentJudgment": agent.get("output") or {},
        "taskSnapshot": task_snapshot.get("output") or {},
        "taskPool": pool.get("output") or {},
    }
    product_snapshot_count = _count(outputs["productSnapshot"], "productSnapshotCount")
    product_signal_count = _count(outputs["productSignalSnapshot"], "productSignalCount")
    product_signal_package_count = _count(outputs["productSignalSnapshot"], "productSignalPackageCount") or product_signal_count
    signal_count = _count(outputs["signalPool"], "signalCount")
    judgment_count = _count(outputs["agentJudgment"], "judgmentCount")
    task_snapshot_count = _count(outputs["taskSnapshot"], "taskSnapshotCount")
    created_count = _count(outputs["taskPool"], "createdTaskCount")
    refs = {
        "productSnapshotRef": _ref(outputs["productSnapshot"], "productSnapshotRef", "outputRef"),
        "productSignalSnapshotRef": _ref(outputs["productSignalSnapshot"], "productSignalSnapshotRef", "outputRef"),
        "taskSignalRef": _ref(outputs["signalPool"], "taskSignalRef", "outputRef"),
        "ragContextRef": _ref(outputs["ragContext"], "ragContextRef", "outputRef"),
        "agentJudgmentRef": _ref(outputs["agentJudgment"], "agentJudgmentRef", "outputRef"),
        "taskSnapshotRef": _ref(outputs["taskSnapshot"], "outputRef"),
        "taskPoolRef": _ref(outputs["taskPool"], "outputRef"),
    }
    station_summaries = {
        "operatingSnapshot": _station_summary(operating, keys=["storeCount", "productCount"]),
        "productSnapshot": _station_summary(product_snapshot, keys=["productSnapshotCount", "productCount"]),
        "productSignalSnapshot": _station_summary(product_signal, keys=["productSignalPackageCount", "productSignalCount", "signalCount"]),
        "signal": _station_summary(signal, keys=["signalCount", "productSignalCount"]),
        "rag": _station_summary(rag, keys=["contextCount", "signalCount"]),
        "agent": _station_summary(agent, keys=["judgmentCount", "pendingTaskSnapshotCount"]),
        "taskSnapshot": _station_summary(task_snapshot, keys=["taskSnapshotCount"]),
        "taskPool": _station_summary(pool, keys=["candidateSnapshotCount", "createdTaskCount"]),
    }
    return {
        "version": V144_TASK_MAINLINE_VERSION,
        "mode": "v1451_compact_mainline",
        "dataVersion": data_version,
        "source": source,
        "agentBatchSize": batch_size,
        "taskGeneration": {
            "version": V144_TASK_MAINLINE_VERSION,
            "mode": "compact_counts_and_refs",
            "productSnapshotCount": product_snapshot_count,
            "productSignalPackageCount": product_signal_package_count,
            "productSignalCount": product_signal_count,
            "signalCount": signal_count,
            "judgmentCount": judgment_count,
            "taskSnapshotCount": task_snapshot_count,
            "createdTaskCount": created_count,
            "observeOrNoiseCount": max(judgment_count - task_snapshot_count, 0),
            "refs": refs,
            "stations": station_summaries,
        },
        "refs": refs,
        "rule": "V14.5.1：主链返回计数和引用，完整站点包只留在后端存储。",
    }


def run_v143_task_mainline(data_version: str, *, user_id: str | None = None, max_signals: int = DEFAULT_AGENT_BATCH_SIZE, force: bool = True, source: str = "v1451_mainline") -> Dict[str, Any]:
    return run_v142_task_mainline(data_version, user_id=user_id, max_signals=max_signals, force=force, source=source)


def run_v144_task_mainline(data_version: str, *, user_id: str | None = None, max_signals: int = DEFAULT_AGENT_BATCH_SIZE, force: bool = True, source: str = "v1451_mainline") -> Dict[str, Any]:
    return run_v142_task_mainline(data_version, user_id=user_id, max_signals=max_signals, force=force, source=source)
