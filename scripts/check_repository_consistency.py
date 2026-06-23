from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.6.0"
REQUIRED = [
    "README.md",
    "src/api/main.py",
    "src/services/v92_backend_flow_service.py",
    "src/services/v93_frontend_module_contract_service.py",
    "src/services/v94_tier_isolation_contract_service.py",
    "src/services/v95_rag_namespace_isolation_service.py",
    "src/services/v96_rag_write_memory_service.py",
    "docs/V9_RAG_WRITE_MEMORY_CONSISTENCY.md",
    "scripts/check_rag_write_memory_consistency.py",
    ".github/workflows/runtime-smoke-test.yml",
    "web_demo/index.html",
]
OLD_PATHS = ["backend/server.py", "src/run_demo.py", "evals/run_evals.py", "web_demo/app.js", "web_demo/app-v2.js"]

def read(path):
    p = ROOT / path
    if not p.exists():
        raise AssertionError(f"missing {path}")
    return p.read_text(encoding="utf-8")

def must(text, marker):
    if marker not in text:
        raise AssertionError(f"missing {marker}")

def main():
    for path in REQUIRED:
        read(path)
    for path in OLD_PATHS:
        if (ROOT / path).exists():
            raise AssertionError(f"old path exists {path}")
    must(read("versioning/VERSION.md"), f"Current Version: v{EXPECTED_VERSION}")
    must(read("README.md"), "当前版本：V9.6.0")
    must(read("README.md"), "/api/architecture/v9/rag-write-memory")
    must(read(".github/workflows/runtime-smoke-test.yml"), "check_rag_write_memory_consistency.py")
    must(read("web_demo/index.html"), f"?v={EXPECTED_VERSION}")
    print("Repository consistency check passed for V9.6.")

if __name__ == "__main__":
    main()
