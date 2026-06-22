"""Executable worker task handlers with trace audit."""

from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

from src.core.context import UserContext
from src.repositories.sqlite_repository import connect, dumps, init_db, loads
from src.services.module_agent_service import run_cycle_agent, run_module_agent
from src.services.module_projection_service import projected_products, projected_report_details, projected_report_groups, projected_traffic, projection_summary
from src.services.report_alert_service import get_v3_dashboard_summary, list_alert_events
from src.services.trace_audit_service import resolve_trace_id, write_audit_log

WORKER_TASK_HANDLERS_VERSION = "5.2.5"


def _result_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def ensure_worker_task_result_table() -> None:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS worker_task_results (
                result_id TEXT PRIMARY KEY,
                tenant_id TEXT DEFAULT 'tenant_demo',
                org_id TEXT DEFAULT 'org_demo',
                task_name TEXT NOT NULL,
                status TEXT NOT NULL,
                payload TEXT,
                result TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL,
                deleted_at TEXT
            )
            """
        )
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(worker_task_results)").fetchall()}
        if "trace_id" not in columns:
            conn.execute("ALTER TABLE worker_task_results ADD COLUMN trace_id TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_worker_task_results_tenant_task ON worker_task_results(tenant_id, task_name, created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_worker_task_results_trace ON worker_task_results(trace_id)")
        conn.commit()


def persist_worker_task_result(ctx: UserContext, task_name: str, payload: Dict[str, Any], result: Dict[str, Any], status: str = "completed") -> Dict[str, Any]:
    ensure_worker_task_result_table()
    trace_id = resolve_trace_id(payload, "WORKERRESULT")
    result_id = _result_id("WRESULT")
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO worker_task_results (
                result_id, tenant_id, org_id, task_name, status, payload,
                result, created_by, trace_id, created_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), NULL)
            """,
            (result_id, ctx.tenant_id, ctx.org_id, task_name, status, dumps({**payload, "traceId": trace_id}), dumps({**result, "traceId": trace_id}), ctx.user_id, trace_id),
        )
        conn.commit()
    write_audit_log(ctx, trace_id=trace_id, event_type="worker_result.created", resource_type="worker_task_result", resource_id=result_id, action=task_name, status=status, payload={"taskName": task_name})
    return {"resultId": result_id, "traceId": trace_id, "status": status, "taskName": task_name}


def list_worker_task_results(ctx: UserContext, task_name: str | None = None, limit: int = 50) -> Dict[str, Any]:
    ensure_worker_task_result_table()
    where = ["tenant_id = ?", "deleted_at IS NULL"]
    params: list[Any] = [ctx.tenant_id]
    if task_name:
        where.append("task_name = ?")
        params.append(task_name)
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM worker_task_results WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT ?", params).fetchall()
    items = []
    for row in rows:
        keys = row.keys()
        items.append({"resultId": row["result_id"], "traceId": row["trace_id"] if "trace_id" in keys else None, "tenantId": row["tenant_id"], "orgId": row["org_id"], "taskName": row["task_name"], "status": row["status"], "payload": loads(row["payload"]), "result": loads(row["result"]), "createdBy": row["created_by"], "createdAt": row["created_at"]})
    return {"version": WORKER_TASK_HANDLERS_VERSION, "count": len(items), "items": items}


def run_projection_refresh(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = projection_summary(ctx.user_id)
    result = {"version": WORKER_TASK_HANDLERS_VERSION, "taskName": "projection_refresh", "traceId": resolve_trace_id(payload, "PROJECTIONTRACE"), "summary": summary, "counts": {"products": len(projected_products(ctx.user_id)), "trafficCards": len(projected_traffic(ctx.user_id)), "reportGroups": len(projected_report_groups(ctx.user_id)), "reportDetails": len(projected_report_details(ctx.user_id))}, "rule": "Worker 只刷新并返回投影摘要，不直接改商品、改价或回写 ERP / CRM。"}
    result["persistence"] = persist_worker_task_result(ctx, "projection_refresh", {**payload, "traceId": result["traceId"]}, result)
    return result


def run_alert_generation(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    limit = int(payload.get("limit") or 20)
    active_only = payload.get("activeOnly", payload.get("active_only", True)) is not False
    trace_id = resolve_trace_id(payload, "ALERTTRACE")
    result = {"version": WORKER_TASK_HANDLERS_VERSION, "taskName": "alert_generation", "traceId": trace_id, "summary": get_v3_dashboard_summary(ctx.user_id), "alerts": list_alert_events(limit=limit, active_only=active_only, user_id=ctx.user_id), "rule": "Worker 当前读取已生成 AlertEvent 并输出摘要；新预警仍由报表导入链路生成，避免重复预警。"}
    result["persistence"] = persist_worker_task_result(ctx, "alert_generation", {**payload, "traceId": trace_id}, result)
    return result


def run_agent_analysis(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    module = payload.get("module") or "task"
    entity_id = payload.get("entityId") or payload.get("entity_id") or payload.get("target") or "日报"
    mode = payload.get("mode") or "analysis"
    trace_id = resolve_trace_id(payload, "AGENTTRACE")
    agent_result = run_cycle_agent(str(entity_id), user_id=ctx.user_id) if module == "cycle" else run_module_agent(str(module), str(entity_id), mode=str(mode), user_id=ctx.user_id)
    result = {"version": WORKER_TASK_HANDLERS_VERSION, "taskName": "agent_analysis", "traceId": trace_id, "module": module, "entityId": entity_id, "agent": agent_result, "found": bool(agent_result), "rule": "Agent Worker 只生成分析和建议，不直接创建经营动作；入池仍走人工确认 / TaskRepository 写路径。"}
    result["persistence"] = persist_worker_task_result(ctx, "agent_analysis", {**payload, "traceId": trace_id}, result, status="completed" if agent_result else "no_result")
    return result


def run_rag_memory_write(ctx: UserContext, payload: Dict[str, Any]) -> Dict[str, Any]:
    trace_id = resolve_trace_id(payload, "RAGTRACE")
    memory_payload = {"source": payload.get("source") or "worker_result", "taskId": payload.get("taskId") or payload.get("task_id"), "caseId": payload.get("caseId") or payload.get("case_id"), "summary": payload.get("summary") or payload.get("content") or "待沉淀经验", "evidence": payload.get("evidence") or {}, "status": "pending_rag_review", "traceId": trace_id, "boundary": "先进入可审计结果表，后续再迁移到正式 RAG Memory 表和向量索引。"}
    result = {"version": WORKER_TASK_HANDLERS_VERSION, "taskName": "rag_memory_write", "traceId": trace_id, "memory": memory_payload}
    result["persistence"] = persist_worker_task_result(ctx, "rag_memory_write", {**payload, "traceId": trace_id}, result, status="pending_review")
    return result
