#!/usr/bin/env python3
"""Repository hygiene checker for V12.6 versions, routes, action gate, and frontend task flow."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_DOCS = [
    "docs/API_CONTRACT.md",
    "docs/MODULE_CHAIN.md",
    "docs/PRODUCT_ARCHITECTURE.md",
    "docs/DATA_TASK_LIFECYCLE.md",
    "docs/V12_REPORT_GATEWAY.md",
    "docs/DEPLOYMENT_RUNBOOK.md",
    "docs/POSTGRESQL_CUTOVER.md",
    "docs/archive/README.md",
]

STATIC_MUST_CONTAIN = {
    "README.md": ["V12.6", "经营动作权限", "系统估算", "RAG", "web_demo/", "docs/archive/README.md", "scripts/check_repo_hygiene.py"],
    "docs/MODULE_CHAIN.md": ["operating_cadence_task_service", "action_authorization_gate_service", "action_impact_estimation_service", "rag_business_memory_service", "/api/modules/todo"],
    "docs/DEPLOYMENT_RUNBOOK.md": ["12.6.0", "DEMO_ACCOUNT_SWITCH=true", "check_repo_hygiene.py", "/api/modules/todo", "actionAuthorization"],
    "src/services/risk_task_service.py": ["v12_6_baseline_first_action_gate_operating_task_generation", "ACTION_AUTHORIZATION_VERSION", "RAG_BUSINESS_MEMORY_VERSION"],
    "src/services/module_task_service.py": ["apply_v126_task_governance", "actionAuthorization", "actionImpactEstimate", "ragBusinessMemory"],
    "src/services/action_authorization_gate_service.py": ["ACTION_AUTHORIZATION_VERSION = \"12.6.0\"", "operatorProvidesFactsOnly", "manager_approval_required"],
    "src/services/action_impact_estimation_service.py": ["ACTION_IMPACT_ESTIMATION_VERSION = \"12.6.0\"", "system_estimates_operator_does_not_forecast", "conservative"],
    "src/services/rag_business_memory_service.py": ["RAG_BUSINESS_MEMORY_VERSION = \"12.6.0\"", "companyBaseline", "memoryWriteback"],
    "web_demo/modules/todo/page.js": ["TASK CENTER · V12.6", "列表只按紧急程度和时间排序", "task-report"],
    "web_demo/modules/operating-unit/page.js": ["查看商品", "查看任务", "operating-store-buttons"],
    "web_demo/core/task-actions.js": ["openTaskReport", "openTodoTask"],
}

CRITICAL_APPAPI_ENDPOINTS = [
    "/api/data/source-connections",
    "/api/accounts/switch",
    "/api/data/import-diagnostics",
    "/api/data/metric-facts/summary",
    "/api/data/data-gaps/summary",
    "/api/modules/todo",
    "/api/system/reset-runtime-data",
]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def semantic_version_from_root() -> str:
    text = read_text("VERSION.md")
    match = re.search(r"```text\s*([0-9]+\.[0-9]+\.[0-9]+)\s*```", text, re.S)
    if not match:
        raise AssertionError("VERSION.md missing fenced semantic version")
    return match.group(1)


def semantic_version_from_versioning() -> str:
    text = read_text("versioning/VERSION.md")
    match = re.search(r"Current Version:\s*([0-9]+\.[0-9]+\.[0-9]+)", text)
    if not match:
        raise AssertionError("versioning/VERSION.md missing Current Version")
    return match.group(1)


def index_asset_versions() -> set[str]:
    return set(re.findall(r"[?&]v=([0-9]+\.[0-9]+\.[0-9]+)", read_text("web_demo/index.html")))


def normalize_route(path: str) -> str:
    text = str(path or "").strip().strip("`").split("?", 1)[0]
    return text.rstrip("/") if len(text) > 1 else text


def route_to_regex(route: str) -> re.Pattern[str]:
    pieces = [r"[^/]+" if part.startswith("{") and part.endswith("}") else re.escape(part) for part in normalize_route(route).split("/")]
    return re.compile("^" + "/".join(pieces) + "$" )


def app_routes() -> set[str]:
    from src.api.main import app
    return {normalize_route(getattr(route, "path", "")) for route in app.routes if normalize_route(getattr(route, "path", ""))}


def route_present(route: str, routes: set[str]) -> bool:
    route = normalize_route(route)
    if route in routes:
        return True
    pattern = route_to_regex(route)
    return any(pattern.match(item) for item in routes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository docs and route hygiene.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    root_version = semantic_version_from_root()
    versioning_version = semantic_version_from_versioning()
    if root_version != versioning_version:
        errors.append(f"VERSION.md is {root_version}, versioning/VERSION.md is {versioning_version}")
    version = root_version

    from src.api.main import app
    from src.api.routes import health

    if str(app.version) != version:
        errors.append(f"FastAPI app.version is {app.version}, expected {version}")
    if getattr(health, "API_VERSION", None) != version:
        errors.append(f"health.API_VERSION is {getattr(health, 'API_VERSION', None)}, expected {version}")
    assets = index_asset_versions()
    if assets != {version}:
        errors.append(f"web_demo/index.html asset versions are {sorted(assets)}, expected only {version}")

    for doc in REQUIRED_DOCS:
        if not (ROOT / doc).exists():
            errors.append(f"required doc missing: {doc}")
        elif doc not in read_text("README.md"):
            errors.append(f"README.md does not index required doc: {doc}")

    for path, needles in STATIC_MUST_CONTAIN.items():
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                errors.append(f"{path} missing required marker: {needle}")

    if "当前 UI 修改依据" not in read_text("frontend/README_DEPRECATED.md"):
        errors.append("frontend/README_DEPRECATED.md missing current-entry deprecation wording")
    if "历史归档" not in read_text("docs/archive/README.md"):
        errors.append("docs/archive/README.md missing archive warning")

    routes = app_routes()
    missing_critical = [route for route in CRITICAL_APPAPI_ENDPOINTS if not route_present(route, routes)]
    if missing_critical:
        errors.append("critical frontend/API endpoints missing from FastAPI app: " + ", ".join(missing_critical))

    result: dict[str, Any] = {
        "ok": not errors,
        "version": version,
        "rootVersion": root_version,
        "versioningVersion": versioning_version,
        "appVersion": str(app.version),
        "healthVersion": getattr(health, "API_VERSION", None),
        "assetVersions": sorted(assets),
        "routeCount": len(routes),
        "missingCriticalRoutes": missing_critical,
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2)) if args.json else print("=== repo hygiene ===\n" + json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
