from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]

CHECK_FILES = [
    "src/api/main.py",
    "src/api/routes/health.py",
    "src/api/routes/modules/agents.py",
    "src/api/routes/v9_readiness.py",
    "scripts/check_v99.py",
]

RUNTIME_PATHS = {
    "/api/health": "9.9.0",
    "/api/architecture/v9/ops-authorization": "9.8.0",
    "/api/architecture/v9/delivery-readiness": "9.9.0",
    "/api/architecture/v9/readiness": "9.9.0",
}


def read(path):
    p = ROOT / path
    if not p.exists():
        raise AssertionError(f"missing {path}")
    return p.read_text(encoding="utf-8")


def must(text, marker):
    if marker not in text:
        raise AssertionError(f"missing {marker}")


def compile_files():
    for path in CHECK_FILES:
        py_compile.compile(str(ROOT / path), doraise=True)


def assert_json_version(client, path, expected_version):
    response = client.get(path, headers={"X-Mock-User-Id": "U001"})
    if response.status_code != 200:
        raise AssertionError(f"{path} returned {response.status_code}: {response.text}")
    payload = response.json()
    actual = payload.get("version")
    if actual != expected_version:
        raise AssertionError(f"{path} version mismatch: expected {expected_version}, got {actual}")
    return payload


def check_runtime_routes():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    from fastapi.testclient import TestClient
    from src.api.main import app

    registered_paths = {getattr(route, "path", "") for route in app.routes}
    for path in RUNTIME_PATHS:
        if path not in registered_paths:
            raise AssertionError(f"runtime route not mounted: {path}")

    client = TestClient(app)
    for path, expected_version in RUNTIME_PATHS.items():
        assert_json_version(client, path, expected_version)

    readiness = assert_json_version(client, "/api/architecture/v9/readiness", "9.9.0")
    entries = readiness.get("entries") or {}
    must(str(entries), "/api/architecture/v9/ops-authorization")
    must(str(entries), "/api/architecture/v9/delivery-readiness")


def main():
    compile_files()
    main_py = read("src/api/main.py")
    health = read("src/api/routes/health.py")
    agents = read("src/api/routes/modules/agents.py")
    readiness = read("src/api/routes/v9_readiness.py")
    changelog = read("docs/CHANGELOG.md")
    index = read("web_demo/index.html")
    system_status = read("web_demo/modules/system-status/page.js")

    must(main_py, "API_VERSION = \"9.9.0\"")
    must(main_py, "v9_readiness")
    must(main_py, "app.include_router(v9_readiness.router)")
    for marker in ["approvals", "audit", "import_jobs", "task_persistence", "report_task_sync", "trends", "worker_jobs"]:
        must(main_py, marker)
    must(health, "API_VERSION = \"9.9.0\"")
    must(health, "v99ReadinessEntry")
    must(agents, "AGENT_REGISTRY_VERSION = \"9.9.0\"")
    must(agents, "v99DeliveryReadiness")
    must(readiness, "/v9/ops-authorization")
    must(readiness, "/v9/delivery-readiness")
    must(readiness, "/v9/readiness")
    must(readiness, "\"version\": \"9.9.0\"")
    must(read("src/services/v98_ops_authorization_service.py"), "V98_OPS_AUTH_VERSION")
    must(read("src/services/v99_delivery_readiness_service.py"), "V99_DELIVERY_VERSION")
    must(read("versioning/VERSION.md"), "9.9.0")
    must(changelog, "## V9.9.0")
    must(changelog, "## V9.8.0")
    must(index, "?v=9.9.0")
    must(system_status, "SYSTEM STATUS · V9.9")
    must(system_status, "/api/architecture/v9/readiness")
    check_runtime_routes()
    print("V9.9 architecture guard passed.")


if __name__ == "__main__":
    main()
