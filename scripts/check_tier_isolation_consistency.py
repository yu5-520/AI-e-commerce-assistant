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

def must(text, marker, owner):
    if marker not in text:
        raise AssertionError(f"{owner} missing {marker}")

def main():
    version = read("versioning/VERSION.md")
    must(version, f"Current Version: v{EXPECTED_VERSION}", "VERSION")
    if assign(read("src/api/main.py"), "API_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad api version")
    if assign(read("src/api/routes/health.py"), "API_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad health version")
    if assign(read("src/api/routes/modules/agents.py"), "AGENT_REGISTRY_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad agent version")
    service = read("src/services/v94_tier_isolation_contract_service.py")
    architecture = read("src/api/routes/architecture.py")
    for marker in ["starter", "professional", "enterprise", "tier_isolation_contract_summary"]:
        must(service, marker, "tier service")
    must(architecture, "@router.get(\"/v9/tier-isolation\")", "architecture")
    must(read("web_demo/index.html"), f"?v={EXPECTED_VERSION}", "web_demo/index.html")
    must(read(".github/workflows/runtime-smoke-test.yml"), "scripts/check_tier_isolation_consistency.py", "workflow")
    print("Tier isolation consistency check passed for V9.5.")

if __name__ == "__main__":
    main()
