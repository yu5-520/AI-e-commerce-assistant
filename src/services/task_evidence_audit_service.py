"""Persist task evidence submissions and reviews into SQLite audit tables."""

from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

from src.repositories.sqlite_repository import connect, dumps
from src.services.task_state_machine_service import ensure_task_persistence_tables, mirror_task

EVIDENCE_AUDIT_VERSION = "5.1.8"


def _audit_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}".upper()


def _task_ids(task: Dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(task.get("tenantId") or task.get("tenant_id") or "tenant_demo"),
        str(task.get("orgId") or task.get("org_id") or "org_demo"),
        str(task.get("id") or task.get("taskId") or task.get("task_id") or ""),
    )


def persist_evidence_submission(task: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
    """Write an operator evidence submission to task_evidence and task_logs."""

    ensure_task_persistence_tables()
    tenant_id, org_id, task_id = _task_ids(task)
    created_at = record.get("submittedAt") or task.get("updatedAt")
    evidence_id = record.get("id") or _audit_id("EVIDENCE")
    payload = {"version": EVIDENCE_AUDIT_VERSION, "kind": "submission", "task": task, "record": record}
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO task_evidence (
                evidence_id, task_id, tenant_id, org_id, submitter_id,
                evidence_type, note, payload, created_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (evidence_id, task_id, tenant_id, org_id, record.get("submittedById"), "submission", record.get("summary") or record.get("result"), dumps(payload), created_at),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO task_logs (
                log_id, task_id, tenant_id, org_id, log_type, action,
                result, payload, created_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (_audit_id("LOG"), task_id, tenant_id, org_id, "evidence_submission", record.get("action"), record.get("summary") or record.get("result"), dumps(payload), created_at),
        )
        conn.commit()
    mirror_task(task, tenant_id=tenant_id, org_id=org_id)
    return {"version": EVIDENCE_AUDIT_VERSION, "taskId": task_id, "evidenceId": evidence_id, "type": "submission", "persisted": True}


def persist_evidence_review(task: Dict[str, Any], review: Dict[str, Any]) -> Dict[str, Any]:
    """Write a manager evidence review to task_evidence and task_logs."""

    ensure_task_persistence_tables()
    tenant_id, org_id, task_id = _task_ids(task)
    created_at = review.get("reviewedAt") or task.get("updatedAt")
    evidence_id = review.get("id") or _audit_id("REVIEW")
    payload = {"version": EVIDENCE_AUDIT_VERSION, "kind": "review", "task": task, "review": review}
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO task_evidence (
                evidence_id, task_id, tenant_id, org_id, submitter_id,
                evidence_type, note, payload, created_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (evidence_id, task_id, tenant_id, org_id, review.get("reviewerId"), "review", review.get("comment"), dumps(payload), created_at),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO task_logs (
                log_id, task_id, tenant_id, org_id, log_type, action,
                result, payload, created_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """,
            (_audit_id("LOG"), task_id, tenant_id, org_id, "evidence_review", review.get("decision"), review.get("comment"), dumps(payload), created_at),
        )
        conn.commit()
    mirror_task(task, tenant_id=tenant_id, org_id=org_id)
    return {"version": EVIDENCE_AUDIT_VERSION, "taskId": task_id, "evidenceId": evidence_id, "type": "review", "persisted": True}
