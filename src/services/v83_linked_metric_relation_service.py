"""V8.3 linked metric relation service.

V8.0 records weight snapshots. V8.1 explains period fluctuation. V8.2 checks
RAG standard-line hits. V8.3 starts linked metric reasoning: it combines metrics,
period directions, and RAG hits to explain whether a fluctuation points to投流质量、
商品承接、库存占用、店铺结构 or 运营行为 issues. It still does not score weight or
create adjustment tasks.
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

V83_LINKED_RELATION_VERSION = "8.3.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_linked_relation_tables() -> None:
    ensure_weight_snapshot_tables()
    ensure_weight_comparison_tables()
    ensure_weight_rag_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS linked_metric_relations_v8 (
                relation_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                relation_type TEXT NOT NULL,
                relation_name TEXT NOT NULL,
                risk_direction TEXT NOT NULL,
                confidence TEXT,
                evidence_count INTEGER DEFAULT 0,
                metric_keys TEXT,
                related_hit_ids TEXT,
                related_comparison_ids TEXT,
                conclusion TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_linked_relations_object_v8 ON linked_metric_relations_v8(tenant_id, org_id, object_type, object_id, relation_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_linked_relations_risk_v8 ON linked_metric_relations_v8(risk_direction, confidence, created_at)")
        conn.commit()


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _row_snapshot(row: Any) -> Dict[str, Any]:
    return {"snapshotId": row["snapshot_id"], "tenantId": row["tenant_id"], "orgId": row["org_id"], "objectType": row["object_type"], "objectId": row["object_id"], "objectName": row["object_name"], "snapshotVersion": row["snapshot_version"], "snapshotAt": row["snapshot_at"], "metrics": loads(row["metrics"]), "dimensions": loads(row["dimensions"]), "payload": loads(row["payload"]), "createdAt": row["created_at"]}


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


def _load_comparisons(ctx: UserContext) -> Dict[str, Dict[str, Dict[str, Any]]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_metric_comparisons_v8
            WHERE tenant_id = ? AND org_id = ?
            ORDER BY created_at DESC
            LIMIT 1200
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    result: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        key = f"{row['object_type']}::{row['object_id']}"
        metric_key = f"{row['metric_name']}::{row['comparison_type']}"
        if metric_key not in result[key]:
            result[key][metric_key] = {"comparisonId": row["comparison_id"], "metricName": row["metric_name"], "comparisonType": row["comparison_type"], "direction": row["direction"], "changeRate": row["change_rate"], "confidence": row["confidence"]}
    return result


def _load_hits(ctx: UserContext) -> Dict[str, Dict[str, Dict[str, Any]]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM weight_rag_standard_hits_v8
            WHERE tenant_id = ? AND org_id = ?
            ORDER BY created_at DESC
            LIMIT 1200
            """,
            (ctx.tenant_id, ctx.org_id),
        ).fetchall()
    result: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        key = f"{row['object_type']}::{row['object_id']}"
        metric = row["metric_name"]
        if metric not in result[key]:
            result[key][metric] = {"hitId": row["hit_id"], "metricName": metric, "hitStatus": row["hit_status"], "severity": row["severity"], "consecutiveLowCount": row["consecutive_low_count"], "domain": row["domain"]}
    return result


def _period_direction(comparisons: Dict[str, Dict[str, Any]], metric: str) -> str | None:
    item = comparisons.get(f"{metric}::period_over_period") or comparisons.get(f"{metric}::multi_period_average")
    return item.get("direction") if item else None


def _period_change(comparisons: Dict[str, Dict[str, Any]], metric: str) -> float:
    item = comparisons.get(f"{metric}::period_over_period") or comparisons.get(f"{metric}::multi_period_average") or {}
    return _num(item.get("changeRate"), 0.0)


def _is_bad_hit(hits: Dict[str, Dict[str, Any]], metric: str) -> bool:
    return (hits.get(metric) or {}).get("hitStatus") in {"below_standard", "above_risk_line"}


