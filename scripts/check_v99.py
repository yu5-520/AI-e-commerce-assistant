from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]

CHECK_FILES = [
    "src/api/main.py",
    "src/api/routes/health.py",
    "src/api/routes/modules/agents.py",
    "src/api/routes/v9_readiness.py",
    "scripts/check_v99.py",
]


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


def main():
    compile_files()
    main_py = read("src/api/main.py")
    health = read("src/api/routes/health.py")
    agents = read("src/api/routes/modules/agents.py")
    readiness = read("src/api/routes/v9_readiness.py")
    index = read("web_demo/index.html")

    must(main_py, "API_VERSION = \"9.9.0\"")
    for marker in ["approvals", "audit", "import_jobs", "task_persistence", "report_task_sync", "trends", "worker_jobs"]:
        must(main_py, marker)
    must(health, "API_VERSION = \"9.9.0\"")
    must(health, "/api/architecture/v9/ops-authorization")
    must(health, "/api/architecture/v9/delivery-readiness")
    must(agents, "AGENT_REGISTRY_VERSION = \"9.9.0\"")
    must(agents, "v99DeliveryReadiness")
    must(readiness, "/v9/ops-authorization")
    must(readiness, "/v9/delivery-readiness")
    must(read("src/services/v98_ops_authorization_service.py"), "V98_OPS_AUTH_VERSION")
    must(read("src/services/v99_delivery_readiness_service.py"), "V99_DELIVERY_VERSION")
    must(read("versioning/VERSION.md"), "9.9.0")
    must(index, "?v=9.9.0")
    print("V9.9 architecture guard passed.")


if __name__ == "__main__":
    main()
