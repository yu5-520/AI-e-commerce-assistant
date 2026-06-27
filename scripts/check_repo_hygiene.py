#!/usr/bin/env python3
"""Repository hygiene checker for V12.3 docs, versions, and route contracts.

Hard goals:
- keep VERSION.md, versioning/VERSION.md, FastAPI app.version, health.API_VERSION
  and web asset versions aligned;
- keep README as a current execution index instead of a historical changelog;
- keep current docs on the V12 fact/layout/gap/evidence chain;
- make frontend/ explicitly deprecated;
- warn or fail when API_CONTRACT routes do not map to the running FastAPI app.
"""

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

CURRENT_DOCS = [
    "README.md",
    "docs/API_CONTRACT.md",
    "docs/MODULE_CHAIN.md",
    "docs/PRODUCT_ARCHITECTURE.md",
    "docs/DATA_TASK_LIFECYCLE.md",
    "docs/DEPLOYMENT_RUNBOOK.md",
]

STATIC_MUST_CONTAIN = {
    "README.md": ["V12.3", "web_demo/", "frontend/", "docs/archive/README.md", "scripts/check_repo_hygiene.py"],
    "docs/MODULE_CHAIN.md": ["metric_fact_store_service", "data_gap_event_service", "import_diagnostics_service", "task_evidence_gate_service", "data_source_compat.py"],
    "docs/API_CONTRACT.md": ["/api/data/source-connections", "/api/data/import-diagnostics", "metricScope", "forbiddenCrossScope"],
    "docs/DEPLOYMENT_RUNBOOK.md": ["12.3.0", "DEMO_ACCOUNT_SWITCH=true", "check_repo_hygiene.py", "/api/data/source-connections"],
    "docs/PRODUCT_ARCHITECTURE.md": ["product_metric_facts", "traffic_source_facts", "data_gap_events", "未识别"],
    "docs/DATA_TASK_LIFECYCLE.md": ["Sheet → Block → Fact → Gap → Staging", "requiredFactTables", "forbiddenCrossScope"],
}

FORBIDDEN_CURRENT_DOC_SNIPPETS = [
    "当前 V11",
    "V11.17 Demo 目标",
    "一次完整 V11",
    "# V11.17 Demo",
    "# V11.16",
    "# V11.15",
    "V11.17 清空",
    "V11 规则",
]

CRITICAL_APPAPI_ENDPOINTS = [
    "/api/data/source-connections",
    "/api/accounts/switch",
    "/api/data/import-diagnostics",
    "/api/data/metric-facts/summary",
    "/api/data/data-gaps/summary",
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
        raise AssertionError("versioning/VERSION.md missing `Current Version: x.y.z`")
    return match.group(1)


def version_minor_marker(version: str) -> str:
    parts = version.split(".")
    return f"V{parts[0]}.{parts[1]}"


def index_asset_versions() -> set[str]:
    text = read_text("web_demo/index.html")
    return set(re.findall(r"[?&]v=([0-9]+\.[0-9]+\.[0-9]+)", text))


def normalize_route(path: str) -> str:
    text = str(path or "").strip().strip("`").strip()
    text = text.split("?", 1)[0]
    if len(text) > 1:
        text = text.rstrip("/")
    return text


def route_to_regex(route: str) -> re.Pattern[str]:
    route = normalize_route(route)
    pieces = []
    for part in route.split("/"):
        if part.startswith("{") and part.endswith("}"):
            pieces.append(r"[^/]+")
        else:
            pieces.append(re.escape(part))
    return re.compile("^" + "/".join(pieces) + "$" )


def app_routes() -> set[str]:
    from src.api.main import app

    return {normalize_route(getattr(route, "path", "")) for route in app.routes if normalize_route(getattr(route, "path", ""))}


def contract_routes() -> list[str]:
    text = read_text("docs/API_CONTRACT.md")
    routes: list[str] = []
    for match in re.finditer(r"(?:GET|POST|DELETE|PUT|PATCH)?\s*(/api/[A-Za-z0-9_./{}?=&:-]+)", text):
        route = normalize_route(match.group(1))
        if route and route not in routes:
            routes.append(route)
    return routes


def route_present(route: str, routes: set[str]) -> bool:
    route = normalize_route(route)
    if route in routes:
        return True
    pattern = route_to_regex(route)
    return any(pattern.match(item) for item in routes)


def doc_has_current_guard(path: str, text: str) -> bool:
    if path == "README.md":
        return "当前基线" in text and "V12.3" in text
    return "V12.3" in text or "当前" in text


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository docs and route hygiene.")
    parser.add_argument("--strict-api-contract", action="store_true", help="Treat API_CONTRACT route misses as errors instead of warnings.")
    parser.add_argument("--json", action="store_true", help="Print JSON result only.")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    root_version = semantic_version_from_root()
    versioning_version = semantic_version_from_versioning()
    if root_version != versioning_version:
        errors.append(f"VERSION.md is {root_version}, versioning/VERSION.md is {versioning_version}")
    version = root_version
    current_marker = version_minor_marker(version)

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

    readme = read_text("README.md")
    for doc in REQUIRED_DOCS:
        if doc not in readme:
            errors.append(f"README.md does not index required doc: {doc}")

    for path in CURRENT_DOCS:
        text = read_text(path)
        if not doc_has_current_guard(path, text):
            warnings.append(f"{path} does not clearly mark itself as current V12.3 documentation")
        for forbidden in FORBIDDEN_CURRENT_DOC_SNIPPETS:
            if forbidden in text:
                errors.append(f"{path} contains forbidden stale marker: {forbidden}")

    if "当前 UI 修改依据" not in read_text("frontend/README_DEPRECATED.md"):
        errors.append("frontend/README_DEPRECATED.md missing current-entry deprecation wording")
    if "历史归档" not in read_text("docs/archive/README.md"):
        errors.append("docs/archive/README.md missing archive warning")

    for path, needles in STATIC_MUST_CONTAIN.items():
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                errors.append(f"{path} missing required marker: {needle}")

    routes = app_routes()
    contract = contract_routes()
    missing_contract_routes = [route for route in contract if not route_present(route, routes)]
    missing_critical = [route for route in CRITICAL_APPAPI_ENDPOINTS if not route_present(route, routes)]
    if missing_critical:
        errors.append("critical frontend/API endpoints missing from FastAPI app: " + ", ".join(missing_critical))
    if missing_contract_routes:
        message = "API_CONTRACT routes not found in FastAPI app: " + ", ".join(missing_contract_routes)
        if args.strict_api_contract:
            errors.append(message)
        else:
            warnings.append(message)

    result: dict[str, Any] = {
        "ok": not errors,
        "version": version,
        "versionMarker": current_marker,
        "rootVersion": root_version,
        "versioningVersion": versioning_version,
        "appVersion": str(app.version),
        "healthVersion": getattr(health, "API_VERSION", None),
        "assetVersions": sorted(assets),
        "requiredDocs": REQUIRED_DOCS,
        "routeCount": len(routes),
        "contractRouteCount": len(contract),
        "missingContractRoutes": missing_contract_routes,
        "missingCriticalRoutes": missing_critical,
        "warnings": warnings,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=== repo hygiene ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
