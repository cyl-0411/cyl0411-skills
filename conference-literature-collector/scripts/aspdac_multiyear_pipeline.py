#!/usr/bin/env python3
"""Collect ASP-DAC 2023/2024/2025 metadata and QEC candidate reports."""

from __future__ import annotations

import argparse
import csv
import difflib
import html
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


YEAR_CONFIG = {
    2025: {
        "program_url": "https://www.aspdac.com/aspdac2025/archive/program/program.html",
        "abstract_url": "https://www.aspdac.com/aspdac2025/archive/program/program_abst.html",
        "dblp_url": "https://dblp.org/db/conf/aspdac/aspdac2025.html",
        "publisher": "ACM",
        "isbn": "979-8-4007-0635-6",
        "location": "Tokyo, Japan",
        "dates": "January 20-23, 2025",
        "proceedings": "Proceedings of the 30th Asia and South Pacific Design Automation Conference, ASPDAC 2025",
    },
    2024: {
        "program_url": "https://tsys.jp/aspdac/2024/program/program.html",
        "abstract_url": "https://tsys.jp/aspdac/2024/program/program_abst.html",
        "dblp_url": "https://dblp.org/db/conf/aspdac/aspdac2024.html",
        "publisher": "IEEE",
        "isbn": "979-8-3503-9355-2",
        "location": "Incheon, Korea",
        "dates": "January 22-25, 2024",
        "proceedings": "Proceedings of the 29th Asia and South Pacific Design Automation Conference, ASPDAC 2024",
    },
    2023: {
        "program_url": "https://www.aspdac.com/aspdac2023/archive/program/program.html",
        "abstract_url": "https://www.aspdac.com/aspdac2023/archive/program/program_abst.html",
        "dblp_url": "https://dblp.org/db/conf/aspdac/aspdac2023.html",
        "publisher": "ACM",
        "isbn": "978-1-4503-9783-4",
        "location": "Tokyo, Japan",
        "dates": "January 16-19, 2023",
        "proceedings": "Proceedings of the 28th Asia and South Pacific Design Automation Conference, ASPDAC 2023",
    },
}

STRICT_QEC_RE = re.compile(
    r"\bquantum\b|\bqubit\b|\bqubits\b|\bQEC\b|quantum error correction|"
    r"surface code|\bFTQC\b|\bqLDPC\b|fault[- ]tolerant quantum|magic[- ]state|"
    r"syndrome|quantum circuit simulation|quantum routing|"
    r"decision diagrams? for measurements?|oracle synthesis|single-flux quantum",
    re.I,
)

CORE_QEC_RE = re.compile(
    r"quantum error correction|\bQEC\b|surface code|\bqLDPC\b|"
    r"fault[- ]tolerant quantum|syndrome|"
    r"decoder(?:s|ing)?[^.]{0,40}(?:quantum|surface code|qldpc)|"
    r"(?:quantum|surface code|qldpc)[^.]{0,40}decoder(?:s|ing)?",
    re.I,
)

ADJACENT_QEC_RE = re.compile(
    r"quantum circuit simulation|quantum routing|oracle synthesis|"
    r"quantum circuits?|measurements? of quantum circuits?|single-flux quantum|"
    r"trapped-ion quantum",
    re.I,
)


@dataclass
class FetchResult:
    url: str
    data: bytes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True, choices=sorted(YEAR_CONFIG))
    parser.add_argument("--root", type=Path, required=True)
    return parser.parse_args()


