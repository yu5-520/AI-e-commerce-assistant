"""V14.9.2 task generation run and data metro-line status service.

The data line reports the current task-generation run, not the global task-pool
size. This keeps 判断 / 整合 / 任务 from being inflated by old pool entries or
retry duplicates.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps, ensure_columns, loads

TASK_GENERATION_RUN_VERSION = "14.9.2"
DONE_STATUS = {"已完成", "已拒绝", "已确认", "已归档", "已通过", "已写入复盘"}


def now_iso() -> str:
    return datetime.now().isoformat()


def make_run_id() -> str:
    return f"TGR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}"


def _table_exists(conn: Any, table_name: str) -> bool:
    return bool(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone())


def _count(conn: Any, table_name: str) -> int:
    if not _table_exists(conn, table_name):
        return 0
    return int(conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()["count"] or 0)


def _count_by_version(conn: Any, table_name: str, data_version: str | None) -> int:
    if not data_version or not _table_exists(conn, table_name):
        return _count(conn, table_name)
    try:
        return int(conn.execute(f"SELECT COUNT(*) AS count FROM {table_name} WHERE data_version = ?", (data_version,)).fetchone()["count"] or 0)
    except Exception:
        return _count(conn, table_name)


def ensure_task_generation_run_tables() -> None:
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_generation_runs_v14 (
                run_id TEXT PRIMARY KEY,
                data_version TEXT,
                status TEXT NOT NULL,
                input_bundle_count INTEGER DEFAULT 0,
                agent_judgment_count INTEGER DEFAULT 0,
                product_judgment_package_count INTEGER DEFAULT 0,
                task_decision_count INTEGER DEFAULT 0,
                formal_task_count INTEGER DEFAULT 0,
                observe_only_count INTEGER DEFAULT 0,
                data_gap_task_count INTEGER DEFAULT 0,
                manager_review_count INTEGER DEFAULT 0,
                task_pool_created_count INTEGER DEFAULT 0,
                frontend_task_view_count INTEGER DEFAULT 0,
                reason TEXT,
                payload TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        ensure_columns(conn, "task_generation_runs_v14", {"data_version": "TEXT", "status": "TEXT", "input_bundle_count": "INTEGER DEFAULT 0", "agent_judgment_count": "INTEGER DEFAULT 0", "product_judgment_package_count": "INTEGER DEFAULT 0", "task_decision_count": "INTEGER DEFAULT 0", "formal_task_count": "INTEGER DEFAULT 0", "observe_only_count": "INTEGER DEFAULT 0", "data_gap_task_count": "INTEGER DEFAULT 0", "manager_review_count": "INTEGER DEFAULT 0", "task_pool_created_count": "INTEGER DEFAULT 0", "frontend_task_view_count": "INTEGER DEFAULT 0", "reason": "TEXT", "payload": "TEXT", "created_at": "TEXT", "updated_at": "TEXT"})
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_generation_runs_v14_version ON task_generation_runs_v14(data_version, created_at)")
        conn.commit()


def record_task_generation_run(*, data_version: str | None, input_bundle_count: int = 0, agent_judgment_count: int = 0, product_judgment_package_count: int = 0, task_decision_count: int = 0, by_decision: Dict[str, int] | None = None, streamed_task_snapshot_count: int = 0, task_pool_created_count: int = 0, skipped_formal_count: int = 0, zero_task_reasons: List[str] | None = None, source: str = "agent_judgment_station") -> Dict[str, Any]:
    ensure_task_generation_run_tables()
    by_decision = by_decision or {}
    formal_task_count = int(by_decision.get("create_task_snapshot", 0) or 0) + int(by_decision.get("manager_review_required", 0) or 0)
    observe_only_count = int(by_decision.get("observe_only", 0) or 0) + int(by_decision.get("no_task", 0) or 0)
    manager_review_count = int(by_decision.get("manager_review_required", 0) or 0)
    data_gap_task_count = int(by_decision.get("data_gap_task", 0) or 0)
    if task_pool_created_count:
        status = "completed_with_product_tasks"
        reason = f"双 Agent 链路已完成，{product_judgment_package_count} 个商品判断包生成 {task_pool_created_count} 个正式任务。"
    elif formal_task_count:
        status = "completed_no_pool_entries"
        reason = "Agent2 已有正式任务决策，但未成功进入任务池，需要检查 task_snapshot/task_pool。"
    else:
        status = "completed_no_formal_task"
        reason = "双 Agent 链路已完成，本轮无正式执行任务。"
    if zero_task_reasons and not task_pool_created_count:
        reason = str(zero_task_reasons[0] or reason)
    now = now_iso()
    run_id = make_run_id()
    payload = {"version": TASK_GENERATION_RUN_VERSION, "runId": run_id, "dataVersion": data_version, "status": status, "source": source, "inputBundleCount": int(input_bundle_count or 0), "agentJudgmentCount": int(agent_judgment_count or 0), "productJudgmentPackageCount": int(product_judgment_package_count or 0), "taskDecisionCount": int(task_decision_count or 0), "formalTaskCount": int(formal_task_count or 0), "observeOnlyCount": int(observe_only_count or 0), "dataGapTaskCount": int(data_gap_task_count or 0), "managerReviewCount": int(manager_review_count or 0), "streamedTaskSnapshotCount": int(streamed_task_snapshot_count or 0), "taskPoolCreatedCount": int(task_pool_created_count or 0), "skippedFormalCount": int(skipped_formal_count or 0), "byDecision": by_decision, "reason": reason, "zeroTaskReasons": zero_task_reasons or [], "createdAt": now, "updatedAt": now, "rule": "V14.9.2: data-line shows current-run taskPoolCreatedCount; global task_pool_entries cannot inflate this run."}
    with connect() as conn:
        frontend_task_count = _count(conn, "frontend_task_view")
        payload["frontendTaskViewCount"] = frontend_task_count
        conn.execute("""
            INSERT INTO task_generation_runs_v14 (run_id, data_version, status, input_bundle_count, agent_judgment_count, product_judgment_package_count, task_decision_count, formal_task_count, observe_only_count, data_gap_task_count, manager_review_count, task_pool_created_count, frontend_task_view_count, reason, payload, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, data_version, status, int(input_bundle_count or 0), int(agent_judgment_count or 0), int(product_judgment_package_count or 0), int(task_decision_count or 0), formal_task_count, observe_only_count, data_gap_task_count, manager_review_count, int(task_pool_created_count or 0), frontend_task_count, reason, dumps(payload), now, now))
        conn.commit()
    return payload


