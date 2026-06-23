"""V8.5 context weight adjustment service.

V8.4 gives every product, store, and operator an object-level weight state.
V8.5 adds context correction: the same product score is interpreted differently
in a brand main store, a profit core store, a growth store, or a test store.
This layer outputs adjusted states and task-intensity hints, but still does not
create tasks, change permissions, or punish operators automatically.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.v84_weight_score_service import ensure_weight_score_tables, generate_weight_scores

V85_CONTEXT_WEIGHT_VERSION = "8.5.0"

PROTECTED_STORE_ROLES = {"brand_main_store", "profit_core_store", "traffic_core_store"}
TEST_STORE_ROLES = {"test_store", "low_weight_store"}
GROWTH_STORE_ROLES = {"growth_store"}

PRODUCT_STATE_LABELS = {
    "promote_candidate": "升权候选",
    "maintain": "维持",
    "observe": "观察",
    "repair": "修复",
    "test_repair": "测试修复",
    "demote_candidate": "降权候选",
    "hard_demote_candidate": "强降权候选",
    "stop_loss_review": "止损复核",
}

STORE_STATE_LABELS = {
    "expand_candidate": "扩权候选",
    "maintain": "维持",
    "observe": "观察",
    "resource_limit_candidate": "限制资源候选",
    "demotion_review": "降权复核",
    "manager_intervention": "总管介入",
}

OPERATOR_STATE_LABELS = {
    "promotion_suggestion": "升权建议",
    "maintain": "维持",
    "coaching_observe": "辅导观察",
    "demotion_review": "降权复核",
    "permission_adjustment_review": "权限调整复核",
}

INTENSITY_LABELS = {
    "L1": "观察",
    "L2": "修复",
    "L3": "降权候选",
    "L4": "强降权候选",
    "L5": "止损复核",
    "H1": "人工复核依据",
    "H2": "辅导观察",
    "H3": "权限调整复核",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_context_weight_tables() -> None:
    ensure_weight_score_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS context_weight_adjustments_v8 (
                adjustment_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                parent_type TEXT,
                parent_id TEXT,
                base_score REAL NOT NULL,
                adjusted_score REAL NOT NULL,
                base_state TEXT,
                adjusted_state TEXT NOT NULL,
                adjusted_label TEXT,
                risk_level TEXT,
                task_intensity_level TEXT,
                task_intensity_label TEXT,
                context_type TEXT,
                context_summary TEXT,
                context_factors TEXT,
                related_score_id TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_context_weight_object_v8 ON context_weight_adjustments_v8(tenant_id, org_id, object_type, object_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_context_weight_state_v8 ON context_weight_adjustments_v8(adjusted_state, risk_level, task_intensity_level)")
        conn.commit()


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _row_to_score(row: Any) -> Dict[str, Any]:
    return {
        "scoreId": row["score_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "weightScore": row["weight_score"],
        "weightState": row["weight_state"],
        "stateLabel": row["state_label"],
        "riskLevel": row["risk_level"],
        "scoreDirection": row["score_direction"],
        "positiveCount": row["positive_count"],
        "neutralCount": row["neutral_count"],
        "negativeCount": row["negative_count"],
        "evidenceCount": row["evidence_count"],
        "relatedRelationIds": loads(row["related_relation_ids"]),
        "relatedHitIds": loads(row["related_hit_ids"]),
        "relatedComparisonIds": loads(row["related_comparison_ids"]),
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def _row_to_snapshot(row: Any) -> Dict[str, Any]:
    return {
        "snapshotId": row["snapshot_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "parentType": row["parent_type"],
        "parentId": row["parent_id"],
        "metrics": loads(row["metrics"]),
        "dimensions": loads(row["dimensions"]),
        "snapshotVersion": row["snapshot_version"],
        "snapshotAt": row["snapshot_at"],
    }


def _latest_scores(ctx: UserContext) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_scores_v8 s
            WHERE tenant_id = ? AND org_id = ?
              AND created_at = (
                SELECT MAX(inner_s.created_at)
                FROM weight_scores_v8 inner_s
                WHERE inner_s.tenant_id = s.tenant_id
                  AND inner_s.org_id = s.org_id
                  AND inner_s.object_type = s.object_type
                  AND inner_s.object_id = s.object_id
              )
            ORDER BY object_type ASC, object_id ASC
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    return [_row_to_score(row) for row in rows]


def _latest_snapshots(ctx: UserContext) -> Dict[str, Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_metric_snapshots_v8 s
            WHERE tenant_id = ? AND org_id = ?
              AND snapshot_at = (
                SELECT MAX(inner_s.snapshot_at)
                FROM weight_metric_snapshots_v8 inner_s
                WHERE inner_s.tenant_id = s.tenant_id
                  AND inner_s.org_id = s.org_id
                  AND inner_s.object_type = s.object_type
                  AND inner_s.object_id = s.object_id
              )
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    return {f"{row['object_type']}::{row['object_id']}": _row_to_snapshot(row) for row in rows}


def _score_maps(scores: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    result: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for score in scores:
        result[score["objectType"]][score["objectId"]] = score
    return result


def _traffic_share(product_snapshot: Dict[str, Any] | None, store_snapshot: Dict[str, Any] | None) -> float:
    if not product_snapshot or not store_snapshot:
        return 0.0
    product_traffic = _num((product_snapshot.get("metrics") or {}).get("traffic"), 0.0)
    store_traffic = _num((store_snapshot.get("metrics") or {}).get("naturalTraffic"), 0.0)
    if store_traffic <= 0:
        return 0.0
    return min(product_traffic / store_traffic, 1.0)


def _state_by_score(object_type: str, score: float, role_tag: str | None = None) -> tuple[str, str, str]:
    if object_type == "product":
        if score >= 82:
            state = "promote_candidate"
        elif score >= 64:
            state = "maintain"
        elif score >= 52:
            state = "observe"
        elif score >= 40:
            state = "test_repair" if role_tag in TEST_STORE_ROLES else "repair"
        elif score >= 28:
            state = "hard_demote_candidate" if role_tag in PROTECTED_STORE_ROLES else "demote_candidate"
        else:
            state = "stop_loss_review" if role_tag in PROTECTED_STORE_ROLES else "demote_candidate"
        label = PRODUCT_STATE_LABELS[state]
    elif object_type == "store":
        if score >= 82:
            state = "expand_candidate"
        elif score >= 65:
            state = "maintain"
        elif score >= 52:
            state = "observe"
        elif score >= 38:
            state = "resource_limit_candidate"
        elif score >= 24:
            state = "demotion_review"
        else:
            state = "manager_intervention"
        label = STORE_STATE_LABELS[state]
    else:
        if score >= 82:
            state = "promotion_suggestion"
        elif score >= 65:
            state = "maintain"
        elif score >= 48:
            state = "coaching_observe"
        elif score >= 30:
            state = "demotion_review"
        else:
            state = "permission_adjustment_review"
        label = OPERATOR_STATE_LABELS[state]
    if score < 35:
        risk = "高"
    elif score < 55:
        risk = "中"
    elif score < 75:
        risk = "观察"
    else:
        risk = "低"
    return state, label, risk


def _product_adjustment(score: Dict[str, Any], snapshot: Dict[str, Any] | None, store_score: Dict[str, Any] | None, store_snapshot: Dict[str, Any] | None) -> Dict[str, Any]:
    base = _num(score.get("weightScore"), 0.0)
    store_base = _num((store_score or {}).get("weightScore"), 60.0)
    role_tag = ((store_snapshot or {}).get("dimensions") or {}).get("storeRoleTag") or "unknown_store"
    share = _traffic_share(snapshot, store_snapshot)
    negative_count = int(_num(score.get("negativeCount"), 0.0))
    delta = 0.0
    factors = {"storeRoleTag": role_tag, "storeWeightScore": store_base, "trafficShare": round(share, 4), "negativeCount": negative_count}
    context_type = "standard_store_context"
    summary = "按普通店铺上下文解释商品权重。"
    if role_tag in PROTECTED_STORE_ROLES:
        context_type = "protected_store_context"
        if base < 55:
            delta -= 10 + min(share * 10, 8) + min(negative_count * 2, 6)
            summary = "商品处于高权重保护型店铺，负向波动会放大处理强度。"
        elif base >= 75:
            delta += 4
            summary = "商品处于高权重店铺且表现较稳，可作为核心资源候选。"
    elif role_tag in TEST_STORE_ROLES:
        context_type = "test_store_context"
        if base < 55:
            delta += 8
            summary = "商品处于测试/低权重店铺，先增加试错缓冲，不直接强降权。"
        else:
            delta -= 2
            summary = "测试店铺表现需要更多样本验证。"
    elif role_tag in GROWTH_STORE_ROLES:
        context_type = "growth_store_context"
        if base < 55:
            delta += 3
            summary = "成长店铺短期波动先谨慎修正，避免打断增长。"
        elif base >= 75:
            delta += 5
            summary = "成长店铺中表现较好的商品可进入升权候选观察。"
    if store_base >= 78 and base < 45:
        delta -= 5
        factors["storeDragRisk"] = "high"
        summary = "商品低分叠加高权重店铺，存在拖累店铺资产的风险。"
    adjusted = _clamp(base + delta)
    state, label, risk = _state_by_score("product", adjusted, role_tag=role_tag)
    if state == "stop_loss_review":
        intensity = "L5"
    elif state == "hard_demote_candidate":
        intensity = "L4"
    elif state == "demote_candidate":
        intensity = "L3"
    elif state in {"repair", "test_repair"}:
        intensity = "L2"
    else:
        intensity = "L1"
    return {"adjustedScore": adjusted, "adjustedState": state, "adjustedLabel": label, "riskLevel": risk, "taskIntensityLevel": intensity, "taskIntensityLabel": INTENSITY_LABELS[intensity], "contextType": context_type, "contextSummary": summary, "contextFactors": factors}


def _store_adjustment(score: Dict[str, Any], snapshot: Dict[str, Any] | None) -> Dict[str, Any]:
    base = _num(score.get("weightScore"), 0.0)
    role_tag = ((snapshot or {}).get("dimensions") or {}).get("storeRoleTag") or "unknown_store"
    delta = 0.0
    summary = "按店铺自身角色解释店铺权重。"
    context_type = "store_context"
    if role_tag in PROTECTED_STORE_ROLES:
        context_type = "protected_store_context"
        if base < 55:
            delta -= 6
            summary = "保护型店铺低分需要更快总管介入。"
        elif base >= 75:
            delta += 5
            summary = "保护型店铺表现稳定，是高权重经营资产。"
    elif role_tag in TEST_STORE_ROLES:
        context_type = "test_store_context"
        if base < 55:
            delta += 4
            summary = "测试/低权重店铺允许更长测试周期。"
    adjusted = _clamp(base + delta)
    state, label, risk = _state_by_score("store", adjusted)
    intensity = "L4" if state in {"demotion_review", "manager_intervention"} else ("L3" if state == "resource_limit_candidate" else "L1")
    return {"adjustedScore": adjusted, "adjustedState": state, "adjustedLabel": label, "riskLevel": risk, "taskIntensityLevel": intensity, "taskIntensityLabel": INTENSITY_LABELS[intensity], "contextType": context_type, "contextSummary": summary, "contextFactors": {"storeRoleTag": role_tag}}


def _operator_adjustment(score: Dict[str, Any], snapshot: Dict[str, Any] | None) -> Dict[str, Any]:
    base = _num(score.get("weightScore"), 0.0)
    metrics = (snapshot or {}).get("metrics") or {}
    assigned_store_count = int(_num(metrics.get("assignedStoreCount"), 0.0))
    delta = 0.0
    summary = "运营权重只进入复核和建议，不自动处罚。"
    if assigned_store_count >= 2 and base < 55:
        delta += 3
        summary = "运营负责多店铺时低分需要结合店铺难度复核，先做缓冲。"
    if base >= 78 and assigned_store_count >= 1:
        delta += 4
        summary = "运营在有店铺责任情况下表现较好，可作为升权建议证据。"
    adjusted = _clamp(base + delta)
    state, label, risk = _state_by_score("operator", adjusted)
    intensity = "H3" if state == "permission_adjustment_review" else ("H2" if state in {"coaching_observe", "demotion_review"} else "H1")
    return {"adjustedScore": adjusted, "adjustedState": state, "adjustedLabel": label, "riskLevel": risk, "taskIntensityLevel": intensity, "taskIntensityLabel": INTENSITY_LABELS[intensity], "contextType": "operator_human_review_context", "contextSummary": summary, "contextFactors": {"assignedStoreCount": assigned_store_count, "humanSafetyBoundary": "must_review_by_manager_or_owner"}}


def _build_adjustment(score: Dict[str, Any], snapshots: Dict[str, Dict[str, Any]], maps: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
    key = f"{score['objectType']}::{score['objectId']}"
    snapshot = snapshots.get(key)
    parent_type = (snapshot or {}).get("parentType")
    parent_id = (snapshot or {}).get("parentId")
    if score["objectType"] == "product":
        store_snapshot = snapshots.get(f"store::{parent_id}") if parent_id else None
        store_score = maps.get("store", {}).get(parent_id or "")
        adjusted = _product_adjustment(score, snapshot, store_score, store_snapshot)
    elif score["objectType"] == "store":
        adjusted = _store_adjustment(score, snapshot)
    else:
        adjusted = _operator_adjustment(score, snapshot)
    return {
        "adjustmentId": make_id("CWADJ"),
        "tenantId": score["tenantId"],
        "orgId": score["orgId"],
        "objectType": score["objectType"],
        "objectId": score["objectId"],
        "objectName": score.get("objectName"),
        "parentType": parent_type,
        "parentId": parent_id,
        "baseScore": _num(score.get("weightScore")),
        "adjustedScore": round(adjusted["adjustedScore"], 2),
        "baseState": score.get("weightState"),
        "adjustedState": adjusted["adjustedState"],
        "adjustedLabel": adjusted["adjustedLabel"],
        "riskLevel": adjusted["riskLevel"],
        "taskIntensityLevel": adjusted["taskIntensityLevel"],
        "taskIntensityLabel": adjusted["taskIntensityLabel"],
        "contextType": adjusted["contextType"],
        "contextSummary": adjusted["contextSummary"],
        "contextFactors": adjusted["contextFactors"],
        "relatedScoreId": score.get("scoreId"),
        "payload": {"version": V85_CONTEXT_WEIGHT_VERSION, "rule": "V8.5 只做上下文权重修正和任务强度提示，不生成任务。", "baseStateLabel": score.get("stateLabel")},
        "createdAt": now_iso(),
    }


def _insert_adjustment(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO context_weight_adjustments_v8 (
                adjustment_id, tenant_id, org_id, object_type, object_id, object_name, parent_type, parent_id,
                base_score, adjusted_score, base_state, adjusted_state, adjusted_label, risk_level,
                task_intensity_level, task_intensity_label, context_type, context_summary, context_factors,
                related_score_id, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["adjustmentId"], item["tenantId"], item["orgId"], item["objectType"], item["objectId"], item.get("objectName"), item.get("parentType"), item.get("parentId"), item["baseScore"], item["adjustedScore"], item.get("baseState"), item["adjustedState"], item["adjustedLabel"], item["riskLevel"], item["taskIntensityLevel"], item["taskIntensityLabel"], item["contextType"], item["contextSummary"], dumps(item.get("contextFactors") or {}), item.get("relatedScoreId"), dumps(item.get("payload") or {}), item["createdAt"]),
        )
        conn.commit()


def generate_context_weight_adjustments(ctx: UserContext) -> Dict[str, Any]:
    ensure_context_weight_tables()
    scores = _latest_scores(ctx)
    if not scores:
        generate_weight_scores(ctx)
        scores = _latest_scores(ctx)
    snapshots = _latest_snapshots(ctx)
    maps = _score_maps(scores)
    created = [_build_adjustment(score, snapshots, maps) for score in scores]
    for item in created:
        _insert_adjustment(item)
    by_state: Dict[str, int] = defaultdict(int)
    by_intensity: Dict[str, int] = defaultdict(int)
    by_context: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in created:
        by_state[item["adjustedState"]] += 1
        by_intensity[item["taskIntensityLevel"]] += 1
        by_context[item["contextType"]] += 1
        by_object[item["objectType"]] += 1
    return {"version": V85_CONTEXT_WEIGHT_VERSION, "createdCount": len(created), "byAdjustedState": dict(by_state), "byTaskIntensity": dict(by_intensity), "byContextType": dict(by_context), "byObjectType": dict(by_object), "adjustments": created, "rule": "V8.5 输出上下文修正后的权重状态和任务强度提示；V8.7 才生成任务。"}


def _row_to_adjustment(row: Any) -> Dict[str, Any]:
    return {
        "adjustmentId": row["adjustment_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "parentType": row["parent_type"],
        "parentId": row["parent_id"],
        "baseScore": row["base_score"],
        "adjustedScore": row["adjusted_score"],
        "baseState": row["base_state"],
        "adjustedState": row["adjusted_state"],
        "adjustedLabel": row["adjusted_label"],
        "riskLevel": row["risk_level"],
        "taskIntensityLevel": row["task_intensity_level"],
        "taskIntensityLabel": row["task_intensity_label"],
        "contextType": row["context_type"],
        "contextSummary": row["context_summary"],
        "contextFactors": loads(row["context_factors"]),
        "relatedScoreId": row["related_score_id"],
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def context_weight_summary(ctx: UserContext, object_type: str | None = None, task_intensity_level: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_context_weight_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if object_type in {"product", "store", "operator"}:
        filters.append("object_type = ?")
        params.append(object_type)
    if task_intensity_level:
        filters.append("task_intensity_level = ?")
        params.append(task_intensity_level)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM context_weight_adjustments_v8 WHERE {' AND '.join(filters)} ORDER BY created_at DESC LIMIT ?", tuple(params)).fetchall()
    adjustments = [_row_to_adjustment(row) for row in rows]
    by_state: Dict[str, int] = defaultdict(int)
    by_intensity: Dict[str, int] = defaultdict(int)
    by_context: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in adjustments:
        by_state[item["adjustedState"]] += 1
        by_intensity[item["taskIntensityLevel"]] += 1
        by_context[item["contextType"]] += 1
        by_object[item["objectType"]] += 1
    return {"version": V85_CONTEXT_WEIGHT_VERSION, "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "roleId": ctx.role_id, "adjustmentCount": len(adjustments), "byAdjustedState": dict(by_state), "byTaskIntensity": dict(by_intensity), "byContextType": dict(by_context), "byObjectType": dict(by_object), "intensityLabels": INTENSITY_LABELS, "adjustments": adjustments, "rule": "V8.5 根据店铺角色、店铺权重、商品拖累和运营责任上下文修正权重状态；不生成任务。"}
