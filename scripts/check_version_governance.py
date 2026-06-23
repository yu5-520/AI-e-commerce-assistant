from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "versioning" / "VERSION.md"
TECH_CHANGELOG_FILE = ROOT / "versioning" / "CHANGELOG.md"
PRODUCT_CHANGELOG_FILE = ROOT / "docs" / "product" / "CHANGELOG.md"
API_MAIN_FILE = ROOT / "src" / "api" / "main.py"
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "runtime-smoke-test.yml"

ACTIVE_DOCS = ["README.md", "docs/V9_SAAS_CONSISTENCY_BASE.md", "docs/V9_REPOSITORY_CONSISTENCY.md", "docs/V9_BACKEND_FLOW_CONSISTENCY.md", "docs/V9_FRONTEND_MODULE_CONSISTENCY.md", "docs/V9_TIER_ISOLATION_CONSISTENCY.md"]
REMOVED_PATHS = ["src/run_demo.py", "evals/run_evals.py", "web_demo/app.js", "web_demo/app-v2.js", "backend/server.py"]


def read(path: Path) -> str:
    if not path.exists():
        raise AssertionError(f"missing {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def version_from(text: str) -> str:
    match = re.search(r"Current Version:\s*v?(\d+\.\d+\.\d+)", text)
    if not match:
        raise AssertionError("VERSION missing current version")
    return match.group(1)


def api_version(text: str) -> str:
    match = re.search(r'API_VERSION\s*=\s*["\'](\d+\.\d+\.\d+)["\']', text)
    if not match:
        raise AssertionError("main.py missing API_VERSION")
    return match.group(1)


def must(text: str, marker: str, owner: str) -> None:
    if marker not in text:
        raise AssertionError(f"{owner} missing {marker}")


def main() -> None:
    current = version_from(read(VERSION_FILE))
    if api_version(read(API_MAIN_FILE)) != current:
        raise AssertionError("VERSION and API_VERSION mismatch")
    tech_log = read(TECH_CHANGELOG_FILE)
    product_log = read(PRODUCT_CHANGELOG_FILE)
    workflow = read(WORKFLOW_FILE)
    must(tech_log, f"## v{current}", "versioning/CHANGELOG.md")
    must(product_log, f"## v{current}", "docs/product/CHANGELOG.md")
    for marker in ["/api/modules", "/api/accounts"]:
        must(tech_log, marker, "versioning/CHANGELOG.md")
        must(product_log, marker, "docs/product/CHANGELOG.md")
    for marker in ["scripts/check_version_governance.py", "scripts/check_repository_consistency.py", "scripts/check_backend_flow_consistency.py", "scripts/check_frontend_module_consistency.py", "scripts/check_tier_isolation_consistency.py", "scripts/smoke_test_runtime.py", "scripts/smoke_test_api.py"]:
        must(workflow, marker, "runtime-smoke-test.yml")
    for path in REMOVED_PATHS:
        if (ROOT / path).exists():
            raise AssertionError(f"old path exists {path}")
    for doc in ACTIVE_DOCS:
        read(ROOT / doc)
    print(f"Version governance check passed for v{current}.")


if __name__ == "__main__":
    main()
