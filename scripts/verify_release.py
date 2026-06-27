#!/usr/bin/env python3
"""Release consistency verifier.

V12.3 rule:
Version alignment is a hard gate. Route inspection is a deployability signal,
with warning mode by default for low-spec ECS and transitional routers.
Set --route-mode strict or ROUTE_GUARD_MODE=strict to make missing routes block
deployment.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CRITICAL_ROUTES = {
    "/api/health",
    "/api/modules/dashboard",
    "/api/modules/operating-unit",
    "/api/modules/product",
    "/api/modules/todo",
    "/api/data/source-connections",
    "/api/data/metric-facts/summary",
    "/api/data/data-gaps/summary",
    "/api/data/import-diagnostics",
    "/api/system/runtime-diagnostics",
    "/api/system/reset-runtime-data",
    "/api/system/backfill-operating-objects",
}


def normalize_path(path: str) -> str:
    text = str(path or "").strip()
    if len(text) > 1:
        text = text.rstrip("/")
    return text


def read_root_version() -> str:
    text = (ROOT / "VERSION.md").read_text(encoding="utf-8")
    match = re.search(r"```text\s*([0-9]+\.[0-9]+\.[0-9]+)\s*```", text, re.S)
    if not match:
        raise AssertionError("VERSION.md missing fenced semantic version")
    return match.group(1)


def read_versioning_version() -> str:
    text = (ROOT / "versioning" / "VERSION.md").read_text(encoding="utf-8")
    match = re.search(r"Current Version:\s*([0-9]+\.[0-9]+\.[0-9]+)", text)
    if not match:
        raise AssertionError("versioning/VERSION.md missing `Current Version: x.y.z`")
    return match.group(1)


def read_index_asset_versions() -> set[str]:
    index_file = ROOT / "web_demo" / "index.html"
    if not index_file.exists():
        return set()
    text = index_file.read_text(encoding="utf-8")
    return set(re.findall(r"[?&]v=([0-9]+\.[0-9]+\.[0-9]+)", text))


def app_routes() -> set[str]:
    from src.api.main import app

    routes = {normalize_path(getattr(route, "path", "")) for route in app.routes}
    return {path for path in routes if path}


def route_present(routes: set[str], expected: str) -> bool:
    expected = normalize_path(expected)
    return expected in routes or f"{expected}/" in routes


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify release consistency before deployment.")
    parser.add_argument("--expected-version", default=None, help="Optional expected semantic version, e.g. 12.3.0")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    parser.add_argument("--route-mode", choices=["warn", "strict", "off"], default=os.getenv("ROUTE_GUARD_MODE", "warn"), help="How to treat missing critical routes. Default: warn")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    root_version = read_root_version()
    versioning_version = read_versioning_version()
    version = root_version
    if root_version != versioning_version:
        errors.append(f"VERSION.md is {root_version}, versioning/VERSION.md is {versioning_version}")
    if args.expected_version and version != args.expected_version:
        errors.append(f"VERSION.md is {version}, expected {args.expected_version}")

    from src.api.main import app
    from src.api.routes import health

    if str(app.version) != version:
        errors.append(f"FastAPI app.version is {app.version}, expected {version}")
    if getattr(health, "API_VERSION", None) != version:
        errors.append(f"health.API_VERSION is {getattr(health, 'API_VERSION', None)}, expected {version}")

    asset_versions = read_index_asset_versions()
    if not asset_versions:
        errors.append("web_demo/index.html has no cache-busting asset versions")
    elif asset_versions != {version}:
        errors.append(f"frontend asset versions are {sorted(asset_versions)}, expected only {version}")

    routes = app_routes()
    missing_routes = sorted(route for route in CRITICAL_ROUTES if not route_present(routes, route))
    if missing_routes and args.route_mode != "off":
        message = "critical routes missing: " + ", ".join(missing_routes)
        if args.route_mode == "strict":
            errors.append(message)
        else:
            warnings.append(message)

    result: dict[str, Any] = {
        "ok": not errors,
        "version": version,
        "rootVersion": root_version,
        "versioningVersion": versioning_version,
        "appVersion": str(app.version),
        "healthVersion": getattr(health, "API_VERSION", None),
        "assetVersions": sorted(asset_versions),
        "routeMode": args.route_mode,
        "routeCount": len(routes),
        "routesSample": sorted(routes)[:80],
        "criticalRoutes": sorted(CRITICAL_ROUTES),
        "missingRoutes": missing_routes,
        "warnings": warnings,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=== release consistency ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
