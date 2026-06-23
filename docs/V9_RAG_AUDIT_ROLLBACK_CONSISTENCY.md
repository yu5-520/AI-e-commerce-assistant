# V9.7 RAG Audit Rollback

V9.7 fixes the audit rollback contract for RAG memory.

## Lifecycle

```text
rollback_request
impact_scope_check
approval_trace_check
rollback_decision
tombstone_write
memory_restore_or_disable
audit_review
accountability_report
```

## Roles

```text
requester
reviewer
approver
operator
auditor
```

## Gates

```text
requestGate
approvalGate
executionGate
auditGate
accountabilityGate
```

## Entry

```text
/api/architecture/v9/rag-audit-rollback
```

## Files

```text
src/services/v97_rag_audit_rollback_service.py
src/api/routes/architecture.py
scripts/check_rag_audit_rollback_consistency.py
```
