"""V8.6 cross validation service.

V8.5 produces context-corrected weight states and task-intensity hints.
V8.6 cross-validates those hints across product, store, operator, upstream score,
linked relation, RAG hit, and period comparison evidence. It determines whether a
candidate action is confirmed, conflicted, buffered, protected, or needs review.
It still does not create real tasks or execute weight changes.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.v85_context_weight_adjustment_service import ensure_context_weight_tables, generate_context_weight_adjustments

V86_CROSS_VALIDATION_VERSION = "8.6.0"

HARD_INTENSITIES = {"L4", "L5"}
TASK_READY_STATUSES = {"confirmed", "protected_confirmed"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_cross_validation_tables() -> None:
    ensure_context_weight_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weight_cross_validations_v8 (
                validation_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                parent_type TEXT,
                parent_id TEXT,
                validation_status TEXT NOT NULL,
                validation_label TEXT,
                readiness TEXT NOT NULL,
                confidence TEXT,
                final_intensity_level TEXT,
                final_intensity_label TEXT,
                cross_score REAL,
                evidence_count INTEGER DEFAULT 0,
                conflict_count INTEGER DEFAULT 0,
                related_adjustment_ids TEXT,
                related_score_ids TEXT,
                cross_factors TEXT,
                conclusion TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cross_validations_object_v8 ON weight_cross_validations_v8(tenant_id, org_id, object_type, object_id, validation_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cross_validations_readiness_v8 ON weight_cross_validations_v8(readiness, final_intensity_level, confidence)")
        conn.commit()


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_adjustments(ctx: UserContext) -> List[Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM context_weight_adjustments_v8 a
            WHERE tenant_id = ? AND org_id = ?
              AND created_at = (
                SELECT MAX(inner_a.created_at)
                FROM context_weight_adjustments_v8 inner_a
                WHERE inner_a.tenant_id = a.tenant_id
                  AND inner_a.org_id = a.org_id
                  AND inner_a.object_type = a.object_type
                  AND inner_a.object_id = a.object_id
              )
            ORDER BY object_type ASC, object_id ASC
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    return [_row_to_adjustment(row) for row in rows]


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


def _load_latest_relations(ctx: UserContext) -> Dict[str, List[Dict[str, Any]]]:
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
        result[key].append({"relationId": row["relation_id"], "riskDirection": row["risk_direction"], "confidence": row["confidence"], "evidenceCount": row["evidence_count"], "relationType": row["relation_type"]})
    return result


def _load_latest_hits(ctx: UserContext) -> Dict[str, List[Dict[str, Any]]]:
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
        result[key].append({"hitId": row["hit_id"], "hitStatus": row["hit_status"], "severity": row["severity"], "metricName": row["metric_name"], "consecutiveLowCount": row["consecutive_low_count"]})
    return result


def _load_latest_scores(ctx: UserContext) -> Dict[str, Dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_scores_v8
            WHERE tenant_id = ? AND org_id = ?
            ORDER BY created_at DESC
            LIMIT 800
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    result: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = f"{row['object_type']}::{row['object_id']}"
        if key not in result:
            result[key] = {"scoreId": row["score_id"], "weightScore": row["weight_score"], "weightState": row["weight_state"], "riskLevel": row["risk_level"], "scoreDirection": row["score_direction"]}
    return result


def _maps(adjustments: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    result: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for item in adjustments:
        result[item["objectType"]][item["objectId"]] = item
    return result


def _negative_count(relations: List[Dict[str, Any]]) -> int:
    return len([item for item in relations if item.get("riskDirection") == "negative"])


def _positive_count(relations: List[Dict[str, Any]]) -> int:
    return len([item for item in relations if item.get("riskDirection") == "positive"])


def _bad_hit_count(hits: List[Dict[str, Any]]) -> int:
    return len([item for item in hits if item.get("hitStatus") in {"below_standard", "above_risk_line"}])


def _high_hit_count(hits: List[Dict[str, Any]]) -> int:
    return len([item for item in hits if item.get("severity") == "高"])


def _label(status: str) -> str:
    return {"confirmed": "交叉确认", "protected_confirmed": "保护型确认", "conflict": "存在冲突", "buffered": "缓冲观察", "needs_review": "需要复核", "human_review_only": "仅人工复核", "insufficient_evidence": "证据不足"}.get(status, status)


def _ready(status: str, object_type: str) -> str:
    if object_type == "operator":
        return "human_review_only"
    return "ready_for_task_group" if status in TASK_READY_STATUSES else "not_ready"


def _confidence(evidence_count: int, conflict_count: int) -> str:
    if conflict_count >= 2:
        return "low"
    if evidence_count >= 6:
        return "high"
    if evidence_count >= 3:
        return "medium"
    return "low"


def _intensity_for_status(item: Dict[str, Any], status: str) -> tuple[str, str]:
    original = item.get("taskIntensityLevel") or "L1"
    if item["objectType"] == "operator":
        level = original if str(original).startswith("H") else "H1"
    elif status in {"conflict", "buffered", "insufficient_evidence"}:
        level = "L2" if original in HARD_INTENSITIES else original
    elif status == "protected_confirmed" and original == "L3":
        level = "L4"
    else:
        level = original
    labels = {"L1": "观察", "L2": "修复", "L3": "降权候选", "L4": "强降权候选", "L5": "止损复核", "H1": "人工复核依据", "H2": "辅导观察", "H3": "权限调整复核"}
    return level, labels.get(level, level)


def _product_validation(item: Dict[str, Any], maps: Dict[str, Dict[str, Dict[str, Any]]], relations: Dict[str, List[Dict[str, Any]]], hits: Dict[str, List[Dict[str, Any]]], scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    key = f"product::{item['objectId']}"
    store = maps.get("store", {}).get(item.get("parentId") or "")
    item_relations = relations.get(key, [])
    item_hits = hits.get(key, [])
    negative = _negative_count(item_relations)
    positive = _positive_count(item_relations)
    bad_hits = _bad_hit_count(item_hits)
    high_hits = _high_hit_count(item_hits)
    store_score = _num((store or {}).get("adjustedScore"), 60.0)
    store_intensity = (store or {}).get("taskIntensityLevel")
    role_tag = (item.get("contextFactors") or {}).get("storeRoleTag")
    hard = item.get("taskIntensityLevel") in HARD_INTENSITIES
    conflict_count = 0
    status = "needs_review"
    conclusion = "商品权重需要结合店铺与自身证据继续复核。"
    factors = {"storeAdjustedScore": store_score, "storeIntensity": store_intensity, "storeRoleTag": role_tag, "negativeRelations": negative, "positiveRelations": positive, "badHits": bad_hits, "highHits": high_hits}
    if hard and store_score >= 70 and (negative >= 1 or high_hits >= 1 or bad_hits >= 2):
        status = "protected_confirmed" if role_tag in {"brand_main_store", "profit_core_store", "traffic_core_store"} else "confirmed"
        conclusion = "商品负向证据与高权重店铺上下文一致，可进入后续交叉任务组候选。"
    elif hard and store_score < 55:
        status = "conflict"
        conflict_count = 2
        conclusion = "商品强动作与低分店铺同时出现，可能是店铺结构问题，不宜直接归因到单品。"
    elif item.get("taskIntensityLevel") in {"L1", "L2"} and positive >= 1 and bad_hits <= 1:
        status = "buffered"
        conclusion = "商品存在正向或缓冲证据，先观察或修复，不进入强动作。"
    elif bad_hits >= 2 and negative >= 1:
        status = "confirmed"
        conclusion = "商品标准线与联动关系同时异常，可作为后续任务候选。"
    elif positive >= 1 and negative == 0:
        status = "buffered"
        conclusion = "商品有正向联动，暂不进入降权任务候选。"
    else:
        status = "insufficient_evidence"
        conclusion = "商品证据不足，等待更多周期数据。"
    evidence_count = negative + positive + bad_hits + len(item.get("relatedScoreId") or "") // 100 + (1 if store else 0)
    return {"status": status, "confidence": _confidence(evidence_count, conflict_count), "conflictCount": conflict_count, "evidenceCount": evidence_count, "crossFactors": factors, "conclusion": conclusion, "relatedAdjustmentIds": [item["adjustmentId"]] + ([store["adjustmentId"]] if store else []), "relatedScoreIds": [scores.get(key, {}).get("scoreId") or item.get("relatedScoreId")]}


def _store_validation(item: Dict[str, Any], maps: Dict[str, Dict[str, Dict[str, Any]]], relations: Dict[str, List[Dict[str, Any]]], hits: Dict[str, List[Dict[str, Any]]], scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    products = [p for p in maps.get("product", {}).values() if p.get("parentId") == item["objectId"]]
    hard_products = [p for p in products if p.get("taskIntensityLevel") in HARD_INTENSITIES]
    product_negatives = len([p for p in products if p.get("adjustedScore", 100) < 55])
    item_relations = relations.get(f"store::{item['objectId']}", [])
    bad_hits = _bad_hit_count(hits.get(f"store::{item['objectId']}", []))
    conflict_count = 0
    status = "needs_review"
    conclusion = "店铺需要结合商品结构验证。"
    if item.get("taskIntensityLevel") in {"L3", "L4"} and product_negatives >= 2:
        status = "confirmed"
        conclusion = "店铺低权重与多个商品异常一致，可进入店铺资源调整候选。"
    elif item.get("taskIntensityLevel") in {"L3", "L4"} and not products:
        status = "insufficient_evidence"
        conclusion = "店铺缺少商品侧交叉样本，不进入强动作。"
    elif item.get("taskIntensityLevel") in {"L3", "L4"} and product_negatives == 0:
        status = "conflict"
        conflict_count = 2
        conclusion = "店铺低分但商品侧未同步异常，需要复核数据口径或流量结构。"
    elif hard_products and item.get("adjustedScore", 0) >= 65:
        status = "protected_confirmed"
        conclusion = "店铺整体健康但存在拖累单品，后续任务应指向商品而不是店铺降权。"
    else:
        status = "buffered" if item.get("adjustedScore", 0) >= 55 else "needs_review"
    evidence_count = len(products) + len(hard_products) + bad_hits + _negative_count(item_relations)
    return {"status": status, "confidence": _confidence(evidence_count, conflict_count), "conflictCount": conflict_count, "evidenceCount": evidence_count, "crossFactors": {"productCount": len(products), "negativeProductCount": product_negatives, "hardProductCount": len(hard_products), "storeBadHits": bad_hits}, "conclusion": conclusion, "relatedAdjustmentIds": [item["adjustmentId"]] + [p["adjustmentId"] for p in products[:8]], "relatedScoreIds": [scores.get(f"store::{item['objectId']}", {}).get("scoreId") or item.get("relatedScoreId")]}


def _operator_validation(item: Dict[str, Any], maps: Dict[str, Dict[str, Dict[str, Any]]], relations: Dict[str, List[Dict[str, Any]]], hits: Dict[str, List[Dict[str, Any]]], scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    key = f"operator::{item['objectId']}"
    bad_hits = _bad_hit_count(hits.get(key, []))
    negative = _negative_count(relations.get(key, []))
    positive = _positive_count(relations.get(key, []))
    assigned = (item.get("contextFactors") or {}).get("assignedStoreCount")
    status = "human_review_only"
    conflict_count = 0
    conclusion = "运营对象只输出人工复核依据，不能自动处罚或自动调整权限。"
    if bad_hits >= 2 and negative >= 1:
        conclusion = "运营多项证据异常，可进入人工复核/辅导候选，但必须由总管或老板确认。"
    elif positive >= 1 and bad_hits == 0:
        conclusion = "运营正向证据较好，可作为升权建议材料，但仍需人工审批。"
    evidence_count = bad_hits + negative + positive
    return {"status": status, "confidence": _confidence(evidence_count, conflict_count), "conflictCount": conflict_count, "evidenceCount": evidence_count, "crossFactors": {"badHits": bad_hits, "negativeRelations": negative, "positiveRelations": positive, "assignedStoreCount": assigned, "humanSafetyBoundary": "must_review_by_manager_or_owner"}, "conclusion": conclusion, "relatedAdjustmentIds": [item["adjustmentId"]], "relatedScoreIds": [scores.get(key, {}).get("scoreId") or item.get("relatedScoreId")]}


def _build_validation(item: Dict[str, Any], maps: Dict[str, Dict[str, Dict[str, Any]]], relations: Dict[str, List[Dict[str, Any]]], hits: Dict[str, List[Dict[str, Any]]], scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    if item["objectType"] == "product":
        result = _product_validation(item, maps, relations, hits, scores)
    elif item["objectType"] == "store":
        result = _store_validation(item, maps, relations, hits, scores)
    else:
        result = _operator_validation(item, maps, relations, hits, scores)
    final_level, final_label = _intensity_for_status(item, result["status"])
    return {"validationId": make_id("WCV"), "tenantId": item["tenantId"], "orgId": item["orgId"], "objectType": item["objectType"], "objectId": item["objectId"], "objectName": item.get("objectName"), "parentType": item.get("parentType"), "parentId": item.get("parentId"), "validationStatus": result["status"], "validationLabel": _label(result["status"]), "readiness": _ready(result["status"], item["objectType"]), "confidence": result["confidence"], "finalIntensityLevel": final_level, "finalIntensityLabel": final_label, "crossScore": round(_num(item.get("adjustedScore")), 2), "evidenceCount": result["evidenceCount"], "conflictCount": result["conflictCount"], "relatedAdjustmentIds": [value for value in result["relatedAdjustmentIds"] if value], "relatedScoreIds": [value for value in result["relatedScoreIds"] if value], "crossFactors": result["crossFactors"], "conclusion": result["conclusion"], "payload": {"version": V86_CROSS_VALIDATION_VERSION, "sourceAdjustedState": item.get("adjustedState"), "sourceIntensity": item.get("taskIntensityLevel"), "rule": "V8.6 只做交叉验证，不生成真实任务。"}, "createdAt": now_iso()}


def _insert_validation(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO weight_cross_validations_v8 (
                validation_id, tenant_id, org_id, object_type, object_id, object_name, parent_type, parent_id,
                validation_status, validation_label, readiness, confidence, final_intensity_level, final_intensity_label,
                cross_score, evidence_count, conflict_count, related_adjustment_ids, related_score_ids, cross_factors,
                conclusion, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["validationId"], item["tenantId"], item["orgId"], item["objectType"], item["objectId"], item.get("objectName"), item.get("parentType"), item.get("parentId"), item["validationStatus"], item["validationLabel"], item["readiness"], item["confidence"], item["finalIntensityLevel"], item["finalIntensityLabel"], item["crossScore"], item["evidenceCount"], item["conflictCount"], dumps(item.get("relatedAdjustmentIds") or []), dumps(item.get("relatedScoreIds") or []), dumps(item.get("crossFactors") or {}), item.get("conclusion"), dumps(item.get("payload") or {}), item["createdAt"]),
        )
        conn.commit()


def generate_cross_validations(ctx: UserContext) -> Dict[str, Any]:
    ensure_cross_validation_tables()
    adjustments = _load_adjustments(ctx)
    if not adjustments:
        generate_context_weight_adjustments(ctx)
        adjustments = _load_adjustments(ctx)
    maps = _maps(adjustments)
    relations = _load_latest_relations(ctx)
    hits = _load_latest_hits(ctx)
    scores = _load_latest_scores(ctx)
    created = [_build_validation(item, maps, relations, hits, scores) for item in adjustments]
    for item in created:
        _insert_validation(item)
    by_status: Dict[str, int] = defaultdict(int)
    by_ready: Dict[str, int] = defaultdict(int)
    by_intensity: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in created:
        by_status[item["validationStatus"]] += 1
        by_ready[item["readiness"]] += 1
        by_intensity[item["finalIntensityLevel"]] += 1
        by_object[item["objectType"]] += 1
    return {"version": V86_CROSS_VALIDATION_VERSION, "createdCount": len(created), "byValidationStatus": dict(by_status), "byReadiness": dict(by_ready), "byFinalIntensity": dict(by_intensity), "byObjectType": dict(by_object), "validations": created, "rule": "V8.6 输出交叉验证结果和任务组准备度；V8.7 才生成交叉任务组。"}


def _row_to_validation(row: Any) -> Dict[str, Any]:
    return {"validationId": row["validation_id"], "tenantId": row["tenant_id"], "orgId": row["org_id"], "objectType": row["object_type"], "objectId": row["object_id"], "objectName": row["object_name"], "parentType": row["parent_type"], "parentId": row["parent_id"], "validationStatus": row["validation_status"], "validationLabel": row["validation_label"], "readiness": row["readiness"], "confidence": row["confidence"], "finalIntensityLevel": row["final_intensity_level"], "finalIntensityLabel": row["final_intensity_label"], "crossScore": row["cross_score"], "evidenceCount": row["evidence_count"], "conflictCount": row["conflict_count"], "relatedAdjustmentIds": loads(row["related_adjustment_ids"]), "relatedScoreIds": loads(row["related_score_ids"]), "crossFactors": loads(row["cross_factors"]), "conclusion": row["conclusion"], "payload": loads(row["payload"]), "createdAt": row["created_at"]}


def cross_validation_summary(ctx: UserContext, object_type: str | None = None, validation_status: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_cross_validation_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if object_type in {"product", "store", "operator"}:
        filters.append("object_type = ?")
        params.append(object_type)
    if validation_status:
        filters.append("validation_status = ?")
        params.append(validation_status)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM weight_cross_validations_v8 WHERE {' AND '.join(filters)} ORDER BY created_at DESC LIMIT ?", tuple(params)).fetchall()
    validations = [_row_to_validation(row) for row in rows]
    by_status: Dict[str, int] = defaultdict(int)
    by_ready: Dict[str, int] = defaultdict(int)
    by_intensity: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for item in validations:
        by_status[item["validationStatus"]] += 1
        by_ready[item["readiness"]] += 1
        by_intensity[item["finalIntensityLevel"]] += 1
        by_object[item["objectType"]] += 1
    return {"version": V86_CROSS_VALIDATION_VERSION, "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "roleId": ctx.role_id, "validationCount": len(validations), "byValidationStatus": dict(by_status), "byReadiness": dict(by_ready), "byFinalIntensity": dict(by_intensity), "byObjectType": dict(by_object), "validations": validations, "rule": "V8.6 交叉验证只决定任务组准备度，不生成真实任务、不执行动作。"}
