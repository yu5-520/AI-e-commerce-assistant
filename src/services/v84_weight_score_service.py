"""V8.4 object weight scoring service.

V8.3 explains linked metric relations. V8.4 turns snapshots, comparisons,
RAG hits, and linked relations into object-level weight states for product,
store, and operator. It still does not generate adjustment tasks, change
permissions, or punish operators automatically.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.v80_weight_snapshot_service import ensure_weight_snapshot_tables, generate_weight_snapshots
from src.services.v81_weight_comparison_service import ensure_weight_comparison_tables, generate_weight_comparisons
from src.services.v82_weight_rag_gate_service import ensure_weight_rag_tables, generate_weight_rag_hits
from src.services.v83_linked_metric_relation_service import ensure_linked_relation_tables, generate_linked_metric_relations

V84_WEIGHT_SCORE_VERSION = "8.4.0"

CORE_METRICS = {
    "product": {"roi", "conversionRate", "grossMargin", "refundRate", "goodReviewRate", "stock", "traffic"},
    "store": {"storeRoi", "goodReviewRate", "naturalTraffic", "productHealthRate", "ctr"},
    "operator": {"taskCompletionRate", "onTimeRate", "reviewQualityScore", "evidenceCompleteness", "storeMaintenanceScore"},
}

STATE_LABELS = {
    "product": {
        "promote_candidate": "升权候选",
        "maintain": "维持",
        "observe": "观察",
        "repair": "修复",
        "demote_candidate": "降权候选",
        "stop_loss_review": "止损复核",
    },
    "store": {
        "expand_candidate": "扩权候选",
        "maintain": "维持",
        "observe": "观察",
        "resource_limit_candidate": "限制资源候选",
        "demotion_review": "降权复核",
        "manager_intervention": "总管介入",
    },
    "operator": {
        "promotion_suggestion": "升权建议",
        "maintain": "维持",
        "coaching_observe": "辅导观察",
        "demotion_review": "降权复核",
        "permission_adjustment_review": "权限调整复核",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_weight_score_tables() -> None:
    ensure_weight_snapshot_tables()
    ensure_weight_comparison_tables()
    ensure_weight_rag_tables()
    ensure_linked_relation_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weight_scores_v8 (
                score_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                weight_score REAL NOT NULL,
                weight_state TEXT NOT NULL,
                state_label TEXT,
                risk_level TEXT,
                score_direction TEXT,
                positive_count INTEGER DEFAULT 0,
                neutral_count INTEGER DEFAULT 0,
                negative_count INTEGER DEFAULT 0,
                evidence_count INTEGER DEFAULT 0,
                related_relation_ids TEXT,
                related_hit_ids TEXT,
                related_comparison_ids TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_scores_object_v8 ON weight_scores_v8(tenant_id, org_id, object_type, object_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_scores_state_v8 ON weight_scores_v8(weight_state, risk_level, score_direction)")
        conn.commit()


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _row_snapshot(row: Any) -> Dict[str, Any]:
    return {
        "snapshotId": row["snapshot_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "snapshotVersion": row["snapshot_version"],
        "snapshotAt": row["snapshot_at"],
        "metrics": loads(row["metrics"]),
        "dimensions": loads(row["dimensions"]),
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def _latest_snapshots(ctx: UserContext) -> List[Dict[str, Any]]:
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
            ORDER BY object_type ASC, object_id ASC
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    return [_row_snapshot(row) for row in rows]


def _load_relations(ctx: UserContext) -> Dict[str, List[Dict[str, Any]]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM linked_metric_relations_v8
            WHERE tenant_id = ? AND org_id = ?
            ORDER BY created_at DESC
            LIMIT 1200
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    result: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = f"{row['object_type']}::{row['object_id']}"
        result[key].append({
            "relationId": row["relation_id"],
            "relationType": row["relation_type"],
            "relationName": row["relation_name"],
            "riskDirection": row["risk_direction"],
            "confidence": row["confidence"],
            "evidenceCount": row["evidence_count"],
            "metricKeys": loads(row["metric_keys"]),
            "relatedHitIds": loads(row["related_hit_ids"]),
            "relatedComparisonIds": loads(row["related_comparison_ids"]),
            "conclusion": row["conclusion"],
        })
    return result


def _load_hits(ctx: UserContext) -> Dict[str, List[Dict[str, Any]]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_rag_standard_hits_v8
            WHERE tenant_id = ? AND org_id = ?
            ORDER BY created_at DESC
            LIMIT 1600
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    result: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = f"{row['object_type']}::{row['object_id']}"
        result[key].append({
            "hitId": row["hit_id"],
            "metricName": row["metric_name"],
            "hitStatus": row["hit_status"],
            "severity": row["severity"],
            "consecutiveLowCount": row["consecutive_low_count"],
            "domain": row["domain"],
        })
    return result


def _load_comparisons(ctx: UserContext) -> Dict[str, List[Dict[str, Any]]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_metric_comparisons_v8
            WHERE tenant_id = ? AND org_id = ?
            ORDER BY created_at DESC
            LIMIT 1600
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    result: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = f"{row['object_type']}::{row['object_id']}"
        result[key].append({
            "comparisonId": row["comparison_id"],
            "metricName": row["metric_name"],
            "comparisonType": row["comparison_type"],
            "direction": row["direction"],
            "changeRate": row["change_rate"],
            "confidence": row["confidence"],
        })
    return result


def _relation_delta(relation: Dict[str, Any]) -> float:
    confidence_weight = {"high": 1.2, "medium": 1.0, "low": 0.7}.get(str(relation.get("confidence")), 1.0)
    evidence_bonus = min(_num(relation.get("evidenceCount")), 5.0) * 0.6
    if relation.get("riskDirection") == "positive":
        return 8.0 * confidence_weight + evidence_bonus
    if relation.get("riskDirection") == "negative":
        return -(10.0 * confidence_weight + evidence_bonus)
    return -1.5 if relation.get("riskDirection") == "neutral" else 0.0


def _hit_delta(hit: Dict[str, Any], object_type: str) -> float:
    status = hit.get("hitStatus")
    if status == "within_standard":
        return 2.0
    severity = hit.get("severity")
    base = {"高": -9.0, "中": -6.0, "低": -3.0, "观察": -2.0}.get(str(severity), -2.0)
    if object_type == "operator":
        base *= 0.65
    consecutive = min(_num(hit.get("consecutiveLowCount")), 4.0)
    return base - consecutive


def _comparison_delta(comparison: Dict[str, Any], object_type: str) -> float:
    metric = comparison.get("metricName")
    if metric not in CORE_METRICS.get(object_type, set()):
        return 0.0
    direction = comparison.get("direction")
    comparison_type = comparison.get("comparisonType")
    change = abs(_num(comparison.get("changeRate"), 0.0))
    weight = 1.0 if comparison_type == "period_over_period" else 0.55
    if direction == "up":
        return min(4.0, 2.0 + change * 4.0) * weight
    if direction == "down":
        return -min(4.5, 2.5 + change * 5.0) * weight
    if direction == "stable":
        return 0.8 * weight
    return 0.0


def _state_for_score(object_type: str, score: float, negative_count: int, positive_count: int) -> tuple[str, str, str, str]:
    if object_type == "product":
        if score >= 82 and positive_count >= 1:
            state = "promote_candidate"
        elif score >= 65:
            state = "maintain"
        elif score >= 52:
            state = "observe"
        elif score >= 38:
            state = "repair"
        elif score >= 24:
            state = "demote_candidate"
        else:
            state = "stop_loss_review"
    elif object_type == "store":
        if score >= 82 and positive_count >= 1:
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
    else:
        if score >= 82 and positive_count >= 1:
            state = "promotion_suggestion"
        elif score >= 65:
            state = "maintain"
        elif score >= 48:
            state = "coaching_observe"
        elif score >= 30:
            state = "demotion_review"
        else:
            state = "permission_adjustment_review"
    if score >= 75:
        risk = "低"
        direction = "positive"
    elif score >= 55:
        risk = "观察"
        direction = "stable"
    elif score >= 35:
        risk = "中"
        direction = "negative"
    else:
        risk = "高"
        direction = "negative"
    if negative_count >= 3 and score < 55:
        risk = "高" if score < 40 else "中"
    return state, STATE_LABELS[object_type][state], risk, direction


def _object_score(snapshot: Dict[str, Any], relations: List[Dict[str, Any]], hits: List[Dict[str, Any]], comparisons: List[Dict[str, Any]]) -> Dict[str, Any]:
    object_type = snapshot["objectType"]
    score = 62.0
    if object_type == "operator":
        score = 66.0
    relation_delta = sum(_relation_delta(item) for item in relations)
    hit_delta = sum(_hit_delta(item, object_type) for item in hits)
    comparison_delta = sum(_comparison_delta(item, object_type) for item in comparisons[:20])
    score = _clamp(score + relation_delta + hit_delta + comparison_delta)
    positive_count = len([item for item in relations if item.get("riskDirection") == "positive"])
    neutral_count = len([item for item in relations if item.get("riskDirection") == "neutral"])
    negative_count = len([item for item in relations if item.get("riskDirection") == "negative"])
    state, label, risk, direction = _state_for_score(object_type, score, negative_count, positive_count)
    relation_ids = [item["relationId"] for item in relations]
    hit_ids = [item["hitId"] for item in hits[:20] if item.get("hitStatus") != "within_standard"]
    comparison_ids = [item["comparisonId"] for item in comparisons[:20]]
    return {
        "scoreId": make_id("WSCORE"),
        "tenantId": snapshot["tenantId"],
        "orgId": snapshot["orgId"],
        "objectType": object_type,
        "objectId": snapshot["objectId"],
        "objectName": snapshot.get("objectName"),
        "weightScore": round(score, 2),
        "weightState": state,
        "stateLabel": label,
        "riskLevel": risk,
        "scoreDirection": direction,
        "positiveCount": positive_count,
        "neutralCount": neutral_count,
        "negativeCount": negative_count,
        "evidenceCount": len(relation_ids) + len(hit_ids) + len(comparison_ids),
        "relatedRelationIds": relation_ids,
        "relatedHitIds": hit_ids,
        "relatedComparisonIds": comparison_ids,
        "payload": {
            "version": V84_WEIGHT_SCORE_VERSION,
            "snapshotVersion": snapshot.get("snapshotVersion"),
            "calculation": {
                "baseScore": 66.0 if object_type == "operator" else 62.0,
                "relationDelta": round(relation_delta, 2),
                "hitDelta": round(hit_delta, 2),
                "comparisonDelta": round(comparison_delta, 2),
            },
            "rule": "V8.4 只生成对象权重状态，不生成升降权任务。",
            "operatorSafetyBoundary": "运营权重只用于复核和建议，不能自动处罚或自动改权限。" if object_type == "operator" else None,
        },
        "createdAt": now_iso(),
    }


def _insert_score(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO weight_scores_v8 (
                score_id, tenant_id, org_id, object_type, object_id, object_name, weight_score,
                weight_state, state_label, risk_level, score_direction, positive_count, neutral_count,
                negative_count, evidence_count, related_relation_ids, related_hit_ids, related_comparison_ids,
                payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["scoreId"], item["tenantId"], item["orgId"], item["objectType"], item["objectId"], item.get("objectName"), item["weightScore"], item["weightState"], item["stateLabel"], item["riskLevel"], item["scoreDirection"], item["positiveCount"], item["neutralCount"], item["negativeCount"], item["evidenceCount"], dumps(item.get("relatedRelationIds") or []), dumps(item.get("relatedHitIds") or []), dumps(item.get("relatedComparisonIds") or []), dumps(item.get("payload") or {}), item["createdAt"]),
        )
        conn.commit()


def generate_weight_scores(ctx: UserContext) -> Dict[str, Any]:
    ensure_weight_score_tables()
    snapshots = _latest_snapshots(ctx)
    if not snapshots:
        generate_weight_snapshots(ctx)
        snapshots = _latest_snapshots(ctx)
    relations = _load_relations(ctx)
    if not relations:
        generate_linked_metric_relations(ctx)
        relations = _load_relations(ctx)
    hits = _load_hits(ctx)
    if not hits:
        generate_weight_rag_hits(ctx)
        hits = _load_hits(ctx)
    comparisons = _load_comparisons(ctx)
    if not comparisons:
        generate_weight_comparisons(ctx)
        comparisons = _load_comparisons(ctx)
    created: List[Dict[str, Any]] = []
    for snapshot in snapshots:
        key = f"{snapshot['objectType']}::{snapshot['objectId']}"
        item = _object_score(snapshot, relations.get(key, []), hits.get(key, []), comparisons.get(key, []))
        created.append(item)
        _insert_score(item)
    by_state: Dict[str, int] = defaultdict(int)
    by_risk: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in created:
        by_state[item["weightState"]] += 1
        by_risk[item["riskLevel"]] += 1
        by_object[item["objectType"]] += 1
    return {"version": V84_WEIGHT_SCORE_VERSION, "createdCount": len(created), "byState": dict(by_state), "byRiskLevel": dict(by_risk), "byObjectType": dict(by_object), "scores": created, "rule": "V8.4 生成对象权重评分和状态；V8.5 才做上下文权重修正，V8.7 才生成任务。"}


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


def weight_score_summary(ctx: UserContext, object_type: str | None = None, weight_state: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_weight_score_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if object_type in {"product", "store", "operator"}:
        filters.append("object_type = ?")
        params.append(object_type)
    if weight_state:
        filters.append("weight_state = ?")
        params.append(weight_state)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM weight_scores_v8 WHERE {' AND '.join(filters)} ORDER BY created_at DESC LIMIT ?", tuple(params)).fetchall()
    scores = [_row_to_score(row) for row in rows]
    by_state: Dict[str, int] = defaultdict(int)
    by_risk: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in scores:
        by_state[item["weightState"]] += 1
        by_risk[item["riskLevel"]] += 1
        by_object[item["objectType"]] += 1
    return {"version": V84_WEIGHT_SCORE_VERSION, "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "roleId": ctx.role_id, "scoreCount": len(scores), "byState": dict(by_state), "byRiskLevel": dict(by_risk), "byObjectType": dict(by_object), "stateLabels": STATE_LABELS, "scores": scores, "rule": "V8.4 权重评分只输出状态，不自动生成任务、不自动改变权限。"}
