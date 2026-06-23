from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.5.0"

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

def main():
    version = read("versioning/VERSION.md")
    if f"Current Version: v{EXPECTED_VERSION}" not in version:
        raise AssertionError("bad version")
    if assign(read("src/api/main.py"), "API_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad api version")
    if assign(read("src/api/routes/health.py"), "API_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad health version")
    if assign(read("src/api/routes/modules/agents.py"), "AGENT_REGISTRY_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad agent version")
    read("docs/V9_FRONTEND_MODULE_CONSISTENCY.md")
    read("src/services/v93_frontend_module_contract_service.py")
    if f"?v={EXPECTED_VERSION}" not in read("web_demo/index.html"):
        raise AssertionError("bad frontend cache")
    print("Frontend module consistency check passed for V9.5.")

if __name__ == "__main__":
    main()
