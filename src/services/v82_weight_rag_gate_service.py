"""V8.2 weight RAG standard-line hit service.

V8.0 normalized product / store / operator into weight snapshots. V8.1 explained
period fluctuation. V8.2 connects the V6 RAG indicator rule idea to V8 weight
objects: each object metric is checked against a standard line and stored as a
hit record. V8.2 still does not score weight, generate adjustment tasks, or
automatically punish operators.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, loads
from src.services.indicator_rag_service import ensure_indicator_rag_tables
from src.services.v80_weight_snapshot_service import ensure_weight_snapshot_tables, generate_weight_snapshots
from src.services.v81_weight_comparison_service import ensure_weight_comparison_tables

V82_WEIGHT_RAG_VERSION = "8.2.0"

STANDARD_LINES: List[Dict[str, Any]] = [
    {"objectType": "product", "metricName": "roi", "metricLabel": "ROI", "operator": "min", "threshold": 1.6, "domain": "流量", "ruleId": "RAG_RULE_TRAFFIC_GENERAL", "summary": "ROI 低于投放修复线，后续进入商品权重观察。"},
    {"objectType": "product", "metricName": "ctr", "metricLabel": "点击率", "operator": "min", "threshold": 0.025, "domain": "流量", "ruleId": "RAG_RULE_TRAFFIC_GENERAL", "summary": "点击率低于投放修复线，后续需要结合主图/标题联动判断。"},
    {"objectType": "product", "metricName": "conversionRate", "metricLabel": "转化率", "operator": "min", "threshold": 0.03, "domain": "流量", "ruleId": "RAG_RULE_TRAFFIC_GENERAL", "summary": "转化率低于承接线，后续进入商品承接能力判断。"},
    {"objectType": "product", "metricName": "grossMargin", "metricLabel": "毛利率", "operator": "min", "threshold": 0.25, "domain": "利润", "ruleId": "RAG_RULE_PROFIT_GENERAL", "summary": "毛利低于利润保护线，不允许盲目扩大投产。"},
    {"objectType": "product", "metricName": "refundRate", "metricLabel": "售后率", "operator": "max", "threshold": 0.08, "domain": "售后", "ruleId": "RAG_RULE_AFTERSALE_GENERAL", "summary": "售后率高于风险线，后续进入售后风险联动。"},
    {"objectType": "product", "metricName": "goodReviewRate", "metricLabel": "好评率", "operator": "min", "threshold": 0.94, "domain": "售后", "ruleId": "RAG_RULE_AFTERSALE_GENERAL", "summary": "好评率低于保护线，核心店铺场景会放大任务强度。"},
    {"objectType": "store", "metricName": "storeRoi", "metricLabel": "店铺ROI", "operator": "min", "threshold": 1.6, "domain": "流量", "ruleId": "RAG_RULE_TRAFFIC_GENERAL", "summary": "店铺 ROI 低于标准线，后续影响商品任务强度。"},
    {"objectType": "store", "metricName": "goodReviewRate", "metricLabel": "店铺好评率", "operator": "min", "threshold": 0.94, "domain": "售后", "ruleId": "RAG_RULE_AFTERSALE_GENERAL", "summary": "店铺好评率低于保护线，后续进入店铺权重判断。"},
    {"objectType": "store", "metricName": "naturalTraffic", "metricLabel": "自然流量", "operator": "min", "threshold": 3000, "domain": "流量", "ruleId": "RAG_RULE_TRAFFIC_GENERAL", "summary": "自然流量低于基础线，后续需要结合店铺角色标签判断。"},
    {"objectType": "store", "metricName": "ctr", "metricLabel": "店铺点击率", "operator": "min", "threshold": 0.025, "domain": "流量", "ruleId": "RAG_RULE_TRAFFIC_GENERAL", "summary": "店铺点击率低于基础线，后续结合商品结构验证。"},
    {"objectType": "store", "metricName": "productHealthRate", "metricLabel": "商品健康率", "operator": "min", "threshold": 0.6, "domain": "趋势", "ruleId": "RAG_RULE_HIGH_RISK_GATE", "summary": "健康商品比例低，后续进入店铺资源限制候选。"},
    {"objectType": "operator", "metricName": "taskCompletionRate", "metricLabel": "任务完成率", "operator": "min", "threshold": 0.85, "domain": "组织", "ruleId": "RAG_RULE_OPERATOR_WEIGHT", "summary": "任务完成率低于标准线，只能生成复核依据，不能自动处罚。"},
    {"objectType": "operator", "metricName": "onTimeRate", "metricLabel": "准时率", "operator": "min", "threshold": 0.85, "domain": "组织", "ruleId": "RAG_RULE_OPERATOR_WEIGHT", "summary": "准时率低于标准线，后续结合店铺难度和任务证据验证。"},
    {"objectType": "operator", "metricName": "reviewQualityScore", "metricLabel": "复盘质量分", "operator": "min", "threshold": 75, "domain": "组织", "ruleId": "RAG_RULE_OPERATOR_WEIGHT", "summary": "复盘质量低于标准线，只进入辅导/复核候选。"},
    {"objectType": "operator", "metricName": "evidenceCompleteness", "metricLabel": "证据完整度", "operator": "min", "threshold": 0.8, "domain": "组织", "ruleId": "RAG_RULE_OPERATOR_WEIGHT", "summary": "证据完整度不足，后续影响审批可信度。"},
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_weight_rag_tables() -> None:
    ensure_indicator_rag_tables()
    ensure_weight_snapshot_tables()
    ensure_weight_comparison_tables()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS weight_rag_standard_hits_v8 (
                hit_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT NOT NULL,
                object_name TEXT,
                metric_name TEXT NOT NULL,
                metric_label TEXT,
                standard_line REAL,
                current_value REAL,
                operator TEXT,
                hit_status TEXT NOT NULL,
                severity TEXT,
                consecutive_low_count INTEGER DEFAULT 0,
                rule_id TEXT,
                domain TEXT,
                snapshot_version TEXT,
                comparison_direction TEXT,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_rag_hits_object_v8 ON weight_rag_standard_hits_v8(tenant_id, org_id, object_type, object_id, hit_status, severity)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_weight_rag_hits_metric_v8 ON weight_rag_standard_hits_v8(metric_name, hit_status, created_at)")
        conn.commit()


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _load_latest_snapshots(ctx: UserContext) -> List[Dict[str, Any]]:
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
    return [_row_to_snapshot(row) for row in rows]


def _load_recent_values(ctx: UserContext, object_type: str, object_id: str, metric_name: str, limit: int = 4) -> List[float]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT metrics FROM weight_metric_snapshots_v8
            WHERE tenant_id = ? AND org_id = ? AND object_type = ? AND object_id = ?
            ORDER BY snapshot_at DESC
            LIMIT ?
            """,
            (ctx.tenant_id, ctx.org_id, object_type, object_id, limit),
        ).fetchall()
    values: List[float] = []
    for row in rows:
        metrics = loads(row["metrics"])
        value = metrics.get(metric_name)
        if _is_number(value):
            values.append(float(value))
    return values


