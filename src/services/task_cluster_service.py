"""V12.7.2 task clustering service.

Repeated product signals are merged into a real backend task object. The primary
cluster task keeps a stable task id, affected products, detail report and status
that can be accepted/submitted/reviewed by the same lifecycle endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from src.services import module_task_service

TASK_CLUSTER_VERSION = "12.7.2"
DONE_STATUS = {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}
GROUPABLE_QUEUE_TYPES = {"daily_operating_task", "weekly_review_task"}
GROUPABLE_ACTIONS = {"inventory_restock", "creative_material_test", "title_test", "main_image_test", "traffic_expansion", "generic_operation"}

REASON_LABELS = {
    "inventory_capacity": "库存警告",
    "click_material": "点击素材排查",
    "conversion_landing": "转化承接排查",
    "ad_efficiency": "投放效率复核",
    "refund_after_sales": "售后退款排查",
    "roi_gmv": "ROI/GMV经营复核",
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _gate(task: Dict[str, Any]) -> Dict[str, Any]:
    return task.get("actionAuthorization") or task.get("v127ActionGate") or task.get("v126ActionGate") or {}


def _text(task: Dict[str, Any]) -> str:
    detail = task.get("taskDetailReport") or {}
    card = task.get("taskCard") or {}
    return " ".join([
        _clean(task.get("title")),
        _clean(task.get("task")),
        _clean(task.get("riskDomain")),
        _clean(task.get("reason")),
        _clean(card.get("title")),
        _clean(card.get("subtitle")),
        _clean(detail.get("warningSummary")),
        " ".join(_clean(step) for step in (task.get("sopSteps") or [])),
    ])


def _action_type(task: Dict[str, Any]) -> str:
    gate = _gate(task)
    text = _text(task)
    action = _clean(gate.get("actionType") or task.get("actionType") or "generic_operation")
    if any(token in text for token in ("库存归零", "库存", "补货", "调拨", "可售天数", "断货", "缺货")):
        return "inventory_restock"
    return action


def _reason_family(task: Dict[str, Any]) -> str:
    text = _text(task)
    if any(token in text for token in ("库存归零", "库存", "补货", "调拨", "可售天数", "断货", "缺货")):
        return "inventory_capacity"
    if "点击率" in text or "点击" in text or "素材" in text or "主图" in text:
        return "click_material"
    if "转化" in text or "详情" in text or "评价" in text or "客服" in text:
        return "conversion_landing"
    if "广告" in text or "预算" in text or "投放" in text or "人群" in text or "关键词" in text:
        return "ad_efficiency"
    if "退款" in text or "售后" in text:
        return "refund_after_sales"
    if "GMV" in text or "ROI" in text:
        return "roi_gmv"
    return _action_type(task)


def _action_label(task: Dict[str, Any]) -> str:
    family = _reason_family(task)
    if family in REASON_LABELS:
        return REASON_LABELS[family]
    gate = _gate(task)
    if gate.get("actionLabel"):
        return _clean(gate.get("actionLabel"))
    return _clean(task.get("riskDomain") or "经营排查")


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
    return _action_type(task) in GROUPABLE_ACTIONS or _reason_family(task) in REASON_LABELS


def _affected_product(task: Dict[str, Any]) -> Dict[str, Any]:
    detail = task.get("taskDetailReport") or {}
    metrics = detail.get("evidencePack") or task.get("evidencePack") or task.get("evidence") or []
    return {
        "taskId": task.get("id"),
        "productId": task.get("productId") or task.get("entityId"),
        "productTitle": task.get("title") or task.get("productTitle"),
        "store": task.get("store") or task.get("storeName"),
        "platform": task.get("platform"),
        "reason": task.get("reason") or detail.get("warningSummary") or _action_label(task),
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
    primary["sourceTrail"] = list(dict.fromkeys([*(primary.get("sourceTrail") or []), "V12.7.2后端真实聚合任务"]))
    gate = dict(_gate(primary))
    if gate:
        gate["actionType"] = _action_type(primary)
        gate["actionLabel"] = action_label
        gate["version"] = "12.7.2"
        primary["actionAuthorization"] = gate
        primary["v127ActionGate"] = gate
        primary["v126ActionGate"] = gate
    card = dict(primary.get("taskCard") or {})
    card["title"] = title
    card["subtitle"] = f"{action_label}｜批量执行"
    primary["taskCard"] = card
    detail = dict(primary.get("taskDetailReport") or {})
    detail["title"] = f"批量任务详情｜{title}"
    detail["taskClusterVersion"] = TASK_CLUSTER_VERSION
    detail["affectedProducts"] = affected
    detail["affectedProductCount"] = len(affected)
    detail["warningSummary"] = f"同一店铺出现 {len(affected)} 个同类经营信号，已合并为一个真实后端任务；接收、提交、复核和详情都使用该任务 ID。"
    detail["suggestedActions"] = primary.get("sopSteps") or detail.get("suggestedActions") or []
    detail["operationChecklist"] = primary.get("sopSteps") or detail.get("operationChecklist") or []
    detail["actionAuthorization"] = primary.get("actionAuthorization")
    detail["relatedTask"] = {"id": primary.get("id"), "batchTask": True, "affectedProductCount": len(affected)}
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
    return {"version": TASK_CLUSTER_VERSION, "mode": "backend_real_task_lifecycle_cluster", "clusterCount": cluster_count, "mergedDuplicateCount": merged_count}
