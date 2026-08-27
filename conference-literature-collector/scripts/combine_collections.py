#!/usr/bin/env python3
"""Combine normalized paper metadata from arbitrary collections into Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_json_value(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def parse_input(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError("--input must be LABEL=PATH")
    label, raw_path = spec.split("=", 1)
    if not label.strip() or not raw_path.strip():
        raise argparse.ArgumentTypeError("--input must contain a label and path")
    return label.strip(), Path(raw_path).expanduser()


def load_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("papers", payload.get("records"))
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise ValueError(f"Expected a JSON array of objects: {path}")
    return payload


def escape(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True, type=parse_input, metavar="LABEL=PATH")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", default="Combined Literature Collection")
    parser.add_argument("--filter-field")
    parser.add_argument("--filter-value", default="true")
    parser.add_argument("--id-field", default="paper_id")
    parser.add_argument("--year-field", default="year")
    parser.add_argument("--title-field", default="title")
    parser.add_argument("--url-field", default="doi_url")
    parser.add_argument("--bucket-field", default="topic")
    args = parser.parse_args()

    wanted = parse_json_value(args.filter_value)
    rows: list[tuple[str, dict[str, Any]]] = []
    for label, path in args.input:
        for row in load_rows(path):
            if args.filter_field and row.get(args.filter_field) != wanted:
                continue
            rows.append((label, row))

    rows.sort(key=lambda item: (str(item[1].get(args.year_field, "")), str(item[1].get(args.id_field, "")), item[0]))
    lines = [f"# {args.title}", "", f"Collections: {len(args.input)}; records: {len(rows)}.", "", "| Collection | Year | ID | Paper | Bucket |", "|---|---|---|---|---|"]
    for label, row in rows:
        title = escape(row.get(args.title_field, "Untitled"))
        url = row.get(args.url_field) or row.get("official_url") or ""
        paper = f"[{title}]({url})" if url else title
        lines.append(f"| {escape(label)} | {escape(row.get(args.year_field))} | {escape(row.get(args.id_field))} | {paper} | {escape(row.get(args.bucket_field))} |")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