def _latest_comparison_direction(ctx: UserContext, object_type: str, object_id: str, metric_name: str) -> str | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT direction FROM weight_metric_comparisons_v8
            WHERE tenant_id = ? AND org_id = ? AND object_type = ? AND object_id = ? AND metric_name = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (ctx.tenant_id, ctx.org_id, object_type, object_id, metric_name),
        ).fetchone()
    return row["direction"] if row else None


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
        "snapshotVersion": row["snapshot_version"],
        "snapshotAt": row["snapshot_at"],
        "metrics": loads(row["metrics"]),
        "dimensions": loads(row["dimensions"]),
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def _violates(value: float, standard: Dict[str, Any]) -> bool:
    threshold = float(standard["threshold"])
    if standard["operator"] == "min":
        return value < threshold
    return value > threshold


def _violation_gap(value: float, standard: Dict[str, Any]) -> float:
    threshold = float(standard["threshold"])
    if threshold == 0:
        return 0.0
    if standard["operator"] == "min":
        return max(0.0, (threshold - value) / abs(threshold))
    return max(0.0, (value - threshold) / abs(threshold))


def _consecutive_violation_count(values: List[float], standard: Dict[str, Any]) -> int:
    count = 0
    for value in values:
        if _violates(value, standard):
            count += 1
        else:
            break
    return count


def _severity(gap: float, consecutive: int, object_type: str) -> str:
    if consecutive >= 3 or gap >= 0.3:
        return "高"
    if consecutive >= 2 or gap >= 0.15:
        return "中"
    if object_type == "operator":
        return "观察"
    return "低"


def _hit_status(value: float, standard: Dict[str, Any]) -> str:
    if _violates(value, standard):
        return "below_standard" if standard["operator"] == "min" else "above_risk_line"
    return "within_standard"


def _insert_hit(item: Dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO weight_rag_standard_hits_v8 (
                hit_id, tenant_id, org_id, object_type, object_id, object_name, metric_name, metric_label,
                standard_line, current_value, operator, hit_status, severity, consecutive_low_count, rule_id,
                domain, snapshot_version, comparison_direction, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item["hitId"], item["tenantId"], item["orgId"], item["objectType"], item["objectId"], item.get("objectName"), item["metricName"], item.get("metricLabel"), item["standardLine"], item["currentValue"], item["operator"], item["hitStatus"], item["severity"], item["consecutiveLowCount"], item.get("ruleId"), item.get("domain"), item.get("snapshotVersion"), item.get("comparisonDirection"), dumps(item.get("payload") or {}), item["createdAt"]),
        )
        conn.commit()


