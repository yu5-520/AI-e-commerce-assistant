"""Version governance guard for the active product trunk."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VERSION_FILE = ROOT / "versioning" / "VERSION.md"
CHANGELOG_FILE = ROOT / "versioning" / "CHANGELOG.md"
PRODUCT_CHANGELOG_FILE = ROOT / "docs" / "product" / "CHANGELOG.md"
API_MAIN_FILE = ROOT / "src" / "api" / "main.py"
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "runtime-smoke-test.yml"

ACTIVE_DOCS = [
    "README.md",
    "docs/V9_SAAS_CONSISTENCY_BASE.md",
    "docs/V9_REPOSITORY_CONSISTENCY.md",
    "docs/V9_BACKEND_FLOW_CONSISTENCY.md",
    "docs/V9_FRONTEND_MODULE_CONSISTENCY.md",
    "docs/server-deploy.md",
    "docs/product/README.md",
    "docs/product/mvp-scope.md",
    "docs/product/module-boundary.md",
]

REMOVED_ACTIVE_PATHS = [
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
    "agents/base.py",
    "agents/__init__.py",
    "runtime/agent_registry.json",
    "runtime/module_chain.json",
    "modules/platforms",
    "modules/operation_modes",
    "modules/frontend",
    "src/reports/generate_demo_report.py",
    "docs/product/product-map.md",
    "docs/product/user-flow.md",
    "docs/product/domain-model.md",
]

REMOVED_ROUTE_PREFIXES = ["/api/demo", "/api/products", "/api/customers", "/api/diagnosis", "/api/tasks", "/api/reports", "/api/evals", "/api/logs"]
FORBIDDEN_DOC_SNIPPETS = ["python -m src.run_demo", "/api/demo/run", "暴露 Evals 结果", "frontend/app.js", "frontend/material-sampler.js", "scripts/material_observer.py::", "runtime/agent_registry.json", "runtime/module_chain.json", "generate_demo_report.py", "demo_report.md", "modules/operation_modes", "modules/platforms", "data-import.css", "web_demo/app-v2.js", "当前 v1.0.2", "GET  /api/business/today", "GET  /api/business/products"]


def read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"Missing required governance file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def extract_current_version(version_text: str) -> str:
    match = re.search(r"Current Version:\s*v?(\d+\.\d+\.\d+)", version_text)
    if not match:
        raise AssertionError("versioning/VERSION.md must contain `Current Version: vX.Y.Z`.")
    return match.group(1)


def extract_api_version(api_text: str) -> str:
    constant_match = re.search(r'API_VERSION\s*=\s*["\'](\d+\.\d+\.\d+)["\']', api_text)
    if constant_match:
        return constant_match.group(1)
    literal_match = re.search(r'version=["\'](\d+\.\d+\.\d+)["\']', api_text)
    if literal_match:
        return literal_match.group(1)
    raise AssertionError("src/api/main.py must declare API_VERSION = \"X.Y.Z\" or FastAPI version=\"X.Y.Z\".")


def assert_contains(text: str, needle: str, owner: str) -> None:
    if needle not in text:
        raise AssertionError(f"{owner} must mention `{needle}`.")


def main() -> None:
    version_text = read(VERSION_FILE)
    changelog_text = read(CHANGELOG_FILE)
    product_changelog_text = read(PRODUCT_CHANGELOG_FILE)
    api_text = read(API_MAIN_FILE)
    workflow_text = read(WORKFLOW_FILE)

    current_version = extract_current_version(version_text)
    api_version = extract_api_version(api_text)
    if current_version != api_version:
        raise AssertionError(f"Version mismatch: VERSION.md has v{current_version}, src/api/main.py has {api_version}.")

    version_header = f"## v{current_version}"
    assert_contains(changelog_text, version_header, "versioning/CHANGELOG.md")
    assert_contains(product_changelog_text, version_header, "docs/product/CHANGELOG.md")
    assert_contains(changelog_text, "/api/modules", "versioning/CHANGELOG.md")
    assert_contains(product_changelog_text, "/api/modules", "docs/product/CHANGELOG.md")
    assert_contains(changelog_text, "/api/accounts", "versioning/CHANGELOG.md")
    assert_contains(product_changelog_text, "/api/accounts", "docs/product/CHANGELOG.md")

    forbidden_workflow_refs = ["src/run_demo.py", "evals/run_evals.py", "python evals/run_evals.py", "python -m src.run_demo", "backend/server.py"]
    for ref in forbidden_workflow_refs:
        if ref in workflow_text:
            raise AssertionError(f"GitHub Actions workflow still references removed or legacy entrypoint: {ref}")

    required_workflow_refs = ["scripts/check_version_governance.py", "scripts/check_repository_consistency.py", "scripts/check_backend_flow_consistency.py", "scripts/check_frontend_module_consistency.py", "scripts/smoke_test_runtime.py", "scripts/smoke_test_api.py"]
    for ref in required_workflow_refs:
        assert_contains(workflow_text, ref, "runtime-smoke-test.yml")

    for path_text in REMOVED_ACTIVE_PATHS:
        path = ROOT / path_text
        if path.exists():
            raise AssertionError(f"Removed legacy path still exists in active trunk: {path_text}")
    for route_prefix in REMOVED_ROUTE_PREFIXES:
        if route_prefix in api_text:
            raise AssertionError(f"src/api/main.py should not mount removed route prefix: {route_prefix}")
    for doc_path_text in ACTIVE_DOCS:
        doc_text = read(ROOT / doc_path_text)
        for snippet in FORBIDDEN_DOC_SNIPPETS:
            if snippet in doc_text:
                raise AssertionError(f"Active doc {doc_path_text} still contains stale snippet: {snippet}")

    print(f"Version governance check passed for v{current_version}.")


if __name__ == "__main__":
    main()
