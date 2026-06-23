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
    must(read("src/api/main.py"), "API_VERSION = \"9.9.0\"")
    must(read("src/api/routes/health.py"), "API_VERSION = \"9.9.0\"")
    must(read("src/services/v99_delivery_readiness_service.py"), "V99_DELIVERY_VERSION")
    must(read("docs/V9_DELIVERY_READINESS_CONSISTENCY.md"), "V9.9")
    must(read("versioning/VERSION.md"), "v9.9.0")
    print("V9.9 guard passed.")


if __name__ == "__main__":
    main()
