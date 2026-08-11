from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8", "utf-8-sig"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(
        f"{path} is not valid UTF-8/UTF-8-SIG. "
        "Fix the source document encoding before rebuilding the index."
    ) from last_error


def parse_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    meta: dict[str, object] = {}
    current_key: str | None = None
    for raw in match.group(1).splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") and current_key:
            meta.setdefault(current_key, [])
            value = parse_scalar(stripped[2:])
            if isinstance(meta[current_key], list):
                meta[current_key].append(value)
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key
            if value:
                if value.startswith("[") and value.endswith("]"):
                    items = [parse_scalar(item) for item in value[1:-1].split(",") if item.strip()]
                    meta[key] = items
                else:
                    meta[key] = parse_scalar(value)
            else:
                meta[key] = []
    return meta, text[match.end() :]


def as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]


def strip_markdown(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`{1,3}([^`]*)`{1,3}", r"\1", text)
    text = re.sub(r"^[#>*\-\s]+", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def first_heading(body: str, fallback: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def make_doc(repo_root: Path, path: Path, kind: str, include_frontmatter: bool = True) -> dict[str, object]:
    raw = read_text(path)
    meta, body = parse_frontmatter(raw) if include_frontmatter else ({}, raw)
    rel = path.relative_to(repo_root).as_posix()
    title = str(meta.get("title") or first_heading(body, path.stem))
    flow_stage = as_list(meta.get("flow_stage"))
    knowledge_area = as_list(meta.get("knowledge_area"))
    tags = as_list(meta.get("tags"))
    curation_status = str(meta.get("curation_status") or "")
    source_path = str(meta.get("source_path") or "")
    clean = strip_markdown(body)
    return {
        "id": rel,
        "kind": kind,
        "title": title,
        "path": rel,
        "source_path": source_path,
        "flow_stage": flow_stage,
        "knowledge_area": knowledge_area,
        "tags": tags,
        "curation_status": curation_status,
        "text": clean,
    }


def iter_docs(repo_root: Path, include_tags: bool, include_innovus: bool) -> list[dict[str, object]]:
    documents: list[dict[str, object]] = []

    articles = repo_root / "docs" / "articles"
    if articles.exists():
        for path in sorted(articles.glob("*.md")):
            if path.name.lower() == "index.md":
                continue
            documents.append(make_doc(repo_root, path, "article"))

    if include_tags:
        tag_root = repo_root / "docs" / "tags"
        if tag_root.exists():
            for path in sorted(tag_root.glob("*.md")):
                documents.append(make_doc(repo_root, path, "tag-index", include_frontmatter=False))

    if include_innovus:
        innovus_root = repo_root / "innovus" / "docs" / "innovus_flow_commands"
        if innovus_root.exists():
            for path in sorted(innovus_root.glob("*.md")):
                documents.append(make_doc(repo_root, path, "innovus-flow", include_frontmatter=False))

    return documents


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Build a local IC backend document search index.")
    parser.add_argument("--repo-root", default=".", help="Path to IC_Backend_WIKI root.")
    parser.add_argument("--out", required=True, help="Output JSON index path.")
    parser.add_argument("--include-tags", action="store_true", help="Index docs/tags pages as secondary references.")
    parser.add_argument("--include-innovus", action="store_true", help="Index Innovus flow command notes.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not (repo_root / "docs").exists():
        print(f"error: repo root does not contain docs/: {repo_root}", file=sys.stderr)
        return 2

    documents = iter_docs(repo_root, include_tags=args.include_tags, include_innovus=args.include_innovus)
    index = {
        "version": 1,
        "repo_root": str(repo_root),
        "built_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "documents": documents,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"indexed {len(documents)} documents -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
