"""V12.4.1 task generation facade.

Risk tasks are still supported, but task generation is no longer only a single
baseline alarm.  The facade now combines:

- V12.2 strict scoped evidence-gated risk tasks;
- V12.4.1 ROI/GMV centred upload-frequency + 3/7/14/30/90 day cadence tasks;
- daily/weekly report seeds from candidate signals.
"""

from __future__ import annotations

from typing import Any, Dict

from src.services.operating_cadence_task_service import OPERATING_CADENCE_VERSION, generate_operating_cadence_tasks, operating_cadence_summary
from src.services.risk_task_v66_service import RISK_TASK_VERSION as STRICT_RISK_TASK_VERSION
from src.services.risk_task_v66_service import ensure_risk_task_tables, generate_risk_tasks_for_signals as _generate_scoped_risk_tasks
from src.services.risk_task_v66_service import risk_task_summary as _scoped_risk_task_summary

RISK_TASK_VERSION = "12.4.1"


def generate_risk_tasks_for_signals(data_version: str | None = None, limit: int = 200, requester_role_id: str = "operator") -> Dict[str, Any]:
    """Generate strict risk tasks plus ROI/GMV operating cadence tasks.

    The old facade name is kept so import routes do not break.  The behavior is
    upgraded: facts that do not cross redline thresholds can still create daily
    ROI/GMV operating tasks or report seeds when upload cadence and trend windows
    show meaningful business movement.
    """
    risk_result = _generate_scoped_risk_tasks(data_version=data_version, limit=limit, requester_role_id=requester_role_id)
    cadence_result = generate_operating_cadence_tasks(data_version=data_version, max_tasks=16)
    risk_tasks = risk_result.get("tasks") or []
    cadence_tasks = cadence_result.get("tasks") or []
    return {
        **risk_result,
        "version": RISK_TASK_VERSION,
        "mode": "v12_4_1_redline_plus_roi_gmv_operating_cadence_task_generation",
        "dataVersion": data_version,
        "strictRiskTaskVersion": STRICT_RISK_TASK_VERSION,
        "operatingCadenceVersion": OPERATING_CADENCE_VERSION,
        "primaryAxis": "ROI_GMV",
        "createdTaskCount": len(risk_tasks) + len(cadence_tasks),
        "strictRiskCreatedTaskCount": len(risk_tasks),
        "operatingCadenceCreatedTaskCount": len(cadence_tasks),
        "tasks": [*risk_tasks, *cadence_tasks],
        "strictRiskSync": risk_result,
        "operatingCadenceSync": cadence_result,
        "dailyReportSeedCount": len((cadence_result.get("cadence") or {}).keys()) and len(cadence_result.get("topSignals") or []),
        "rule": "V12.4.1：红线继续硬控；日常运营以ROI和GMV为主轴，库存、流量、点击、转化、退款、毛利用于解释原因并生成动作。",
    }


def risk_task_summary(limit: int = 30) -> Dict[str, Any]:
    summary = _scoped_risk_task_summary(limit=limit)
    cadence = operating_cadence_summary(limit=limit)
    summary["version"] = RISK_TASK_VERSION
    summary["primaryAxis"] = "ROI_GMV"
    summary["operatingCadenceSummary"] = cadence
    summary["rule"] = "V12.4.1：任务池、候选任务、趋势信号和观察项共同支撑日报/周报；日报/周报优先围绕ROI、GMV和广告消耗组织。"
    return summary
