"""V14 Agent Judgment Station service.

Agent Judgment is the flexible decision layer after Signal Pool and RAG Context.
It may call the LLM provider, but it never controls station interfaces, permissions,
budget approvals, lifecycle transitions, or execution APIs. Its output is a
structured judgment package that must be frozen by task_snapshot_station before
entering task_pool_station.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads
from src.services.llm_provider_service import generate_json
from src.services.rag_context_station_service import build_rag_context_snapshot, latest_rag_context
from src.services.signal_pool_service import list_signals
from src.services.task_snapshot_station_service import create_task_snapshot

AGENT_JUDGMENT_STATION_VERSION = "14.0.0"
VALID_DECISIONS = {"create_task_snapshot", "manager_review_required", "observe_only", "ignore_noise"}
SNAPSHOT_DECISIONS = {"create_task_snapshot", "manager_review_required"}


def now_iso() -> str:
    return datetime.now().isoformat()


def make_judgment_id() -> str:
    return f"AJ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}"


def ensure_agent_judgment_tables() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_judgments_v14 (
                judgment_id TEXT PRIMARY KEY,
                data_version TEXT,
                signal_id TEXT,
                entity_type TEXT,
                entity_id TEXT,
                decision TEXT NOT NULL,
                confidence REAL DEFAULT 0,
                status TEXT NOT NULL,
                rag_context_ref TEXT,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_columns(
            conn,
            "agent_judgments_v14",
            {
                "data_version": "TEXT",
                "signal_id": "TEXT",
                "entity_type": "TEXT",
                "entity_id": "TEXT",
                "confidence": "REAL DEFAULT 0",
                "rag_context_ref": "TEXT",
                "updated_at": "TEXT",
            },
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_judgments_v14_version ON agent_judgments_v14(data_version, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_judgments_v14_decision ON agent_judgments_v14(decision, status, created_at)")
        conn.commit()


def _row_to_judgment(row: Any) -> Dict[str, Any]:
    payload = loads(row["payload"])
    return {
        **payload,
        "judgmentId": row["judgment_id"],
        "dataVersion": row["data_version"],
        "signalId": row["signal_id"],
        "entityType": row["entity_type"],
        "entityId": row["entity_id"],
        "decision": row["decision"],
        "confidence": float(row["confidence"] or 0),
        "status": row["status"],
        "ragContextRef": row["rag_context_ref"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def list_agent_judgments(data_version: str | None = None, status: str | None = None, limit: int = 200) -> Dict[str, Any]:
    ensure_agent_judgment_tables()
    clauses = []
    params: List[Any] = []
    if data_version:
        clauses.append("data_version = ?")
        params.append(data_version)
    if status:
        clauses.append("status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM agent_judgments_v14 {where} ORDER BY created_at DESC LIMIT ?", [*params, limit]).fetchall()
    items = [_row_to_judgment(row) for row in rows]
    by_decision: Dict[str, int] = defaultdict(int)
    for item in items:
        by_decision[str(item.get("decision"))] += 1
    return {"version": AGENT_JUDGMENT_STATION_VERSION, "dataVersion": data_version, "judgmentCount": len(items), "byDecision": dict(by_decision), "judgments": items}


def _decision_template(signal: Dict[str, Any], rag_context: Dict[str, Any]) -> Dict[str, Any]:
    signal_type = str(signal.get("signalType") or "")
    strength = str(signal.get("signalStrength") or "low")
    metric = signal.get("metricCode") or "经营指标"
    entity_type = signal.get("entityType") or "product"
    entity_id = signal.get("entityId") or signal.get("productId") or signal.get("dataVersion") or "latest"
    if signal_type.startswith("redline_"):
        decision = "manager_review_required"
        priority = "高"
        task_type = "红线复核任务"
        reason = "信号命中红线风险，Agent建议生成总管复核任务，但不允许自动执行。"
    elif signal_type.startswith("data_gap_"):
        decision = "create_task_snapshot"
        priority = "中"
        task_type = "数据补齐/归属复核任务"
        reason = "该信号暴露数据缺口，影响后续趋势判断，建议生成补数或归属复核任务。"
    elif signal_type == "metric_large_wave" or strength == "medium":
        decision = "create_task_snapshot"
        priority = "中"
        task_type = "经营波动复核任务"
        reason = "指标出现较大波动，需结合RAG经验和运营信息复核是否进入执行动作。"
    elif signal_type == "normal_wave_candidate":
        decision = "ignore_noise"
        priority = "低"
        task_type = "正常波动留痕"
        reason = "波动幅度较小，默认作为正常波动候选留痕，除非RAG上下文提示特殊类目或高权重对象。"
    else:
        decision = "observe_only"
        priority = "低"
        task_type = "观察信号"
        reason = "该信号需要进入观察池，暂不直接生成运营执行任务。"
    deadline = "6小时内" if priority == "高" else "24小时内" if priority == "中" else "后台观察"
    evidence = ["对应报表来源", "指标事实值", "运营补充说明"]
    if signal_type.startswith("data_gap_"):
        evidence = ["缺失字段样例", "正确商品/店铺归属", "补齐后的报表或截图"]
    task_plan = {
        "title": f"{task_type}｜{entity_id}",
        "subtitle": signal_type,
        "entityType": entity_type,
        "entityId": entity_id,
        "taskType": task_type,
        "actionType": "agent_judgment_required",
        "priority": priority,
        "deadline": deadline,
        "riskDomain": metric,
        "sopSteps": [
            f"{deadline}复核 {metric} 信号与原始报表证据。",
            "结合店铺/商品权重、类目基线、历史复盘和运营上下文确认处理方向。",
            "提交截图、数据口径、处理结论和需要总管复核的指标。",
        ],
        "evidenceRequirements": evidence,
        "reviewMetrics": ["ROI", "GMV/支付金额", "点击率", "转化率", "退款率", "毛利率", "库存"],
        "needManagerReview": decision == "manager_review_required",
        "reason": reason,
    }
    return {
        "decision": decision,
        "confidence": 0.78 if decision in SNAPSHOT_DECISIONS else 0.62,
        "reason": reason,
        "taskPlan": task_plan,
        "evidenceRequirements": evidence,
        "reviewMetrics": task_plan["reviewMetrics"],
        "riskBoundary": [
            "Agent不直接改价、改预算、改库存、自动发布或自动退款。",
            "高风险动作只能生成复核/申请任务，执行权由生命周期和权限站点控制。",
        ],
        "ragContextApplied": bool(rag_context),
    }


def _normalize_llm_output(output: Dict[str, Any], fallback: Dict[str, Any]) -> Dict[str, Any]:
    decision = output.get("decision")
    if decision not in VALID_DECISIONS:
        return fallback
    merged = {**fallback, **{key: value for key, value in output.items() if value is not None}}
    merged["decision"] = decision
    try:
        merged["confidence"] = max(0.0, min(1.0, float(merged.get("confidence") or fallback.get("confidence") or 0)))
    except Exception:
        merged["confidence"] = fallback.get("confidence") or 0.5
    if not isinstance(merged.get("taskPlan"), dict):
        merged["taskPlan"] = fallback.get("taskPlan") or {}
    if not isinstance(merged.get("evidenceRequirements"), list):
        merged["evidenceRequirements"] = fallback.get("evidenceRequirements") or []
    if not isinstance(merged.get("reviewMetrics"), list):
        merged["reviewMetrics"] = fallback.get("reviewMetrics") or []
    return merged


def _judge_signal(signal: Dict[str, Any], rag_context: Dict[str, Any]) -> Dict[str, Any]:
    fallback = _decision_template(signal, rag_context)
    llm_result = generate_json(
        prompt_name="task_signal_agent_judgment",
        payload={
            "signal": signal,
            "ragContext": rag_context,
            "fallbackDecision": fallback,
            "interfaceBoundary": "Agent只能输出判断；站点接口、权限、预算、生命周期由代码控制。",
        },
        expected_keys=["decision", "confidence", "reason", "taskPlan"],
        agent_name="V14 Task Signal Agent",
        schema_name="v14_agent_judgment",
    )
    output = llm_result.get("output") or {}
    judgment = _normalize_llm_output(output, fallback)
    judgment["llm"] = {
        "provider": llm_result.get("provider"),
        "model": llm_result.get("model"),
        "status": llm_result.get("status"),
        "fallbackUsed": llm_result.get("fallbackUsed"),
        "trace": llm_result.get("trace"),
    }
    return judgment


def _save_judgment(signal: Dict[str, Any], rag_context: Dict[str, Any], judgment: Dict[str, Any]) -> Dict[str, Any]:
    ensure_agent_judgment_tables()
    judgment_id = make_judgment_id()
    created_at = now_iso()
    payload = {
        "version": AGENT_JUDGMENT_STATION_VERSION,
        "judgmentId": judgment_id,
        "stationId": "agent_judgment_station",
        "dataVersion": signal.get("dataVersion"),
        "signalId": signal.get("signalId"),
        "entityType": signal.get("entityType"),
        "entityId": signal.get("entityId"),
        "signal": signal,
        "ragContextRef": rag_context.get("ragContextRef") or rag_context.get("outputRef"),
        "ragContext": rag_context,
        "decision": judgment.get("decision"),
        "confidence": judgment.get("confidence") or 0,
        "reason": judgment.get("reason"),
        "taskPlan": judgment.get("taskPlan") or {},
        "evidenceRequirements": judgment.get("evidenceRequirements") or [],
        "reviewMetrics": judgment.get("reviewMetrics") or [],
        "riskBoundary": judgment.get("riskBoundary") or [],
        "agentJudgment": judgment,
        "directInterfaceControlAllowed": False,
        "rule": "V14：Agent判断只生成结构化决策，不控制接口、不直接创建任务、不越权执行。",
    }
    status = "pending_task_snapshot" if judgment.get("decision") in SNAPSHOT_DECISIONS else "judgment_recorded"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO agent_judgments_v14 (
                judgment_id, data_version, signal_id, entity_type, entity_id,
                decision, confidence, status, rag_context_ref, payload,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                judgment_id,
                signal.get("dataVersion"),
                signal.get("signalId"),
                signal.get("entityType"),
                signal.get("entityId"),
                judgment.get("decision"),
                float(judgment.get("confidence") or 0),
                status,
                payload["ragContextRef"],
                dumps(payload),
                created_at,
                created_at,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM agent_judgments_v14 WHERE judgment_id = ?", (judgment_id,)).fetchone()
    return _row_to_judgment(row)


def run_agent_judgment_station(data_version: str | None = None, *, rag_context_ref: str | None = None, max_signals: int = 32) -> Dict[str, Any]:
    """Run RAG-enhanced Agent judgment over the current signal pool."""
    ensure_agent_judgment_tables()
    rag_context = latest_rag_context(data_version)
    if not rag_context:
        rag_context = build_rag_context_snapshot(data_version=data_version)
    signals = (list_signals(data_version=data_version, status="pending_rag_agent", limit=max_signals).get("signals") or [])[:max_signals]
    judgments = [_save_judgment(signal, rag_context, _judge_signal(signal, rag_context)) for signal in signals]
    by_decision: Dict[str, int] = defaultdict(int)
    for item in judgments:
        by_decision[str(item.get("decision"))] += 1
    ref = f"agent_judgment:{data_version or 'latest'}"
    return {
        "version": AGENT_JUDGMENT_STATION_VERSION,
        "mode": "rag_enhanced_agent_judgment_no_interface_control",
        "dataVersion": data_version,
        "ragContextRef": rag_context_ref or rag_context.get("ragContextRef") or rag_context.get("outputRef"),
        "agentJudgmentRef": ref,
        "outputRef": ref,
        "signalCount": len(signals),
        "judgmentCount": len(judgments),
        "pendingTaskSnapshotCount": sum(1 for item in judgments if item.get("decision") in SNAPSHOT_DECISIONS),
        "byDecision": dict(by_decision),
        "judgments": judgments,
        "rule": "V14：经营判断交给RAG增强Agent；代码只接收结构化判断并交给task_snapshot_station固化。",
    }


def materialize_task_snapshots_from_judgments(data_version: str | None = None, *, created_by: str | None = None, limit: int = 50) -> Dict[str, Any]:
    result = list_agent_judgments(data_version=data_version, status="pending_task_snapshot", limit=limit)
    snapshots: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for item in result.get("judgments") or []:
        decision = item.get("decision")
        if decision not in SNAPSHOT_DECISIONS:
            skipped.append({"judgmentId": item.get("judgmentId"), "reason": "decision_not_for_task_snapshot", "decision": decision})
            continue
        snapshot = create_task_snapshot(
            {
                "dataVersion": item.get("dataVersion"),
                "decision": decision,
                "confidence": item.get("confidence"),
                "entityType": item.get("entityType"),
                "entityId": item.get("entityId"),
                "signalRef": item.get("signalId"),
                "ragContext": item.get("ragContext") or {},
                "agentJudgment": item.get("agentJudgment") or {},
                "taskPlan": item.get("taskPlan") or {},
                "evidenceRequirements": item.get("evidenceRequirements") or [],
                "systemFacts": {"signal": item.get("signal") or {}, "judgmentId": item.get("judgmentId")},
                "source": "agent_judgment_station",
            },
            created_by=created_by,
        )
        snapshots.append(snapshot)
        with connect() as conn:
            payload = item
            payload["taskSnapshotId"] = snapshot.get("taskSnapshotId")
            conn.execute(
                "UPDATE agent_judgments_v14 SET status = ?, payload = ?, updated_at = ? WHERE judgment_id = ?",
                ("task_snapshot_created", dumps(payload), now_iso(), item.get("judgmentId")),
            )
            conn.commit()
    return {
        "version": AGENT_JUDGMENT_STATION_VERSION,
        "dataVersion": data_version,
        "taskSnapshotCount": len(snapshots),
        "snapshots": snapshots,
        "skipped": skipped,
        "outputRef": f"task_snapshot:{data_version or 'latest'}",
        "rule": "V14：task_snapshot_station只固化Agent判断；仍不直接创建可见任务。",
    }
