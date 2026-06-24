"""V10.4 report-import driven task sync contract.

This layer does not replace the existing V3/V6 import, alert, trend and risk-task logic.
It wraps import results into a product-facing contract so the frontend can refresh
Dashboard, Operation, Tasks, Data and Logs without exposing the internal pipeline.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List

V104_IMPORT_SYNC_VERSION = "10.4.0"
V104_UPDATED_MODULES = ["dashboard", "operation", "tasks", "reports", "logs"]
V104_UPDATED_MODULE_LABELS = ["总览", "经营", "任务", "数据", "日志"]
V104_FRONTEND_REFRESH_TARGETS = ["dashboard", "operating-unit", "business-actions", "data-check", "business-report"]


def _as_list(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _import_items(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    if isinstance(result.get("results"), list):
        return _as_list(result.get("results"))
    return [result]


def _created_task_count(result: Dict[str, Any]) -> int:
    base = int(result.get("createdTaskCount") or 0)
    risk_sync = result.get("riskTaskSync") if isinstance(result.get("riskTaskSync"), dict) else {}
    base = max(base, int(risk_sync.get("createdTaskCount") or 0))
    children = _import_items(result)
    if len(children) > 1 or children[0] is not result:
        base = max(base, sum(_created_task_count(item) for item in children))
    return base


def _alert_count(result: Dict[str, Any]) -> int:
    base = int(result.get("alertCount") or 0)
    risk_sync = result.get("riskTaskSync") if isinstance(result.get("riskTaskSync"), dict) else {}
    base = max(base, int(risk_sync.get("signalCount") or 0))
    children = _import_items(result)
    if len(children) > 1 or children[0] is not result:
        base = max(base, sum(_alert_count(item) for item in children))
    return base


def _row_count(result: Dict[str, Any]) -> int:
    base = int(result.get("rowCount") or 0)
    children = _import_items(result)
    if len(children) > 1 or children[0] is not result:
        base = max(base, sum(_row_count(item) for item in children))
    return base


def _data_versions(result: Dict[str, Any]) -> List[str]:
    values: List[str] = []
    if result.get("dataVersion"):
        values.append(str(result["dataVersion"]))
    for item in _import_items(result):
        if item is result:
            continue
        values.extend(_data_versions(item))
    return list(dict.fromkeys(values))


def _dataset_names(result: Dict[str, Any]) -> List[str]:
    values: List[str] = []
    if result.get("datasetName"):
        values.append(str(result["datasetName"]))
    for item in _import_items(result):
        if item is result:
            continue
        values.extend(_dataset_names(item))
    return list(dict.fromkeys(values))


def _task_ids_from_alerts(alerts: Iterable[Dict[str, Any]]) -> List[str]:
    ids: List[str] = []
    for alert in alerts:
        task_id = alert.get("taskId")
        if task_id:
            ids.append(str(task_id))
    return list(dict.fromkeys(ids))


def _task_ids(result: Dict[str, Any]) -> List[str]:
    ids = _task_ids_from_alerts(_as_list(result.get("alerts")))
    for item in _import_items(result):
        if item is result:
            continue
        ids.extend(_task_ids(item))
    return list(dict.fromkeys(ids))


def build_v104_import_sync(result: Dict[str, Any], *, source: str = "report_import") -> Dict[str, Any]:
    created_task_count = _created_task_count(result)
    alert_count = _alert_count(result)
    row_count = _row_count(result)
    data_versions = _data_versions(result)
    dataset_names = _dataset_names(result)
    task_ids = _task_ids(result)
    return {
        "version": V104_IMPORT_SYNC_VERSION,
        "source": source,
        "status": "completed",
        "importJobId": result.get("importId") or result.get("jobId") or result.get("mode") or source,
        "datasetNames": dataset_names,
        "dataVersions": data_versions,
        "rowCount": row_count,
        "alertCount": alert_count,
        "createdTaskCount": created_task_count,
        "createdTaskIds": task_ids,
        "updatedModules": V104_UPDATED_MODULES,
        "updatedModuleLabels": V104_UPDATED_MODULE_LABELS,
        "frontendRefreshTargets": V104_FRONTEND_REFRESH_TARGETS,
        "summary": f"已更新，生成 {created_task_count} 个任务",
        "taskFlow": {
            "dashboard": "总览任务台已更新",
            "operation": "经营模块已同步最新数据",
            "tasks": f"任务池新增或合并 {created_task_count} 个任务",
            "reports": "数据接入记录已更新",
            "logs": "同步和任务动作已留痕",
        },
        "userMessage": f"已更新，生成 {created_task_count} 个任务",
        "nextAction": "open_tasks" if created_task_count else "review_report",
    }


def attach_v104_import_sync(result: Dict[str, Any], *, source: str = "report_import") -> Dict[str, Any]:
    payload = deepcopy(result)
    payload["v104ImportTaskSync"] = build_v104_import_sync(payload, source=source)
    payload["updatedModules"] = payload["v104ImportTaskSync"]["updatedModules"]
    payload["createdTaskCount"] = max(int(payload.get("createdTaskCount") or 0), payload["v104ImportTaskSync"]["createdTaskCount"])
    payload["summary"] = payload["v104ImportTaskSync"]["summary"]
    payload["userMessage"] = payload["v104ImportTaskSync"]["userMessage"]
    return payload
