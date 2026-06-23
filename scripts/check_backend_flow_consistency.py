from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.5.0"


def read(path: str) -> str:
    target = ROOT / path
    if not target.exists():
        raise AssertionError(f"missing {path}")
    return target.read_text(encoding="utf-8")


def assign(text: str, name: str) -> str:
    match = re.search(rf'{name}\s*=\s*["\']([^"\']+)["\']', text)
    if not match:
        raise AssertionError(f"missing {name}")
    return match.group(1)


def must(text: str, marker: str, owner: str) -> None:
    if marker not in text:
        raise AssertionError(f"{owner} missing {marker}")


def main() -> None:
    version = read("versioning/VERSION.md")
    main_py = read("src/api/main.py")
    health = read("src/api/routes/health.py")
    agents = read("src/api/routes/modules/agents.py")
    docs = read("docs/V9_BACKEND_FLOW_CONSISTENCY.md")
    service = read("src/services/v92_backend_flow_service.py")
    architecture = read("src/api/routes/architecture.py")
    workflow = read(".github/workflows/runtime-smoke-test.yml")
    index_html = read("web_demo/index.html")
    must(version, f"Current Version: v{EXPECTED_VERSION}", "VERSION")
    if assign(main_py, "API_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad API_VERSION")
    if assign(health, "API_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad health version")
    if assign(agents, "AGENT_REGISTRY_VERSION") != EXPECTED_VERSION:
        raise AssertionError("bad agent version")
    for marker in ["ImportJob", "DataVersion", "ModuleProjection", "WeightSignal", "RagMemoryCandidate"]:
        must(docs, marker, "backend docs")
        must(service, marker, "backend service")
    must(architecture, "@router.get(\"/v9/backend-flow\")", "architecture")
    must(workflow, "scripts/check_backend_flow_consistency.py", "workflow")
    must(index_html, f"?v={EXPECTED_VERSION}", "web_demo/index.html")
    print("Backend flow consistency check passed for V9.5.")


if __name__ == "__main__":
    main()
