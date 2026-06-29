"""V14.2 task generation mainline orchestrator.

This service is shared by the pipeline route and import hooks. It runs the same
station chain every time so upload, manual debug and UI refresh do not diverge.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.station_contract_service import run_station_contract

V142_TASK_MAINLINE_VERSION = "14.2.0"


def _count(output: Dict[str, Any], key: str) -> int:
    value = output.get(key)
    try:
        return int(value or 0)
    except Exception:
        return 0


def run_v142_task_mainline(data_version: str, *, user_id: str | None = None, max_signals: int = 50, force: bool = True, source: str = "v142_mainline") -> Dict[str, Any]:
    base = {"dataVersion": data_version, "userId": user_id, "maxSignals": max_signals, "force": force, "source": source}
    operating = run_station_contract("operating_snapshot_station", {**base, "operatingObjectRef": f"operating_objects:{data_version}", "upstreamStage": "operating_objects_ready"})
    product_snapshot = run_station_contract("system_product_snapshot_station", {**base, "upstreamStage": "operating_unit_snapshot_ready"})
    product_signal = run_station_contract("product_signal_snapshot_station", {**base, "productSnapshotRef": (product_snapshot.get("output") or {}).get("productSnapshotRef"), "upstreamStage": "system_product_snapshot_ready"})
    signal = run_station_contract("task_signal_station", {**base, "productSignalSnapshotRef": (product_signal.get("output") or {}).get("productSignalSnapshotRef"), "upstreamStage": "product_signal_snapshot_ready"})
    rag = run_station_contract("rag_context_station", {**base, "taskSignalRef": (signal.get("output") or {}).get("taskSignalRef"), "limit": max_signals, "upstreamStage": "task_signal_ready"})
    agent = run_station_contract("agent_judgment_station", {**base, "ragContextRef": (rag.get("output") or {}).get("ragContextRef"), "upstreamStage": "rag_context_ready"})
    task_snapshot = run_station_contract("task_snapshot_station", {**base, "limit": max_signals, "upstreamStage": "agent_judgment_ready"})
    pool = run_station_contract("task_pool_station", {**base, "limit": max_signals, "upstreamStage": "task_snapshot_ready"})
    outputs = {
        "operatingSnapshot": operating.get("output") or {},
        "productSnapshot": product_snapshot.get("output") or {},
        "productSignalSnapshot": product_signal.get("output") or {},
        "signalPool": signal.get("output") or {},
        "ragContext": rag.get("output") or {},
        "agentJudgment": agent.get("output") or {},
        "taskSnapshot": task_snapshot.get("output") or {},
        "taskPool": pool.get("output") or {},
    }
    product_snapshot_count = _count(outputs["productSnapshot"], "productSnapshotCount")
    product_signal_count = _count(outputs["productSignalSnapshot"], "productSignalCount")
    signal_count = _count(outputs["signalPool"], "signalCount")
    judgment_count = _count(outputs["agentJudgment"], "judgmentCount")
    task_snapshot_count = _count(outputs["taskSnapshot"], "taskSnapshotCount")
    created_count = _count(outputs["taskPool"], "createdTaskCount")
    return {
        "version": V142_TASK_MAINLINE_VERSION,
        "mode": "snapshot_product_signal_rag_agent_task_mainline",
        "dataVersion": data_version,
        "source": source,
        "stationRuns": {"operatingSnapshot": operating, "productSnapshot": product_snapshot, "productSignalSnapshot": product_signal, "signal": signal, "rag": rag, "agent": agent, "taskSnapshot": task_snapshot, "taskPool": pool},
        "taskGeneration": {"version": V142_TASK_MAINLINE_VERSION, "mode": "system_snapshot_to_signal_snapshot_to_agent", "productSnapshotCount": product_snapshot_count, "productSignalCount": product_signal_count, "signalCount": signal_count, "judgmentCount": judgment_count, "taskSnapshotCount": task_snapshot_count, "createdTaskCount": created_count, "observeOrNoiseCount": max(judgment_count - task_snapshot_count, 0), "outputs": outputs},
        "rule": "V14.2：商品模块可见的系统商品快照先固化，再比对成商品信号快照，最后进入RAG和Agent判断。",
    }
