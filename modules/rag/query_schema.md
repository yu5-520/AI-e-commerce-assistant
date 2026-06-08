# RAG Query Schema

RAG query is extracted from user input before retrieval.

## Required Query Keys
- platform
- mode
- product
- user_input

## Optional Query Keys
- category
- user_goal
- price_band
- inventory_stage
- season
- feedback_level_min
- pattern_types

## Pattern Types
- title_pattern
- image_pattern
- sku_pattern
- price_pattern
- operation_case

## Default Query Rule
If user input is short, infer only safe fields from title and body. Do not invent category, effect data, or operation results.

## Example
Input: `[自然流] 防晒衣 成本19 卖39 库存200`

Query keys:
- platform: pinduoduo
- mode: natural-flow
- product: 防晒衣
- price_band: 39
- user_goal: natural flow test / inventory clearance if stated
