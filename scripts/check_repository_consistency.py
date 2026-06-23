"""Repository consistency guard for V9 SaaS enterprise baseline."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.3.0"

REQUIRED_DIRECTORIES = [
    "src/api",
    "src/core",
    "src/services",
    "src/repositories",
    "src/middleware",
    "web_demo/core",
    "web_demo/modules",
    "docs",
    "docs/product",
    "scripts",
    "versioning",
    ".github/workflows",
]

REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "src/api/main.py",
    "src/services/v92_backend_flow_service.py",
    "src/services/v93_frontend_module_contract_service.py",
    "scripts/check_version_governance.py",
    "scripts/check_repository_consistency.py",
    "scripts/check_backend_flow_consistency.py",
    "scripts/check_frontend_module_consistency.py",
    "scripts/smoke_test_runtime.py",
    "scripts/smoke_test_api.py",
    ".github/workflows/runtime-smoke-test.yml",
    "docs/V9_SAAS_CONSISTENCY_BASE.md",
    "docs/V9_REPOSITORY_CONSISTENCY.md",
    "docs/V9_BACKEND_FLOW_CONSISTENCY.md",
    "docs/V9_FRONTEND_MODULE_CONSISTENCY.md",
    "docs/V8_WEIGHT_SYSTEM.md",
    "docs/P0_SAAS_ARCHITECTURE.md",
    "docs/POSTGRESQL_ALEMBIC.md",
    "docs/CHANGELOG.md",
    "docs/product/CHANGELOG.md",
    "versioning/VERSION.md",
    "versioning/CHANGELOG.md",
    "web_demo/index.html",
]

REMOVED_OR_LEGACY_PATHS = [
    "backend/server.py",
    "src/run_demo.py",
    "src/services/workflow_service.py",
    "src/services/eval_service.py",
    "evals/run_evals.py",
    "web_demo/app.js",
    "web_demo/app-v2.js",
    "web_demo/data-import.css",
    "scripts/material_observer.py",
    "agents/material_observer_agent.py",
    "agents/registry.py",
    "runtime/agent_registry.json",
    "runtime/module_chain.json",
    "modules/platforms",
    "modules/operation_modes",
    "modules/frontend",
]

README_REQUIRED_SNIPPETS = [
    "当前版本：V9.3.0",
    "docs/V9_REPOSITORY_CONSISTENCY.md",
    "docs/V9_BACKEND_FLOW_CONSISTENCY.md",
    "docs/V9_FRONTEND_MODULE_CONSISTENCY.md",
    "/api/modules",
    "/api/accounts",
    "/api/architecture/v9/backend-flow",
    "/api/architecture/v9/frontend-modules",
    "基础版 / Starter",
    "专业版 / Professional",
    "企业版 / Enterprise",
]

WORKFLOW_REQUIRED_SNIPPETS = [
    "scripts/check_version_governance.py",
    "scripts/check_repository_consistency.py",
    "scripts/check_backend_flow_consistency.py",
    "scripts/check_frontend_module_consistency.py",
    "scripts/smoke_test_runtime.py",
    "scripts/smoke_test_api.py",
]


def read(path_text: str) -> str:
    path = ROOT / path_text
    if not path.exists():
        raise AssertionError(f"Missing required file: {path_text}")
    return path.read_text(encoding="utf-8")


def assert_exists(path_text: str) -> None:
    if not (ROOT / path_text).exists():
        raise AssertionError(f"Missing required repository path: {path_text}")


def assert_missing(path_text: str) -> None:
    if (ROOT / path_text).exists():
        raise AssertionError(f"Legacy repository path should not exist in V9 trunk: {path_text}")


def assert_contains(text: str, snippet: str, owner: str) -> None:
    if snippet not in text:
        raise AssertionError(f"{owner} must contain `{snippet}`")


def main() -> None:
    for directory in REQUIRED_DIRECTORIES:
        assert_exists(directory)
    for file_path in REQUIRED_FILES:
        assert_exists(file_path)
    for legacy_path in REMOVED_OR_LEGACY_PATHS:
        assert_missing(legacy_path)

    readme = read("README.md")
    workflow = read(".github/workflows/runtime-smoke-test.yml")
    version = read("versioning/VERSION.md")
    index_html = read("web_demo/index.html")

    assert_contains(version, f"Current Version: v{EXPECTED_VERSION}", "versioning/VERSION.md")
    for snippet in README_REQUIRED_SNIPPETS:
        assert_contains(readme, snippet, "README.md")
    for snippet in WORKFLOW_REQUIRED_SNIPPETS:
        assert_contains(workflow, snippet, "runtime-smoke-test.yml")
    assert_contains(index_html, f"?v={EXPECTED_VERSION}", "web_demo/index.html")

    print("Repository consistency check passed for V9.3.")


if __name__ == "__main__":
    main()
