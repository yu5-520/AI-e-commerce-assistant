from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.6.0"

def read(path):
    p = ROOT / path
    if not p.exists():
        raise AssertionError(f"missing {path}")
    return p.read_text(encoding="utf-8")

def assign(text, name):
    m = re.search(rf'{name}\s*=\s*["\']([^"\']+)["\']', text)
    if not m:
        raise AssertionError(f"missing {name}")
    return m.group(1)

def must(text, marker):
    if marker not in text:
        raise AssertionError(f"missing {marker}")

def main():
    must(read("versioning/VERSION.md"), f"Current Version: v{EXPECTED_VERSION}")
    if assign(read("src/api/main.py"), "API_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad api")
    if assign(read("src/api/routes/health.py"), "API_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad health")
    if assign(read("src/api/routes/modules/agents.py"), "AGENT_REGISTRY_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad agent")
    service = read("src/services/v96_rag_write_memory_service.py")
    for marker in ["V96_RAG_WRITE_VERSION", "MEMORY_LIFECYCLE", "WRITE_POLICIES", "APPROVAL_GATES", "rag_write_memory_summary"]:
        must(service, marker)
    arch = read("src/api/routes/architecture.py")
    must(arch, "rag_write_memory_summary")
    must(arch, "@router.get(\"/v9/rag-write-memory\")")
    read("docs/V9_RAG_WRITE_MEMORY_CONSISTENCY.md")
    must(read("web_demo/index.html"), f"?v={EXPECTED_VERSION}")
    must(read(".github/workflows/runtime-smoke-test.yml"), "check_rag_write_memory_consistency.py")
    print("RAG write memory check passed for V9.6.")

if __name__ == "__main__":
    main()
