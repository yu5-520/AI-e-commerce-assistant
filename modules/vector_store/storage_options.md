# Vector Store Options

Vector store implementation should be staged.

## Stage 1: File-based Simulation
Use JSON/Markdown samples to define chunk structure and metadata.
Goal: validate what should be embedded and how retrieval should work.

## Stage 2: Lightweight MVP Store
Possible options:
- SQLite with vector extension
- Chroma
- FAISS
- LanceDB

Goal: low-cost retrieval for MVP and local/server experiments.

## Stage 3: Production Store
Possible options:
- Milvus
- PostgreSQL + pgvector
- Elasticsearch/OpenSearch vector search
- Cloud vendor vector retrieval services

## Selection Principle
Do not choose vector infrastructure before knowledge chunk schema and metadata rules are stable.
