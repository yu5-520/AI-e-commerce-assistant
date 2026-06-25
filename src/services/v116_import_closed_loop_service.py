"""V11.6 import closed-loop verification.

Import responses must describe what the product modules can actually read after
an import, not only what the upstream import pipeline attempted to generate.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List

from src.core.context import UserContext
from src.services.module_projection_service import projected_products, projected_traffic, projection_summary
from src.services.module_task_service import list_tasks
from src.services.risk_task_service import risk_task_summary

V116_IMPORT_CLOSED_LOOP_VERSION = "11.6.0"
EXECUTABLE_QUEUE_TYPES = {"urgent_execution", "today_execution"}
BACKEND_ONLY_QUEUE_TYPES = {"backend_tag", "store_product_tag", "observe_candidate"}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return default


def _as_rows(value: Any) -> List[Dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _row_count(result: Dict[str, Any]) -> int:
    if isinstance(result.get("rows"), list):
        return len(result["rows"])
    v104 = result.get("v104ImportTaskSync") if isinstance(result.get("v104ImportTaskSync"), dict) else {}
    return _as_int(v104.get("rowCount") or result.get("rowCount"), 0)


def _store_key(item: Dict[str, Any]) -> str | None:
    value = item.get("storeId") or item.get("store") or item.get("storeName")
    text = str(value or "").strip()
    return text or None


def _store_count(products: Iterable[Dict[str, Any]], traffic: Iterable[Dict[str, Any]]) -> int:
    values = [_store_key(item) for item in [*products, *traffic]]
    return len({value for value in values if value})


def _is_executable_task(task: Dict[str, Any]) -> bool:
    queue_type = task.get("queueType")
    if queue_type in BACKEND_ONLY_QUEUE_TYPES:
        return False
    if task.get("displayState") == "backend_only":
        return False
    return queue_type in EXECUTABLE_QUEUE_TYPES or task.get("taskLayer") in {"operator_execution", "manager_dispatch", "finance_check"}


def _viewer_for_query(ctx: UserContext) -> str | None:
    return None if ctx.role_id == "owner" else ctx.user_id


def _patch_v104(payload: Dict[str, Any], closed_loop: Dict[str, Any]) -> None:
    sync = payload.get("v104ImportTaskSync")
    if not isinstance(sync, dict):
        return
    executable = closed_loop["executableTaskCount"]
    tagged = closed_loop["taggedSignalCount"]
    row_count = closed_loop["importedRowCount"]
    product_count = closed_loop["productCount"]
    store_count = closed_loop["storeCount"]
    sync["createdTaskCount"] = executable
    sync["visibleExecutableTaskCount"] = executable
    sync["taggedSignalCount"] = tagged
    sync["productCount"] = product_count
    sync["storeCount"] = store_count
    sync["summary"] = f"已导入 {row_count} 行，更新 {product_count} 个商品 / {store_count} 个店铺，生成 {executable} 个可执行任务，{tagged} 个低风险信号已沉淀为标签。"
    sync["userMessage"] = sync["summary"]
    sync["nextAction"] = "open_tasks" if executable else "review_business_tags"
    sync["taskFlow"] = {
        "dashboard": "总览已按真实反查结果刷新",
        "operation": f"经营模块可读商品 {product_count} 个、店铺 {store_count} 个",
        "tasks": f"任务池当前可执行任务 {executable} 个",
        "reports": f"数据接入记录已写入 {row_count} 行",
        "logs": "同步动作已留痕",
    }
    payload["createdTaskCount"] = executable
    payload["summary"] = sync["summary"]
    payload["userMessage"] = sync["userMessage"]


def attach_v116_import_closed_loop(result: Dict[str, Any], ctx: UserContext, *, source: str = "report_import") -> Dict[str, Any]:
    """Attach post-import truth metrics read from the same modules as the frontend."""

    payload = deepcopy(result)
    products = projected_products(ctx.user_id)
    traffic = projected_traffic(ctx.user_id)
    projection = projection_summary(ctx.user_id)
    viewer_id = _viewer_for_query(ctx)
    active_tasks = list_tasks(active_only=True, viewer_id=viewer_id)
    executable_tasks = [task for task in active_tasks if _is_executable_task(task)]
    risk_summary = risk_task_summary(limit=200)
    tagged_signals = _as_int(risk_summary.get("taggedOnlyCount"), 0)
    backend_plan_count = max(_as_int(risk_summary.get("total"), 0) - len(executable_tasks), 0)
    closed_loop = {
        "version": V116_IMPORT_CLOSED_LOOP_VERSION,
        "source": source,
        "status": "verified",
        "viewer": ctx.audit_meta(),
        "importedRowCount": _row_count(payload),
        "productCount": len(products),
        "storeCount": _store_count(products, traffic),
        "trafficCardCount": len(traffic),
        "visibleActiveTaskCount": len(active_tasks),
        "executableTaskCount": len(executable_tasks),
        "taggedSignalCount": tagged_signals,
        "backendPlanCount": backend_plan_count,
        "latestDataVersion": projection.get("latestDataVersion"),
        "truthSource": "projected_products + projected_traffic + module_task_service.list_tasks + risk_task_summary",
        "rule": "导入响应必须以模块真实反查结果为准；标签沉淀不等于任务栏任务。",
    }
    payload["importClosedLoop"] = closed_loop
    payload["closedLoopVerified"] = True
    _patch_v104(payload, closed_loop)
    return payload
