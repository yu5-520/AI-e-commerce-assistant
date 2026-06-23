from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.6.0"

def read(path):
    p = ROOT / path
    if not p.exists():
        raise AssertionError(f"missing {path}")
    return p.read_text(encoding="utf-8")

def pick(text, name):
    m = re.search(rf'{name}\s*=\s*["\']([^"\']+)["\']', text)
    if not m:
        raise AssertionError(f"missing {name}")
    return m.group(1)

def must(text, marker):
    if marker not in text:
        raise AssertionError(f"missing {marker}")

def main():
    must(read("versioning/VERSION.md"), f"Current Version: v{EXPECTED_VERSION}")
    if pick(read("src/api/main.py"), "API_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad api")
    if pick(read("src/api/routes/health.py"), "API_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad health")
    if pick(read("src/api/routes/modules/agents.py"), "AGENT_REGISTRY_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad agent")
    service = read("src/services/v95_rag_namespace_isolation_service.py")
    for marker in ["shared_desensitized_rag", "tenant_isolated_rag", "private_customer_rag"]:
        must(service, marker)
        must(read("docs/V9_RAG_NAMESPACE_ISOLATION.md"), marker)
    must(read("src/api/routes/architecture.py"), "@router.get(\"/v9/rag-isolation\")")
    must(read("web_demo/index.html"), f"?v={EXPECTED_VERSION}")
    print("RAG namespace isolation check passed for V9.6.")

if __name__ == "__main__":
    main()
