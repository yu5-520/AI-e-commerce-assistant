# Vector Metadata Schema

Every vectorized knowledge chunk should keep metadata for filtering and ranking.

## Required Metadata
- id
- pattern_type
- platform
- mode
- category
- product
- feedback_level
- user_experience_score
- operation_effect_score
- source_type
- source_result_id
- created_at
- updated_at

## Optional Metadata
- user_goal
- price_band
- inventory_stage
- season
- sku_role
- activity_type
- ad_stage
- applicable_boundary

## Filtering Rule
Before semantic similarity search, filter by platform, mode, and minimum feedback level when possible.

## Ranking Rule
Operation effect score has higher priority than user experience score for reusable operation knowledge.
