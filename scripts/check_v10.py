from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]

CHECK_FILES = [
    "src/api/main.py",
    "src/api/routes/health.py",
    "src/api/routes/v10_product.py",
    "src/services/v100_task_driven_product_service.py",
    "src/services/dashboard_service.py",
    "scripts/check_v10.py",
]

RUNTIME_PATHS = {
    "/api/health": "10.3.0",
    "/api/architecture/v10/task-driven-product": "10.3.0",
    "/api/architecture/v10/readiness": "10.3.0",
    "/api/architecture/v9/readiness": "9.9.0",
}

V10_NAV_LABELS = ["总览", "报表", "经营", "任务", "日志", "账号", "系统"]
COLLAPSED_NAV_LABELS = ["商品", "竞品", "上新", "流量"]
DASHBOARD_SECTIONS = ["todayPriorityTasks", "highRiskItems", "latestReportResult", "pendingReviewItems", "completionProgress"]


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

    product = assert_json_version(client, "/api/architecture/v10/task-driven-product", "10.3.0")
    must(str(product), "all user intervention must appear as a task")
    must(str(product), "tag_change_task")
    must(str(product), "dashboardWorkbenchSections")
    must(str(product), "todayPriorityTasks")
    must(str(product), "dashboard answers what should be handled today")
    if len(product.get("minimalNavigation") or []) != 7:
        raise AssertionError("V10 minimal navigation must contain exactly 7 entries")
    if product.get("dashboardWorkbenchSections") != DASHBOARD_SECTIONS:
        raise AssertionError("V10.3 dashboard sections changed unexpectedly")

    readiness = assert_json_version(client, "/api/architecture/v10/readiness", "10.3.0")
    must(str(readiness), "dashboardWorkbenchSections")
    must(str(readiness), "dashboardRules")

    dashboard = client.get("/api/modules/dashboard", headers={"X-Mock-User-Id": "U001"})
    if dashboard.status_code != 200:
        raise AssertionError(f"/api/modules/dashboard returned {dashboard.status_code}: {dashboard.text}")
    payload = dashboard.json()
    if payload.get("version") != "10.3.0":
        raise AssertionError("dashboard service version must be 10.3.0")
    if payload.get("dashboardMode") != "today_task_workbench":
        raise AssertionError("dashboard must be today_task_workbench")
    workbench = payload.get("todayWorkbench") or {}
    for section in DASHBOARD_SECTIONS:
        if section not in workbench:
            raise AssertionError(f"dashboard workbench missing {section}")


def check_sidebar_navigation(index_html):
    nav_start = index_html.index('<nav class="nav"')
    nav_end = index_html.index("</nav>", nav_start)
    nav_block = index_html[nav_start:nav_end]
    for label in V10_NAV_LABELS:
        must(nav_block, f">{label}<")
    for label in COLLAPSED_NAV_LABELS:
        must_not(nav_block, f">{label}<")
    if nav_block.count('data-route=') != 7:
        raise AssertionError("V10 sidebar must expose exactly 7 main entries")


def main():
    compile_files()
    main_py = read("src/api/main.py")
    health = read("src/api/routes/health.py")
    v10_route = read("src/api/routes/v10_product.py")
    v10_service = read("src/services/v100_task_driven_product_service.py")
    dashboard_service = read("src/services/dashboard_service.py")
    changelog = read("docs/CHANGELOG.md")
    version = read("versioning/VERSION.md")
    readme = read("README.md")
    index = read("web_demo/index.html")
    bootstrap = read("web_demo/bootstrap.js")
    minimal_ui = read("web_demo/minimal-ui.css")
    v103_css = read("web_demo/v103-workbench.css")
    dashboard_page = read("web_demo/modules/dashboard/page.js")
    report_page = read("web_demo/modules/report/page.js")
    operation_page = read("web_demo/modules/operating-unit/page.js")
    system_status = read("web_demo/modules/system-status/page.js")
    v10_doc = read("docs/V10_TASK_DRIVEN_PRODUCT.md")

    must(main_py, "API_VERSION = \"10.3.0\"")
    must(main_py, "v10_product")
    must(main_py, "app.include_router(v10_product.router)")
    must(health, "API_VERSION = \"10.3.0\"")
    must(health, "v100Entry")
    must(v10_route, "\"version\": \"10.3.0\"")
    must(v10_route, "dashboardWorkbenchSections")
    must(v10_route, "dashboardRules")
    must(v10_service, "V100_TASK_PRODUCT_VERSION = \"10.3.0\"")
    must(v10_service, "V103_DASHBOARD_WORKBENCH_SECTIONS")
    must(v10_service, "todayPriorityTasks")
    must(dashboard_service, "DASHBOARD_VERSION = \"10.3.0\"")
    must(dashboard_service, "today_task_workbench")
    must(dashboard_service, "todayWorkbench")
    must(changelog, "## V10.3.0")
    must(version, "10.3.0")
    must(readme, "V10.3.0")
    must(index, "?v=10.3.0")
    must(index, "v103-workbench.css?v=10.3.0")
    check_sidebar_navigation(index)
    must(bootstrap, "V10_MAIN_NAV")
    must(bootstrap, "INTERNAL_TO_V10_NAV")
    must(minimal_ui, "V10.2 productized UI")
    must(v103_css, "V10.3 dashboard workbench")
    must(v103_css, "dashboard-workbench-grid")
    must(dashboard_page, "今日优先任务")
    must(dashboard_page, "高风险事项")
    must(dashboard_page, "待复核事项")
    must(dashboard_page, "今日完成进度")
    must(report_page, "route: \"data-check\"")
    must(report_page, "上传报表")
    must(operation_page, "data-operation-route")
    must(operation_page, "business-products")
    must(system_status, "SYSTEM STATUS · V10.3")
    must(system_status, "dashboardWorkbenchSections")
    must(v10_doc, "V10.3 dashboard workbench")
    check_runtime_routes()
    print("V10.3 dashboard workbench guard passed.")


if __name__ == "__main__":
    main()
