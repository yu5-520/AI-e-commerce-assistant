# RAG Retrieval Pipeline

RAG retrieval connects query schema, knowledge retrieval, vector retrieval, and LLM generation.

## Pipeline
1. Extract query keys from Issue title, body, and comment.
2. Read active mode and platform from runtime/module_chain.json.
3. Use metadata filtering first: platform, mode, feedback_level_min.
4. Use vector retrieval for semantic similarity when vector store is available.
5. Use knowledge_retrieval_chain as fallback when vector store is unavailable.
6. Rerank retrieved patterns by business value.
7. Build a small context pack.
8. Send user input, active modules, and context pack to LLM.

## Retrieval Priority
- L4 effective knowledge
- L3 executed knowledge
- L2 liked knowledge
- structural module rules

## Safety Rule
Never let retrieved knowledge override explicit user input. Retrieved knowledge is reference context, not truth by itself.
