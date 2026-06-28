"""V12.5 task generation facade.

The facade keeps strict red-line risk tasks, but daily ROI/GMV operating tasks
must now pass the baseline-first cadence gate:

- first report = baseline only;
- two reports = comparison / month-over-month style operating review;
- three reports or a 7 day window = short trend tasks;
- red-line tasks can still be created on the first report.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.operating_cadence_task_service import OPERATING_CADENCE_VERSION, generate_operating_cadence_tasks, operating_cadence_summary
from src.services.risk_task_v66_service import RISK_TASK_VERSION as STRICT_RISK_TASK_VERSION
from src.services.risk_task_v66_service import ensure_risk_task_tables, generate_risk_tasks_for_signals as _generate_scoped_risk_tasks
from src.services.risk_task_v66_service import risk_task_summary as _scoped_risk_task_summary

RISK_TASK_VERSION = "12.5.0"


def generate_risk_tasks_for_signals(data_version: str | None = None, limit: int = 200, requester_role_id: str = "operator") -> Dict[str, Any]:
    """Generate strict risk tasks plus baseline-gated ROI/GMV cadence tasks."""
    risk_result = _generate_scoped_risk_tasks(data_version=data_version, limit=limit, requester_role_id=requester_role_id)
    cadence_result = generate_operating_cadence_tasks(data_version=data_version, max_tasks=16)
    risk_tasks = risk_result.get("tasks") or []
    cadence_tasks = cadence_result.get("tasks") or []
    return {
        **risk_result,
        "version": RISK_TASK_VERSION,
        "mode": "v12_5_baseline_first_redline_plus_roi_gmv_operating_task_generation",
        "dataVersion": data_version,
        "strictRiskTaskVersion": STRICT_RISK_TASK_VERSION,
        "operatingCadenceVersion": OPERATING_CADENCE_VERSION,
        "primaryAxis": "ROI_GMV",
        "baselineMode": bool(cadence_result.get("baselineMode")),
        "comparisonReady": bool(cadence_result.get("comparisonReady")),
        "trendReady": bool(cadence_result.get("trendReady")),
        "createdTaskCount": len(risk_tasks) + len(cadence_tasks),
        "strictRiskCreatedTaskCount": len(risk_tasks),
        "operatingCadenceCreatedTaskCount": len(cadence_tasks),
        "blockedByBaselineCount": cadence_result.get("blockedByBaselineCount", 0),
        "tasks": [*risk_tasks, *cadence_tasks],
        "strictRiskSync": risk_result,
        "operatingCadenceSync": cadence_result,
        "dailyReportSeedCount": len(cadence_result.get("topSignals") or []),
        "rule": "V12.5：首份报表只建基线，非红线 ROI/GMV 经营任务必须至少有两份可比报表；红线仍强制进入执行队列。",
    }


def risk_task_summary(limit: int = 30) -> Dict[str, Any]:
    summary = _scoped_risk_task_summary(limit=limit)
    cadence = operating_cadence_summary(limit=limit)
    summary["version"] = RISK_TASK_VERSION
    summary["primaryAxis"] = "ROI_GMV"
    summary["baselineFirst"] = True
    summary["operatingCadenceSummary"] = cadence
    summary["rule"] = "V12.5：任务池、候选任务、趋势信号和观察项共同支撑日报/周报；首份报表只做基线观察，后续报表对比后才生成经营任务。"
    return summary
