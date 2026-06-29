"""Archived V12.12 RAG/LLM Agent service.

Original path: src/services/v1212_rag_llm_agent_service.py
Original blob sha before migration: d7fa624b0c91d062811f193a10a1f05ae2dee844
Archived in: V12.14.3 Deprecated Physical Archive Migration
Replacement station: agent_enhance_station
Allowed usage: archive_only
Delete after: 12.16

This file is intentionally non-executable from the business mainline. The old
source remains recoverable from Git history. Do not import this module from
main.py, station registry, pipeline routes or frontend code.
"""

ARCHIVE_RECORD = {
    "legacyId": "v1212_rag_llm_agent_service",
    "originalPath": "src/services/v1212_rag_llm_agent_service.py",
    "originalBlobSha": "d7fa624b0c91d062811f193a10a1f05ae2dee844",
    "replacementStation": "agent_enhance_station",
    "allowedUsage": "archive_only",
    "deleteAfterVersion": "12.16",
    "rule": "archive_only: no mainline imports allowed",
}
