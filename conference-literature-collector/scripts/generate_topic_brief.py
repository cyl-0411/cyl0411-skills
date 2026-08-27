#!/usr/bin/env python3
"""Generate a configuration-driven topic brief from normalized metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("papers", payload.get("records"))
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise ValueError(f"Expected a JSON array of objects: {path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--metadata", type=Path, default=Path("metadata/papers.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/topic_paper_briefs.md"))
    args = parser.parse_args()

    root = args.root.resolve()
    config_path = args.config if args.config.is_absolute() else root / args.config
    metadata_path = args.metadata if args.metadata.is_absolute() else root / args.metadata
    output_path = args.output if args.output.is_absolute() else root / args.output
    config = json.loads(config_path.read_text(encoding="utf-8"))
    rows = load_rows(metadata_path)
    id_field = config.get("id_field", "paper_id")
    by_id = {str(row.get(id_field, "")): row for row in rows}
    selected_ids = [str(value) for value in config.get("paper_ids", [key for key in by_id if key])]
    missing = [key for key in selected_ids if key not in by_id]
    if missing:
        raise ValueError("Configured paper IDs are missing from metadata: " + ", ".join(missing))

    notes = config.get("notes", {})
    lines = [f"# {config.get('title', 'Topic Paper Briefs')}", ""]
    if config.get("scope"):
        lines.extend([str(config["scope"]), ""])
    lines.extend(["## Corpus", "", f"- Metadata records: {len(rows)}", f"- Selected records: {len(selected_ids)}", ""])
    for paper_id in selected_ids:
        row, note = by_id[paper_id], notes.get(paper_id, {})
        lines.extend([f"## {paper_id} — {row.get(config.get('title_field', 'title'), 'Untitled')}", ""])
        abstract = row.get(config.get("abstract_field", "abstract"))
        if abstract:
            lines.append(f"- Abstract: {abstract}")
        for label, key in (("Category", "category"), ("Summary", "summary"), ("Innovation", "innovation"), ("Comparison", "comparison"), ("Takeaway", "takeaway")):
            if note.get(key):
                lines.append(f"- {label}: {note[key]}")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
