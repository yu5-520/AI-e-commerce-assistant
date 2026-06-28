"""V12.7.1 task clustering service.

The task generator can find the same operating reason on many products. The user
should see one execution task per store/action/reason group, with affected
products listed in the detail report, instead of many identical cards.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from src.services import module_task_service

TASK_CLUSTER_VERSION = "12.7.1"
DONE_STATUS = {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}
GROUPABLE_QUEUE_TYPES = {"daily_operating_task", "weekly_review_task"}
GROUPABLE_ACTIONS = {"creative_material_test", "title_test", "main_image_test", "traffic_expansion", "generic_operation"}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _gate(task: Dict[str, Any]) -> Dict[str, Any]:
    return task.get("actionAuthorization") or task.get("v127ActionGate") or task.get("v126ActionGate") or {}


def _action_type(task: Dict[str, Any]) -> str:
    return _clean(_gate(task).get("actionType") or task.get("actionType") or "generic_operation")


def _action_label(task: Dict[str, Any]) -> str:
    gate = _gate(task)
    action = _action_type(task)
    if gate.get("actionLabel"):
        return _clean(gate.get("actionLabel"))
    if action == "creative_material_test":
        return "素材点击排查"
    if action == "title_test":
        return "标题搜索排查"
    if action == "main_image_test":
        return "主图点击排查"
    if action == "traffic_expansion":
        return "流量入口排查"
    return _clean(task.get("riskDomain") or "经营排查")


def _reason_family(task: Dict[str, Any]) -> str:
    text = " ".join([
        _clean(task.get("riskDomain")),
        _clean(task.get("reason")),
        _clean((task.get("taskDetailReport") or {}).get("warningSummary")),
        _clean(task.get("task")),
    ])
    if "点击率" in text or "点击" in text or "素材" in text or "主图" in text:
        return "click_material"
    if "转化" in text or "详情" in text or "评价" in text or "客服" in text:
        return "conversion_landing"
    if "广告" in text or "预算" in text or "投放" in text or "人群" in text or "关键词" in text:
        return "ad_efficiency"
    if "库存" in text or "补货" in text or "可售" in text:
        return "inventory_capacity"
    if "退款" in text or "售后" in text:
        return "refund_after_sales"
    if "GMV" in text or "ROI" in text:
        return "roi_gmv"
    return _action_type(task)


def _store_key(task: Dict[str, Any]) -> str:
    ids = task.get("visibleStoreIds") or task.get("storeIds") or []
    if ids:
        return _clean(ids[0])
    return _clean(task.get("storeId") or task.get("storeName") or task.get("store") or "default_store")


def _group_key(task: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    return (
        _store_key(task),
        _action_type(task),
        _reason_family(task),
        _clean(task.get("assigneeId") or "operator"),
        _clean(task.get("deadline") or task.get("timeBucket") or "today"),
    )


def _groupable(task: Dict[str, Any]) -> bool:
    if task.get("status") in DONE_STATUS or task.get("displayState") == "backend_only":
        return False
    if task.get("priority") == "高" or task.get("riskLevel") == "高":
        return False
    if task.get("queueType") not in GROUPABLE_QUEUE_TYPES:
        return False
    if task.get("taskLayer") not in {None, "operator_execution"}:
        return False
    action = _action_type(task)
    return action in GROUPABLE_ACTIONS or _reason_family(task) in {"click_material", "conversion_landing", "ad_efficiency", "roi_gmv"}


def _affected_product(task: Dict[str, Any]) -> Dict[str, Any]:
    detail = task.get("taskDetailReport") or {}
    metrics = detail.get("evidencePack") or task.get("evidencePack") or task.get("evidence") or []
    return {
        "taskId": task.get("id"),
        "productId": task.get("productId") or task.get("entityId"),
        "productTitle": task.get("title") or task.get("productTitle"),
        "store": task.get("store") or task.get("storeName"),
        "platform": task.get("platform"),
        "reason": task.get("reason") or detail.get("warningSummary"),
        "metrics": metrics[:6] if isinstance(metrics, list) else [],
    }


def _merge_task(primary: Dict[str, Any], group: List[Dict[str, Any]], group_key: Tuple[str, str, str, str, str]) -> None:
    affected = [_affected_product(task) for task in group]
    action_label = _action_label(primary)
    store = primary.get("store") or primary.get("storeName") or "店铺"
    title = f"{store}｜{action_label}｜{len(affected)}个商品"
    primary["batchTask"] = True
    primary["taskClusterVersion"] = TASK_CLUSTER_VERSION
    primary["clusterKey"] = "|".join(group_key)
    primary["clusterTaskIds"] = [task.get("id") for task in group if task.get("id")]
    primary["affectedProductCount"] = len(affected)
    primary["affectedProducts"] = affected
    primary["title"] = title
    primary["productTitle"] = title
    primary["entityType"] = "商品组"
    primary["productId"] = f"{len(affected)}个商品"
    card = dict(primary.get("taskCard") or {})
    card["title"] = title
    card["subtitle"] = f"{action_label}｜同类任务聚合"
    primary["taskCard"] = card
    detail = dict(primary.get("taskDetailReport") or {})
    detail["title"] = f"批量任务详情｜{title}"
    detail["taskClusterVersion"] = TASK_CLUSTER_VERSION
    detail["affectedProducts"] = affected
    detail["affectedProductCount"] = len(affected)
    detail["warningSummary"] = f"同一店铺出现 {len(affected)} 个同类经营信号，已聚合成一个批量执行任务，避免重复商品任务刷屏。"
    detail["suggestedActions"] = primary.get("sopSteps") or detail.get("suggestedActions") or []
    detail["operationChecklist"] = primary.get("sopSteps") or detail.get("operationChecklist") or []
    primary["taskDetailReport"] = detail
    for duplicate in group[1:]:
        duplicate["status"] = "已归档"
        duplicate["workflowStatus"] = "已归档"
        duplicate["displayState"] = "backend_only"
        duplicate["queueType"] = "merged_duplicate"
        duplicate["clusterParentTaskId"] = primary.get("id")
        duplicate["updatedAt"] = module_task_service.now_iso()


def cluster_open_tasks() -> Dict[str, Any]:
    groups: Dict[Tuple[str, str, str, str, str], List[Dict[str, Any]]] = {}
    for task in module_task_service.TASKS:
        if _groupable(task):
            groups.setdefault(_group_key(task), []).append(task)
    cluster_count = 0
    merged_count = 0
    for key, group in groups.items():
        if len(group) < 2:
            continue
        group.sort(key=lambda task: (-len((task.get("evidencePack") or [])), _clean(task.get("createdAt"))))
        _merge_task(group[0], group, key)
        cluster_count += 1
        merged_count += len(group) - 1
    return {"version": TASK_CLUSTER_VERSION, "clusterCount": cluster_count, "mergedDuplicateCount": merged_count}
