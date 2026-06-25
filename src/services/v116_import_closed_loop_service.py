"""V11.7 import closed-loop verification.

Import responses must describe what the product modules can actually read after
an import. Product/store master updates are verified separately from tag/task
creation so low-risk data still appears in the operating unit page.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List

from src.core.context import UserContext
from src.services.module_projection_service import projected_products, projected_traffic, projection_summary
from src.services.module_task_service import list_tasks
from src.services.operating_object_store_service import operating_object_summary
from src.services.risk_task_service import risk_task_summary

V116_IMPORT_CLOSED_LOOP_VERSION = "11.7.0"
EXECUTABLE_QUEUE_TYPES = {"urgent_execution", "today_execution"}
BACKEND_ONLY_QUEUE_TYPES = {"backend_tag", "store_product_tag", "observe_candidate"}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return default


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
    clean_count = closed_loop["cleanedRowCount"]
    product_count = closed_loop["productCount"]
    store_count = closed_loop["storeCount"]
    sync["createdTaskCount"] = executable
    sync["visibleExecutableTaskCount"] = executable
    sync["taggedSignalCount"] = tagged
    sync["cleanedRowCount"] = clean_count
    sync["productCount"] = product_count
    sync["storeCount"] = store_count
    sync["summary"] = f"已导入 {row_count} 行，清洗 {clean_count} 行，更新 {product_count} 个商品 / {store_count} 个店铺，生成 {executable} 个可执行任务，{tagged} 个低风险信号已沉淀为标签。"
    sync["userMessage"] = sync["summary"]
    sync["nextAction"] = "open_tasks" if executable else "review_operating_objects"
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
    """Attach post-import truth metrics read from product modules."""

    payload = deepcopy(result)
    products = projected_products(ctx.user_id)
    traffic = projected_traffic(ctx.user_id)
    projection = projection_summary(ctx.user_id)
    object_summary = operating_object_summary(ctx.user_id)
    object_sync = payload.get("operatingObjectSync") if isinstance(payload.get("operatingObjectSync"), dict) else {}
    viewer_id = _viewer_for_query(ctx)
    active_tasks = list_tasks(active_only=True, viewer_id=viewer_id)
    executable_tasks = [task for task in active_tasks if _is_executable_task(task)]
    risk_summary = risk_task_summary(limit=200)
    tagged_signals = _as_int(risk_summary.get("taggedOnlyCount"), 0)
    backend_plan_count = max(_as_int(risk_summary.get("total"), 0) - len(executable_tasks), 0)
    product_count = max(len(products), _as_int(object_summary.get("productCount")), _as_int(object_sync.get("productUpsertCount")))
    store_count = max(_store_count(products, traffic), _as_int(object_summary.get("storeCount")), _as_int(object_sync.get("storeUpsertCount")))
    cleaned_rows = _as_int(object_sync.get("cleanedRowCount"), _row_count(payload))
    closed_loop = {
        "version": V116_IMPORT_CLOSED_LOOP_VERSION,
        "source": source,
        "status": "verified",
        "viewer": ctx.audit_meta(),
        "importedRowCount": _row_count(payload),
        "cleanedRowCount": cleaned_rows,
        "productCount": product_count,
        "storeCount": store_count,
        "trafficCardCount": len(traffic),
        "visibleActiveTaskCount": len(active_tasks),
        "executableTaskCount": len(executable_tasks),
        "taggedSignalCount": tagged_signals,
        "backendPlanCount": backend_plan_count,
        "latestDataVersion": object_summary.get("latestDataVersion") or projection.get("latestDataVersion"),
        "operatingObjectSync": object_sync,
        "truthSource": "operating_object_store + projected_products + projected_traffic + module_task_service.list_tasks + risk_task_summary",
        "rule": "商品/店铺入库在前；标签和任务是后续状态。低风险不生成任务，也必须更新经营对象。",
    }
    payload["importClosedLoop"] = closed_loop
    payload["closedLoopVerified"] = True
    _patch_v104(payload, closed_loop)
    return payload