def generate_weight_rag_hits(ctx: UserContext) -> Dict[str, Any]:
    ensure_weight_rag_tables()
    snapshots = _load_latest_snapshots(ctx)
    if not snapshots:
        generate_weight_snapshots(ctx)
        snapshots = _load_latest_snapshots(ctx)
    standards_by_type: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for standard in STANDARD_LINES:
        standards_by_type[standard["objectType"]].append(standard)
    created: List[Dict[str, Any]] = []
    created_at = now_iso()
    for snapshot in snapshots:
        metrics = snapshot.get("metrics") or {}
        for standard in standards_by_type.get(snapshot["objectType"], []):
            metric_name = standard["metricName"]
            value = metrics.get(metric_name)
            if not _is_number(value):
                continue
            current = float(value)
            recent_values = _load_recent_values(ctx, snapshot["objectType"], snapshot["objectId"], metric_name)
            consecutive = _consecutive_violation_count(recent_values, standard)
            gap = _violation_gap(current, standard)
            status = _hit_status(current, standard)
            item = {
                "hitId": make_id("WRAG"),
                "tenantId": ctx.tenant_id,
                "orgId": ctx.org_id,
                "objectType": snapshot["objectType"],
                "objectId": snapshot["objectId"],
                "objectName": snapshot.get("objectName"),
                "metricName": metric_name,
                "metricLabel": standard.get("metricLabel"),
                "standardLine": float(standard["threshold"]),
                "currentValue": current,
                "operator": standard["operator"],
                "hitStatus": status,
                "severity": _severity(gap, consecutive, snapshot["objectType"]) if status != "within_standard" else "正常",
                "consecutiveLowCount": consecutive,
                "ruleId": standard.get("ruleId"),
                "domain": standard.get("domain"),
                "snapshotVersion": snapshot.get("snapshotVersion"),
                "comparisonDirection": _latest_comparison_direction(ctx, snapshot["objectType"], snapshot["objectId"], metric_name),
                "payload": {
                    "version": V82_WEIGHT_RAG_VERSION,
                    "summary": standard.get("summary"),
                    "dimensions": snapshot.get("dimensions") or {},
                    "violationGap": gap,
                    "rule": "V8.2 只判断是否命中 RAG 标准线，不生成升降权和任务。",
                    "operatorSafetyBoundary": "运营对象只进入复核依据，不自动处罚。" if snapshot["objectType"] == "operator" else None,
                },
                "createdAt": created_at,
            }
            created.append(item)
            _insert_hit(item)
    counts: Dict[str, int] = defaultdict(int)
    severity_counts: Dict[str, int] = defaultdict(int)
    for item in created:
        counts[item["hitStatus"]] += 1
        severity_counts[item["severity"]] += 1
    return {"version": V82_WEIGHT_RAG_VERSION, "createdCount": len(created), "byHitStatus": dict(counts), "bySeverity": dict(severity_counts), "hits": created, "rule": "V8.2 接入 RAG 标准线命中；V8.3 才做联动比对，V8.4 才做权重评分。"}


def _row_to_hit(row: Any) -> Dict[str, Any]:
    return {
        "hitId": row["hit_id"],
        "tenantId": row["tenant_id"],
        "orgId": row["org_id"],
        "objectType": row["object_type"],
        "objectId": row["object_id"],
        "objectName": row["object_name"],
        "metricName": row["metric_name"],
        "metricLabel": row["metric_label"],
        "standardLine": row["standard_line"],
        "currentValue": row["current_value"],
        "operator": row["operator"],
        "hitStatus": row["hit_status"],
        "severity": row["severity"],
        "consecutiveLowCount": row["consecutive_low_count"],
        "ruleId": row["rule_id"],
        "domain": row["domain"],
        "snapshotVersion": row["snapshot_version"],
        "comparisonDirection": row["comparison_direction"],
        "payload": loads(row["payload"]),
        "createdAt": row["created_at"],
    }


def weight_rag_summary(ctx: UserContext, object_type: str | None = None, hit_status: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_weight_rag_tables()
    filters = ["tenant_id = ?", "org_id = ?"]
    params: List[Any] = [ctx.tenant_id, ctx.org_id]
    if object_type in {"product", "store", "operator"}:
        filters.append("object_type = ?")
        params.append(object_type)
    if hit_status in {"below_standard", "above_risk_line", "within_standard"}:
        filters.append("hit_status = ?")
        params.append(hit_status)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM weight_rag_standard_hits_v8 WHERE {' AND '.join(filters)} ORDER BY created_at DESC LIMIT ?", tuple(params)).fetchall()
    hits = [_row_to_hit(row) for row in rows]
    by_status: Dict[str, int] = defaultdict(int)
    by_severity: Dict[str, int] = defaultdict(int)
    by_object: Dict[str, int] = defaultdict(int)
    by_domain: Dict[str, int] = defaultdict(int)
    for item in hits:
        by_status[item["hitStatus"]] += 1
        by_severity[item["severity"]] += 1
        by_object[item["objectType"]] += 1
        by_domain[item["domain"]] += 1
    return {
        "version": V82_WEIGHT_RAG_VERSION,
        "tenantId": ctx.tenant_id,
        "orgId": ctx.org_id,
        "roleId": ctx.role_id,
        "hitCount": len(hits),
        "byHitStatus": dict(by_status),
        "bySeverity": dict(by_severity),
        "byObjectType": dict(by_object),
        "byDomain": dict(by_domain),
        "hits": hits,
        "standardLines": STANDARD_LINES,
        "rule": "V8.2 以 RAG 标准线解释权重指标是否达标；不生成任务，不改变权限。",
    }