def _latest_generation_run(conn: Any) -> Dict[str, Any] | None:
    ensure_task_generation_run_tables()
    row = conn.execute("SELECT payload FROM task_generation_runs_v14 ORDER BY created_at DESC LIMIT 1").fetchone()
    return loads(row["payload"]) if row else None


def _latest_product_bundle_count(conn: Any) -> tuple[int, str | None]:
    if not _table_exists(conn, "product_signal_snapshots_v14"):
        return 0, None
    row = conn.execute("SELECT data_version, payload FROM product_signal_snapshots_v14 ORDER BY updated_at DESC LIMIT 1").fetchone()
    if not row:
        return 0, None
    payload = loads(row["payload"])
    bundles = (payload.get("productSignalPackages") or payload.get("signals") or []) if isinstance(payload, dict) else []
    return (len(bundles) if isinstance(bundles, list) else 0), row["data_version"]


def _decision_counts(conn: Any, data_version: str | None = None) -> Dict[str, int]:
    if _table_exists(conn, "task_generation_decisions_v15"):
        if data_version:
            rows = conn.execute("SELECT decision, COUNT(*) AS count FROM task_generation_decisions_v15 WHERE data_version = ? GROUP BY decision", (data_version,)).fetchall()
        else:
            rows = conn.execute("SELECT decision, COUNT(*) AS count FROM task_generation_decisions_v15 GROUP BY decision").fetchall()
        return {str(row["decision"]): int(row["count"] or 0) for row in rows}
    if _table_exists(conn, "agent_judgments_v14"):
        rows = conn.execute("SELECT decision, COUNT(*) AS count FROM agent_judgments_v14 GROUP BY decision").fetchall()
        return {str(row["decision"]): int(row["count"] or 0) for row in rows}
    return {}


def _headline(*, bundle_count: int, raw_count: int, package_count: int, run_task_count: int, residual: bool = False) -> str:
    if residual:
        return "运行态有残留，请重新清空演示数据"
    if bundle_count <= 0:
        return "等待数据接入"
    if raw_count <= 0:
        return "数据已建档，等待 Agent 判断"
    if package_count <= 0:
        return "Agent 判断完成，等待商品判断包整合"
    if run_task_count <= 0:
        return f"判断已整合为 {package_count} 个商品判断包，暂无正式任务"
    return f"数据链路已完成，本轮生成 {run_task_count} 个正式任务"


def _station(id_: str, label: str, status: str, note: str = "") -> Dict[str, str]:
    return {"id": id_, "label": label, "status": status, "note": note}


