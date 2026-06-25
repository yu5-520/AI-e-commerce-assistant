"""Task report service for V11.8 structured SOP task packages.

The detail page no longer invents a legacy fallback report from old task fields.
If a task lacks taskDetailReport, the UI should show a clear structure-missing
state and ask the user to regenerate the task from the new chain.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from src.services.account_service import get_user
from src.services.module_task_service import list_tasks

ROLE_INSIGHTS = {
    "owner": {"title": "老板战略视角", "summary": "重点看预算、利润、售后和组织责任是否闭环。", "focus": ["利润影响", "组织瓶颈", "预算是否继续放大", "责任链是否闭环"], "hidden": []},
    "manager": {"title": "店群管理视角", "summary": "重点判断任务是否拆给正确运营、提交证据是否充分、同类问题是否反复出现。", "focus": ["派发对象", "处理进度", "复核质量", "退回原因"], "hidden": ["跨店群老板级归因"]},
    "operator": {"title": "运营执行视角", "summary": "重点看我为什么要处理、要检查哪些字段、处理完提交什么证据。", "focus": ["执行清单", "字段检查", "提交证据", "退回补充"], "hidden": ["财务利润细节", "其他运营任务", "组织瓶颈"]},
    "finance": {"title": "财务经营视角", "summary": "重点看退款成本、广告消耗、利润承接、库存资金和数据可信度。", "focus": ["利润承接", "退款成本", "ROI 可信度", "库存资金"], "hidden": ["运营派发按钮", "人员复核动作"]},
    "observer": {"title": "只读摘要视角", "summary": "只确认风险已进入流程、当前状态和最终归档结果。", "focus": ["风险状态", "处理进度", "归档结果"], "hidden": ["财务细节", "人员绩效", "任务责任链"]},
}


def _now() -> str:
    return datetime.now().isoformat()


def _apply_role_insight(report: Dict[str, Any], user_id: str | None = None) -> Dict[str, Any]:
    user = get_user(user_id)
    if not user:
        return report
    insight = ROLE_INSIGHTS.get(user.get("roleId"), ROLE_INSIGHTS["observer"])
    report["viewer"] = {"userId": user.get("id"), "name": user.get("name"), "roleName": user.get("roleName"), "insightDepth": user.get("insightDepth"), "permissionNames": user.get("permissionNames", [])}
    report["roleInsight"] = insight
    report["insightDepth"] = user.get("insightDepth")
    return report


def _structure_missing_report(task_id: str, user_id: str | None = None, task: Dict[str, Any] | None = None) -> Dict[str, Any]:
    report = {
        "reportId": f"RPT-STRUCTURE-MISSING-{task_id}",
        "reportType": "structure_missing",
        "module": "task",
        "sourceModule": "V11.8任务结构守卫",
        "sourceRoute": "business-actions",
        "entityId": task_id,
        "taskId": task_id,
        "taskStatus": (task or {}).get("status") or "结构缺失",
        "generatedAt": _now(),
        "title": f"任务结构缺失｜{task_id}",
        "warningSummary": "该任务不是由 V11.8 经营对象 + 指标证据 + SOP 任务包生成，已禁止用旧字段自动拼接详情报告。",
        "riskLevel": (task or {}).get("priority") or "中",
        "evidence": [{"label": "缺失结构", "value": "taskDetailReport / evidencePack / sopSteps / ownership"}],
        "aiAssessment": "旧任务详情兜底已删除。请重新从经营对象主档和指标证据生成结构化任务。",
        "suggestedActions": ["返回数据页重新生成任务", "检查经营对象是否已入库", "确认任务是否来自 V11.8 SOP 任务包"],
        "operationChecklist": ["确认商品/店铺归属", "确认指标证据", "重新生成 SOP 任务包"],
        "dataNeeded": ["经营对象主档", "指标证据", "趋势信号", "权限归属"],
        "humanDecision": ["是否重新生成任务", "是否归档旧任务"],
        "nextStep": "重新导入或重新生成任务，直到任务包含 taskDetailReport。",
        "agentBoundary": "详情页只展示任务生成链路写入的结构化报告，不再编造兜底报告。",
        "fallbackDetail": False,
        "structureMissing": True,
        "relatedTask": task,
    }
    return _apply_role_insight(report, user_id)


def _report_from_structured_task(task: Dict[str, Any], task_id: str, user_id: str | None = None) -> Dict[str, Any]:
    detail = dict(task.get("taskDetailReport") or {})
    card = task.get("taskCard") or {}
    detail.setdefault("reportId", f"RPT-TASK-{task_id}")
    detail.setdefault("reportType", "task")
    detail.setdefault("module", "task")
    detail.setdefault("sourceModule", task.get("sourceModule") or "V11.8 SOP任务包")
    detail.setdefault("sourceRoute", task.get("sourceRoute") or "business-actions")
    detail.setdefault("entityId", task.get("entityId") or task.get("productId") or task_id)
    detail.setdefault("taskId", task_id)
    detail.setdefault("taskStatus", task.get("status"))
    detail.setdefault("generatedAt", _now())
    detail.setdefault("title", f"任务详情报告｜{card.get('title') or task.get('title') or task_id}")
    detail.setdefault("warningSummary", task.get("reason") or "结构化 SOP 任务。")
    detail.setdefault("riskLevel", task.get("priority") or "中")
    detail.setdefault("evidence", task.get("evidencePack") or task.get("evidence") or [])
    detail.setdefault("suggestedActions", task.get("sopSteps") or [])
    detail.setdefault("operationChecklist", task.get("sopSteps") or [])
    detail.setdefault("dataNeeded", ["经营对象主档", "指标证据", "复核截图或数据"])
    detail.setdefault("humanDecision", ["是否完成处理", "是否提交复核", "是否需要补充数据"])
    detail.setdefault("nextStep", "按 SOP 完成处理，并提交证据给复核人。")
    detail["taskCard"] = card
    detail["evidencePack"] = task.get("evidencePack") or detail.get("evidencePack") or []
    detail["sopSteps"] = task.get("sopSteps") or detail.get("sopSteps") or []
    detail["reviewMetrics"] = task.get("reviewMetrics") or detail.get("reviewMetrics") or {}
    detail["completionGate"] = task.get("completionGate") or detail.get("completionGate") or []
    detail["failureThreshold"] = task.get("failureThreshold") or detail.get("failureThreshold") or {}
    detail["ownership"] = task.get("ownership") or {}
    detail["agentJudgment"] = task.get("agentJudgment") or {}
    detail["relatedTask"] = task
    detail["fallbackDetail"] = False
    detail["structureMissing"] = False
    return _apply_role_insight(detail, user_id)


def get_candidate_report(module: str, entity_id: str, user_id: str | None = None) -> Dict[str, Any] | None:
    return _structure_missing_report(entity_id, user_id)


def get_task_report(task_id: str, user_id: str | None = None) -> Dict[str, Any] | None:
    task = next((item for item in list_tasks(active_only=False, viewer_id=user_id) if item.get("id") == task_id), None)
    if not task:
        return _structure_missing_report(task_id, user_id)
    if not task.get("taskDetailReport"):
        return _structure_missing_report(task_id, user_id, task)
    return _report_from_structured_task(task, task_id, user_id)