def ensure_dirs(root: Path) -> dict[str, Path]:
    paths = {
        "root": root,
        "papers": root / "papers",
        "metadata": root / "metadata",
        "reports": root / "reports",
        "logs": root / "logs",
        "tools": root / "tools",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def fetch_bytes(url: str, *, retries: int = 4, delay: float = 1.0) -> FetchResult:
    ctx = ssl._create_unverified_context()
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "aspdac-multiyear-pipeline/1.0 (+metadata collection)"
                },
            )
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                return FetchResult(resp.geturl(), resp.read())
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries:
                time.sleep(delay * attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def fetch_text(url: str, encoding: str = "utf-8") -> str:
    return fetch_bytes(url).data.decode(encoding, errors="replace")


def clean_html(fragment: str) -> str:
    fragment = re.sub(r"<!--.*?-->", " ", fragment, flags=re.S)
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"</(p|div|h\d|li|tr|td|th|font|b)>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    text = html.unescape(fragment)
    text = text.replace("\x92", "'")
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_first(pattern: str, text: str, flags: int = re.S | re.I) -> str:
    match = re.search(pattern, text, flags)
    return clean_html(match.group(1)) if match else ""


def norm_title(title: str) -> str:
    title = html.unescape(title).lower()
    title = re.sub(r"&apos;", "'", title)
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def slugify(value: str, max_len: int = 72) -> str:
    value = html.unescape(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:max_len].strip("-") or "paper"


def doi_to_safe(doi: str) -> str:
    return re.sub(r"[^A-Za-z0-9.]+", "_", doi).strip("_")


def parse_session_map(program_html: str) -> tuple[dict[str, dict], list[str]]:
    anchors = list(re.finditer(r'<a name="(\d[A-Z])"></a>', program_html, re.I))
    session_map: dict[str, dict] = {}
    paper_order: list[str] = []
    for idx, match in enumerate(anchors):
        sid = match.group(1)
        start = match.start()
        end = anchors[idx + 1].start() if idx + 1 < len(anchors) else len(program_html)
        block = program_html[start:end]
        title = extract_first(
            rf'<a name="{re.escape(sid)}"></a>.*?(?:Session\s+{re.escape(sid)}</b>|{re.escape(sid)}</b>)(.*?)(?:<a name="\d[A-Z]-\d+"></a>|<table class="tbl1")',
            block,
        )
        title = re.sub(r"^(Session\s+\w+\s*)", "", title, flags=re.I).strip(" :")
        title = title.split("Time:", 1)[0].strip(" -")
        if not title:
            title = extract_first(rf"Session\s+{re.escape(sid)}</b>(.*?)<", block)
        paper_ids = re.findall(r'<a name="(\d[A-Z]-\d+)"></a>', block, re.I)
        for pid in paper_ids:
            paper_order.append(pid)
            session_map[pid] = {
                "session_id": sid,
                "session_title": title or sid,
                "program_url": "",
            }
    return session_map, paper_order


def parse_abstract_blocks(year: int, abstract_html: str, session_map: dict[str, dict], paper_order: list[str]) -> list[dict]:
    ids = re.findall(r'<a name="(\d[A-Z]-\d+)"></a>', abstract_html, re.I)
    records: list[dict] = []
    config = YEAR_CONFIG[year]
    for idx, pid in enumerate(ids):
        start_token = f'<a name="{pid}"></a>'
        start = abstract_html.find(start_token)
        if start < 0:
            continue
        next_start = len(abstract_html)
        if idx + 1 < len(ids):
            next_token = f'<a name="{ids[idx + 1]}"></a>'
            candidate = abstract_html.find(next_token, start + len(start_token))
            if candidate > 0:
                next_start = candidate
        block = abstract_html[start:next_start]
        title = extract_first(r"Title</font></td><td>(.*?)</td></tr>", block)
        authors = extract_first(r"Author</font></td><td>(.*?)</td></tr>", block)
        pages = extract_first(r"Page</font></td><td>(.*?)</td></tr>", block)
        keywords = extract_first(r"Keyword</font></td><td>(.*?)</td></tr>", block)
        abstract = extract_first(r"Abstract</font></td><td>(.*?)</td></tr>", block)
        time_info = " ".join(re.findall(r"<font size=-1>\((.*?)\)</font>", block, re.I)).strip()
        if not title:
            continue
        session = session_map.get(pid, {"session_id": pid.split("-")[0], "session_title": pid.split("-")[0]})
        records.append(
            {
                "year": year,
                "paper_id": pid,
                "session_id": session["session_id"],
                "session_title": session["session_title"],
                "talk_time": time_info,
                "title": title.rstrip("."),
                "authors": authors,
                "pages": pages,
                "keywords": keywords,
                "abstract": abstract,
                "official_url": f"{config['abstract_url']}#{pid}",
                "publisher": config["publisher"],
                "doi": "",
                "doi_url": "",
                "dblp_key": "",
                "dblp_url": "",
                "ee_url": "",
                "bibtex_url": "",
                "ris_url": "",
                "dblp_match_score": 0.0,
                "in_dblp": False,
            }
        )
    order_index = {pid: idx for idx, pid in enumerate(paper_order)}
    records.sort(key=lambda r: order_index.get(r["paper_id"], 99999))
    return records


def parse_dblp(dblp_html: str) -> tuple[list[dict], dict]:
    proceedings_match = re.search(
        r"Proceedings of the .*? ISBN ([0-9\-Xx]+)",
        clean_html(dblp_html),
        re.I,
    )
    proceedings_line = proceedings_match.group(0) if proceedings_match else ""
    blocks = re.split(r'<li class="entry inproceedings"', dblp_html)[1:]
    records: list[dict] = []
    for part in blocks:
        block = '<li class="entry inproceedings"' + part
        key_match = re.search(r'dblp key:\s*</[^>]+>\s*<[^>]*>\s*([^<\s]+)', block, re.I | re.S)
        if not key_match:
            key_match = re.search(r'<li class="entry inproceedings" id="([^"]+)"', block, re.I)
        key = clean_html(key_match.group(1)) if key_match else ""
        title = extract_first(r'<span class="title" itemprop="name">(.*?)</span>', block)
        if not title:
            title = extract_first(r":\s*(.*?)\.\s*<span itemprop=", block)
        if not title:
            continue
        authors = [
            html.unescape(name)
            for name in re.findall(r'itemprop="name" title="([^"]+)"', block, re.I)
        ]
        pages = extract_first(r"<span itemprop=\"pagination\">(.*?)</span>", block)
        doi_match = re.search(r'https://doi\.org/([^"<>\s]+)', block, re.I)
        ee_match = re.search(r'electronic edition(?: @ ieee\.org)?[^>]*>\s*</[^>]+>\s*<[^>]+href="([^"]+)"', block, re.I | re.S)
        rec_key_match = re.search(r'persistent URL:\s*</[^>]+>\s*<[^>]+>\s*([^<]+)', block, re.I | re.S)
        rec_url = clean_html(rec_key_match.group(1)) if rec_key_match else ""
        records.append(
            {
                "title": title.rstrip("."),
                "authors": "; ".join(authors),
                "pages": pages,
                "doi": urllib.parse.unquote(html.unescape(doi_match.group(1))) if doi_match else "",
                "doi_url": f"https://doi.org/{urllib.parse.unquote(html.unescape(doi_match.group(1)))}" if doi_match else "",
                "ee_url": html.unescape(ee_match.group(1)) if ee_match else "",
                "dblp_key": key,
                "dblp_url": rec_url,
                "bibtex_url": f"{rec_url}.bib" if rec_url else "",
                "ris_url": f"{rec_url}.ris" if rec_url else "",
            }
        )
    return records, {"proceedings_line": proceedings_line}


def merge_records(official: list[dict], dblp: list[dict], year: int) -> tuple[list[dict], list[dict]]:
    dblp_by_norm = {norm_title(row["title"]): row for row in dblp}
    dblp_norms = list(dblp_by_norm.keys())
    matched_keys: set[str] = set()
    merged: list[dict] = []
    for rec in official:
        title_key = norm_title(rec["title"])
        match = dblp_by_norm.get(title_key)
        score = 1.0 if match else 0.0
        if not match and dblp_norms:
            best_key = max(
                dblp_norms,
                key=lambda candidate: difflib.SequenceMatcher(None, title_key, candidate).ratio(),
            )
            best_score = difflib.SequenceMatcher(None, title_key, best_key).ratio()
            if best_score >= 0.84:
                match = dblp_by_norm[best_key]
                score = best_score
        out = dict(rec)
        if match:
            out.update(
                {
                    "pages": match.get("pages") or out.get("pages", ""),
                    "authors": out.get("authors") or match.get("authors", ""),
                    "doi": match.get("doi", ""),
                    "doi_url": match.get("doi_url", ""),
                    "ee_url": match.get("ee_url", ""),
                    "dblp_key": match.get("dblp_key", ""),
                    "dblp_url": match.get("dblp_url", ""),
                    "bibtex_url": match.get("bibtex_url", ""),
                    "ris_url": match.get("ris_url", ""),
                    "in_dblp": True,
                    "dblp_match_score": round(score, 3),
                }
            )
            if match.get("dblp_key"):
                matched_keys.add(match["dblp_key"])
        merged.append(classify_record(out, year))
    unmatched = [row for row in dblp if row.get("dblp_key") not in matched_keys]
    technical = [row for row in merged if row.get("in_dblp")]
    return technical, unmatched


def classify_record(record: dict, year: int) -> dict:
    haystack = " ".join(
        str(record.get(field, "")) for field in ("title", "keywords", "abstract")
    )
    record["is_quantum_candidate"] = bool(STRICT_QEC_RE.search(haystack))
    if not record["is_quantum_candidate"]:
        record["qec_relevance"] = "not_quantum"
        record["qec_similarity"] = "none"
        return record

    if CORE_QEC_RE.search(haystack):
        record["qec_relevance"] = "QEC-simulator-core"
        record["qec_similarity"] = "high"
    elif ADJACENT_QEC_RE.search(haystack):
        record["qec_relevance"] = "QEC-adjacent"
        record["qec_similarity"] = "medium"
    else:
        record["qec_relevance"] = "quantum-non-QEC"
        record["qec_similarity"] = "low"
    return record


def pdf_filename(record: dict) -> str:
    stem = f"{record['paper_id']}__{slugify(record['title'])}"
    if record.get("doi"):
        return f"{stem}__{doi_to_safe(record['doi'])}.pdf"
    return f"{stem}.pdf"


def build_download_report(root: Path, records: list[dict], year: int) -> list[dict]:
    rows: list[dict] = []
    for rec in records:
        pdf_path = root / "papers" / pdf_filename(rec)
        if pdf_path.exists() and pdf_path.stat().st_size > 10000:
            if rec["publisher"] == "IEEE":
                status = "downloaded_ieee_xplore"
            elif rec["publisher"] == "ACM":
                status = "downloaded_acm_dl"
            else:
                status = "downloaded_open_access"
            rel_pdf = str(pdf_path.relative_to(root))
            failure = ""
        else:
            rel_pdf = ""
            if rec.get("doi"):
                status = "institution_required_or_no_open_version_found"
                failure = f"{rec['publisher']} DOI available but PDF not downloaded yet."
            else:
                status = "metadata_only_no_doi"
                failure = "No DBLP DOI match found."
        rows.append(
            {
                "collection": f"aspdac{year}",
                "paper_id": rec["paper_id"],
                "title": rec["title"],
                "doi": rec.get("doi", ""),
                "doi_url": rec.get("doi_url", ""),
                "ee_url": rec.get("ee_url", ""),
                "source_url": rec.get("doi_url") or rec.get("ee_url") or rec.get("official_url", ""),
                "download_status": status,
                "pdf_path": rel_pdf,
                "failure_reason": failure,
            }
        )
    return rows


def abstract_excerpt(text: str, limit: int = 520) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def innovation_notes(record: dict) -> tuple[str, str]:
    title = record["title"]
    abstract = record.get("abstract", "")
    hay = f"{title} {abstract}".lower()
    if "decoder" in hay or "decoding" in hay or "surface code" in hay:
        return (
            "Directly targets decoding flow or hardware support for QEC.",
            "Closest to a QEC simulator's decoder/plugin layer and timing model.",
        )
    if "simulation" in hay:
        return (
            "Focuses on quantum-circuit simulation efficiency.",
            "Useful as a modeling or benchmarking reference, but not a full QEC control-loop simulator by itself.",
        )
    if "routing" in hay or "oracle synthesis" in hay or "measurements" in hay:
        return (
            "Improves a quantum CAD stage adjacent to fault-tolerant execution.",
            "Relevant to workload generation, compiler front-end constraints, or measurement-side representation.",
        )
    if "single-flux quantum" in hay:
        return (
            "Studies SFQ clocking/control structures for quantum systems.",
            "More relevant to control hardware assumptions than to decoding algorithms.",
        )
    return (
        "Quantum-related method or architecture paper.",
        "Potentially useful as adjacent context rather than a direct simulator blueprint.",
    )


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_quantum_candidates(paths: dict[str, Path], records: list[dict], download_rows: list[dict], year: int) -> None:
    row_by_id = {row["paper_id"]: row for row in download_rows}
    candidates = [row for row in records if row.get("is_quantum_candidate")]
    lines = [
        f"# ASP-DAC {year} Quantum / QEC Candidates",
        "",
        f"- Candidate count: {len(candidates)}",
        f"- QEC-simulator-core: {sum(1 for row in candidates if row['qec_relevance'] == 'QEC-simulator-core')}",
        f"- QEC-adjacent: {sum(1 for row in candidates if row['qec_relevance'] == 'QEC-adjacent')}",
        f"- Quantum-non-QEC: {sum(1 for row in candidates if row['qec_relevance'] == 'quantum-non-QEC')}",
        "",
    ]
    for group in ("QEC-simulator-core", "QEC-adjacent", "quantum-non-QEC"):
        items = [row for row in candidates if row["qec_relevance"] == group]
        if not items:
            continue
        lines.extend([f"## {group}", ""])
        for rec in items:
            download = row_by_id.get(rec["paper_id"], {})
            lines.extend(
                [
                    f"### {rec['paper_id']} - {rec['title']}",
                    "",
                    f"- Session: {rec.get('session_title') or rec.get('session_id')}",
                    f"- Authors: {rec.get('authors') or 'N/A'}",
                    f"- DOI: {rec.get('doi') or 'N/A'}",
                    f"- Pages: {rec.get('pages') or 'N/A'}",
                    f"- Download: {download.get('download_status', 'not recorded')}"
                    + (f" ({download.get('pdf_path')})" if download.get("pdf_path") else ""),
                    f"- Keywords: {rec.get('keywords') or 'N/A'}",
                    "",
                    abstract_excerpt(rec.get("abstract", "No abstract available.")),
                    "",
                ]
            )
    (paths["reports"] / "quantum_candidates.md").write_text("\n".join(lines), encoding="utf-8")


def write_qec_briefs(paths: dict[str, Path], records: list[dict], year: int) -> None:
    candidates = [row for row in records if row.get("is_quantum_candidate")]
    lines = [
        f"# ASP-DAC {year} QEC / Quantum Briefs",
        "",
        "These notes are based on titles, official abstracts, and metadata. They are intentionally concise and geared toward QEC simulator design scouting.",
        "",
    ]
    for rec in candidates:
        innovation, comparison = innovation_notes(rec)
        lines.extend(
            [
                f"## {rec['paper_id']} - {rec['title']}",
                "",
                f"- Relevance: {rec['qec_relevance']} ({rec['qec_similarity']})",
                f"- Abstract takeaway: {abstract_excerpt(rec.get('abstract', 'No abstract available.'), 700)}",
                f"- Innovation point: {innovation}",
                f"- Comparison to QEC simulator work: {comparison}",
                "",
            ]
        )
    (paths["reports"] / "qec_paper_briefs.md").write_text("\n".join(lines), encoding="utf-8")


def write_summary(paths: dict[str, Path], records: list[dict], download_rows: list[dict], year: int, unmatched: list[dict]) -> None:
    candidates = [row for row in records if row.get("is_quantum_candidate")]
    lines = [
        f"# ASP-DAC {year} Collection Summary",
        "",
        f"- Technical papers indexed: {len(records)}",
        f"- Quantum/QEC candidates: {len(candidates)}",
        f"- QEC-simulator-core: {sum(1 for row in candidates if row['qec_relevance'] == 'QEC-simulator-core')}",
        f"- Downloaded PDFs: {sum(1 for row in download_rows if row['download_status'].startswith('downloaded_'))}",
        f"- Unmatched DBLP technical records after merge: {len(unmatched)}",
        "",
        "## Files",
        "",
        f"- `metadata/aspdac{year}_papers.json` / `.csv`",
        "- `logs/download_report.csv`",
        "- `reports/quantum_candidates.md`",
        "- `reports/qec_paper_briefs.md`",
        "",
    ]
    (paths["reports"] / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


def verify(paths: dict[str, Path], records: list[dict], download_rows: list[dict], unmatched: list[dict]) -> None:
    verification = {
        "technical_records": len(records),
        "quantum_candidates": sum(1 for row in records if row.get("is_quantum_candidate")),
        "qec_core": sum(1 for row in records if row.get("qec_relevance") == "QEC-simulator-core"),
        "downloaded_pdfs": sum(1 for row in download_rows if row["download_status"].startswith("downloaded_")),
        "missing_doi": sum(1 for row in records if not row.get("doi")),
        "unmatched_dblp": len(unmatched),
        "sample_records": [
            {
                "paper_id": row["paper_id"],
                "title": row["title"],
                "doi": row.get("doi", ""),
                "pages": row.get("pages", ""),
            }
            for row in records[:10]
        ],
    }
    write_json(paths["logs"] / "verification_summary.json", verification)


def main() -> int:
    args = parse_args()
    year = args.year
    config = YEAR_CONFIG[year]
    paths = ensure_dirs(args.root)

    print(f"[fetch] ASP-DAC {year} official program")
    program_html = fetch_text(config["program_url"], encoding="latin1")
    abstract_html = fetch_text(config["abstract_url"], encoding="latin1")
    print(f"[fetch] ASP-DAC {year} DBLP")
    dblp_html = fetch_text(config["dblp_url"])

    session_map, paper_order = parse_session_map(program_html)
    official = parse_abstract_blocks(year, abstract_html, session_map, paper_order)
    dblp, proceedings_meta = parse_dblp(dblp_html)
    merged, unmatched = merge_records(official, dblp, year)

    for rec in merged:
        rec["proceedings"] = {
            "conference": config["proceedings"],
            "publisher": config["publisher"],
            "year": year,
            "isbn": config["isbn"],
            "location": config["location"],
            "dates": config["dates"],
            "dblp_summary": proceedings_meta.get("proceedings_line", ""),
        }

    download_rows = build_download_report(args.root, merged, year)

    metadata_json = paths["metadata"] / f"aspdac{year}_papers.json"
    metadata_csv = paths["metadata"] / f"aspdac{year}_papers.csv"
    write_json(metadata_json, merged)
    write_csv(
        metadata_csv,
        merged,
        [
            "year",
            "paper_id",
            "session_id",
            "session_title",
            "talk_time",
            "title",
            "authors",
            "pages",
            "keywords",
            "abstract",
            "qec_relevance",
            "qec_similarity",
            "is_quantum_candidate",
            "publisher",
            "doi",
            "doi_url",
            "ee_url",
            "dblp_key",
            "dblp_url",
            "official_url",
            "in_dblp",
            "dblp_match_score",
        ],
    )
    write_json(paths["metadata"] / "dblp_records.json", dblp)
    write_json(paths["metadata"] / "dblp_unmatched.json", unmatched)
    write_csv(
        paths["logs"] / "download_report.csv",
        download_rows,
        ["collection", "paper_id", "title", "doi", "doi_url", "ee_url", "source_url", "download_status", "pdf_path", "failure_reason"],
    )
    write_quantum_candidates(paths, merged, download_rows, year)
    write_qec_briefs(paths, merged, year)
    write_summary(paths, merged, download_rows, year, unmatched)
    verify(paths, merged, download_rows, unmatched)

    print(
        json.dumps(
            {
                "year": year,
                "technical_records": len(merged),
                "quantum_candidates": sum(1 for row in merged if row.get("is_quantum_candidate")),
                "qec_core": sum(1 for row in merged if row.get("qec_relevance") == "QEC-simulator-core"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