def read_data_line_status() -> Dict[str, Any]:
    ensure_task_generation_run_tables()
    with connect() as conn:
        bundle_count, bundle_data_version = _latest_product_bundle_count(conn)
        latest_run = _latest_generation_run(conn)
        run_data_version = latest_run.get("dataVersion") if latest_run else None
        data_version = run_data_version or bundle_data_version
        raw_judgment_count = _count_by_version(conn, "agent_product_judgments_v15", data_version) or _count_by_version(conn, "agent_judgments_v14", data_version)
        package_count = _count_by_version(conn, "product_judgment_packages_v15", data_version)
        task_decision_count = _count_by_version(conn, "task_generation_decisions_v15", data_version)
        pool_total_count = _count(conn, "task_pool_entries")
        frontend_task_count = _count(conn, "frontend_task_view")
        frontend_product_count = _count(conn, "frontend_product_view")
        decision_counts = _decision_counts(conn, data_version)
        formal_decision_count = int(decision_counts.get("create_task_snapshot", 0) or 0) + int(decision_counts.get("manager_review_required", 0) or 0)
        observe_count = int(decision_counts.get("observe_only", 0) or 0) + int(decision_counts.get("no_task", 0) or 0)
        run_task_count = pool_total_count
        if latest_run:
            raw_judgment_count = int(latest_run.get("agentJudgmentCount") or raw_judgment_count)
            package_count = int(latest_run.get("productJudgmentPackageCount") or package_count)
            task_decision_count = int(latest_run.get("taskDecisionCount") or task_decision_count)
            observe_count = int(latest_run.get("observeOnlyCount") or observe_count)
            formal_decision_count = int(latest_run.get("formalTaskCount") or formal_decision_count)
            run_task_count = int(latest_run.get("taskPoolCreatedCount") or 0)
        upstream_empty = bundle_count == 0 and frontend_product_count == 0 and pool_total_count == 0 and task_decision_count == 0 and package_count == 0
        stale_run_only = bool(upstream_empty and latest_run and raw_judgment_count == 0)
        residual = bool(upstream_empty and (raw_judgment_count > 0 or package_count > 0 or task_decision_count > 0 or pool_total_count > 0))
        if stale_run_only:
            latest_run = None
            data_version = None
            raw_judgment_count = 0
            package_count = 0
            task_decision_count = 0
            observe_count = 0
            formal_decision_count = 0
            run_task_count = 0
        import_status = "passed" if bundle_count or frontend_product_count else "waiting"
        profile_status = "passed" if frontend_product_count or bundle_count else "waiting"
        bundle_status = "passed" if bundle_count else ("current" if import_status == "passed" else "waiting")
        judgment_status = "error" if residual else "passed" if raw_judgment_count else ("current" if bundle_count else "waiting")
        package_status = "error" if residual else "passed" if package_count else ("current" if raw_judgment_count else "waiting")
        if residual:
            task_status = "error"
        elif package_count and run_task_count <= 0 and formal_decision_count <= 0:
            task_status = "empty"
        elif run_task_count > 0:
            task_status = "passed"
        elif formal_decision_count > 0:
            task_status = "current"
        else:
            task_status = "waiting"
        view_status = "passed" if frontend_product_count or frontend_task_count or raw_judgment_count else "waiting"
        line_status = "attention" if residual else "completed" if package_count or run_task_count else "processing" if bundle_count else "waiting"
        if formal_decision_count > 0 and run_task_count <= 0:
            line_status = "attention"
        headline = _headline(bundle_count=bundle_count, raw_count=raw_judgment_count, package_count=package_count, run_task_count=run_task_count, residual=residual)
        stations = [_station("import", "接入", import_status, "数据入库"), _station("profile", "建档", profile_status, f"商品 {frontend_product_count or bundle_count}"), _station("bundle", "全量包", bundle_status, f"{bundle_count} 个包"), _station("judgment", "判断", judgment_status, f"{raw_judgment_count} 条" if raw_judgment_count else "等待"), _station("package", "整合", package_status, f"{package_count} 个包" if package_count else "等待"), _station("task", "任务", task_status, f"本轮 {run_task_count}" if run_task_count else "无正式任务" if task_status == "empty" else "待清空" if residual else "等待"), _station("view", "展示", view_status, "已刷新" if view_status == "passed" else "等待")]
        return {"version": TASK_GENERATION_RUN_VERSION, "ready": bool(bundle_count or raw_judgment_count or latest_run), "lineStatus": line_status, "headline": headline, "dataVersion": data_version, "formalTaskCount": int(run_task_count or 0), "taskPoolTotalCount": int(pool_total_count or 0), "formalJudgmentCount": int(formal_decision_count or 0), "observeOnlyCount": int(observe_count or 0), "dataGapTaskCount": int(latest_run.get("dataGapTaskCount") or 0) if latest_run else 0, "agentJudgmentCount": int(raw_judgment_count or 0), "rawJudgmentCount": int(raw_judgment_count or 0), "productJudgmentPackageCount": int(package_count or 0), "taskDecisionCount": int(task_decision_count or 0), "inputBundleCount": int(bundle_count or 0), "frontendTaskViewCount": int(frontend_task_count or 0), "runtimeResidual": residual, "staleRunIgnored": stale_run_only, "stations": stations, "latestRun": latest_run, "decisionCounts": decision_counts, "updatedAt": now_iso(), "rule": "V14.9.2 metro line shows current-run counts: 接入 / 建档 / 全量包 / 判断 / 整合 / 任务 / 展示. Global task_pool_entries is reported separately as taskPoolTotalCount."}
