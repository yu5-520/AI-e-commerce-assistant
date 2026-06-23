# V9.8 Ops Authorization

V9.8 fixes enterprise role separation.

## Roles

```text
owner_high_level
business_manager
operator
external_ops_admin
audit_observer
```

## Flow

```text
change_request
risk_scope_check
owner_decision
ops_apply_if_authorized
audit_trace_write
business_visibility_sync
post_change_review
```

## Service

```text
src/services/v98_ops_authorization_service.py
```
