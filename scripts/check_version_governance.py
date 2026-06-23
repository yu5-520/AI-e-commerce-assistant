from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]

def read(path):
    p = ROOT / path
    if not p.exists():
        raise AssertionError(f"missing {path}")
    return p.read_text(encoding="utf-8")

def version(text):
    m = re.search(r"Current Version:\s*v?(\d+\.\d+\.\d+)", text)
    if not m:
        raise AssertionError("missing current version")
    return m.group(1)

def api_version(text):
    m = re.search(r'API_VERSION\s*=\s*["\'](\d+\.\d+\.\d+)["\']', text)
    if not m:
        raise AssertionError("missing API_VERSION")
    return m.group(1)

def must(text, marker, owner):
    if marker not in text:
        raise AssertionError(f"{owner} missing {marker}")

def main():
    current = version(read("versioning/VERSION.md"))
    if api_version(read("src/api/main.py")) != current:
        raise AssertionError("version mismatch")
    tech = read("versioning/CHANGELOG.md")
    product = read("docs/product/CHANGELOG.md")
    workflow = read(".github/workflows/runtime-smoke-test.yml")
    must(tech, f"## v{current}", "tech changelog")
    must(product, f"## v{current}", "product changelog")
    for marker in ["/api/modules", "/api/accounts"]:
        must(tech, marker, "tech changelog")
        must(product, marker, "product changelog")
    for marker in ["scripts/check_version_governance.py", "scripts/check_repository_consistency.py", "scripts/check_backend_flow_consistency.py", "scripts/check_frontend_module_consistency.py", "scripts/check_tier_isolation_consistency.py", "scripts/check_rag_namespace_isolation.py"]:
        must(workflow, marker, "workflow")
    for path in ["README.md", "docs/V9_RAG_NAMESPACE_ISOLATION.md"]:
        read(path)
    print(f"Version governance check passed for v{current}.")

if __name__ == "__main__":
    main()
