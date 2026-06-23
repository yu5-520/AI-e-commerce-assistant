"""V6.2 risk-graded task generation service.

V6.1 produced product snapshots, metric trends, and business signals. V6.2 turns
those signals into low / medium / high risk tasks with different execution
boundaries. High-risk tasks are not direct investment actions in this version;
they are review / approval candidates until RAG indicator gates and permission
budgets are added in later versions.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, loads
from src.services import module_task_service

RISK_TASK_VERSION = "6.2.0"
RISK_RANK = {"高": 1, "中": 2, "低": 3}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_risk_task_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_task_plans_v6 (
                plan_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                store_id TEXT,
                data_version TEXT,
                risk_level TEXT NOT NULL,
                task_type TEXT NOT NULL,
                task_id TEXT,
                status TEXT NOT NULL,
                payload TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risk_task_plans_product_v6 ON risk_task_plans_v6(product_id, store_id, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_risk_task_plans_version_v6 ON risk_task_plans_v6(data_version, created_at)")
        conn.commit()


def _signal_payload(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    if payload:
        return payload
    return dict(row)


def _load_signals(data_version: str | None = None, limit: int = 200) -> List[Dict[str, Any]]:
    ensure_risk_task_tables()
    if data_version:
        query = "SELECT * FROM business_signals_v6 WHERE data_version = ? ORDER BY created_at DESC LIMIT ?"
        params: tuple[Any, ...] = (data_version, limit)
    else:
        query = "SELECT * FROM business_signals_v6 ORDER BY created_at DESC LIMIT ?"
        params = (limit,)
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_signal_payload(row) for row in rows]


def _product_context(product_id: str, store_id: str | None = None) -> Dict[str, Any]:
    if store_id:
        query = "SELECT * FROM product_master_v6 WHERE product_id = ? AND (store_id = ? OR store_id IS NULL) LIMIT 1"
        params: tuple[Any, ...] = (product_id, store_id)
    else:
        query = "SELECT * FROM product_master_v6 WHERE product_id = ? LIMIT 1"
        params = (product_id,)
    with connect() as conn:
        row = conn.execute(query, params).fetchone()
    if not row:
        return {"productId": product_id, "storeId": store_id, "title": f"商品 {product_id}"}
    payload = loads(row["payload"])
    return {**payload, "productId": product_id, "storeId": store_id or row["store_id"]}


def _dominant_risk(signals: Iterable[Dict[str, Any]]) -> str:
    risks = [str(item.get("riskLevel") or "低") for item in signals]
    return sorted(risks, key=lambda item: RISK_RANK.get(item, 9))[0] if risks else "低"


def _risk_domain(signals: List[Dict[str, Any]]) -> str:
    text = " ".join(str(item.get("signalType") or "") + " " + str(item.get("sourceMetric") or "") for item in signals)
    if any(word in text for word in ["库存", "stock", "available_stock"]):
        return "库存"
    if any(word in text for word in ["ROI", "roi", "流量", "click", "ctr", "conversion"]):
        return "流量"
    if any(word in text for word in ["毛利", "gross_margin", "成本", "价格"]):
        return "利润"
    if any(word in text for word in ["售后", "退款", "差评", "refund", "bad_review"]):
        return "售后"
    return "趋势"


def _task_type(risk_level: str, domain: str, signals: List[Dict[str, Any]]) -> str:
    signal_names = " ".join(str(item.get("signalType") or "") for item in signals)
    if risk_level == "高":
        return "高风险人工复核任务"
    if "库存" in domain:
        return "中风险库存观察任务" if risk_level == "中" else "低风险库存趋势观察"
    if "流量" in domain:
        return "中风险 ROI / 流量修复任务" if risk_level == "中" else "低风险流量趋势观察"
    if "售后" in domain:
        return "中风险售后风险排查任务" if risk_level == "中" else "低风险售后观察"
    if "增长信号" in signal_names and risk_level == "低":
        return "低风险趋势观察任务"
    return "中风险经营信号复核任务" if risk_level == "中" else "低风险数据观察任务"


def _deadline_for(risk_level: str) -> str:
    if risk_level == "高":
        return "今日内"
    if risk_level == "中":
        return "3天内"
    return "本周内"


def _task_layer_for(risk_level: str, domain: str) -> str:
    if risk_level == "高":
        return "manager_dispatch"
    if domain in {"利润", "流量", "售后"}:
        return "finance_check" if domain == "利润" else "operator_execution"
    return "operator_execution"


def _visible_roles_for(risk_level: str, domain: str) -> List[str]:
    if risk_level == "高":
        return ["owner", "manager", "finance"]
    if domain == "利润":
        return ["manager", "finance"]
    return ["manager", "operator"]


def _execution_policy(risk_level: str, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics = [item.get("metricLabel") or item.get("sourceMetric") for item in signals]
    if risk_level == "低":
        return {
            "riskMode": "direct_generation",
            "allowedAction": "生成观察 / 排查任务",
            "requiresRagMetrics": False,
            "requiresApproval": False,
            "rule": "低风险任务只消耗排查与复盘人力，不直接扩大库存或预算，允许 Agent 直接生成任务内容。",
        }
    if risk_level == "中":
        return {
            "riskMode": "metric_bounded_execution",
            "allowedAction": "生成带指标边界的修复 / 观察任务",
            "requiresRagMetrics": True,
            "requiresApproval": False,
            "metricPlaceholders": metrics,
            "rule": "中风险任务允许进入执行，但必须在 V6.3 接 RAG 指标后补齐库存、ROI、点击率、转化率、毛利率等边界。",
        }
    return {
        "riskMode": "review_gate_only",
        "allowedAction": "只能生成复核 / 审批候选，不允许直接加库存、加投放或扩大预算",
        "requiresRagMetrics": True,
        "requiresApproval": True,
        "metricPlaceholders": metrics,
        "rule": "高风险任务涉及扩大投产，V6.2 仅生成复核候选；后续必须通过历史趋势、RAG 指标和权限额度门控。",
    }


def _task_payload(product: Dict[str, Any], signals: List[Dict[str, Any]], data_version: str | None) -> Dict[str, Any]:
    risk_level = _dominant_risk(signals)
    domain = _risk_domain(signals)
    task_type = _task_type(risk_level, domain, signals)
    product_id = product.get("productId") or signals[0].get("productId")
    store_id = product.get("storeId") or signals[0].get("storeId")
    signal_labels = [f"{item.get('signalType')} / {item.get('metricLabel') or item.get('sourceMetric')} / {item.get('trendDirection')}" for item in signals]
    priority = risk_level
    if risk_level == "高":
        title = f"{product.get('title') or product_id} · 高风险趋势复核"
    elif risk_level == "中":
        title = f"{product.get('title') or product_id} · {domain}修复任务"
    else:
        title = f"{product.get('title') or product_id} · 趋势观察任务"
    policy = _execution_policy(risk_level, signals)
    return {
        "id": make_id("RISK"),
        "title": title,
        "task": task_type,
        "taskType": task_type,
        "priority": priority,
        "deadline": _deadline_for(risk_level),
        "timeBucket": _deadline_for(risk_level),
        "source": "趋势中心",
        "sourceModule": "趋势中心",
        "sourceRoute": "trend-center",
        "productRoute": "trend-center",
        "productId": product_id,
        "entityId": product_id,
        "entityType": "商品",
        "store": product.get("storeName") or store_id or "未绑定店铺",
        "storeName": product.get("storeName"),
        "storeIds": [store_id] if store_id else [],
        "platform": product.get("platform") or "未知平台",
        "category": product.get("category") or "未分类",
        "riskDomain": domain,
        "actionType": "复核" if risk_level == "高" else "修复" if risk_level == "中" else "观察",
        "taskLayer": _task_layer_for(risk_level, domain),
        "visibleRoleIds": _visible_roles_for(risk_level, domain),
        "sourceEvent": f"V6.2:{data_version or 'latest'}:{product_id}:{domain}:{risk_level}",
        "riskGrade": risk_level,
        "riskPolicy": policy,
        "judgmentTags": ["V6.2风险分级", f"{risk_level}风险", domain, *[str(item.get("signalType")) for item in signals[:3]]],
        "evidence": [
            {
                "type": "trend_signal",
                "title": item.get("signalType"),
                "metric": item.get("metricLabel") or item.get("sourceMetric"),
                "changeRate": item.get("changeRate"),
                "reason": item.get("reason"),
                "dataVersion": item.get("dataVersion"),
            }
            for item in signals
        ],
        "reason": "；".join(item.get("reason") or item.get("signalType") or "趋势信号" for item in signals[:4]),
        "agentJudgment": {
            "status": "v6_2_risk_graded_task",
            "riskLevel": risk_level,
            "summary": f"系统基于 {len(signals)} 条经营信号生成{risk_level}风险任务。",
            "policy": policy,
            "signals": signal_labels,
            "nextVersionBoundary": "V6.3 接入公司 RAG 指标后，中高风险任务需要补齐具体库存安全线、ROI、点击率、转化率、毛利率等指标。",
        },
        "sourceTrail": ["报表中心", "趋势中心", "风险分级任务"],
    }


def _save_plan(product_id: str, store_id: str | None, data_version: str | None, risk_level: str, task_type: str, task_id: str | None, status: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    ensure_risk_task_tables()
    plan = {
        "planId": make_id("RPLAN"),
        "productId": product_id,
        "storeId": store_id,
        "dataVersion": data_version,
        "riskLevel": risk_level,
        "taskType": task_type,
        "taskId": task_id,
        "status": status,
        "payload": payload,
        "createdAt": now_iso(),
    }
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO risk_task_plans_v6 (plan_id, product_id, store_id, data_version, risk_level, task_type, task_id, status, payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (plan["planId"], product_id, store_id, data_version, risk_level, task_type, task_id, status, dumps(plan), plan["createdAt"]),
        )
        conn.commit()
    return plan


def generate_risk_tasks_for_signals(data_version: str | None = None, limit: int = 200) -> Dict[str, Any]:
    """Generate low / medium / high risk tasks from V6.1 business signals."""
    ensure_risk_task_tables()
    signals = _load_signals(data_version=data_version, limit=limit)
    groups: Dict[tuple[str, str | None, str | None], List[Dict[str, Any]]] = defaultdict(list)
    for signal in signals:
        product_id = signal.get("productId")
        if not product_id:
            continue
        key = (str(product_id), signal.get("storeId"), signal.get("dataVersion") or data_version)
        groups[key].append(signal)
    created_tasks: List[Dict[str, Any]] = []
    plans: List[Dict[str, Any]] = []
    skipped = 0
    for (product_id, store_id, version), items in groups.items():
        dominant = _dominant_risk(items)
        task_candidates = [item for item in items if item.get("taskCandidate")]
        # Low-risk signals create one observation task only when there are at least two signals;
        # medium/high risk signals create tasks as soon as a candidate appears.
        if dominant == "低" and len(items) < 2:
            skipped += 1
            continue
        if dominant in {"中", "高"} and not task_candidates:
            skipped += 1
            continue
        product = _product_context(product_id, store_id)
        payload = _task_payload(product, items, version)
        task = module_task_service.create_task(payload)
        created_tasks.append(task)
        plans.append(_save_plan(product_id, store_id, version, payload["riskGrade"], payload["taskType"], task.get("id"), "created", {"task": task, "signals": items}))
    return {
        "version": RISK_TASK_VERSION,
        "mode": "risk_graded_signal_task_generation",
        "dataVersion": data_version,
        "signalCount": len(signals),
        "groupCount": len(groups),
        "createdTaskCount": len(created_tasks),
        "skippedGroupCount": skipped,
        "tasks": created_tasks,
        "plans": plans,
        "rule": "低风险可直接生成观察/排查任务；中风险生成带指标边界的修复任务；高风险只生成复核/审批候选，不直接扩大投产。",
    }


def risk_task_summary(limit: int = 30) -> Dict[str, Any]:
    ensure_risk_task_tables()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM risk_task_plans_v6 ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    plans = [loads(row["payload"]) for row in rows]
    by_level: Dict[str, int] = defaultdict(int)
    for plan in plans:
        by_level[str(plan.get("riskLevel") or "低")] += 1
    return {
        "version": RISK_TASK_VERSION,
        "total": len(plans),
        "byLevel": dict(by_level),
        "latestPlans": plans,
    }
