#!/usr/bin/env python3
"""Check current repository files against the V16 MVP manifest.

This script does not delete anything. It prints the current V16 whitelist and the
unmarked files that should be reviewed before the MVP purge step.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Set

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "config" / "v16_mvp_file_manifest.json"


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


def main() -> int:
    manifest = load_manifest()
    keep = as_set(manifest, "v16_keep")
    support = as_set(manifest, "v16_support")
    docs = as_set(manifest, "v16_docs")
    tools = as_set(manifest, "v16_tools")
    frontend_prefixes = sorted(as_set(manifest, "v16_frontend_prefixes"))
    purge_candidates = as_set(manifest, "purge_candidates_after_import_check")
    whitelisted_exact = keep | support | docs | tools

    files = git_files()
    marked = []
    unmarked = []
    purge_present = []
    for path in files:
        if path in whitelisted_exact or under_prefix(path, frontend_prefixes):
            marked.append(path)
        else:
            unmarked.append(path)
        if path in purge_candidates:
            purge_present.append(path)

    print(f"Manifest version: {manifest.get('manifestVersion')}")
    print(f"Baseline: {manifest.get('baseline')}")
    print(f"V16 marked files: {len(marked)}")
    print(f"Unmarked files: {len(unmarked)}")
    print(f"First purge candidates still present: {len(purge_present)}")

    if purge_present:
        print("\n[PURGE CANDIDATES PRESENT]")
        for path in purge_present:
            print(path)

    if unmarked:
        print("\n[UNMARKED FILES - REVIEW BEFORE DELETE]")
        for path in unmarked:
            print(path)

    print("\nRule: unmarked files are deletion candidates unless promoted into config/v16_mvp_file_manifest.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
