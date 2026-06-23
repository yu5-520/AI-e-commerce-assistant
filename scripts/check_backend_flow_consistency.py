"""Backend main-flow consistency guard.

This check keeps the V9 backend-flow contract aligned across docs, runtime,
architecture routes, health, Agent registry, and CI.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.3.0"

REQUIRED_FILES = [
    "docs/V9_BACKEND_FLOW_CONSISTENCY.md",
    "src/services/v92_backend_flow_service.py",
    "src/api/routes/architecture.py",
    "src/api/routes/data_import.py",
    "src/api/routes/modules/__init__.py",
    "src/api/routes/health.py",
    "src/api/routes/modules/agents.py",
    "web_demo/index.html",
]

FLOW_TERMS = ["ImportJob", "DataVersion", "RawRows", "ModuleProjection", "AlertEvent", "WeightSignal", "DecisionTask", "AgentReport", "ApprovalFlow", "ExecutionFeedback", "ReviewLog", "RagMemoryCandidate"]
DATA_IMPORT_REQUIRED = ["@router.post(\"/preview\")", "@router.post(\"/import/confirm\")", "@router.post(\"/import/report\")", "_attach_v62_trend_and_risk_sync", "ingest_product_trends", "generate_risk_tasks_for_signals"]
MODULE_ROUTER_REQUIRED = ["dashboard.router", "operating_unit.router", "product.router", "report.router", "task_report.router", "agents.router", "rag_memory.router", "feedback_flywheel.router", "todo.router", "log.router"]
ARCHITECTURE_REQUIRED = ["backend_flow_summary", "@router.get(\"/v9/backend-flow\")", "weight_snapshot_summary", "weight_comparison_summary", "weight_rag_summary", "linked_relation_summary", "weight_score_summary", "context_weight_summary", "cross_validation_summary", "weight_task_group_summary", "weight_approval_summary", "weight_execution_summary", "weight_execution_review_summary"]


def read(path_text: str) -> str:
    path = ROOT / path_text
    if not path.exists():
        raise AssertionError(f"Missing required backend-flow file: {path_text}")
    return path.read_text(encoding="utf-8")


def assert_contains(text: str, snippet: str, owner: str) -> None:
    if snippet not in text:
        raise AssertionError(f"{owner} must contain `{snippet}`")


def extract_assignment(text: str, name: str, owner: str) -> str:
    match = re.search(rf'{name}\s*=\s*["\']([^"\']+)["\']', text)
    if not match:
        raise AssertionError(f"{owner} must declare {name}.")
    return match.group(1)


def main() -> None:
    for file_path in REQUIRED_FILES:
        if not (ROOT / file_path).exists():
            raise AssertionError(f"Missing required file: {file_path}")

    version = read("versioning/VERSION.md")
    main_py = read("src/api/main.py")
    health = read("src/api/routes/health.py")
    agents = read("src/api/routes/modules/agents.py")
    docs = read("docs/V9_BACKEND_FLOW_CONSISTENCY.md")
    service = read("src/services/v92_backend_flow_service.py")
    architecture = read("src/api/routes/architecture.py")
    data_import = read("src/api/routes/data_import.py")
    modules = read("src/api/routes/modules/__init__.py")
    workflow = read(".github/workflows/runtime-smoke-test.yml")
    index_html = read("web_demo/index.html")

    assert_contains(version, f"Current Version: v{EXPECTED_VERSION}", "versioning/VERSION.md")
    if extract_assignment(main_py, "API_VERSION", "src/api/main.py") != EXPECTED_VERSION:
        raise AssertionError("src/api/main.py API_VERSION must match the current V9 trunk")
    if extract_assignment(health, "API_VERSION", "src/api/routes/health.py") != EXPECTED_VERSION:
        raise AssertionError("src/api/routes/health.py API_VERSION must match the current V9 trunk")
    if extract_assignment(agents, "AGENT_REGISTRY_VERSION", "src/api/routes/modules/agents.py") != EXPECTED_VERSION:
        raise AssertionError("src/api/routes/modules/agents.py AGENT_REGISTRY_VERSION must match the current V9 trunk")

    for term in FLOW_TERMS:
        assert_contains(docs, term, "docs/V9_BACKEND_FLOW_CONSISTENCY.md")
        assert_contains(service, term, "src/services/v92_backend_flow_service.py")
    for snippet in DATA_IMPORT_REQUIRED:
        assert_contains(data_import, snippet, "src/api/routes/data_import.py")
    for snippet in MODULE_ROUTER_REQUIRED:
        assert_contains(modules, snippet, "src/api/routes/modules/__init__.py")
    for snippet in ARCHITECTURE_REQUIRED:
        assert_contains(architecture, snippet, "src/api/routes/architecture.py")

    assert_contains(workflow, "scripts/check_backend_flow_consistency.py", "runtime-smoke-test.yml")
    assert_contains(index_html, f"?v={EXPECTED_VERSION}", "web_demo/index.html")

    print("Backend flow consistency check passed for current V9 trunk.")


if __name__ == "__main__":
    main()
