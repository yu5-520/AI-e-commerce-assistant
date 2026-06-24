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
    "/api/health": "10.1.0",
    "/api/architecture/v10/task-driven-product": "10.1.0",
    "/api/architecture/v10/readiness": "10.1.0",
    "/api/architecture/v9/readiness": "9.9.0",
}

V10_NAV_LABELS = ["总览", "报表", "经营", "任务", "日志", "账号", "系统"]
COLLAPSED_NAV_LABELS = ["商品", "竞品", "上新", "流量"]


def read(path):
    p = ROOT / path
    if not p.exists():
        raise AssertionError(f"missing {path}")
    return p.read_text(encoding="utf-8")


def must(text, marker):
    if marker not in text:
        raise AssertionError(f"missing {marker}")


def must_not(text, marker):
    if marker in text:
        raise AssertionError(f"unexpected {marker}")


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

    product = assert_json_version(client, "/api/architecture/v10/task-driven-product", "10.1.0")
    must(str(product), "all user intervention must appear as a task")
    must(str(product), "tag_change_task")
    must(str(product), "collapsedOperationRoutes")
    must(str(product), "business-products")
    if len(product.get("minimalNavigation") or []) != 7:
        raise AssertionError("V10.1 minimal navigation must contain exactly 7 entries")

    readiness = assert_json_version(client, "/api/architecture/v10/readiness", "10.1.0")
    entries = readiness.get("entries") or {}
    must(str(entries), "/api/architecture/v10/task-driven-product")
    must(str(readiness), "collapsedOperationRoutes")


def check_sidebar_navigation(index_html):
    nav_start = index_html.index('<nav class="nav"')
    nav_end = index_html.index("</nav>", nav_start)
    nav_block = index_html[nav_start:nav_end]
    for label in V10_NAV_LABELS:
        must(nav_block, f">{label}<")
    for label in COLLAPSED_NAV_LABELS:
        must_not(nav_block, f">{label}<")
    if nav_block.count('data-route=') != 7:
        raise AssertionError("V10.1 sidebar must expose exactly 7 main entries")


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
    bootstrap = read("web_demo/bootstrap.js")
    operation_page = read("web_demo/modules/operating-unit/page.js")
    system_status = read("web_demo/modules/system-status/page.js")
    v10_doc = read("docs/V10_TASK_DRIVEN_PRODUCT.md")

    must(main_py, "API_VERSION = \"10.1.0\"")
    must(main_py, "v10_product")
    must(main_py, "app.include_router(v10_product.router)")
    must(health, "API_VERSION = \"10.1.0\"")
    must(health, "v100Entry")
    must(v10_route, "\"version\": \"10.1.0\"")
    must(v10_route, "collapsedOperationRoutes")
    must(v10_service, "V100_TASK_PRODUCT_VERSION = \"10.1.0\"")
    must(v10_service, "NAVIGATION_COMPRESSION_RULES")
    must(v10_service, "COLLAPSED_OPERATION_ROUTES")
    must(changelog, "## V10.1.0")
    must(version, "10.1.0")
    must(readme, "V10.1.0")
    must(index, "?v=10.1.0")
    check_sidebar_navigation(index)
    must(bootstrap, "V10_MAIN_NAV")
    must(bootstrap, "INTERNAL_TO_V10_NAV")
    must(operation_page, "data-operation-route")
    must(operation_page, "business-products")
    must(system_status, "SYSTEM STATUS · V10.1")
    must(system_status, "collapsedOperationRoutes")
    must(v10_doc, "V10.1 navigation compression")
    check_runtime_routes()
    print("V10.1 navigation compression guard passed.")


if __name__ == "__main__":
    main()
