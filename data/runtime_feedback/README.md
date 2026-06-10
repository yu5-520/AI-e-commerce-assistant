# Runtime Feedback

This folder stores feedback records from frontend result actions.

Each feedback record is created by:

```text
POST /api/feedback
```

Records include:
- feedback_id
- created_at
- result_id
- action
- section
- note
- raw payload

Typical actions:
- liked
- used_title
- used_sku
- used_activity
- needs_rewrite

Current status: local MVP storage only. Future VIP storage should separate users, products, permissions, and private knowledge bases.
