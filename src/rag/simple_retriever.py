"""A tiny keyword retriever that simulates the RAG node.

This is intentionally simple for the MVP: it reads markdown files from
knowledge_base/ and scores them by keyword overlap. Later it can be replaced by
Embedding + vector database retrieval.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = ROOT_DIR / "knowledge_base"


def _load_documents() -> List[Dict[str, str]]:
    docs: List[Dict[str, str]] = []
    if not KNOWLEDGE_DIR.exists():
        return docs

    for path in KNOWLEDGE_DIR.glob("*.md"):
        docs.append(
            {
                "source": path.name,
                "content": path.read_text(encoding="utf-8"),
            }
        )
    return docs


def retrieve(query: str, top_k: int = 3) -> List[Dict[str, object]]:
    """Return top matching knowledge documents for a query."""
    keywords = [token.strip().lower() for token in query.replace("/", " ").split() if token.strip()]
    docs = _load_documents()
    scored: List[Dict[str, object]] = []

    for doc in docs:
        content_lower = doc["content"].lower()
        score = sum(content_lower.count(keyword) for keyword in keywords)
        if score > 0:
            scored.append(
                {
                    "source": doc["source"],
                    "score": score,
                    "snippet": doc["content"][:240].replace("\n", " "),
                }
            )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]
