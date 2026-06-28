"""V12.8 RAG feedback loop service.

Completed recap cycles can become structured RAG candidates. Approved/effective
experience cards are then retrieved during future task generation.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

from src.services.experience_memory_service import draft_experience_from_task, search_cases
from src.services.module_task_service import find_task

RAG_FEEDBACK_LOOP_VERSION = "12.8.0"


def _problem_type(task: Dict[str, Any]) -> str:
    text = " ".join(str(value or "") for value in [task.get("riskDomain"), task.get("taskType"), task.get("title"), task.get("reason"), task.get("task")])
    if any(token in text for token in ("库存", "补货", "可售天数", "断货", "缺货", "活动")):
        return "low_inventory_activity"
    if any(token in text for token in ("点击", "CTR", "主图", "标题", "素材")):
        return "low_ctr_low_conversion"
    if any(token in text for token in ("转化", "详情页", "承接")):
        return "detail_page_conversion"
    if any(token in text for token in ("ROI", "退款", "售后", "低")):
        return "low_roi_high_refund"
    return "general_operation"


def build_rag_candidate_from_recap(task_id: str, *, recap_result: Dict[str, Any] | None = None, user_id: str | None = None) -> Dict[str, Any] | None:
    task = find_task(task_id)
    if not task:
        return None
    recap_result = recap_result or {}
    card = draft_experience_from_task(
        task_id,
        operator_submission=task.get("submissionNote") or task.get("submitSummary") or "运营提交材料待补充。",
        manager_review=recap_result.get("conclusion") or task.get("reviewNote") or "复盘完成，等待人工审核是否进入RAG。",
        before_metrics=recap_result.get("beforeMetrics") or task.get("beforeMetrics") or {},
        after_metrics=recap_result.get("afterMetrics") or task.get("afterMetrics") or {},
        user_id=user_id,
    )
    if not card:
        return None
    return {
        "version": RAG_FEEDBACK_LOOP_VERSION,
        "source": "automatic_recap_completed",
        "taskId": task_id,
        "recapResult": recap_result,
        "ragCandidate": card,
        "rule": "复盘有指标变化和复核结论时生成RAG候选；正式召回前仍需人工审核为approved。",
    }


def retrieve_rag_feedback_for_task(task: Dict[str, Any], *, limit: int = 5) -> Dict[str, Any]:
    problem_type = _problem_type(task)
    result = search_cases(
        query=" ".join(str(value or "") for value in [task.get("title"), task.get("reason"), task.get("task")]),
        category_id=task.get("categoryId"),
        platform=task.get("platform"),
        store_id=(task.get("storeIds") or task.get("visibleStoreIds") or [task.get("storeId") or "global"])[0],
        problem_type=problem_type,
        effective_only=True,
        min_quality=0.7,
        limit=limit,
    )
    items: List[Dict[str, Any]] = [deepcopy(item) for item in result.get("items") or []]
    return {
        "version": RAG_FEEDBACK_LOOP_VERSION,
        "mode": "approved_experience_cards_to_task_generation",
        "problemType": problem_type,
        "items": items,
        "matchedCount": len(items),
        "retrieval": {key: value for key, value in result.items() if key not in {"items"}},
        "rule": "只召回approved且effective的经验卡；pending_review仅作为候选，不直接增强任务。",
    }


def apply_rag_feedback_to_task(task: Dict[str, Any]) -> Dict[str, Any]:
    feedback = retrieve_rag_feedback_for_task(task)
    memory = dict(task.get("ragBusinessMemory") or {})
    memory["feedbackLoopVersion"] = RAG_FEEDBACK_LOOP_VERSION
    memory["approvedExperienceCards"] = feedback.get("items") or []
    memory["approvedExperienceMatchedCount"] = feedback.get("matchedCount", 0)
    memory["feedbackRule"] = feedback.get("rule")
    return {**task, "ragBusinessMemory": memory, "ragFeedbackLoop": feedback}
