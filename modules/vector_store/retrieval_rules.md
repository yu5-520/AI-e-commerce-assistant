# Vector Retrieval Rules

Vector retrieval should find similar reusable operation patterns before LLM generation.

## Retrieval Flow
1. Extract query keys from user input: platform, mode, product, category, user goal, price band.
2. Filter metadata first: platform, mode, minimum feedback level.
3. Run semantic similarity search on filtered chunks.
4. Prefer L4 effective chunks, then L3 executed chunks, then L2 liked chunks.
5. Return only a small context pack for generation.

## Default Limits
- title patterns: 1-2 chunks
- image patterns: 1-2 chunks
- SKU patterns: 0-1 chunk
- price patterns: 0-1 chunk
- operation cases: 0-2 chunks

## Rule
Do not send the whole vector store to the LLM. Keep retrieval precise and small.
