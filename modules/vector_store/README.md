# Vector Store Module

Vector store is the retrieval infrastructure for RAG.

It does not replace the knowledge base. The knowledge base decides what should be stored; the vector store decides how to find semantically similar reusable patterns.

Core responsibilities:
- define what knowledge chunks should be embedded
- define metadata for filtering
- define chunking rules
- define retrieval and rerank rules
- define storage options for MVP and production

Rule: do not vectorize every AI output. Only vectorize feedback-filtered patterns such as L2 liked, L3 executed, and L4 effective knowledge.
