# Feedback API Contract

Future backend endpoints for feedback and knowledge flow.

## POST /api/feedback
Input:
- result_id
- platform
- mode
- product
- section
- item
- usage_feedback
- execution_feedback
- effect_feedback
- user_note

Output:
- feedback_id
- feedback_level
- knowledge_candidate_status

## POST /api/knowledge/promote
Promote verified feedback into reusable knowledge.

## GET /api/knowledge/search
Retrieve relevant patterns by platform, mode, category, product, and feedback level.

Current GitHub stage does not implement these APIs. This file defines the future backend boundary.
