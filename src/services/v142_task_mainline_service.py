"""V14.3 task generation mainline orchestrator.

The mainline runs full product signal packages in batches. Agent judgment creates
budgeted task snapshots immediately; task lifecycle does not wait for all signal
packages to finish.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.station_contract_service import run_station_contract

V142_TASK_MAINLINE_VERSION = "14.3.0"
V143_TASK_MAINLINE_VERSION = "14.3.0"
DEFAULT_AGENT_BATCH_SIZE = 20


def _count(output: Dict[str, Any], key: str) -> int:
    value = output.get(key)
    try:
        return int(value or 0)
    except Exception:
        return 0


def run_v142_task_mainline(data_version: str, *, user_id: str | None = None, max_signals: int = DEFAULT_AGENT_BATCH_SIZE, force: bool = True, source: str = "v143_mainline") -> Dict[str, Any]:
    batch_size = max(1, int(max_signals or DEFAULT_AGENT_BATCH_SIZE))
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
    return {"version": V143_TASK_MAINLINE_VERSION, "mode": "full_signal_package_rag_budget_agent_queue", "dataVersion": data_version, "source": source, "agentBatchSize": batch_size, "stationRuns": {"operatingSnapshot": operating, "productSnapshot": product_snapshot, "productSignalSnapshot": product_signal, "signal": signal, "rag": rag, "agent": agent, "taskSnapshot": task_snapshot, "taskPool": pool}, "taskGeneration": {"version": V143_TASK_MAINLINE_VERSION, "mode": "full_signal_package_to_budgeted_task_snapshot", "productSnapshotCount": product_snapshot_count, "productSignalPackageCount": product_signal_package_count, "productSignalCount": product_signal_count, "signalCount": signal_count, "judgmentCount": judgment_count, "taskSnapshotCount": task_snapshot_count, "createdTaskCount": created_count, "observeOrNoiseCount": max(judgment_count - task_snapshot_count, 0), "outputs": outputs}, "rule": "V14.3：系统全量生成商品信号包，RAG定义运营价值和预算边界，Agent按批判断；任务一生成就进入快照、预算预占和任务池。"}


def run_v143_task_mainline(data_version: str, *, user_id: str | None = None, max_signals: int = DEFAULT_AGENT_BATCH_SIZE, force: bool = True, source: str = "v143_mainline") -> Dict[str, Any]:
    return run_v142_task_mainline(data_version, user_id=user_id, max_signals=max_signals, force=force, source=source)
