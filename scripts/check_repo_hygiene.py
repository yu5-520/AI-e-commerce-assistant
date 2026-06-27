#!/usr/bin/env python3
"""Repository hygiene checker for docs, versions, and current route contracts.

V11.17 purpose:
- keep VERSION.md, FastAPI app.version, health.API_VERSION and web asset versions aligned;
- keep README and runbook tied to the current minor version dynamically;
- warn when API_CONTRACT routes do not map to the running FastAPI app;
- fail only on issues that can break deployment or mislead the next code change.
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
    "docs/PRODUCT_ARCHITECTURE.md",
    "docs/MODULE_CHAIN.md",
    "docs/API_CONTRACT.md",
    "docs/DATA_TASK_LIFECYCLE.md",
    "docs/DEPLOYMENT_RUNBOOK.md",
    "docs/POSTGRESQL_CUTOVER.md",
]

STATIC_MUST_CONTAIN = {
    "README.md": ["scripts/check_repo_hygiene.py", "reset-runtime-data", "AppApi.product"],
    "docs/MODULE_CHAIN.md": ["operating_object_store_service", "v116_import_closed_loop_service", "dirty_runtime_residue", "AppApi.product"],
    "docs/API_CONTRACT.md": ["/api/data/versions/{data_version}/detail", "/api/system/reset-runtime-data?confirm=true", "business_signals_v6"],
    "docs/DEPLOYMENT_RUNBOOK.md": ["check_repo_hygiene.py", "business_signals_v6", "/api/modules/product"],
}


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_version() -> str:
    text = read_text("versioning/VERSION.md")
    match = re.search(r"Current Version:\s*([0-9]+\.[0-9]+\.[0-9]+)", text)
    if not match:
        raise AssertionError("versioning/VERSION.md missing `Current Version: x.y.z`")
    return match.group(1)


def version_minor_marker(version: str) -> str:
    return f"V{version.rsplit('.', 1)[0]}"


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository docs and route hygiene.")
    parser.add_argument("--strict-api-contract", action="store_true", help="Treat API_CONTRACT route misses as errors instead of warnings.")
    parser.add_argument("--json", action="store_true", help="Print JSON result only.")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    version = read_version()
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

    readme = read_text("README.md")
    runbook = read_text("docs/DEPLOYMENT_RUNBOOK.md")
    if current_marker not in readme and version not in readme:
        errors.append(f"README.md does not mention the current version marker {current_marker}")
    if current_marker not in runbook and version not in runbook:
        errors.append(f"docs/DEPLOYMENT_RUNBOOK.md does not mention the current version marker {current_marker}")

    for doc in REQUIRED_DOCS:
        if not (ROOT / doc).exists():
            errors.append(f"required doc missing: {doc}")
        elif doc not in readme:
            errors.append(f"README.md does not index required doc: {doc}")

    for path, needles in STATIC_MUST_CONTAIN.items():
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                errors.append(f"{path} missing required marker: {needle}")

    routes = app_routes()
    missing_contract_routes = [route for route in contract_routes() if not route_present(route, routes)]
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
        "appVersion": str(app.version),
        "healthVersion": getattr(health, "API_VERSION", None),
        "assetVersions": sorted(assets),
        "requiredDocs": REQUIRED_DOCS,
        "routeCount": len(routes),
        "contractRouteCount": len(contract_routes()),
        "missingContractRoutes": missing_contract_routes,
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
