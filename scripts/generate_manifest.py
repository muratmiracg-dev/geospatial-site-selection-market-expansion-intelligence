"""Generate review manifest, SHA-256 ledger and repository tree."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".ruff_cache", ".pytest_cache", "__pycache__", ".venv"}
EXCLUDED_NAMES = {
    ".coverage",
    "MANIFEST.sha256",
    "project_manifest.json",
    "repository_tree.txt",
    "Geospatial_Site_Selection_Market_Expansion_Intelligence_READY_FOR_REVIEW.zip",
}


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return (
        path.is_file()
        and not any(part in EXCLUDED_PARTS for part in relative.parts)
        and path.name not in EXCLUDED_NAMES
        and not path.name.endswith(".inspect.ndjson")
    )


def main() -> None:
    files = sorted(path for path in ROOT.rglob("*") if included(path))
    records = []
    checksum_lines = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        relative = path.relative_to(ROOT).as_posix()
        records.append({"path": relative, "bytes": path.stat().st_size, "sha256": digest})
        checksum_lines.append(f"{digest}  {relative}")

    manifest = {
        "project": "Geospatial Site Selection & Market Expansion Intelligence",
        "status": "READY_FOR_REVIEW_NOT_PUBLISHED",
        "file_count": len(records),
        "total_bytes": sum(record["bytes"] for record in records),
        "hash_ledger_exclusions": sorted(EXCLUDED_NAMES),
        "files": records,
    }
    (ROOT / "project_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (ROOT / "MANIFEST.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    tree_paths = [record["path"] for record in records] + [
        "MANIFEST.sha256",
        "project_manifest.json",
        "repository_tree.txt",
    ]
    nested: dict[str, dict] = {}
    for relative in sorted(tree_paths):
        node = nested
        for part in Path(relative).parts:
            node = node.setdefault(part, {})

    tree_lines = ["geospatial-site-selection-market-expansion-intelligence/"]

    def add_tree(node: dict[str, dict], prefix: str) -> None:
        items = sorted(node.items(), key=lambda item: (not bool(item[1]), item[0].lower()))
        for index, (name, children) in enumerate(items):
            last = index == len(items) - 1
            tree_lines.append(f"{prefix}{'└── ' if last else '├── '}{name}")
            if children:
                add_tree(children, f"{prefix}{'    ' if last else '│   '}")

    add_tree(nested, "")
    (ROOT / "repository_tree.txt").write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(records), "bytes": manifest["total_bytes"]}))


if __name__ == "__main__":
    main()
