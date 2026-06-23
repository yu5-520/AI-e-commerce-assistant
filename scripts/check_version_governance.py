from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]

def read(path):
    p = ROOT / path
    if not p.exists():
        raise AssertionError(f"missing {path}")
    return p.read_text(encoding="utf-8")

def pick_version(text):
    m = re.search(r"Current Version:\s*v?(\d+\.\d+\.\d+)", text)
    if not m:
        raise AssertionError("missing current version")
    return m.group(1)

def pick_api(text):
    m = re.search(r'API_VERSION\s*=\s*["\'](\d+\.\d+\.\d+)["\']', text)
    if not m:
        raise AssertionError("missing api version")
    return m.group(1)

def must(text, marker):
    if marker not in text:
        raise AssertionError(f"missing {marker}")

def main():
    current = pick_version(read("versioning/VERSION.md"))
    if pick_api(read("src/api/main.py")) != current:
        raise AssertionError("version mismatch")
    must(read("versioning/CHANGELOG.md"), f"## v{current}")
    must(read("docs/product/CHANGELOG.md"), f"## v{current}")
    workflow = read(".github/workflows/runtime-smoke-test.yml")
    for marker in ["check_version_governance.py", "check_repository_consistency.py", "check_backend_flow_consistency.py", "check_frontend_module_consistency.py", "check_tier_isolation_consistency.py", "check_rag_namespace_isolation.py", "check_rag_write_memory_consistency.py"]:
        must(workflow, marker)
    read("README.md")
    read("docs/V9_RAG_WRITE_MEMORY_CONSISTENCY.md")
    print(f"Version governance check passed for v{current}.")

if __name__ == "__main__":
    main()
