"""Frontend module consistency guard for V9.3.

This check keeps V9 frontend module strategy aligned across docs, runtime,
architecture routes, frontend assets, and CI. V9.3 does not add business modules;
it fixes stable module boundaries and tiered presentation depth.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.3.0"

REQUIRED_FILES = [
    "docs/V9_FRONTEND_MODULE_CONSISTENCY.md",
    "src/services/v93_frontend_module_contract_service.py",
    "src/api/routes/architecture.py",
    "src/api/routes/health.py",
    "src/api/routes/modules/agents.py",
    "web_demo/index.html",
]

STABLE_NAV_ITEMS = [
    "总览",
    "经营单元",
    "商品",
    "竞品",
    "上新",
    "流量",
    "报表中心",
    "待办",
    "日志",
    "系统状态",
    "账号",
]

STABLE_API_ENTRIES = [
    "/api/modules/dashboard",
    "/api/modules/operating-unit",
    "/api/modules/product",
    "/api/modules/competitor",
    "/api/modules/listing",
    "/api/modules/traffic",
    "/api/modules/report",
    "/api/modules/todo",
    "/api/modules/log",
    "/api/accounts",
]

REQUIRED_CONTRACT_SNIPPETS = [
    "V93_FRONTEND_MODULE_VERSION",
    "STABLE_FRONTEND_MODULES",
    "TIER_PRESENTATION_DEPTH",
    "FORBIDDEN_FRONTEND_EXPANSION",
    "frontend_module_contract_summary",
    "storeWeightSummary",
    "productWeightSummary",
    "taskIntensity",
    "executionFeedback",
    "ragMemoryCandidate",
]

FORBIDDEN_PRIMARY_MODULE_LABELS = [
    "店铺权重中心",
    "商品权重中心",
    "交叉验证中心",
    "执行回写中心",
    "RAG证据中心",
    "RAG 证据中心",
]


def read(path_text: str) -> str:
    path = ROOT / path_text
    if not path.exists():
        raise AssertionError(f"Missing required frontend-module file: {path_text}")
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
    docs = read("docs/V9_FRONTEND_MODULE_CONSISTENCY.md")
    service = read("src/services/v93_frontend_module_contract_service.py")
    architecture = read("src/api/routes/architecture.py")
    workflow = read(".github/workflows/runtime-smoke-test.yml")
    index_html = read("web_demo/index.html")
    readme = read("README.md")

    assert_contains(version, f"Current Version: v{EXPECTED_VERSION}", "versioning/VERSION.md")
    if extract_assignment(main_py, "API_VERSION", "src/api/main.py") != EXPECTED_VERSION:
        raise AssertionError("src/api/main.py API_VERSION must be 9.3.0")
    if extract_assignment(health, "API_VERSION", "src/api/routes/health.py") != EXPECTED_VERSION:
        raise AssertionError("src/api/routes/health.py API_VERSION must be 9.3.0")
    if extract_assignment(agents, "AGENT_REGISTRY_VERSION", "src/api/routes/modules/agents.py") != EXPECTED_VERSION:
        raise AssertionError("src/api/routes/modules/agents.py AGENT_REGISTRY_VERSION must be 9.3.0")

    assert_contains(architecture, "frontend_module_contract_summary", "src/api/routes/architecture.py")
    assert_contains(architecture, "@router.get(\"/v9/frontend-modules\")", "src/api/routes/architecture.py")
    assert_contains(health, "/api/architecture/v9/frontend-modules", "src/api/routes/health.py")
    assert_contains(readme, "docs/V9_FRONTEND_MODULE_CONSISTENCY.md", "README.md")

    for snippet in REQUIRED_CONTRACT_SNIPPETS:
        assert_contains(service, snippet, "src/services/v93_frontend_module_contract_service.py")
    for item in STABLE_NAV_ITEMS:
        assert_contains(index_html, item, "web_demo/index.html")
        assert_contains(docs, item, "docs/V9_FRONTEND_MODULE_CONSISTENCY.md")
    for entry in STABLE_API_ENTRIES:
        assert_contains(docs, entry, "docs/V9_FRONTEND_MODULE_CONSISTENCY.md")
        assert_contains(service, entry, "src/services/v93_frontend_module_contract_service.py")
    for label in FORBIDDEN_PRIMARY_MODULE_LABELS:
        if label in index_html:
            raise AssertionError(f"Forbidden frontend primary module label found in web_demo/index.html: {label}")

    assert_contains(index_html, f"?v={EXPECTED_VERSION}", "web_demo/index.html")
    assert_contains(workflow, "scripts/check_frontend_module_consistency.py", "runtime-smoke-test.yml")

    print("Frontend module consistency check passed for V9.3.")


if __name__ == "__main__":
    main()
