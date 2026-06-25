#!/usr/bin/env python3
"""Release consistency verifier.

V11.11 deployment rule:
A release is deployable only when VERSION.md, FastAPI app.version,
/api/health version constant, frontend asset cache version, and critical API
routes are aligned. This script intentionally fails fast before systemd is
restarted.
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

CRITICAL_ROUTES = {
    "/api/health",
    "/api/modules/dashboard",
    "/api/modules/operating-unit",
    "/api/modules/product",
    "/api/modules/todo",
    "/api/system/runtime-diagnostics",
    "/api/system/backfill-operating-objects",
}


def read_version() -> str:
    version_file = ROOT / "versioning" / "VERSION.md"
    text = version_file.read_text(encoding="utf-8")
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

    return {getattr(route, "path", "") for route in app.routes}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify release consistency before deployment.")
    parser.add_argument("--expected-version", default=None, help="Optional expected semantic version, e.g. 11.11.0")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    args = parser.parse_args()

    errors: list[str] = []
    version = read_version()
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
    missing_routes = sorted(CRITICAL_ROUTES - routes)
    if missing_routes:
        errors.append("critical routes missing: " + ", ".join(missing_routes))

    result: dict[str, Any] = {
        "ok": not errors,
        "version": version,
        "appVersion": str(app.version),
        "healthVersion": getattr(health, "API_VERSION", None),
        "assetVersions": sorted(asset_versions),
        "criticalRoutes": sorted(CRITICAL_ROUTES),
        "missingRoutes": missing_routes,
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
