"""V14.4 task intent contract service.

TaskIntent is the stable boundary between Agent output, task snapshots, task pool,
and legacy task creation. New upstream packages can change, but downstream code
only consumes this normalized contract.
"""

from __future__ import annotations

from typing import Any, Dict, List

TASK_INTENT_CONTRACT_VERSION = "14.4.0"


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _metric_rows(*values: Any) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for value in values:
        for item in _as_list(value):
            if isinstance(item, dict):
                if item.get("metricCode") or item.get("label") or item.get("title"):
                    rows.append(item)
            elif isinstance(item, str):
                rows.append({"label": item, "value": None})
    return rows


def _evidence_requirements(*values: Any) -> List[str]:
    result: List[str] = []
    for value in values:
        if isinstance(value, dict):
            required = value.get("required")
            if isinstance(required, list):
                result.extend(str(item) for item in required if item)
            continue
        for item in _as_list(value):
            if isinstance(item, dict):
                label = item.get("title") or item.get("label") or item.get("name")
                if label:
                    result.append(str(label))
            elif item:
                result.append(str(item))
    return list(dict.fromkeys(result))


def normalize_task_intent(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = payload or {}
    task_plan = payload.get("taskPlan") or {}
    signal = payload.get("signal") or ((payload.get("systemFacts") or {}).get("signal") if isinstance(payload.get("systemFacts"), dict) else {}) or {}
    budget = payload.get("operationBudget") or task_plan.get("operationBudget") or {}
    entity = {
        "entityType": payload.get("entityType") or task_plan.get("entityType") or signal.get("entityType") or "product",
        "entityId": payload.get("entityId") or task_plan.get("entityId") or signal.get("entityId"),
        "productId": payload.get("productId") or task_plan.get("productId") or signal.get("productId"),
        "storeId": payload.get("storeId") or task_plan.get("storeId") or signal.get("storeId"),
        "verticalCategory": task_plan.get("verticalCategory") or signal.get("verticalCategory"),
    }
    sop = _as_list(task_plan.get("sopSteps") or payload.get("sop") or payload.get("steps"))
    evidence = _evidence_requirements(payload.get("evidenceRequirements"), task_plan.get("evidenceRequirements"), payload.get("evidencePack"))
    metrics = _metric_rows(payload.get("metricFacts"), payload.get("reviewMetrics"), (signal.get("productMetricSnapshot") or {}).get("metricFacts") if isinstance(signal.get("productMetricSnapshot"), dict) else None)
    intent = {
        "version": TASK_INTENT_CONTRACT_VERSION,
        "taskType": task_plan.get("taskType") or payload.get("taskType") or "general_operation",
        "decision": payload.get("decision") or task_plan.get("decision") or "create_task_snapshot",
        "riskLevel": payload.get("riskLevel") or task_plan.get("riskLevel") or budget.get("riskLevel") or "low",
        "priority": task_plan.get("priority") or payload.get("priority") or "中",
        "title": task_plan.get("title") or payload.get("title") or "经营任务",
        "deadline": task_plan.get("deadline") or payload.get("deadline") or "24小时内",
        "entity": entity,
        "budget": budget,
        "sop": [str(item) for item in sop if item],
        "evidenceRequirements": evidence,
        "metricFacts": metrics,
        "sourceRefs": {
            "signalId": payload.get("signalRef") or payload.get("signalId"),
            "judgmentId": (payload.get("systemFacts") or {}).get("judgmentId") if isinstance(payload.get("systemFacts"), dict) else payload.get("judgmentId"),
            "taskSnapshotId": payload.get("taskSnapshotId"),
        },
    }
    return intent


def validate_task_intent(intent: Dict[str, Any]) -> Dict[str, Any]:
    missing = []
    if not intent.get("decision"):
        missing.append("decision")
    if not intent.get("title"):
        missing.append("title")
    if not isinstance(intent.get("entity"), dict):
        missing.append("entity")
    if not isinstance(intent.get("evidenceRequirements"), list):
        missing.append("evidenceRequirements")
    if not isinstance(intent.get("metricFacts"), list):
        missing.append("metricFacts")
    return {"version": TASK_INTENT_CONTRACT_VERSION, "status": "passed" if not missing else "failed", "missing": missing}


def to_legacy_task_payload(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    intent = normalize_task_intent(payload)
    validation = validate_task_intent(intent)
    entity = intent.get("entity") or {}
    return {
        **(payload or {}),
        "taskIntent": intent,
        "taskIntentValidation": validation,
        "title": intent.get("title"),
        "priority": intent.get("priority"),
        "riskLevel": intent.get("riskLevel"),
        "storeId": entity.get("storeId"),
        "productId": entity.get("productId"),
        "verticalCategory": entity.get("verticalCategory"),
        "operationBudget": intent.get("budget") or {},
        "evidencePack": [{"title": item, "value": None} for item in intent.get("evidenceRequirements") or []],
        "actionImpactInput": {"metrics": intent.get("metricFacts") or [], "budget": intent.get("budget") or {}, "taskType": intent.get("taskType")},
        "sopSteps": intent.get("sop") or [],
    }
