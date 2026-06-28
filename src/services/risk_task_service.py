"""V12.6 task generation facade.

The facade keeps V12.5 baseline-first ROI/GMV cadence, and adds the V12.6
operating action gate. The task generator now treats activity报名、标题/主图测试、
价格、投放、库存、主推位等 as controlled operating actions instead of plain task
text.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.action_authorization_gate_service import ACTION_AUTHORIZATION_VERSION
from src.services.action_impact_estimation_service import ACTION_IMPACT_ESTIMATION_VERSION
from src.services.operating_cadence_task_service import OPERATING_CADENCE_VERSION, generate_operating_cadence_tasks, operating_cadence_summary
from src.services.rag_business_memory_service import RAG_BUSINESS_MEMORY_VERSION
from src.services.risk_task_v66_service import RISK_TASK_VERSION as STRICT_RISK_TASK_VERSION
from src.services.risk_task_v66_service import ensure_risk_task_tables, generate_risk_tasks_for_signals as _generate_scoped_risk_tasks
from src.services.risk_task_v66_service import risk_task_summary as _scoped_risk_task_summary

RISK_TASK_VERSION = "12.6.0"


def _action_gate_counts(tasks: list[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for task in tasks:
        decision = ((task.get("actionAuthorization") or {}).get("decision") or "not_applied")
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def generate_risk_tasks_for_signals(data_version: str | None = None, limit: int = 200, requester_role_id: str = "operator") -> Dict[str, Any]:
    """Generate strict risk tasks plus baseline-gated and action-gated operating tasks."""
    risk_result = _generate_scoped_risk_tasks(data_version=data_version, limit=limit, requester_role_id=requester_role_id)
    cadence_result = generate_operating_cadence_tasks(data_version=data_version, max_tasks=16)
    risk_tasks = risk_result.get("tasks") or []
    cadence_tasks = cadence_result.get("tasks") or []
    all_tasks = [*risk_tasks, *cadence_tasks]
    return {
        **risk_result,
        "version": RISK_TASK_VERSION,
        "mode": "v12_6_baseline_first_action_gate_operating_task_generation",
        "dataVersion": data_version,
        "strictRiskTaskVersion": STRICT_RISK_TASK_VERSION,
        "operatingCadenceVersion": OPERATING_CADENCE_VERSION,
        "actionAuthorizationVersion": ACTION_AUTHORIZATION_VERSION,
        "actionImpactEstimationVersion": ACTION_IMPACT_ESTIMATION_VERSION,
        "ragBusinessMemoryVersion": RAG_BUSINESS_MEMORY_VERSION,
        "primaryAxis": "ROI_GMV",
        "baselineMode": bool(cadence_result.get("baselineMode")),
        "comparisonReady": bool(cadence_result.get("comparisonReady")),
        "trendReady": bool(cadence_result.get("trendReady")),
        "createdTaskCount": len(all_tasks),
        "strictRiskCreatedTaskCount": len(risk_tasks),
        "operatingCadenceCreatedTaskCount": len(cadence_tasks),
        "blockedByBaselineCount": cadence_result.get("blockedByBaselineCount", 0),
        "actionGateDecisionCounts": _action_gate_counts(all_tasks),
        "tasks": all_tasks,
        "strictRiskSync": risk_result,
        "operatingCadenceSync": cadence_result,
        "dailyReportSeedCount": len(cadence_result.get("topSignals") or []),
        "rule": "V12.6：首份报表仍只建基线；经营任务生成后必须经过RAG经营动作权限闸门，系统估算影响，运营只补事实，超权限或低于基线进入主管/老板确认。",
    }


def risk_task_summary(limit: int = 30) -> Dict[str, Any]:
    summary = _scoped_risk_task_summary(limit=limit)
    cadence = operating_cadence_summary(limit=limit)
    summary["version"] = RISK_TASK_VERSION
    summary["primaryAxis"] = "ROI_GMV"
    summary["baselineFirst"] = True
    summary["actionGateVersion"] = ACTION_AUTHORIZATION_VERSION
    summary["actionImpactEstimationVersion"] = ACTION_IMPACT_ESTIMATION_VERSION
    summary["ragBusinessMemoryVersion"] = RAG_BUSINESS_MEMORY_VERSION
    summary["operatingCadenceSummary"] = cadence
    summary["rule"] = "V12.6：任务池、候选任务、趋势信号和观察项共同支撑日报/周报；经营动作统一经过账号权限、对象权重、系统估算和RAG基线校验。"
    return summary