def _is_good_hit(hits: Dict[str, Dict[str, Any]], metric: str) -> bool:
    return (hits.get(metric) or {}).get("hitStatus") == "within_standard"


def _collect_ids(hits: Dict[str, Dict[str, Any]], comparisons: Dict[str, Dict[str, Any]], metrics: List[str]) -> tuple[List[str], List[str]]:
    hit_ids = [hits[m]["hitId"] for m in metrics if m in hits]
    comparison_ids = []
    for metric in metrics:
        for key, value in comparisons.items():
            if key.startswith(f"{metric}::") and value.get("comparisonId"):
                comparison_ids.append(value["comparisonId"])
                break
    return hit_ids, comparison_ids


def _relation(snapshot: Dict[str, Any], relation_type: str, relation_name: str, risk_direction: str, metrics: List[str], hits: Dict[str, Dict[str, Any]], comparisons: Dict[str, Dict[str, Any]], conclusion: str, confidence: str = "medium", extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    hit_ids, comparison_ids = _collect_ids(hits, comparisons, metrics)
    return {"relationId": make_id("LMR"), "tenantId": snapshot["tenantId"], "orgId": snapshot["orgId"], "objectType": snapshot["objectType"], "objectId": snapshot["objectId"], "objectName": snapshot.get("objectName"), "relationType": relation_type, "relationName": relation_name, "riskDirection": risk_direction, "confidence": confidence, "evidenceCount": len(hit_ids) + len(comparison_ids), "metricKeys": metrics, "relatedHitIds": hit_ids, "relatedComparisonIds": comparison_ids, "conclusion": conclusion, "payload": {"version": V83_LINKED_RELATION_VERSION, "dimensions": snapshot.get("dimensions") or {}, "rule": "V8.3 只做联动解释，不生成权重评分和任务。", **(extra or {})}, "createdAt": now_iso()}


def _product_relations(snapshot: Dict[str, Any], hits: Dict[str, Dict[str, Any]], comparisons: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    metrics = snapshot.get("metrics") or {}
    result: List[Dict[str, Any]] = []
    if _period_direction(comparisons, "traffic") == "up" and (_period_direction(comparisons, "roi") == "down" or _is_bad_hit(hits, "roi")):
        result.append(_relation(snapshot, "product_traffic_roi", "流量上升但 ROI 下降", "negative", ["traffic", "roi"], hits, comparisons, "投流质量可能异常，V8.4 前不直接降权，V8.3 只记录联动证据。", "high"))
    if (_is_bad_hit(hits, "roi") or _period_direction(comparisons, "roi") == "down") and (_is_bad_hit(hits, "conversionRate") or _period_direction(comparisons, "conversionRate") == "down") and (_is_bad_hit(hits, "refundRate") or _is_bad_hit(hits, "goodReviewRate")):
        result.append(_relation(snapshot, "product_conversion_aftersale", "ROI、转化与售后联动恶化", "negative", ["roi", "conversionRate", "refundRate", "goodReviewRate"], hits, comparisons, "商品承接能力和售后风险同时恶化，后续进入商品权重评分候选。", "high"))
    if _num(metrics.get("stock")) >= 700 and (_is_bad_hit(hits, "conversionRate") or _period_direction(comparisons, "conversionRate") == "down"):
        result.append(_relation(snapshot, "product_stock_conversion", "库存高且转化承接弱", "negative", ["stock", "conversionRate"], hits, comparisons, "库存占用风险出现，后续需要结合店铺权重判断任务强度。", "medium"))
    if _period_direction(comparisons, "traffic") == "down" and (_is_good_hit(hits, "roi") or _is_good_hit(hits, "grossMargin")):
        result.append(_relation(snapshot, "product_normal_shrink", "缩量但 ROI / 毛利稳定", "neutral", ["traffic", "roi", "grossMargin"], hits, comparisons, "可能是低效流量缩减，不应直接判定商品降权。", "medium"))
    if (_is_good_hit(hits, "roi") and _is_good_hit(hits, "conversionRate") and _period_direction(comparisons, "stock") == "down") or (_period_direction(comparisons, "conversionRate") == "up" and _is_good_hit(hits, "roi")):
        result.append(_relation(snapshot, "product_replenish_candidate", "转化 / ROI 稳定且库存下降", "positive", ["roi", "conversionRate", "stock"], hits, comparisons, "可能存在补货或升权候选，V8.4 再评分。", "medium"))
    return result


def _store_relations(snapshot: Dict[str, Any], hits: Dict[str, Dict[str, Any]], comparisons: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    if (_is_bad_hit(hits, "storeRoi") or _period_direction(comparisons, "storeRoi") == "down") and _is_bad_hit(hits, "productHealthRate"):
        result.append(_relation(snapshot, "store_roi_product_health", "店铺 ROI 与商品健康率同时异常", "negative", ["storeRoi", "productHealthRate"], hits, comparisons, "店铺资源限制候选，但需 V8.6 交叉验证商品结构和运营行为。", "high"))
    if _is_bad_hit(hits, "goodReviewRate") and (_period_direction(comparisons, "naturalTraffic") == "down" or _is_bad_hit(hits, "naturalTraffic")):
        result.append(_relation(snapshot, "store_review_traffic", "好评率与自然流量联动下滑", "negative", ["goodReviewRate", "naturalTraffic"], hits, comparisons, "店铺信任资产可能受损，后续影响商品任务强度。", "high"))
    if _is_good_hit(hits, "storeRoi") and _is_good_hit(hits, "goodReviewRate") and _is_good_hit(hits, "productHealthRate"):
        result.append(_relation(snapshot, "store_stable_high_weight", "店铺 ROI、好评和商品健康达标", "positive", ["storeRoi", "goodReviewRate", "productHealthRate"], hits, comparisons, "店铺具备高权重基础，后续商品拖累会提高任务强度。", "medium"))
    return result


def _operator_relations(snapshot: Dict[str, Any], hits: Dict[str, Dict[str, Any]], comparisons: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    if _is_bad_hit(hits, "taskCompletionRate") and _is_bad_hit(hits, "onTimeRate") and _is_bad_hit(hits, "evidenceCompleteness"):
        result.append(_relation(snapshot, "operator_execution_evidence", "任务完成、准时率与证据完整度同时低标", "negative", ["taskCompletionRate", "onTimeRate", "evidenceCompleteness"], hits, comparisons, "只作为运营复核依据，不自动处罚、不自动降权。", "high", {"operatorSafetyBoundary": "必须由总管/老板人工确认。"}))
    if _is_bad_hit(hits, "reviewQualityScore") and _is_bad_hit(hits, "evidenceCompleteness"):
        result.append(_relation(snapshot, "operator_review_evidence", "复盘质量与证据完整度不足", "negative", ["reviewQualityScore", "evidenceCompleteness"], hits, comparisons, "后续可生成辅导观察候选，但 V8.3 不生成任务。", "medium", {"operatorSafetyBoundary": "只进入复核候选。"}))
    if _is_good_hit(hits, "taskCompletionRate") and _is_good_hit(hits, "onTimeRate") and _is_good_hit(hits, "evidenceCompleteness"):
        result.append(_relation(snapshot, "operator_positive_execution", "任务、准时与证据均达标", "positive", ["taskCompletionRate", "onTimeRate", "evidenceCompleteness"], hits, comparisons, "后续可作为运营升权建议的正向证据，但仍需人工审批。", "medium"))
    return result


def _insert_relation(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO linked_metric_relations_v8 (
                relation_id, tenant_id, org_id, object_type, object_id, object_name, relation_type, relation_name,
                risk_direction, confidence, evidence_count, metric_keys, related_hit_ids, related_comparison_ids,
                conclusion, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["relationId"], item["tenantId"], item["orgId"], item["objectType"], item["objectId"], item.get("objectName"), item["relationType"], item["relationName"], item["riskDirection"], item.get("confidence"), item.get("evidenceCount"), dumps(item.get("metricKeys") or []), dumps(item.get("relatedHitIds") or []), dumps(item.get("relatedComparisonIds") or []), item.get("conclusion"), dumps(item.get("payload") or {}), item["createdAt"]),
        )
        conn.commit()


def generate_linked_metric_relations(ctx: UserContext) -> Dict[str, Any]:
    ensure_linked_relation_tables()
    snapshots = _latest_snapshots(ctx)
    if not snapshots:
        generate_weight_snapshots(ctx)
        snapshots = _latest_snapshots(ctx)
    comparisons = _load_comparisons(ctx)
    if not comparisons:
        generate_weight_comparisons(ctx)
        comparisons = _load_comparisons(ctx)
    hits = _load_hits(ctx)
    if not hits:
        generate_weight_rag_hits(ctx)
        hits = _load_hits(ctx)
    relations: List[Dict[str, Any]] = []
    for snapshot in snapshots:
        key = f"{snapshot['objectType']}::{snapshot['objectId']}"
        item_hits = hits.get(key, {})
        item_comparisons = comparisons.get(key, {})
        if snapshot["objectType"] == "product":
            relations.extend(_product_relations(snapshot, item_hits, item_comparisons))
        elif snapshot["objectType"] == "store":
            relations.extend(_store_relations(snapshot, item_hits, item_comparisons))
        elif snapshot["objectType"] == "operator":
            relations.extend(_operator_relations(snapshot, item_hits, item_comparisons))
    for relation in relations:
        _insert_relation(relation)
    by_type: Dict[str, int] = defaultdict(int)
    by_risk: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for relation in relations:
        by_type[relation["relationType"]] += 1
        by_risk[relation["riskDirection"]] += 1
        by_object[relation["objectType"]] += 1
    return {"version": V83_LINKED_RELATION_VERSION, "createdCount": len(relations), "byRelationType": dict(by_type), "byRiskDirection": dict(by_risk), "byObjectType": dict(by_object), "relations": relations, "rule": "V8.3 只生成联动解释，不生成权重评分、升降权或交叉任务。"}


def _row_to_relation(row: Any) -> Dict[str, Any]:
    return {"relationId": row["relation_id"], "tenantId": row["tenant_id"], "orgId": row["org_id"], "objectType": row["object_type"], "objectId": row["object_id"], "objectName": row["object_name"], "relationType": row["relation_type"], "relationName": row["relation_name"], "riskDirection": row["risk_direction"], "confidence": row["confidence"], "evidenceCount": row["evidence_count"], "metricKeys": loads(row["metric_keys"]), "relatedHitIds": loads(row["related_hit_ids"]), "relatedComparisonIds": loads(row["related_comparison_ids"]), "conclusion": row["conclusion"], "payload": loads(row["payload"]), "createdAt": row["created_at"]}


def linked_relation_summary(ctx: UserContext, object_type: str | None = None, risk_direction: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_linked_relation_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if object_type in {"product", "store", "operator"}:
        filters.append("object_type = ?")
        params.append(object_type)
    if risk_direction in {"positive", "neutral", "negative"}:
        filters.append("risk_direction = ?")
        params.append(risk_direction)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM linked_metric_relations_v8 WHERE {' AND '.join(filters)} ORDER BY created_at DESC LIMIT ?", tuple(params)).fetchall()
    relations = [_row_to_relation(row) for row in rows]
    by_type: Dict[str, int] = defaultdict(int)
    by_risk: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    for relation in relations:
        by_type[relation["relationType"]] += 1
        by_risk[relation["riskDirection"]] += 1
        by_object[relation["objectType"]] += 1
    return {"version": V83_LINKED_RELATION_VERSION, "tenantId": ctx.tenant_id, "orgId": ctx.org_id, "roleId": ctx.role_id, "relationCount": len(relations), "byRelationType": dict(by_type), "byRiskDirection": dict(by_risk), "byObjectType": dict(by_object), "relations": relations, "rule": "V8.3 联动比对用于解释波动方向，不自动生成任务或改变权限。"}
