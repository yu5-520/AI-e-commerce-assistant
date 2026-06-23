"""V8.7 cross task group generation service.

V8.6 decides whether a cross-validated weight conclusion is ready for a task
group. V8.7 turns those validated conclusions into structured weight task-group
drafts. The groups are not executed automatically; V8.8 will add approval flow
before any real weight action is allowed.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.v86_cross_validation_service import ensure_cross_validation_tables, generate_cross_validations

V87_TASK_GROUP_VERSION = "8.7.0"

HARD_INTENSITIES = {"L4", "L5"}
APPROVAL_OWNER_STATES = {"L5", "H3"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_weight_task_group_tables() -> None:
    ensure_cross_validation_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weight_task_groups_v8 (
                task_group_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                parent_type TEXT,
                parent_id TEXT,
                group_type TEXT NOT NULL,
                group_name TEXT NOT NULL,
                group_status TEXT NOT NULL,
                priority TEXT,
                approval_required INTEGER DEFAULT 1,
                approval_role TEXT,
                final_intensity_level TEXT,
                readiness TEXT,
                validation_status TEXT,
                task_count INTEGER DEFAULT 0,
                tasks TEXT,
                evidence_refs TEXT,
                related_validation_id TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_task_groups_object_v8 ON weight_task_groups_v8(tenant_id, org_id, object_type, object_id, group_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_task_groups_status_v8 ON weight_task_groups_v8(group_status, priority, approval_role)")
        conn.commit()


def _row_to_validation(row: Any) -> Dict[str, Any]:
    return {
        "validationId": row["validation_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "parentType": row["parent_type"],
        "parentId": row["parent_id"],
        "validationStatus": row["validation_status"],
        "validationLabel": row["validation_label"],
        "readiness": row["readiness"],
        "confidence": row["confidence"],
        "finalIntensityLevel": row["final_intensity_level"],
        "finalIntensityLabel": row["final_intensity_label"],
        "crossScore": row["cross_score"],
        "evidenceCount": row["evidence_count"],
        "conflictCount": row["conflict_count"],
        "relatedAdjustmentIds": loads(row["related_adjustment_ids"]),
        "relatedScoreIds": loads(row["related_score_ids"]),
        "crossFactors": loads(row["cross_factors"]),
        "conclusion": row["conclusion"],
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def _load_latest_validations(ctx: UserContext) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_cross_validations_v8 v
            WHERE tenant_id = ? AND org_id = ?
              AND created_at = (
                SELECT MAX(inner_v.created_at)
                FROM weight_cross_validations_v8 inner_v
                WHERE inner_v.tenant_id = v.tenant_id
                  AND inner_v.org_id = v.org_id
                  AND inner_v.object_type = v.object_type
                  AND inner_v.object_id = v.object_id
              )
            ORDER BY object_type ASC, object_id ASC
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    return [_row_to_validation(row) for row in rows]


def _priority(item: Dict[str, Any]) -> str:
    level = item.get("finalIntensityLevel")
    if level in {"L5", "H3"}:
        return "P0"
    if level in {"L4", "L3", "H2"}:
        return "P1"
    if item.get("validationStatus") in {"conflict", "needs_review"}:
        return "P2"
    return "P3"


def _approval_role(item: Dict[str, Any]) -> str:
    level = item.get("finalIntensityLevel")
    object_type = item.get("objectType")
    if object_type == "operator":
        return "owner" if level == "H3" else "manager"
    if object_type == "store" and level in {"L4", "L5"}:
        return "owner"
    if level in APPROVAL_OWNER_STATES:
        return "owner"
    return "manager"


def _task(title: str, action: str, owner_role: str, risk: str, evidence: str) -> Dict[str, Any]:
    return {"taskId": make_id("WTASK"), "title": title, "action": action, "ownerRole": owner_role, "riskLevel": risk, "evidenceRequired": evidence, "status": "draft"}


def _product_tasks(item: Dict[str, Any]) -> tuple[str, str, List[Dict[str, Any]]]:
    level = item.get("finalIntensityLevel")
    if level == "L5":
        return "product_stop_loss_group", "商品止损复核任务组", [
            _task("停止扩大投产", "冻结新增投放预算，保留必要基础曝光。", "manager", "高", "投放调整截图与预算变化记录"),
            _task("首页主打位替换", "从店铺首页/核心推荐位移出该商品，并替换为候选主推品。", "manager", "高", "页面位置调整截图"),
            _task("下架/清仓复核", "提交下架、清仓或库存收缩复核，不允许自动执行。", "owner", "高", "库存、ROI、售后与交叉验证报告"),
        ]
    if level == "L4":
        return "product_hard_demote_group", "商品强降权任务组", [
            _task("快速降低投产", "降低投放预算和活动资源，观察 24-72 小时。", "manager", "中高", "投放前后对比"),
            _task("主推位置调整", "从首页主打/核心坑位降级到次级测试位。", "manager", "中高", "坑位调整截图"),
            _task("承接修复复核", "复核标题、主图、价格、评价与详情页承接问题。", "operator", "中", "修改清单与复盘说明"),
        ]
    if level == "L3":
        return "product_demote_group", "商品降权候选任务组", [
            _task("降低测试预算", "减少测试预算或活动资源，避免继续放大亏损。", "manager", "中", "预算调整记录"),
            _task("商品承接修复", "优化标题、主图、卖点、价格或评价承接。", "operator", "中", "A/B 测试记录"),
        ]
    return "product_repair_group", "商品修复观察任务组", [
        _task("标题主图测试", "进行标题、主图、卖点小步测试。", "operator", "低", "测试前后数据"),
        _task("复盘观察", "补充 3-7 天观察复盘。", "operator", "低", "复盘说明"),
    ]


def _store_tasks(item: Dict[str, Any]) -> tuple[str, str, List[Dict[str, Any]]]:
    level = item.get("finalIntensityLevel")
    if level in {"L4", "L5"}:
        return "store_resource_limit_group", "店铺资源限制复核任务组", [
            _task("限制上新/投放额度", "提交店铺上新名额、活动资源或投放额度限制申请。", "manager", "高", "店铺指标与商品结构证据"),
            _task("总管介入复核", "由总管复核店铺结构、商品健康率和运营执行情况。", "manager", "高", "复核结论"),
            _task("老板审批", "涉及店铺降权或资源收缩必须老板审批。", "owner", "高", "审批记录"),
        ]
    return "store_observe_group", "店铺观察修复任务组", [
        _task("店铺结构复核", "复核店铺商品结构、自然流量和售后口径。", "manager", "中", "结构复核记录"),
        _task("异常商品定位", "定位拖累店铺的商品，而不是直接对店铺降权。", "manager", "中", "商品清单"),
    ]


def _operator_tasks(item: Dict[str, Any]) -> tuple[str, str, List[Dict[str, Any]]]:
    level = item.get("finalIntensityLevel")
    if level == "H3":
        return "operator_permission_review_group", "运营权限调整复核任务组", [
            _task("权限调整复核", "提交权限调整申请，但不得自动改权限。", "manager", "高", "任务、证据、复盘与审批记录"),
            _task("老板确认", "人员权限变化必须由老板确认。", "owner", "高", "审批确认"),
        ]
    if level == "H2":
        return "operator_coaching_group", "运营辅导观察任务组", [
            _task("辅导观察", "安排运营辅导，明确任务准时率、证据完整度、复盘质量改进目标。", "manager", "中", "辅导记录"),
            _task("周期复盘", "观察 1-2 个周期后再判断是否进入权限复核。", "manager", "中", "复盘记录"),
        ]
    return "operator_review_group", "运营人工复核任务组", [
        _task("人工复核", "仅生成复核材料，不自动处罚、不自动降权。", "manager", "低", "复核说明"),
    ]


def _review_tasks(item: Dict[str, Any]) -> tuple[str, str, List[Dict[str, Any]]]:
    return "evidence_review_group", "证据复核任务组", [
        _task("补充证据", "补充周期、标准线、联动和上下文证据。", "manager", "中", "补充后的证据链"),
        _task("冲突复核", "复核是否存在店铺问题、商品问题或数据口径冲突。", "manager", "中", "冲突说明"),
    ]


def _build_group(item: Dict[str, Any]) -> Dict[str, Any]:
    object_type = item.get("objectType")
    readiness = item.get("readiness")
    if object_type == "operator":
        group_type, group_name, tasks = _operator_tasks(item)
        group_status = "human_review_draft"
    elif readiness == "ready_for_task_group" and object_type == "product":
        group_type, group_name, tasks = _product_tasks(item)
        group_status = "pending_approval"
    elif readiness == "ready_for_task_group" and object_type == "store":
        group_type, group_name, tasks = _store_tasks(item)
        group_status = "pending_approval"
    else:
        group_type, group_name, tasks = _review_tasks(item)
        group_status = "evidence_review"
    approval_role = _approval_role(item)
    return {
        "taskGroupId": make_id("WTG"),
        "tenantId": item["tenantId"],
        "orgId": item["orgId"],
        "objectType": object_type,
        "objectId": item["objectId"],
        "objectName": item.get("objectName"),
        "parentType": item.get("parentType"),
        "parentId": item.get("parentId"),
        "groupType": group_type,
        "groupName": group_name,
        "groupStatus": group_status,
        "priority": _priority(item),
        "approvalRequired": True,
        "approvalRole": approval_role,
        "finalIntensityLevel": item.get("finalIntensityLevel"),
        "readiness": readiness,
        "validationStatus": item.get("validationStatus"),
        "taskCount": len(tasks),
        "tasks": tasks,
        "evidenceRefs": {
            "validationId": item.get("validationId"),
            "relatedAdjustmentIds": item.get("relatedAdjustmentIds") or [],
            "relatedScoreIds": item.get("relatedScoreIds") or [],
            "crossFactors": item.get("crossFactors") or {},
            "conclusion": item.get("conclusion"),
        },
        "relatedValidationId": item.get("validationId"),
        "payload": {"version": V87_TASK_GROUP_VERSION, "rule": "V8.7 生成权重任务组草案；V8.8 审批通过前不得执行。", "operatorSafetyBoundary": "运营任务组只进入人工复核，不自动处罚。" if object_type == "operator" else None},
        "createdAt": now_iso(),
    }


def _insert_group(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO weight_task_groups_v8 (
                task_group_id, tenant_id, org_id, object_type, object_id, object_name, parent_type, parent_id,
                group_type, group_name, group_status, priority, approval_required, approval_role,
                final_intensity_level, readiness, validation_status, task_count, tasks, evidence_refs,
                related_validation_id, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["taskGroupId"], item["tenantId"], item["orgId"], item["objectType"], item["objectId"], item.get("objectName"), item.get("parentType"), item.get("parentId"), item["groupType"], item["groupName"], item["groupStatus"], item["priority"], 1 if item.get("approvalRequired") else 0, item.get("approvalRole"), item.get("finalIntensityLevel"), item.get("readiness"), item.get("validationStatus"), item.get("taskCount"), dumps(item.get("tasks") or []), dumps(item.get("evidenceRefs") or {}), item.get("relatedValidationId"), dumps(item.get("payload") or {}), item["createdAt"]),
        )
        conn.commit()


def generate_weight_task_groups(ctx: UserContext) -> Dict[str, Any]:
    ensure_weight_task_group_tables()
    validations = _load_latest_validations(ctx)
    if not validations:
        generate_cross_validations(ctx)
        validations = _load_latest_validations(ctx)
    created = [_build_group(item) for item in validations]
    for item in created:
        _insert_group(item)
    by_status: Dict[str, int] = defaultdict(int)
    by_type: Dict[str, int] = defaultdict(int)
    by_priority: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in created:
        by_status[item["groupStatus"]] += 1
        by_type[item["groupType"]] += 1
        by_priority[item["priority"]] += 1
        by_object[item["objectType"]] += 1
    return {"version": V87_TASK_GROUP_VERSION, "createdCount": len(created), "byGroupStatus": dict(by_status), "byGroupType": dict(by_type), "byPriority": dict(by_priority), "byObjectType": dict(by_object), "taskGroups": created, "rule": "V8.7 只生成权重任务组草案；V8.8 接审批流，审批前不得执行。"}


def _row_to_group(row: Any) -> Dict[str, Any]:
    return {"taskGroupId": row["task_group_id"], "tenantId": row["tenant_id"], "orgId": row["org_id"], "objectType": row["object_type"], "objectId": row["object_id"], "objectName": row["object_name"], "parentType": row["parent_type"], "parentId": row["parent_id"], "groupType": row["group_type"], "groupName": row["group_name"], "groupStatus": row["group_status"], "priority": row["priority"], "approvalRequired": bool(row["approval_required"]), "approvalRole": row["approval_role"], "finalIntensityLevel": row["final_intensity_level"], "readiness": row["readiness"], "validationStatus": row["validation_status"], "taskCount": row["task_count"], "tasks": loads(row["tasks"]), "evidenceRefs": loads(row["evidence_refs"]), "relatedValidationId": row["related_validation_id"], "payload": loads(row["payload"]), "createdAt": row["created_at"]}


def weight_task_group_summary(ctx: UserContext, object_type: str | None = None, group_status: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_weight_task_group_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if object_type in {"product", "store", "operator"}:
        filters.append("object_type = ?")
        params.append(object_type)
    if group_status:
        filters.append("group_status = ?")
        params.append(group_status)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM weight_task_groups_v8 WHERE {' AND '.join(filters)} ORDER BY created_at DESC LIMIT ?", tuple(params)).fetchall()
    groups = [_row_to_group(row) for row in rows]
    by_status: Dict[str, int] = defaultdict(int)
    by_type: Dict[str, int] = defaultdict(int)
    by_priority: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in groups:
        by_status[item["groupStatus"]] += 1
        by_type[item["groupType"]] += 1
        by_priority[item["priority"]] += 1
        by_object[item["objectType"]] += 1
    return {"version": V87_TASK_GROUP_VERSION, "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "roleId": ctx.role_id, "taskGroupCount": len(groups), "byGroupStatus": dict(by_status), "byGroupType": dict(by_type), "byPriority": dict(by_priority), "byObjectType": dict(by_object), "taskGroups": groups, "rule": "V8.7 权重任务组仍是草案；V8.8 审批通过后才可进入执行链路。"}
