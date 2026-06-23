from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.5.0"

REQUIRED = [
    "README.md",
    "src/api/main.py",
    "src/services/v92_backend_flow_service.py",
    "src/services/v93_frontend_module_contract_service.py",
    "src/services/v94_tier_isolation_contract_service.py",
    "src/services/v95_rag_namespace_isolation_service.py",
    "docs/V9_BACKEND_FLOW_CONSISTENCY.md",
    "docs/V9_FRONTEND_MODULE_CONSISTENCY.md",
    "docs/V9_TIER_ISOLATION_CONSISTENCY.md",
    "docs/V9_RAG_NAMESPACE_ISOLATION.md",
    "scripts/check_backend_flow_consistency.py",
    "scripts/check_frontend_module_consistency.py",
    "scripts/check_tier_isolation_consistency.py",
    "scripts/check_rag_namespace_isolation.py",
    ".github/workflows/runtime-smoke-test.yml",
    "web_demo/index.html",
]

OLD_PATHS = ["backend/server.py", "src/run_demo.py", "evals/run_evals.py", "web_demo/app.js", "web_demo/app-v2.js"]


def read(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        raise AssertionError(f"missing {path}")
    return target.read_text(encoding="utf-8")


def must_have(text: str, value: str, owner: str) -> None:
    if value not in text:
        raise AssertionError(f"{owner} missing {value}")


def main() -> None:
    for path in REQUIRED:
        if not (ROOT / path).exists():
            raise AssertionError(f"missing {path}")
    for path in OLD_PATHS:
        if (ROOT / path).exists():
            raise AssertionError(f"old path exists {path}")
    readme = read("README.md")
    workflow = read(".github/workflows/runtime-smoke-test.yml")
    version = read("versioning/VERSION.md")
    index_html = read("web_demo/index.html")
    must_have(version, f"Current Version: v{EXPECTED_VERSION}", "VERSION")
    for marker in ["当前版本：V9.5.0", "/api/modules", "/api/accounts", "/api/architecture/v9/rag-isolation", "docs/V9_RAG_NAMESPACE_ISOLATION.md"]:
        must_have(readme, marker, "README")
    for marker in ["scripts/check_version_governance.py", "scripts/check_repository_consistency.py", "scripts/check_backend_flow_consistency.py", "scripts/check_frontend_module_consistency.py", "scripts/check_tier_isolation_consistency.py", "scripts/check_rag_namespace_isolation.py"]:
        must_have(workflow, marker, "workflow")
    must_have(index_html, f"?v={EXPECTED_VERSION}", "web_demo/index.html")
    print("Repository consistency check passed for V9.5.")


if __name__ == "__main__":
    main()
