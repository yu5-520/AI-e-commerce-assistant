from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    p = ROOT / path
    if not p.exists():
        raise AssertionError(f"missing {path}")
    return p.read_text(encoding="utf-8")


def must(text, marker):
    if marker not in text:
        raise AssertionError(f"missing {marker}")


def main():
    must(read("src/api/main.py"), "API_VERSION = \"9.8.0\"")
    must(read("src/api/routes/health.py"), "API_VERSION = \"9.8.0\"")
    must(read("src/services/v98_ops_authorization_service.py"), "V98_OPS_AUTH_VERSION")
    must(read("docs/V9_OPS_AUTHORIZATION_CONSISTENCY.md"), "V9.8")
    print("V9.8 guard passed.")


if __name__ == "__main__":
    main()
