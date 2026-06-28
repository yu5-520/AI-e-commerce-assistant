"""V12.8 task handling evidence service.

Operators submit structured handling evidence, managers review it, and approved
reviews now trigger the task lifecycle orchestrator to schedule recap cycles and
prepare the RAG feedback loop.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List
from uuid import uuid4

from src.services.account_service import get_user, user_display
from src.services.module_task_service import create_log, find_task, now_iso, review_task, submit_task, task_visible_to_viewer
from src.services.task_evidence_audit_service import persist_evidence_review, persist_evidence_submission
from src.services.task_lifecycle_orchestrator_service import TASK_LIFECYCLE_VERSION, handle_evidence_submitted, handle_manager_reviewed
from src.services.task_recap_service import add_recap_candidate

EVIDENCE_VERSION = "12.8.0"

DOMAIN_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "库存": {"title": "库存处理表单", "fields": ["当前库存确认", "预计补货时间", "是否暂停投流", "是否调整主推商品", "是否需要总管协调供货"], "actions": ["确认库存", "确认补货", "暂停投流", "调整主推"]},
    "售后": {"title": "售后处理表单", "fields": ["主要退款原因", "是否商品问题", "是否详情页承诺问题", "是否客服话术问题", "是否暂停放量"], "actions": ["复查退款", "修改承诺", "调整话术", "暂停放量"]},
    "流量": {"title": "流量处理表单", "fields": ["当前 ROI", "是否继续投放", "是否更换素材", "是否降低预算", "是否先查商品承接"], "actions": ["降低预算", "更换素材", "暂停投放", "继续观察"]},
    "价格": {"title": "价格 / 毛利处理表单", "fields": ["当前售价", "当前成本", "活动价是否异常", "是否需要调价", "是否暂停活动"], "actions": ["核对成本", "核对活动价", "暂停活动", "提交财务复核"]},
    "报表": {"title": "报表处理表单", "fields": ["数据是否可信", "是否需要重新导入", "异常字段", "影响范围", "复盘说明"], "actions": ["确认数据", "重新导入", "补充说明", "提交复核"]},
}


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def template_for_task(task: Dict[str, Any]) -> Dict[str, Any]:
    domain = task.get("riskDomain") or "报表"
    template = DOMAIN_TEMPLATES.get(domain, DOMAIN_TEMPLATES["报表"])
    return {"version": EVIDENCE_VERSION, "riskDomain": domain, **deepcopy(template)}


def _safe_form_fields(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    return {str(key): value for key, value in raw.items() if value not in {None, ""}}


def _task_or_none(task_id: str, viewer_id: str | None = None) -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    if viewer_id and not task_visible_to_viewer(task, viewer_id):
        return None
    return task


def get_task_evidence(task_id: str, viewer_id: str | None = None) -> Dict[str, Any] | None:
    task = _task_or_none(task_id, viewer_id)
    if not task:
        return None
    records = task.get("evidenceRecords") or []
    reviews = task.get("evidenceReviews") or []
    return {
        "version": EVIDENCE_VERSION,
        "lifecycleVersion": TASK_LIFECYCLE_VERSION,
        "taskId": task_id,
        "status": task.get("status"),
        "workflowStatus": task.get("workflowStatus"),
        "taskLifecycle": task.get("taskLifecycle"),
        "template": template_for_task(task),
        "records": deepcopy(records),
        "reviews": deepcopy(reviews),
        "latestSubmission": deepcopy(records[0]) if records else None,
        "latestReview": deepcopy(reviews[0]) if reviews else None,
        "submitSummary": task.get("submitSummary") or task.get("submissionNote"),
        "reviewResult": task.get("reviewResult"),
        "reviewComment": task.get("reviewComment") or task.get("reviewNote"),
        "auditPersistence": task.get("evidenceAudit"),
    }


def submit_task_evidence(task_id: str, body: Dict[str, Any] | None = None, submitter_id: str | None = None) -> Dict[str, Any] | None:
    body = body or {}
    task = _task_or_none(task_id, submitter_id)
    if not task:
        return None
    submitter = get_user(submitter_id) if submitter_id else None
    summary = body.get("summary") or body.get("note") or "运营已提交处理结果和证据，等待店群总管复核。"
    action = body.get("action") or body.get("handlingAction") or task.get("taskType") or "处理完成"
    result = body.get("result") or body.get("handlingResult") or "已处理，待复核。"
    form_fields = _safe_form_fields(body.get("formFields") or body.get("fields"))
    record = {
        "id": make_id("EVIDENCE"),
        "taskId": task_id,
        "submittedById": submitter_id or task.get("assigneeId"),
        "submittedByName": submitter.get("name") if submitter else user_display(submitter_id or task.get("assigneeId"), "运营账号"),
        "submittedAt": now_iso(),
        "action": action,
        "summary": summary,
        "result": result,
        "needFollowUp": bool(body.get("needFollowUp")),
        "enterRecap": bool(body.get("enterRecap")),
        "formFields": form_fields,
        "evidenceLinks": body.get("evidenceLinks") or body.get("attachments") or [],
        "status": "待复核",
        "version": EVIDENCE_VERSION,
    }
    records: List[Dict[str, Any]] = [record, *(task.get("evidenceRecords") or [])]
    task.update({
        "evidenceFormVersion": EVIDENCE_VERSION,
        "evidenceTemplate": template_for_task(task),
        "evidenceRecords": records[:10],
        "latestEvidenceRecord": record,
        "submitSummary": summary,
        "submissionNote": summary,
        "handlingAction": action,
        "handlingResult": result,
        "needFollowUp": bool(body.get("needFollowUp")),
        "enterRecap": bool(body.get("enterRecap")),
    })
    result_task = submit_task(task_id, note=summary, submitter_id=submitter_id)
    if result_task:
        result_task["latestEvidenceRecord"] = record
        result_task["evidenceRecords"] = records[:10]
        lifecycle = handle_evidence_submitted(task_id, evidence=record, actor_user_id=submitter_id)
        result_task["taskLifecycle"] = (lifecycle or {}).get("taskLifecycle") or result_task.get("taskLifecycle")
    audit = persist_evidence_submission(result_task or task, record)
    task["evidenceAudit"] = audit
    if result_task:
        result_task["evidenceAudit"] = audit
    create_log({"type": "处理证据提交", "task": task, "status": "待复核", "action": action, "result": summary, "operator": record["submittedByName"]})
    return result_task


def review_task_evidence(task_id: str, body: Dict[str, Any] | None = None, reviewer_id: str | None = None) -> Dict[str, Any] | None:
    body = body or {}
    task = _task_or_none(task_id, reviewer_id)
    if not task:
        return None
    decision = body.get("decision") or "approve"
    approved = decision in {"approve", "approved", "pass", "通过"}
    reviewer = get_user(reviewer_id) if reviewer_id else None
    comment = body.get("comment") or body.get("note") or ("证据充分，复核通过。" if approved else "证据不足，退回补充。")
    review = {
        "id": make_id("REVIEW"),
        "taskId": task_id,
        "reviewerId": reviewer_id or task.get("reviewerId"),
        "reviewerName": reviewer.get("name") if reviewer else user_display(reviewer_id or task.get("reviewerId"), "店群总管"),
        "reviewedAt": now_iso(),
        "decision": "通过" if approved else "退回",
        "comment": comment,
        "evidenceRecordId": (task.get("latestEvidenceRecord") or {}).get("id"),
        "version": EVIDENCE_VERSION,
    }
    reviews = [review, *(task.get("evidenceReviews") or [])]
    task.update({"evidenceReviews": reviews[:10], "latestEvidenceReview": review, "reviewResult": review["decision"], "reviewComment": comment, "reviewNote": comment})
    result_task = review_task(task_id, decision="approve" if approved else "return", note=comment, reviewer_id=reviewer_id)
    if approved:
        recap = add_recap_candidate(task, evidence=task.get("latestEvidenceRecord"), review=review)
        task["recapCandidateId"] = recap.get("id")
        task["recapCandidateStatus"] = recap.get("status")
        lifecycle = handle_manager_reviewed(task_id, approved=True, review=review, actor_user_id=reviewer_id)
        create_log({"type": "复盘周期", "task": task, "status": "已排期", "action": "生成自动复盘周期", "result": "任务已进入自动复盘周期。", "operator": review["reviewerName"]})
        create_log({"type": "复盘候选", "task": task, "status": "候选", "action": f"自动进入{recap.get('recapTarget')}", "result": recap.get("evidenceSummary") or "处理结果已沉淀为复盘候选。", "operator": review["reviewerName"]})
    else:
        lifecycle = handle_manager_reviewed(task_id, approved=False, review=review, actor_user_id=reviewer_id)
    if result_task:
        result_task["latestEvidenceReview"] = review
        result_task["evidenceReviews"] = reviews[:10]
        result_task["recapCandidateId"] = task.get("recapCandidateId")
        result_task["recapCandidateStatus"] = task.get("recapCandidateStatus")
        result_task["taskLifecycle"] = (lifecycle or {}).get("taskLifecycle") or result_task.get("taskLifecycle")
    audit = persist_evidence_review(result_task or task, review)
    task["evidenceAudit"] = audit
    if result_task:
        result_task["evidenceAudit"] = audit
    create_log({"type": "处理证据复核", "task": task, "status": "已完成" if approved else "已退回", "action": f"证据复核{review['decision']}", "result": comment, "operator": review["reviewerName"]})
    return result_task
