"""Archived V112 task chain fix service.

Original path: src/services/v112_task_chain_fix_service.py
Original blob sha before migration: 095965ae638572b653fc3f58ba8fb4e1d0bde964
Archived in: V12.14.3 Deprecated Physical Archive Migration
Replacement station: task_signal_station
Allowed usage: archive_only
Delete after: 12.16

This file is intentionally non-executable from the business mainline. The old
source remains recoverable from Git history. Do not import this module from
main.py, station registry, pipeline routes or frontend code.
"""

ARCHIVE_RECORD = {
    "legacyId": "v112_task_chain_fix_service",
    "originalPath": "src/services/v112_task_chain_fix_service.py",
    "originalBlobSha": "095965ae638572b653fc3f58ba8fb4e1d0bde964",
    "replacementStation": "task_signal_station",
    "allowedUsage": "archive_only",
    "deleteAfterVersion": "12.16",
    "rule": "archive_only: no mainline imports allowed",
}
