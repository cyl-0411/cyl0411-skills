"""Normalize arbitrary conference metadata into the collector's core schema."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


FIELDS = [
    "collection", "conference", "venue_slug", "year", "paper_id", "title",
    "authors", "abstract", "keywords", "session_id", "session_title", "pages",
    "publisher", "doi", "doi_url", "ee_url", "official_url", "citation_pdf_url",
]

ALIASES = {
    "conference": ("conference", "conference_name", "venue", "booktitle"),
    "year": ("year", "publication_year", "conference_year"),
    "paper_id": ("paper_id", "id", "session_paper_id", "paperId"),
    "title": ("title", "paper_title", "name"),
    "authors": ("authors", "author", "creators"),
    "abstract": ("abstract", "summary", "description"),
    "keywords": ("keywords", "keyword", "topics"),
    "session_id": ("session_id", "session", "track_id"),
    "session_title": ("session_title", "track", "track_title"),
    "pages": ("pages", "page", "pagination"),
    "publisher": ("publisher", "publisher_name"),
    "doi": ("doi", "DOI"),
    "doi_url": ("doi_url", "doiUrl"),
    "ee_url": ("ee_url", "electronic_edition", "publisher_url", "url"),
    "official_url": ("official_url", "program_url", "conference_url"),
    "citation_pdf_url": ("citation_pdf_url", "pdf_url", "fulltext_url"),
    "collection": ("collection", "collection_id"),
    "venue_slug": ("venue_slug", "conference_slug"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize conference JSON/CSV into metadata and download logs."
    )
    parser.add_argument("--input", type=Path, required=True, help="Raw JSON or CSV file")
    parser.add_argument("--root", type=Path, required=True, help="Collection project root")
    parser.add_argument("--conference", help="Fallback conference/venue name")
    parser.add_argument("--year", help="Fallback publication year")
    parser.add_argument("--collection", help="Override collection ID for all records")
    return parser.parse_args()


def first(record: dict[str, Any], field: str) -> Any:
    for key in ALIASES[field]:
        value = record.get(key)
        if value not in (None, "", []):
            return value
    return ""


def text(value: Any) -> str:
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                item = item.get("name") or item.get("literal") or json.dumps(item, ensure_ascii=False)
            parts.append(str(item).strip())
        return "; ".join(part for part in parts if part)
    if isinstance(value, dict):
        return str(value.get("name") or value.get("value") or json.dumps(value, ensure_ascii=False))
    return str(value or "").strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "venue"


def load_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("papers", "records", "items", "data"):
            if isinstance(value.get(key), list):
                return value[key]
    raise ValueError("JSON input must be a list or contain papers/records/items/data")


def normalize(raw: dict[str, Any], index: int, args: argparse.Namespace) -> dict[str, str]:
    conference = text(first(raw, "conference")) or text(args.conference)
    year = text(first(raw, "year")) or text(args.year)
    if not conference:
        raise ValueError(f"record {index}: conference is missing")
    if not year:
        raise ValueError(f"record {index}: year is missing")
    venue_slug = text(first(raw, "venue_slug")) or slugify(conference)
    collection = text(args.collection) or text(first(raw, "collection")) or f"{venue_slug}-{year}"
    doi = text(first(raw, "doi"))
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.I)
    paper_id = text(first(raw, "paper_id")) or doi or f"paper-{index:04d}"
    title = text(first(raw, "title"))
    if not title:
        raise ValueError(f"record {index}: title is missing")
    doi_url = text(first(raw, "doi_url")) or (f"https://doi.org/{doi}" if doi else "")
    out = {field: "" for field in FIELDS}
    out.update({
        "collection": collection,
        "conference": conference,
        "venue_slug": venue_slug,
        "year": year,
        "paper_id": paper_id,
        "title": title,
        "doi": doi,
        "doi_url": doi_url,
    })
    for field in FIELDS:
        if field not in {"collection", "conference", "venue_slug", "year", "paper_id", "title", "doi", "doi_url"}:
            out[field] = text(first(raw, field))
    return out


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    raw_records = load_records(args.input)
    records = [normalize(raw, index, args) for index, raw in enumerate(raw_records, 1)]
    root = args.root.resolve()
    for name in ("papers", "metadata", "reports", "logs", "tools"):
        (root / name).mkdir(parents=True, exist_ok=True)

    (root / "metadata" / "papers.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_csv(root / "metadata" / "papers.csv", records, FIELDS)

    log_fields = [
        "collection", "paper_id", "title", "doi", "doi_url", "ee_url",
        "source_url", "download_status", "pdf_path", "failure_reason",
    ]
    logs = []
    for record in records:
        logs.append({
            **record,
            "source_url": record["citation_pdf_url"] or record["doi_url"] or record["ee_url"] or record["official_url"],
            "download_status": "pending",
            "pdf_path": "",
            "failure_reason": "",
        })
    write_csv(root / "logs" / "download_report.csv", logs, log_fields)

    collections = sorted({record["collection"] for record in records})
    manifest = {
        "source_input": str(args.input.resolve()),
        "collections": collections,
        "record_count": len(records),
        "conference_fallback": args.conference or "",
        "year_fallback": args.year or "",
    }
    (root / "metadata" / "collection.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"root": str(root), "collections": collections, "records": len(records)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
