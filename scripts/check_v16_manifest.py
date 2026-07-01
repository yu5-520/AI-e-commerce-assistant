#!/usr/bin/env python3
"""Check current repository files against the V16 MVP manifest.

V16.8 adds purge planning. By default this script only prints the current V16
whitelist and unmarked files. With --write-plan it writes a reviewable purge
plan to /tmp/v16_purge_plan.sh. With --purge it removes unmarked files from the
local working tree. It never commits changes.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "config" / "v16_mvp_file_manifest.json"
DEFAULT_PLAN_PATH = Path("/tmp/v16_purge_plan.sh")
PROTECTED_PREFIXES = {".git/", "web_demo/"}
PROTECTED_EXACT = {".gitignore", ".env.example"}


def load_manifest() -> Dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def git_files() -> List[str]:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def as_set(manifest: Dict[str, object], key: str) -> Set[str]:
    values = manifest.get(key) or []
    return {str(item) for item in values if str(item).strip()}


def under_prefix(path: str, prefixes: Iterable[str]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def classify(path: str) -> str:
    if path.startswith("docs/"):
        return "old_docs"
    if path.startswith("examples/"):
        return "old_examples_mock_data"
    if path.startswith("evals/"):
        return "old_evals"
    if path.startswith("frontend/"):
        return "old_frontend"
    if path.startswith(".github/"):
        return "old_github_templates_workflows"
    if path.startswith("alembic/") or path == "alembic.ini":
        return "old_alembic_migration"
    if path.startswith("knowledge_base/"):
        return "rag_knowledge_base_review"
    if path.startswith("data/"):
        return "old_runtime_or_sample_data"
    if path.startswith("deploy/"):
        return "deploy_review"
    if path.startswith("backend/"):
        return "old_backend_docs"
    if path.startswith("modules/"):
        return "old_module_archives"
    return "unmarked_review"


def split_files(files: List[str], manifest: Dict[str, object]) -> Tuple[List[str], List[str], List[str]]:
    keep = as_set(manifest, "v16_keep")
    support = as_set(manifest, "v16_support")
    docs = as_set(manifest, "v16_docs")
    tools = as_set(manifest, "v16_tools")
    frontend_prefixes = sorted(as_set(manifest, "v16_frontend_prefixes"))
    whitelisted_exact = keep | support | docs | tools
    marked: List[str] = []
    unmarked: List[str] = []
    protected_unmarked: List[str] = []
    for path in files:
        if path in whitelisted_exact or under_prefix(path, frontend_prefixes):
            marked.append(path)
        elif path in PROTECTED_EXACT or under_prefix(path, PROTECTED_PREFIXES):
            protected_unmarked.append(path)
        else:
            unmarked.append(path)
    return marked, unmarked, protected_unmarked


def write_plan(unmarked: List[str], protected_unmarked: List[str], plan_path: Path = DEFAULT_PLAN_PATH) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "echo 'V16.8 purge plan: removing unmarked MVP cleanup candidates'",
        "",
    ]
    for path in sorted(unmarked):
        lines.append(f"git rm -- {shlex.quote(path)}")
    if protected_unmarked:
        lines.extend(["", "echo 'Protected unmarked files were intentionally not removed:'"])
        for path in sorted(protected_unmarked):
            lines.append(f"echo {shlex.quote(path)}")
    plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(plan_path, 0o755)


def purge_local(unmarked: List[str]) -> None:
    if not unmarked:
        return
    subprocess.run(["git", "rm", "--", *unmarked], cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or purge files outside the V16 MVP manifest.")
    parser.add_argument("--write-plan", action="store_true", help="write /tmp/v16_purge_plan.sh")
    parser.add_argument("--purge", action="store_true", help="git rm unmarked files locally; does not commit")
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    args = parser.parse_args()

    manifest = load_manifest()
    files = git_files()
    marked, unmarked, protected_unmarked = split_files(files, manifest)

    categories: Dict[str, int] = {}
    for path in unmarked:
        category = classify(path)
        categories[category] = categories.get(category, 0) + 1

    purge_candidates = as_set(manifest, "purge_candidates_after_import_check")
    purge_present = [path for path in files if path in purge_candidates]

    if args.write_plan:
        write_plan(unmarked, protected_unmarked)
    if args.purge:
        purge_local(unmarked)

    summary = {
        "manifestVersion": manifest.get("manifestVersion"),
        "baseline": manifest.get("baseline"),
        "v16MarkedFiles": len(marked),
        "unmarkedFiles": len(unmarked),
        "protectedUnmarkedFiles": len(protected_unmarked),
        "firstPurgeCandidatesStillPresent": len(purge_present),
        "categories": categories,
        "planPath": str(DEFAULT_PLAN_PATH) if args.write_plan else None,
        "purgedLocally": bool(args.purge),
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    print(f"Manifest version: {summary['manifestVersion']}")
    print(f"Baseline: {summary['baseline']}")
    print(f"V16 marked files: {summary['v16MarkedFiles']}")
    print(f"Unmarked files: {summary['unmarkedFiles']}")
    print(f"Protected unmarked files: {summary['protectedUnmarkedFiles']}")
    print(f"First purge candidates still present: {summary['firstPurgeCandidatesStillPresent']}")

    if categories:
        print("\n[UNMARKED CATEGORIES]")
        for category, count in sorted(categories.items(), key=lambda item: (-item[1], item[0])):
            print(f"{category}: {count}")

    if purge_present:
        print("\n[PURGE CANDIDATES PRESENT]")
        for path in purge_present:
            print(path)

    if unmarked:
        print("\n[UNMARKED FILES - REVIEW BEFORE DELETE]")
        for path in unmarked:
            print(path)

    if protected_unmarked:
        print("\n[PROTECTED UNMARKED FILES - NOT DELETED BY --PURGE]")
        for path in protected_unmarked:
            print(path)

    if args.write_plan:
        print(f"\nWrote purge plan: {DEFAULT_PLAN_PATH}")
        print("Review it, then run: bash /tmp/v16_purge_plan.sh")
    if args.purge:
        print("\nPurged unmarked files locally. Review with: git status --short")

    print("\nRule: unmarked files are deletion candidates unless promoted into config/v16_mvp_file_manifest.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
