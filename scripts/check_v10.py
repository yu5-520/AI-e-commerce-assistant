from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]

CHECK_FILES = [
    "src/api/main.py",
    "src/api/routes/health.py",
    "src/api/routes/v10_product.py",
    "src/api/routes/data_import.py",
    "src/api/routes/modules/todo.py",
    "src/services/v100_task_driven_product_service.py",
    "src/services/v104_import_task_sync_service.py",
    "src/services/v105_cross_account_flow_service.py",
    "src/services/v106_task_action_simplifier.py",
    "src/services/v107_operating_profile_service.py",
    "scripts/check_v10.py",
]

RUNTIME_PATHS = {
    "/api/health": "10.7.0",
    "/api/architecture/v10/task-driven-product": "10.7.0",
    "/api/architecture/v10/readiness": "10.7.0",
    "/api/architecture/v9/readiness": "9.9.0",
}

V10_NAV_LABELS = ["总览", "报表", "经营", "任务", "日志", "账号", "系统"]
COLLAPSED_NAV_LABELS = ["商品", "竞品", "上新", "流量"]
V105_ROLES = ["owner", "manager", "operator"]


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


def get_json(client, path, user_id="U001"):
    response = client.get(path, headers={"X-Mock-User-Id": user_id})
    if response.status_code != 200:
        raise AssertionError(f"{path} returned {response.status_code}: {response.text}")
    return response.json()


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
    for path, expected in RUNTIME_PATHS.items():
        payload = get_json(client, path)
        if payload.get("version") != expected:
            raise AssertionError(f"{path} version mismatch")

    product = get_json(client, "/api/architecture/v10/task-driven-product")
    must(str(product), "operatingProfileRules")
    must(str(product), "agent_assigns_tags_without_user_confirmation")
    must(str(product), "operatingProfileTagTypes")
    if sorted((product.get("roleViewRules") or {}).keys()) != sorted(V105_ROLES):
        raise AssertionError("role view rules must contain owner/manager/operator")

    result = client.post(
        "/api/data/import/report",
        headers={"X-Mock-User-Id": "U001"},
        json={"datasetName": "products", "rows": [{"product_id": "P001", "title": "夏季防晒衣", "stock": 220, "sales": 8, "sale_price": 10, "cost_price": 9, "store_id": "S001"}], "autoCreateTasks": True},
    )
    if result.status_code != 200:
        raise AssertionError(f"import route failed: {result.status_code} {result.text}")
    payload = result.json()
    if (payload.get("v104ImportTaskSync") or {}).get("version") != "10.4.0":
        raise AssertionError("V10.7 must keep V10.4 import sync contract")
    profile = payload.get("v107OperatingProfile") or {}
    if profile.get("version") != "10.7.0":
        raise AssertionError("import must return V10.7 operating profile")
    if profile.get("userConfirmationRequired") is not False:
        raise AssertionError("Agent tags must not require user confirmation")
    must(str(profile), "verticalCategoryTags")
    must(str(profile), "storeWeightTag")
    must(str(profile), "tag_change_task")

    for user_id, role in [("U001", "owner"), ("U002", "manager"), ("U003", "operator")]:
        todo = get_json(client, "/api/modules/todo", user_id=user_id)
        if todo.get("version") != "10.6.0":
            raise AssertionError(f"todo response for {role} must remain V10.6 action surface until V10.8")
        task = next((item for item in todo.get("activeTasks", []) if item.get("taskActionVersion") == "10.6.0"), None)
        if not task:
            raise AssertionError(f"todo response for {role} missing V10.6 action task")
        if len(task.get("visibleTaskActions") or []) > 2:
            raise AssertionError("task card can expose at most two workflow actions")


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
    data_import = read("src/api/routes/data_import.py")
    todo_route = read("src/api/routes/modules/todo.py")
    v10_service = read("src/services/v100_task_driven_product_service.py")
    action_service = read("src/services/v106_task_action_simplifier.py")
    profile_service = read("src/services/v107_operating_profile_service.py")
    changelog = read("docs/CHANGELOG.md")
    version = read("versioning/VERSION.md")
    readme = read("README.md")
    index = read("web_demo/index.html")
    system_status = read("web_demo/modules/system-status/page.js")
    v10_doc = read("docs/V10_TASK_DRIVEN_PRODUCT.md")

    must(main_py, "API_VERSION = \"10.7.0\"")
    must(health, "API_VERSION = \"10.7.0\"")
    must(v10_route, "\"version\": \"10.7.0\"")
    must(v10_route, "operatingProfileRules")
    must(v10_service, "V100_TASK_PRODUCT_VERSION = \"10.7.0\"")
    must(v10_service, "V107_OPERATING_PROFILE_RULES")
    must(profile_service, "V107_OPERATING_PROFILE_VERSION = \"10.7.0\"")
    must(profile_service, "agent_assigns_tags_without_user_confirmation")
    must(profile_service, "userConfirmationRequired")
    must(profile_service, "tagChangeTaskCandidates")
    must(data_import, "attach_v107_operating_profile")
    must(todo_route, "apply_v106_task_actions")
    must(action_service, "V106_TASK_ACTION_VERSION = \"10.6.0\"")
    must(changelog, "## V10.7.0")
    must(version, "10.7.0")
    must(readme, "V10.7.0")
    must(index, "?v=10.7.0")
    check_sidebar_navigation(index)
    must(system_status, "SYSTEM STATUS · V10.7")
    must(system_status, "operatingProfileRules")
    must(v10_doc, "V10.7 Agent operating profile")
    check_runtime_routes()
    print("V10.7 operating profile guard passed.")


if __name__ == "__main__":
    main()
