"""RAG namespace isolation consistency guard for V9.5."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.5.0"

REQUIRED_FILES = [
    "docs/V9_RAG_NAMESPACE_ISOLATION.md",
    "src/services/v95_rag_namespace_isolation_service.py",
    "src/api/routes/architecture.py",
    "src/api/routes/health.py",
    "src/api/routes/modules/agents.py",
    "web_demo/index.html",
]

NAMESPACE_TERMS = ["shared_desensitized_rag", "tenant_isolated_rag", "private_customer_rag"]
GATE_TERMS = ["namespaceResolver", "ingestionGate", "retrievalGate", "writeGate", "templateMaintenanceGate", "deletionGate"]
REQUIRED_SNIPPETS = ["V95_RAG_NAMESPACE_VERSION", "RAG_NAMESPACES", "RAG_ACCESS_GATES", "FORBIDDEN_RAG_ACTIONS", "rag_namespace_isolation_summary"]


def read(path_text: str) -> str:
    path = ROOT / path_text
    if not path.exists():
        raise AssertionError(f"Missing required RAG isolation file: {path_text}")
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
    docs = read("docs/V9_RAG_NAMESPACE_ISOLATION.md")
    service = read("src/services/v95_rag_namespace_isolation_service.py")
    architecture = read("src/api/routes/architecture.py")
    workflow = read(".github/workflows/runtime-smoke-test.yml")
    index_html = read("web_demo/index.html")

    assert_contains(version, f"Current Version: v{EXPECTED_VERSION}", "versioning/VERSION.md")
    if extract_assignment(main_py, "API_VERSION", "src/api/main.py") != EXPECTED_VERSION:
        raise AssertionError("src/api/main.py API_VERSION must be 9.5.0")
    if extract_assignment(health, "API_VERSION", "src/api/routes/health.py") != EXPECTED_VERSION:
        raise AssertionError("src/api/routes/health.py API_VERSION must be 9.5.0")
    if extract_assignment(agents, "AGENT_REGISTRY_VERSION", "src/api/routes/modules/agents.py") != EXPECTED_VERSION:
        raise AssertionError("src/api/routes/modules/agents.py AGENT_REGISTRY_VERSION must be 9.5.0")

    assert_contains(architecture, "rag_namespace_isolation_summary", "src/api/routes/architecture.py")
    assert_contains(architecture, "@router.get(\"/v9/rag-isolation\")", "src/api/routes/architecture.py")
    assert_contains(health, "/api/architecture/v9/rag-isolation", "src/api/routes/health.py")

    for snippet in REQUIRED_SNIPPETS:
        assert_contains(service, snippet, "src/services/v95_rag_namespace_isolation_service.py")
    for term in NAMESPACE_TERMS:
        assert_contains(service, term, "src/services/v95_rag_namespace_isolation_service.py")
        assert_contains(docs, term, "docs/V9_RAG_NAMESPACE_ISOLATION.md")
    for term in GATE_TERMS:
        assert_contains(service, term, "src/services/v95_rag_namespace_isolation_service.py")

    assert_contains(index_html, f"?v={EXPECTED_VERSION}", "web_demo/index.html")
    assert_contains(workflow, "scripts/check_rag_namespace_isolation.py", "runtime-smoke-test.yml")
    print("RAG namespace isolation check passed for V9.5.")


if __name__ == "__main__":
    main()
