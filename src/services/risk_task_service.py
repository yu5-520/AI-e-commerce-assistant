"""Compatibility wrapper for the current V6.5 risk task service."""

from src.services.risk_task_v65_service import (  # noqa: F401
    RISK_TASK_VERSION,
    ensure_risk_task_tables,
    generate_risk_tasks_for_signals,
    risk_task_summary,
)
