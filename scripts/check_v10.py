from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]

CHECK_FILES = [
    "src/api/main.py",
    "src/api/routes/health.py",
    "src/api/routes/v10_product.py",
    "src/api/routes/data_import.py",
    "src/api/routes/modules/operating_unit.py",
    "src/api/routes/modules/todo.py",
    "src/services/data_source_connection_service.py",
    "src/services/v100_task_driven_product_service.py",
    "src/services/v104_import_task_sync_service.py",
    "src/services/v105_cross_account_flow_service.py",
    "src/services/v106_task_action_simplifier.py",
    "src/services/v107_operating_profile_service.py",
    "src/services/v108_tag_change_task_service.py",
    "src/services/v109_acceptance_guard_service.py",
    "scripts/check_v10.py",
]

RUNTIME_PATHS = {
    "/api/health": "10.9.0",
    "/api/architecture/v10/task-driven-product": "10.9.0",
    "/api/architecture/v10/readiness": "10.9.0",
    "/api/architecture/v9/readiness": "9.9.0",
}

V10_NAV_LABELS = ["总览", "数据", "经营", "任务", "日志", "账号", "系统"]
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


def post_json(client, path, user_id="U001", payload=None):
    response = client.post(path, headers={"X-Mock-User-Id": user_id}, json=payload or {})
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
    for path in ["/api/data/source-connections", "/api/data/source-connections/{source_id}/sync", "/api/modules/operating-unit"]:
        if path not in registered_paths:
            raise AssertionError(f"runtime route not mounted: {path}")

    client = TestClient(app)
    for path, expected in RUNTIME_PATHS.items():
        payload = get_json(client, path)
        if payload.get("version") != expected:
            raise AssertionError(f"{path} version mismatch")

    product = get_json(client, "/api/architecture/v10/task-driven-product")
    must(str(product), "acceptanceGuard")
    must(str(product), "acceptanceChain")
    must(str(product), "blockingFailures")
    must(str(product), "rag_memory_candidate_after_review")
    if sorted((product.get("roleViewRules") or {}).keys()) != sorted(V105_ROLES):
        raise AssertionError("role view rules must contain owner/manager/operator")

    connections = get_json(client, "/api/data/source-connections")
    if connections.get("version") != "10.10.0":
        raise AssertionError("data source connection surface must expose V10.10")
    must(str(connections), "api_sources_primary_manual_upload_backup")
    if "erp" not in (connections.get("primarySourceIds") or []) or "manual_upload" not in (connections.get("backupSourceIds") or []):
        raise AssertionError("ERP/CRM/API sources must be primary and manual upload must be backup")
    source_sync = post_json(client, "/api/data/source-connections/erp/sync", user_id="U001")
    source_contract = source_sync.get("sourceConnection") or {}
    if source_contract.get("priority") != "primary" or source_contract.get("sourceId") != "erp":
        raise AssertionError("ERP source sync must use primary source contract")
    if (source_sync.get("v104ImportTaskSync") or {}).get("source") != "erp_api_sync":
        raise AssertionError("ERP source sync must still refresh V10.4 module sync contract")

    operating = get_json(client, "/api/modules/operating-unit", user_id="U001")
    if operating.get("version") != "5.1.0":
        raise AssertionError("operating unit must expose productized V5.1 contract")
    must(str(operating), "storeTags")
    must(str(operating), "operatingJudgment")
    must(str(operating), "店铺权重")
    must_not(str(operating), "ModuleProjection")
    must_not(str(operating), "RAG Memory")

    import_payload = post_json(
        client,
        "/api/data/import/report",
        user_id="U001",
        payload={"datasetName": "products", "rows": [{"product_id": "P001", "title": "夏季防晒衣", "stock": 220, "sales": 8, "sale_price": 10, "cost_price": 9, "store_id": "S001"}], "autoCreateTasks": True},
    )
    if (import_payload.get("v104ImportTaskSync") or {}).get("version") != "10.4.0":
        raise AssertionError("V10.9 must keep V10.4 import sync contract")
    profile = import_payload.get("v107OperatingProfile") or {}
    if profile.get("version") != "10.7.0" or profile.get("userConfirmationRequired") is not False:
        raise AssertionError("V10.9 must keep Agent tags automatic and not require user confirmation")
    tag_sync = import_payload.get("v108TagChangeTaskSync") or {}
    if tag_sync.get("version") != "10.8.0" or tag_sync.get("createdTaskCount", 0) < 1:
        raise AssertionError("V10.9 requires tag-change candidates to become tasks")

    owner_todo = get_json(client, "/api/modules/todo", user_id="U001")
    manager_todo = get_json(client, "/api/modules/todo", user_id="U002")
    operator_todo = get_json(client, "/api/modules/todo", user_id="U003")
    for todo, role in [(owner_todo, "owner"), (manager_todo, "manager"), (operator_todo, "operator")]:
        if todo.get("version") != "10.9.0":
            raise AssertionError(f"todo response for {role} must expose V10.9 acceptance surface")
        must(str(todo), "acceptanceSurface")
        task = next((item for item in todo.get("activeTasks", []) if item.get("taskType") == "标签变化任务"), None)
        if not task:
            raise AssertionError(f"{role} must see tag change task through role projection")
        must(str(task), "profileSnapshot")
        must(str(task), "crossAccountFlowVersion")
        must(str(task), "primaryTaskAction")
        if len(task.get("visibleTaskActions") or []) > 2:
            raise AssertionError("task card can expose at most two workflow actions")

    task_id = next((item for item in operator_todo.get("activeTasks", []) if item.get("taskType") == "标签变化任务"), {}).get("id")
    if not task_id:
        raise AssertionError("operator task id missing")
    accepted = post_json(client, f"/api/modules/todo/{task_id}/accept", user_id="U003", payload={"note": "V10.9 接收标签变化任务"})
    if accepted.get("displayStatus") != "处理中":
        raise AssertionError("operator acceptance should move task to processing")
    submitted = post_json(client, f"/api/modules/todo/{task_id}/submit", user_id="U003", payload={"note": "已按任务处理标签变化。"})
    if submitted.get("displayStatus") != "待复核":
        raise AssertionError("operator submission should route to manager review")
    reviewed = post_json(client, f"/api/modules/todo/{task_id}/review", user_id="U002", payload={"decision": "approve", "note": "V10.9 验收通过。"})
    if reviewed.get("displayStatus") != "已完成":
        raise AssertionError("manager review should complete the task")
    if not reviewed.get("feedbackDraft"):
        raise AssertionError("reviewed task must create RAG memory candidate draft")
    events = get_json(client, "/api/modules/todo/events", user_id="U001")
    if not events.get("events"):
        raise AssertionError("task lifecycle must leave events")


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
    operating_route = read("src/api/routes/modules/operating_unit.py")
    todo_route = read("src/api/routes/modules/todo.py")
    data_source_service = read("src/services/data_source_connection_service.py")
    v10_service = read("src/services/v100_task_driven_product_service.py")
    action_service = read("src/services/v106_task_action_simplifier.py")
    profile_service = read("src/services/v107_operating_profile_service.py")
    tag_task_service = read("src/services/v108_tag_change_task_service.py")
    acceptance_service = read("src/services/v109_acceptance_guard_service.py")
    changelog = read("docs/CHANGELOG.md")
    version = read("versioning/VERSION.md")
    readme = read("README.md")
    index = read("web_demo/index.html")
    api_client = read("web_demo/core/api-client.js")
    report_page = read("web_demo/modules/report/page.js")
    operating_page = read("web_demo/modules/operating-unit/page.js")
    task_store = read("web_demo/core/task-store.js")
    system_status = read("web_demo/modules/system-status/page.js")
    v10_doc = read("docs/V10_TASK_DRIVEN_PRODUCT.md")

    must(main_py, "API_VERSION = \"10.9.0\"")
    must(health, "API_VERSION = \"10.9.0\"")
    must(v10_route, "\"version\": \"10.9.0\"")
    must(v10_route, "acceptanceGuard")
    must(v10_service, "V100_TASK_PRODUCT_VERSION = \"10.9.0\"")
    must(v10_service, "v109_acceptance_summary")
    must(profile_service, "V107_OPERATING_PROFILE_VERSION = \"10.7.0\"")
    must(tag_task_service, "V108_TAG_CHANGE_TASK_VERSION = \"10.8.0\"")
    must(acceptance_service, "V109_ACCEPTANCE_GUARD_VERSION = \"10.9.0\"")
    must(acceptance_service, "rag_memory_candidate_after_review")
    must(data_source_service, "api_sources_primary_manual_upload_backup")
    must(data_import, "source_connections")
    must(data_import, "sync_source_connection")
    must(operating_route, "build_operating_tags")
    must(operating_route, "storeTags")
    must(operating_route, "operatingJudgment")
    must_not(operating_route, "ModuleProjection")
    must_not(operating_route, "RAG Memory")
    must(todo_route, "acceptanceSurface")
    must(action_service, "V106_TASK_ACTION_VERSION = \"10.6.0\"")
    must(changelog, "## V10.9.0")
    must(version, "10.9.0")
    must(readme, "V10.9.0")
    must(index, "?v=10.9.0")
    must(index, "dashboard.css?v=10.9.1")
    must(index, "core/task-store.js?v=10.9.1")
    must(index, "core/api-client.js?v=10.9.2")
    must(index, "modules/report/page.js?v=10.9.2")
    must(index, "modules/operating-unit/page.js?v=10.9.1")
    must(api_client, "syncDataSource")
    must(report_page, "经营数据接入")
    must(report_page, "手动上传只作为备用补数")
    must(operating_page, "店铺经营标签")
    must(operating_page, "operatingJudgment")
    must_not(operating_page, "ModuleProjection")
    must_not(operating_page, "RAG Memory")
    must(task_store, "window.AppTaskStore")
    must(task_store, "window.AppTaskActions")
    must(task_store, "hydrate")
    must(task_store, "openTodoTask")
    check_sidebar_navigation(index)
    must(system_status, "SYSTEM STATUS · V10.9")
    must(system_status, "acceptanceChain")
    must(v10_doc, "V10.9 acceptance guard")
    check_runtime_routes()
    print("V10.9/V10.10 productized operating guard passed.")


if __name__ == "__main__":
    main()
