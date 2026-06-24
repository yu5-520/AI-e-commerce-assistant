from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]

CHECK_FILES = [
    "src/api/main.py",
    "src/api/routes/health.py",
    "src/api/routes/v10_product.py",
    "src/api/routes/data_import.py",
    "src/api/routes/modules/report_v5.py",
    "src/api/routes/modules/operating_unit.py",
    "src/api/routes/modules/rag_memory.py",
    "src/api/routes/modules/todo.py",
    "src/services/data_source_connection_service.py",
    "src/services/demo_rag_seed_data.py",
    "src/services/experience_memory_service.py",
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
    for path in [
        "/api/data/source-connections",
        "/api/data/source-connections/{source_id}/sync",
        "/api/modules/report",
        "/api/modules/operating-unit",
        "/api/modules/rag-memory",
        "/api/modules/rag-memory/search",
    ]:
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

    rag_summary = get_json(client, "/api/modules/rag-memory", user_id="U001")
    if rag_summary.get("version") != "10.11.0":
        raise AssertionError("RAG memory must expose V10.11 baseline")
    if int(rag_summary.get("baselineSeedCount") or 0) < 24:
        raise AssertionError("Demo/MVP RAG seed baseline must contain at least 24 cards")
    if int(rag_summary.get("crossValidationRules") or 0) < 3:
        raise AssertionError("RAG baseline must contain cross-validation rule cards")
    must(str(rag_summary), "正式上线只是升级为向量混合召回")

    rag_search = get_json(client, "/api/modules/rag-memory/search?problem_type=low_roi_high_refund&effective_only=false&limit=8", user_id="U001")
    if not rag_search.get("items"):
        raise AssertionError("RAG search must recall low_roi_high_refund seeds")
    must(str(rag_search), "crossValidationRules")
    must(str(rag_search), "vector_index")

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

    report = get_json(client, "/api/modules/report", user_id="U001")
    if report.get("version") != "5.2.1":
        raise AssertionError("report module must expose true-empty V5.2.1 contract")
    must(str(report), "syncRecords")
    must(str(report), "hasData")

    operating = get_json(client, "/api/modules/operating-unit", user_id="U001")
    if operating.get("version") != "5.2.1":
        raise AssertionError("operating unit must expose true-empty store-row V5.2.1 contract")
    rows = operating.get("storeRows") or []
    if not rows:
        raise AssertionError("operating unit must return storeRows after data sync")
    first = rows[0]
    for field in ["storeName", "storeWeightTag", "productRoleTags", "riskTags", "taskIntensity"]:
        if field not in first:
            raise AssertionError(f"store row missing {field}")

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

    task_agent = post_json(
        client,
        "/api/modules/agents/tasks/generate",
        user_id="U001",
        payload={
            "sourceModule": "product",
            "entityId": "P001",
            "sourcePayload": {"id": "P001", "title": "夏季防晒衣", "roi": "0.8", "refundRate": "9%", "platform": "淘宝", "storeId": "S001", "categoryId": "home_living_goods"},
        },
    )
    if not task_agent.get("ragReferences"):
        raise AssertionError("Task Agent must recall RAG references from seeded baseline")
    must(str(task_agent), "low_roi_high_refund")

    owner_todo = get_json(client, "/api/modules/todo", user_id="U001")
    for todo, role in [(owner_todo, "owner")]:
        if todo.get("version") != "10.9.0":
            raise AssertionError(f"todo response for {role} must expose V10.9 acceptance surface")
        must(str(todo), "acceptanceSurface")


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
    report_route = read("src/api/routes/modules/report_v5.py")
    operating_route = read("src/api/routes/modules/operating_unit.py")
    rag_route = read("src/api/routes/modules/rag_memory.py")
    rag_seed = read("src/services/demo_rag_seed_data.py")
    rag_service = read("src/services/experience_memory_service.py")
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
    dashboard_css = read("web_demo/dashboard.css")
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
    must(report_route, "syncRecords")
    must(report_route, "hasData")
    must(report_route, "_real_sync_records")
    must(operating_route, "build_store_rows")
    must(operating_route, "Account seed stores are permissions, not business data")
    must(operating_route, "storeRows")
    must_not(operating_route, "or store_rows")
    must_not(operating_route, "list(user.get(\"storeIds\")")
    must_not(operating_route, "ModuleProjection")
    must_not(operating_route, "RAG Memory")
    must(todo_route, "acceptanceSurface")
    must(action_service, "V106_TASK_ACTION_VERSION = \"10.6.0\"")
    must(rag_route, "rag_memory_search")
    must(rag_seed, "DEMO_RAG_SEED_VERSION = \"10.11.0\"")
    must(rag_seed, "cross_validation_rule")
    must(rag_seed, "acceptance_rule")
    must(rag_seed, "negative_case")
    must(rag_seed, "vectorUpgradePath")
    must(rag_service, "MEMORY_VERSION = \"10.11.0\"")
    must(rag_service, "structured_experience_cards_with_demo_baseline")
    must(rag_service, "正式上线只是升级为向量混合召回")
    must(rag_service, "crossValidationRules")
    must(changelog, "## V10.9.0")
    must(version, "10.9.0")
    must(readme, "V10.9.0")
    must(index, "?v=10.9.0")
    must(index, "dashboard.css?v=10.9.2")
    must(index, "modules/report/page.js?v=10.9.4")
    must(index, "modules/operating-unit/page.js?v=10.9.3")
    must(api_client, "syncDataSource")
    must(api_client, "resetRuntimeData")
    must(report_page, "realRecords")
    must(report_page, "emptyRecordRow")
    must(operating_page, "店铺经营状态")
    must(operating_page, "storeRows")
    must(operating_page, "operating-store-row")
    must_not(operating_page, "storeTags")
    must(dashboard_css, "operating-store-row")
    must(task_store, "window.AppTaskStore")
    must(system_status, "SYSTEM STATUS · V10.9")
    must(system_status, "acceptanceChain")
    must(v10_doc, "V10.9 acceptance guard")
    check_sidebar_navigation(index)
    check_runtime_routes()
    print("V10.11 demo RAG baseline guard passed.")


if __name__ == "__main__":
    main()
