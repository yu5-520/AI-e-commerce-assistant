# RAG Context Pack

Context pack is the small, selected knowledge package sent to the LLM.

## Context Pack Sections

### 1. User Input Summary
- platform
- mode
- product
- user goal
- cost / price / inventory if available

### 2. Active Runtime Modules
- platform module
- operation mode module
- output template

### 3. Retrieved Knowledge
Use only a small number of high-relevance items:
- 1-2 title patterns
- 1-2 image patterns
- 0-1 SKU patterns
- 0-1 price patterns
- 0-2 operation cases

### 4. Retrieval Reason
Explain why each retrieved item is relevant.

## Rule
Context pack should help the LLM generate better output, not overwhelm it. Keep it short, structured, and directly related to the user request.
