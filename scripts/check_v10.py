from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]

CHECK_FILES = [
    "src/api/main.py",
    "src/api/routes/health.py",
    "src/api/routes/v10_product.py",
    "src/services/v100_task_driven_product_service.py",
    "scripts/check_v10.py",
]

RUNTIME_PATHS = {
    "/api/health": "10.0.0",
    "/api/architecture/v10/task-driven-product": "10.0.0",
    "/api/architecture/v10/readiness": "10.0.0",
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

    product = assert_json_version(client, "/api/architecture/v10/task-driven-product", "10.0.0")
    must(str(product), "all user intervention must appear as a task")
    must(str(product), "tag_change_task")
    must(str(product), "dashboard")
    must(str(product), "tasks")

    readiness = assert_json_version(client, "/api/architecture/v10/readiness", "10.0.0")
    entries = readiness.get("entries") or {}
    must(str(entries), "/api/architecture/v10/task-driven-product")


def main():
    compile_files()
    main_py = read("src/api/main.py")
    health = read("src/api/routes/health.py")
    v10_route = read("src/api/routes/v10_product.py")
    v10_service = read("src/services/v100_task_driven_product_service.py")
    changelog = read("docs/CHANGELOG.md")
    version = read("versioning/VERSION.md")
    readme = read("README.md")
    index = read("web_demo/index.html")
    system_status = read("web_demo/modules/system-status/page.js")
    v10_doc = read("docs/V10_TASK_DRIVEN_PRODUCT.md")

    must(main_py, "API_VERSION = \"10.0.0\"")
    must(main_py, "v10_product")
    must(main_py, "app.include_router(v10_product.router)")
    must(health, "API_VERSION = \"10.0.0\"")
    must(health, "v100Entry")
    must(v10_route, "/v10/task-driven-product")
    must(v10_route, "/v10/readiness")
    must(v10_service, "V100_TASK_PRODUCT_VERSION = \"10.0.0\"")
    must(v10_service, "all user intervention must appear as a task")
    must(v10_service, "tag_change_task")
    must(changelog, "## V10.0.0")
    must(version, "10.0.0")
    must(readme, "V10.0.0")
    must(index, "?v=10.0.0")
    must(system_status, "SYSTEM STATUS · V10")
    must(system_status, "/api/architecture/v10/task-driven-product")
    must(v10_doc, "V10 Task Driven Product")
    check_runtime_routes()
    print("V10 task-driven product guard passed.")


if __name__ == "__main__":
    main()
