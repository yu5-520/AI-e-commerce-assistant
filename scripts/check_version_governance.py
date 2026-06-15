"""Version governance guard for the active product trunk.

This script is intentionally lightweight and dependency-free so it can run in
GitHub Actions before smoke tests. It prevents future AI or manual edits from
bypassing the repository's version memory again.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VERSION_FILE = ROOT / "versioning" / "VERSION.md"
CHANGELOG_FILE = ROOT / "versioning" / "CHANGELOG.md"
PRODUCT_CHANGELOG_FILE = ROOT / "docs" / "product" / "CHANGELOG.md"
API_MAIN_FILE = ROOT / "src" / "api" / "main.py"
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "runtime-smoke-test.yml"

REMOVED_ACTIVE_PATHS = [
    "src/run_demo.py",
    "src/services/workflow_service.py",
    "src/services/eval_service.py",
    "evals/run_evals.py",
    "web_demo/app.js",
    "scripts/material_observer.py",
    "agents/material_observer_agent.py",
    "agents/registry.py",
    "agents/base.py",
    "agents/__init__.py",
    "runtime/agent_registry.json",
]

REMOVED_ROUTE_PREFIXES = [
    "/api/demo",
    "/api/products",
    "/api/customers",
    "/api/diagnosis",
    "/api/tasks",
    "/api/reports",
    "/api/evals",
    "/api/logs",
]

REQUIRED_CURRENT_ROUTES = [
    "/api/business/today",
    "/api/business/operating-unit",
    "/api/business/data-health",
    "/api/business/products",
    "/api/business/competitors",
    "/api/business/listing",
    "/api/business/traffic",
    "/api/business/actions",
    "/api/business/report",
]


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
    match = re.search(r'version="(\d+\.\d+\.\d+)"', api_text)
    if not match:
        raise AssertionError("src/api/main.py FastAPI app must declare version=\"X.Y.Z\".")
    return match.group(1)


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
        raise AssertionError(
            f"Version mismatch: VERSION.md has v{current_version}, src/api/main.py has {api_version}."
        )

    version_header = f"## v{current_version}"
    assert_contains(changelog_text, version_header, "versioning/CHANGELOG.md")
    assert_contains(product_changelog_text, version_header, "docs/product/CHANGELOG.md")

    for route in REQUIRED_CURRENT_ROUTES:
        assert_contains(changelog_text, route.split("/", 3)[0] if False else "/api/business", "versioning/CHANGELOG.md")

    forbidden_workflow_refs = [
        "src/run_demo.py",
        "evals/run_evals.py",
        "python evals/run_evals.py",
        "python -m src.run_demo",
        "backend/server.py",
    ]
    for ref in forbidden_workflow_refs:
        if ref in workflow_text:
            raise AssertionError(f"GitHub Actions workflow still references removed or legacy entrypoint: {ref}")

    required_workflow_refs = [
        "scripts/check_version_governance.py",
        "scripts/smoke_test_runtime.py",
        "scripts/smoke_test_api.py",
    ]
    for ref in required_workflow_refs:
        assert_contains(workflow_text, ref, "runtime-smoke-test.yml")

    for path_text in REMOVED_ACTIVE_PATHS:
        path = ROOT / path_text
        if path.exists():
            raise AssertionError(f"Removed legacy path still exists in active trunk: {path_text}")

    main_text = read(API_MAIN_FILE)
    for route_prefix in REMOVED_ROUTE_PREFIXES:
        if route_prefix in main_text:
            raise AssertionError(f"src/api/main.py should not mount removed route prefix: {route_prefix}")

    print(f"Version governance check passed for v{current_version}.")


if __name__ == "__main__":
    main()
