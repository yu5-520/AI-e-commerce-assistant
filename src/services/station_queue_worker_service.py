"""V14.6.2 background station queue worker.

The worker consumes station_queue outside user upload requests. V14.6.2 keeps the
worker conservative, but the queue itself now prioritizes mature task snapshots
and task pool entries through a fast lane.
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime
from typing import Any, Dict

from src.services.station_queue_service import STATION_QUEUE_VERSION, queue_summary, run_next_station_job

STATION_QUEUE_WORKER_VERSION = "14.6.2"

_STATE: Dict[str, Any] = {
    "enabled": False,
    "running": False,
    "workerId": None,
    "startedAt": None,
    "lastTickAt": None,
    "lastResult": None,
    "totalRuns": 0,
    "totalStationRuns": 0,
    "lastError": None,
}
_THREAD: threading.Thread | None = None
_STOP = threading.Event()
_LOCK = threading.Lock()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except Exception:
        value = default
    return max(minimum, min(value, maximum))


def _env_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except Exception:
        value = default
    return max(minimum, min(value, maximum))


def _now() -> str:
    return datetime.now().isoformat()


def worker_config() -> Dict[str, Any]:
    return {
        "version": STATION_QUEUE_WORKER_VERSION,
        "queueVersion": STATION_QUEUE_VERSION,
        "enabledByEnv": _env_bool("STATION_QUEUE_WORKER_ENABLED", True),
        "intervalSeconds": _env_float("STATION_QUEUE_WORKER_INTERVAL", 2.0, 1.0, 60.0),
        "maxJobsPerTick": _env_int("STATION_QUEUE_WORKER_MAX_JOBS_PER_TICK", 3, 1, 10),
        "systemType": os.getenv("STATION_QUEUE_WORKER_SYSTEM_TYPE", "task_generation"),
        "fastLaneRule": "Queue priority, not batch completion, determines next station. task_pool=1, task_snapshot=5.",
    }


def _set_state(**kwargs: Any) -> None:
    with _LOCK:
        _STATE.update(kwargs)


def worker_status(include_queue: bool = True) -> Dict[str, Any]:
    with _LOCK:
        state = dict(_STATE)
    result = {"version": STATION_QUEUE_WORKER_VERSION, "config": worker_config(), "state": state, "rule": "V14.6.2 worker consumes fast-lane station_queue outside upload requests."}
    if include_queue:
        try:
            result["queueSummary"] = queue_summary(limit=20)
        except Exception as exc:
            result["queueSummaryError"] = str(exc)
    return result


def _worker_loop(worker_id: str) -> None:
    config = worker_config()
    interval = float(config["intervalSeconds"])
    max_jobs = int(config["maxJobsPerTick"])
    system_type = str(config["systemType"])
    _set_state(enabled=True, running=True, workerId=worker_id, startedAt=_now(), lastError=None)
    while not _STOP.is_set():
        tick_results = []
        try:
            for _ in range(max_jobs):
                result = run_next_station_job(worker_id=worker_id, system_type=system_type)
                tick_results.append(result)
                _set_state(totalRuns=int(_STATE.get("totalRuns") or 0) + 1)
                if result.get("ran"):
                    _set_state(totalStationRuns=int(_STATE.get("totalStationRuns") or 0) + 1)
                if not result.get("ran"):
                    break
            _set_state(lastTickAt=_now(), lastResult=tick_results, lastError=None)
        except Exception as exc:
            _set_state(lastTickAt=_now(), lastError=str(exc), lastResult=tick_results)
        _STOP.wait(interval)
    _set_state(running=False, lastTickAt=_now())


def start_station_queue_worker(worker_id: str = "auto-worker") -> Dict[str, Any]:
    global _THREAD
    if not _env_bool("STATION_QUEUE_WORKER_ENABLED", True):
        _set_state(enabled=False, running=False, workerId=worker_id, lastError="disabled_by_env")
        return worker_status(include_queue=False)
    with _LOCK:
        alive = _THREAD is not None and _THREAD.is_alive()
    if alive:
        return worker_status(include_queue=False)
    _STOP.clear()
    thread = threading.Thread(target=_worker_loop, args=(worker_id,), name="station-queue-worker", daemon=True)
    _THREAD = thread
    thread.start()
    time.sleep(0.05)
    return worker_status(include_queue=False)


def stop_station_queue_worker() -> Dict[str, Any]:
    _STOP.set()
    thread = _THREAD
    if thread and thread.is_alive():
        thread.join(timeout=2.0)
    _set_state(enabled=False, running=False, lastTickAt=_now())
    return worker_status(include_queue=False)


def run_worker_tick(worker_id: str = "manual-tick", limit: int | None = None) -> Dict[str, Any]:
    max_jobs = max(1, min(int(limit or worker_config()["maxJobsPerTick"]), 20))
    results = []
    for _ in range(max_jobs):
        result = run_next_station_job(worker_id=worker_id, system_type=str(worker_config()["systemType"]))
        results.append(result)
        if not result.get("ran"):
            break
    _set_state(lastTickAt=_now(), lastResult=results, totalRuns=int(_STATE.get("totalRuns") or 0) + len(results), totalStationRuns=int(_STATE.get("totalStationRuns") or 0) + sum(1 for item in results if item.get("ran")))
    return {"version": STATION_QUEUE_WORKER_VERSION, "ranCount": sum(1 for item in results if item.get("ran")), "results": results, "workerStatus": worker_status(include_queue=True)}
