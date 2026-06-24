from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]

PY_CHECK_FILES = [
    "src/api/main.py",
    "src/api/routes/health.py",
    "src/api/routes/v10_product.py",
    "src/api/routes/data_import.py",
    "src/api/routes/trends.py",
    "src/api/routes/modules/report_v5.py",
    "src/api/routes/modules/operating_unit.py",
    "src/api/routes/modules/rag_memory.py",
    "src/api/routes/modules/todo.py",
    "src/services/data_source_connection_service.py",
    "src/services/demo_rag_seed_data.py",
    "src/services/experience_memory_service.py",
    "src/services/task_agent_service.py",
    "src/services/v1012_metric_trend_evidence_service.py",
    "src/services/v1013_task_sop_engine_service.py",
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
OLD_CHILD_SCRIPTS = ["modules/product/page.js", "modules/competitor/page.js", "modules/listing/page.js", "modules/traffic/page.js"]


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
    for path in PY_CHECK_FILES:
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
    required_paths = [*RUNTIME_PATHS, "/api/data/source-connections", "/api/data/source-connections/{source_id}/sync", "/api/modules/report", "/api/modules/operating-unit", "/api/modules/rag-memory", "/api/modules/rag-memory/search", "/api/trends/metric-evidence", "/api/trends/task-sop"]
    for path in required_paths:
        if path not in registered_paths:
            raise AssertionError(f"runtime route not mounted: {path}")
    client = TestClient(app)
    for path, expected in RUNTIME_PATHS.items():
        payload = get_json(client, path)
        if payload.get("version") != expected:
            raise AssertionError(f"{path} version mismatch")
    rag_summary = get_json(client, "/api/modules/rag-memory", user_id="U001")
    if rag_summary.get("version") != "10.11.0" or int(rag_summary.get("baselineSeedCount") or 0) < 24:
        raise AssertionError("RAG memory must expose V10.11 baseline")
    must(str(rag_summary), "正式上线只是升级为向量混合召回")
    metric_payload = {"sourcePayload": {"id": "P001", "title": "夏季防晒衣", "platform": "淘宝", "categoryId": "home_living_goods", "roi": 0.92, "ctr": 0.037, "conversion_rate": 0.012, "refund_rate": 0.079, "clicks": 360, "impressions": 9730, "orders": 12, "stock": 80, "sales_7d": 35, "previousMetrics": {"roi": 1.42, "ctr": 0.039, "conversion_rate": 0.021, "refund_rate": 0.038}}}
    metric_evidence = post_json(client, "/api/trends/metric-evidence", user_id="U001", payload=metric_payload)
    if metric_evidence.get("version") != "10.12.0":
        raise AssertionError("metric evidence must expose V10.12")
    must(str(metric_evidence), "metric_baseline_rag")
    must(str(metric_evidence), "trendEvidence")
    must(str(metric_evidence), "单点只记录")
    sop = post_json(client, "/api/trends/task-sop", user_id="U001", payload={"problemType": "low_roi_high_refund", "metricEvidence": metric_evidence})
    if sop.get("version") != "10.13.0":
        raise AssertionError("Task SOP must expose V10.13")
    must(str(sop), "低 ROI / 高退款承接与售后排查 SOP")
    must(str(sop), "退款理由 Top5")
    must(str(sop), "客服团队核实")
    connections = get_json(client, "/api/data/source-connections")
    if connections.get("version") != "10.10.0":
        raise AssertionError("data source connection surface must expose V10.10")
    post_json(client, "/api/data/source-connections/erp/sync", user_id="U001")
    report = get_json(client, "/api/modules/report", user_id="U001")
    if report.get("version") != "5.2.1":
        raise AssertionError("report module must expose true-empty V5.2.1 contract")
    operating = get_json(client, "/api/modules/operating-unit", user_id="U001")
    if operating.get("version") != "5.2.1" or not (operating.get("storeRows") or []):
        raise AssertionError("operating unit must expose storeRows after data sync")
    task_agent = post_json(client, "/api/modules/agents/tasks/generate", user_id="U001", payload={"sourceModule": "product", "entityId": "P001", **metric_payload})
    if task_agent.get("version") != "10.13.0":
        raise AssertionError("Task Agent must expose V10.13")
    for marker in ["v1012MetricTrendEvidence", "v1013TaskSop", "taskExecutionSop", "completionGate", "退款理由 Top5"]:
        must(str(task_agent), marker)
    owner_todo = get_json(client, "/api/modules/todo", user_id="U001")
    if owner_todo.get("version") != "10.9.0":
        raise AssertionError("todo response must expose V10.9 acceptance surface")
    must(str(owner_todo), "acceptanceSurface")


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
    trends_route = read("src/api/routes/trends.py")
    report_route = read("src/api/routes/modules/report_v5.py")
    operating_route = read("src/api/routes/modules/operating_unit.py")
    rag_seed = read("src/services/demo_rag_seed_data.py")
    rag_service = read("src/services/experience_memory_service.py")
    metric_service = read("src/services/v1012_metric_trend_evidence_service.py")
    sop_service = read("src/services/v1013_task_sop_engine_service.py")
    task_agent = read("src/services/task_agent_service.py")
    todo_route = read("src/api/routes/modules/todo.py")
    data_source_service = read("src/services/data_source_connection_service.py")
    acceptance_service = read("src/services/v109_acceptance_guard_service.py")
    index = read("web_demo/index.html")
    api_client = read("web_demo/core/api-client.js")
    operating_page = read("web_demo/modules/operating-unit/page.js")
    todo_page = read("web_demo/modules/todo/page.js")
    task_report_page = read("web_demo/modules/task-report/page.js")
    sop_css = read("web_demo/sop-ui.css")
    task_store = read("web_demo/core/task-store.js")
    system_status = read("web_demo/modules/system-status/page.js")
    must(main_py, "API_VERSION = \"10.9.0\"")
    must(health, "API_VERSION = \"10.9.0\"")
    must(v10_route, "\"version\": \"10.9.0\"")
    must(v10_route, "acceptanceGuard")
    must(acceptance_service, "V109_ACCEPTANCE_GUARD_VERSION = \"10.9.0\"")
    must(data_source_service, "api_sources_primary_manual_upload_backup")
    must(data_import, "source_connections")
    must(data_import, "sync_source_connection")
    must(report_route, "syncRecords")
    must(report_route, "hasData")
    must(operating_route, "Account seed stores are permissions, not business data")
    must(operating_route, "storeRows")
    must_not(operating_route, "or store_rows")
    must_not(operating_route, "list(user.get(\"storeIds\")")
    must(todo_route, "acceptanceSurface")
    must(rag_seed, "DEMO_RAG_SEED_VERSION = \"10.11.0\"")
    must(rag_seed, "cross_validation_rule")
    must(rag_service, "MEMORY_VERSION = \"10.11.0\"")
    must(metric_service, "V1012_METRIC_TREND_EVIDENCE_VERSION = \"10.12.0\"")
    must(metric_service, "METRIC_BASELINE_RAG")
    must(metric_service, "trend_compare")
    must(metric_service, "cross_validate")
    must(sop_service, "V1013_TASK_SOP_VERSION = \"10.13.0\"")
    must(sop_service, "退款理由 Top5")
    must(sop_service, "客服团队核实")
    must(sop_service, "completionGate")
    must(sop_service, "SOP 是骨架，公司 RAG 是调参")
    must(task_agent, "TASK_AGENT_VERSION = \"10.13.0\"")
    must(task_agent, "v1013TaskSop")
    must(task_agent, "taskExecutionSop")
    must(task_agent, "completionGate")
    must(trends_route, "/metric-evidence")
    must(trends_route, "/task-sop")
    check_sidebar_navigation(index)
    must(index, "sop-ui.css?v=10.13.1")
    must(index, "modules/task-report/page.js?v=10.13.1")
    must(index, "modules/todo/page.js?v=10.9.1")
    must(index, "modules/operating-unit/page.js?v=10.9.4")
    must(index, "core/api-client.js?v=10.9.3")
    for marker in OLD_CHILD_SCRIPTS:
        must_not(index, marker)
    must(api_client, "metricEvidence")
    must(api_client, "taskSop")
    must(api_client, "syncDataSource")
    must(api_client, "resetRuntimeData")
    must(operating_page, "data-operation-module")
    must_not(operating_page, "data-operation-route")
    must(todo_page, "sopPanel")
    must(todo_page, "taskExecutionSop")
    must(todo_page, "不允许只写处理建议")
    must(task_report_page, "window.TaskReportPage")
    must(task_report_page, "route: \"task-report\"")
    must(sop_css, "todo-sop-panel")
    must(sop_css, "task-report-sop-step")
    must(task_store, "openTaskReport")
    must(system_status, "SYSTEM STATUS · V10.9")
    check_runtime_routes()
    print("V10.13 frontend/backend breakpoint and duplicate guard passed.")


if __name__ == "__main__":
    main()
