from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "9.4.0"


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
    docs = read("docs/V9_FRONTEND_MODULE_CONSISTENCY.md")
    service = read("src/services/v93_frontend_module_contract_service.py")
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
    for marker in ["总览", "经营单元", "商品", "报表中心", "待办", "日志", "账号"]:
        must(index_html, marker, "web_demo/index.html")
        must(docs, marker, "frontend docs")
    for marker in ["frontend_module_contract_summary", "@router.get(\"/v9/frontend-modules\")"]:
        must(architecture, marker, "architecture")
    for marker in ["V93_FRONTEND_MODULE_VERSION", "STABLE_FRONTEND_MODULES", "TIER_PRESENTATION_DEPTH"]:
        must(service, marker, "frontend service")
    must(workflow, "scripts/check_frontend_module_consistency.py", "workflow")
    must(index_html, f"?v={EXPECTED_VERSION}", "web_demo/index.html")
    print("Frontend module consistency check passed for V9.4.")


if __name__ == "__main__":
    main()
