# Knowledge Storage Plan

Future storage should separate history, candidate knowledge, executed knowledge, and effective reusable knowledge.

## Suggested Tables / Collections

### feedback_events
Raw user feedback after AI output.

### knowledge_candidates
Outputs that users liked or selected.

### executed_patterns
Suggestions users actually used in store operation.

### effective_patterns
Patterns with positive operation effect.

## Key Fields
- platform
- mode
- category
- product
- pattern_type
- pattern_content
- feedback_level
- user_experience_score
- operation_effect_score
- applicable_boundary
- source_result_id
- created_at
- updated_at

## Rule
Do not store all AI outputs as reusable knowledge. Promote only after feedback and validation.
