"""V12.7 task generation facade.

The facade keeps baseline-first ROI/GMV cadence and the operating action gate,
then adds V12.7 weight confidence policy: business performance is not governance
weight. High ROI / high GMV / first-report labels can create urgency, but cannot
create high-weight approval protection by themselves.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.action_authorization_gate_service import ACTION_AUTHORIZATION_VERSION
from src.services.action_impact_estimation_service import ACTION_IMPACT_ESTIMATION_VERSION
from src.services.operating_cadence_task_service import OPERATING_CADENCE_VERSION, generate_operating_cadence_tasks, operating_cadence_summary
from src.services.operating_weight_policy_service import OPERATING_WEIGHT_POLICY_VERSION
from src.services.rag_business_memory_service import RAG_BUSINESS_MEMORY_VERSION
from src.services.risk_task_v66_service import RISK_TASK_VERSION as STRICT_RISK_TASK_VERSION
from src.services.risk_task_v66_service import ensure_risk_task_tables, generate_risk_tasks_for_signals as _generate_scoped_risk_tasks
from src.services.risk_task_v66_service import risk_task_summary as _scoped_risk_task_summary

RISK_TASK_VERSION = "12.7.0"


def _action_gate_counts(tasks: list[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for task in tasks:
        decision = ((task.get("actionAuthorization") or {}).get("decision") or "not_applied")
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def _weight_gate_counts(tasks: list[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for task in tasks:
        weight = ((task.get("actionAuthorization") or {}).get("objectWeight") or {})
        key = f"{weight.get('weightLevel', 'unknown')}:{weight.get('weightConfidence', 'unknown')}:{weight.get('weightSource', 'unknown')}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def generate_risk_tasks_for_signals(data_version: str | None = None, limit: int = 200, requester_role_id: str = "operator") -> Dict[str, Any]:
    """Generate strict risk tasks plus baseline-gated, action-gated, weight-confident operating tasks."""
    risk_result = _generate_scoped_risk_tasks(data_version=data_version, limit=limit, requester_role_id=requester_role_id)
    cadence_result = generate_operating_cadence_tasks(data_version=data_version, max_tasks=16)
    risk_tasks = risk_result.get("tasks") or []
    cadence_tasks = cadence_result.get("tasks") or []
    all_tasks = [*risk_tasks, *cadence_tasks]
    return {
        **risk_result,
        "version": RISK_TASK_VERSION,
        "mode": "v12_7_baseline_first_action_gate_weight_confidence_task_generation",
        "dataVersion": data_version,
        "strictRiskTaskVersion": STRICT_RISK_TASK_VERSION,
        "operatingCadenceVersion": OPERATING_CADENCE_VERSION,
        "actionAuthorizationVersion": ACTION_AUTHORIZATION_VERSION,
        "actionImpactEstimationVersion": ACTION_IMPACT_ESTIMATION_VERSION,
        "ragBusinessMemoryVersion": RAG_BUSINESS_MEMORY_VERSION,
        "operatingWeightPolicyVersion": OPERATING_WEIGHT_POLICY_VERSION,
        "primaryAxis": "ROI_GMV",
        "baselineMode": bool(cadence_result.get("baselineMode")),
        "comparisonReady": bool(cadence_result.get("comparisonReady")),
        "trendReady": bool(cadence_result.get("trendReady")),
        "createdTaskCount": len(all_tasks),
        "strictRiskCreatedTaskCount": len(risk_tasks),
        "operatingCadenceCreatedTaskCount": len(cadence_tasks),
        "blockedByBaselineCount": cadence_result.get("blockedByBaselineCount", 0),
        "actionGateDecisionCounts": _action_gate_counts(all_tasks),
        "weightGateCounts": _weight_gate_counts(all_tasks),
        "tasks": all_tasks,
        "strictRiskSync": risk_result,
        "operatingCadenceSync": cadence_result,
        "dailyReportSeedCount": len(cadence_result.get("topSignals") or []),
        "rule": "V12.7：首份报表仍只建基线；高权重是公司治理标签，不是高ROI/高GMV表现标签；只有RAG配置、主管/老板标记或多期历史贡献能触发高权重审批。",
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
    summary["operatingWeightPolicyVersion"] = OPERATING_WEIGHT_POLICY_VERSION
    summary["operatingCadenceSummary"] = cadence
    summary["rule"] = "V12.7：经营表现、任务优先级、生命周期标签和首份报表标签不能当作高权重；高权重必须有明确治理来源和置信度。"
    return summary
