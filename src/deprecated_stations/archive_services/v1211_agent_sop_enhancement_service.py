"""Archived V12.11 Agent SOP enhancement service.

Original path: src/services/v1211_agent_sop_enhancement_service.py
Original blob sha before migration: 203487392aae769ac1918c4e1c6ae88c25b89ef2
Archived in: V12.14.3 Deprecated Physical Archive Migration
Replacement station: agent_enhance_station
Allowed usage: archive_only
Delete after: 12.16

This file is intentionally non-executable from the business mainline. The old
source remains recoverable from Git history. Do not import this module from
main.py, station registry, pipeline routes or frontend code.
"""

ARCHIVE_RECORD = {
    "legacyId": "v1211_agent_sop_enhancement_service",
    "originalPath": "src/services/v1211_agent_sop_enhancement_service.py",
    "originalBlobSha": "203487392aae769ac1918c4e1c6ae88c25b89ef2",
    "replacementStation": "agent_enhance_station",
    "allowedUsage": "archive_only",
    "deleteAfterVersion": "12.16",
    "rule": "archive_only: no mainline imports allowed",
}
