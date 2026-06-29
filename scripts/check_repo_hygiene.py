#!/usr/bin/env python3
"""Repository hygiene checker for current release."""

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

REQUIRED_FILES = [
    "README.md",
    "VERSION.md",
    "versioning/VERSION.md",
    "src/api/main.py",
    "src/api/routes/health.py",
    "src/api/routes/modules/operating_unit.py",
    "src/api/routes/modules/todo.py",
    "src/api/routes/modules/task_report.py",
    "src/services/store_tag_projection_service.py",
    "src/services/operating_weight_policy_service.py",
    "src/services/action_authorization_gate_service.py",
    "src/services/task_report_service.py",
    "src/services/action_impact_estimation_service.py",
    "src/services/task_lifecycle_orchestrator_service.py",
    "src/services/task_recap_scheduler_service.py",
    "src/services/rag_feedback_loop_service.py",
    "web_demo/index.html",
    "web_demo/core/api-client.js",
    "web_demo/modules/todo/page.js",
    "web_demo/modules/task-report/page.js",
    "web_demo/sop-ui.css",
]

STATIC_MUST_CONTAIN = {
    "README.md": ["V12.8.3", "任务卡动作", "primaryTaskAction", "聚合任务详情"],
    "web_demo/modules/todo/page.js": ["TASK CENTER · V12.8.3", "todo-time-rail", "primaryTaskAction", "data-submit"],
    "web_demo/modules/task-report/page.js": ["lifecycleBlock", "affectedProductsBlock", "authorizationBlock", "聚合任务"],
    "web_demo/sop-ui.css": ["todo-queue-row-v1283", "todo-time-rail", "todo-compact-tags"],
    "src/services/task_report_service.py": ["REPORT_VERSION = \"12.8.3\"", "aggregate_task", "affectedProducts", "V12.8.3"],
    "src/api/routes/modules/task_report.py": ["TASK_REPORT_ROUTE_VERSION = \"12.8.3\"", "详情报告临时兜底", "safe fallback 只能兜底"],
    "src/api/routes/modules/operating_unit.py": ["OPERATING_UNIT_VERSION = \"12.8.2\"", "project_store_tags", "权重未确认"],
    "src/services/store_tag_projection_service.py": ["STORE_TAG_PROJECTION_VERSION = \"12.8.2\"", "governanceTag", "dataTags", "businessTags"],
    "src/services/operating_weight_policy_service.py": ["OPERATING_WEIGHT_POLICY_VERSION = \"12.8.2\"", "TRUSTED_GOVERNANCE_SOURCES", "ignoredImportedHighWeightLabel"],
    "src/services/action_authorization_gate_service.py": ["ACTION_AUTHORIZATION_VERSION = \"12.8.2\"", "operatorActivityBudgetRange", "budgetActionIsNotAutomaticManagerApproval", "belowCompanyFloor"],
    "web_demo/core/api-client.js": ["lifecycleSummary", "completeRecapTodo"],
}

FORBIDDEN_CONTAINS = {
    "web_demo/modules/todo/page.js": ["function clusterTasks", "taskClusterVersion: \"12.7.1\"", "TASK CENTER · V12.7.1", "write_recap", "data-review"],
    "src/api/routes/modules/operating_unit.py": ["len(products) >= 10", "return \"高权重店铺\""],
    "src/services/action_authorization_gate_service.py": ["HIGH_RISK_ACTIONS = {\"price_adjustment\", \"ad_budget_adjustment\""],
}

CRITICAL_APPAPI_ENDPOINTS = [
    "/api/data/source-connections",
    "/api/accounts/switch",
    "/api/data/import-diagnostics",
    "/api/data/metric-facts/summary",
    "/api/data/data-gaps/summary",
    "/api/modules/operating-unit",
    "/api/modules/todo",
    "/api/modules/todo/lifecycle/summary",
    "/api/modules/todo/{task_id}/recap/complete",
    "/api/modules/task-reports/tasks/{task_id}",
    "/api/system/reset-runtime-data",
]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def semantic_version_from_root() -> str:
    match = re.search(r"```text\s*([0-9]+\.[0-9]+\.[0-9]+)\s*```", read_text("VERSION.md"), re.S)
    if not match:
        raise AssertionError("VERSION.md missing semantic version")
    return match.group(1)


def semantic_version_from_versioning() -> str:
    match = re.search(r"Current Version:\s*([0-9]+\.[0-9]+\.[0-9]+)", read_text("versioning/VERSION.md"))
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
    parser = argparse.ArgumentParser(description="Check repository release hygiene.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    for path in REQUIRED_FILES:
        if not (ROOT / path).exists():
            errors.append(f"required file missing: {path}")

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

    for path, needles in STATIC_MUST_CONTAIN.items():
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                errors.append(f"{path} missing required marker: {needle}")
    for path, forbidden_items in FORBIDDEN_CONTAINS.items():
        text = read_text(path)
        for forbidden in forbidden_items:
            if forbidden in text:
                errors.append(f"{path} contains forbidden stale marker: {forbidden}")

    routes = app_routes()
    missing_critical = [route for route in CRITICAL_APPAPI_ENDPOINTS if not route_present(route, routes)]
    if missing_critical:
        errors.append("critical endpoints missing: " + ", ".join(missing_critical))

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
