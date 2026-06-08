# RAG Module

RAG connects user input, knowledge base, vector store, and LLM generation.

Knowledge base stores reusable operation patterns.
Vector store retrieves semantically similar patterns.
RAG decides how to package retrieved knowledge and send it to the LLM.

Core responsibilities:
- define query extraction rules
- define retrieval pipeline
- define context pack structure
- define prompt assembly rules
- define fallback behavior when no useful knowledge is retrieved

Rule: RAG should send a small, relevant context pack to the LLM, not the whole knowledge base or vector store.
