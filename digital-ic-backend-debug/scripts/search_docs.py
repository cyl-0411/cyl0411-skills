from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


TOOL_TAGS = {
    "innovus": {"innovus", "tool-usage", "pnr"},
    "icc2": {"icc2", "tool-usage", "pnr"},
    "icc": {"icc2", "tool-usage", "pnr"},
    "pt": {"primetime", "timing", "sta"},
    "primetime": {"primetime", "timing", "sta"},
    "starrc": {"starrc", "extraction"},
    "calibre": {"calibre", "physical-verification", "drc", "lvs"},
    "redhawk": {"redhawk", "ir-em", "power"},
    "tempus": {"tempus", "timing", "sta"},
}

SYMPTOM_TAGS = [
    (re.compile(r"\b(setup|hold|wns|tns|slack|timing|sta)\b", re.I), {"timing", "STA", "sta-signoff"}),
    (re.compile(r"\b(cts|ccopt|postcts|clock\s*tree|skew|latency|IMPCCOPT)\b", re.I), {"clock-tree", "Clock", "cts"}),
    (re.compile(r"\b(drc|lvs|rve|short|open|antenna|VIA\d|M\d\.|OD\.|PO\.)\b", re.I), {"physical-verification", "DRC", "LVS"}),
    (re.compile(r"\b(ir|irdrop|em|redhawk|power\s*em|signal\s*em|ploc)\b", re.I), {"ir-em", "IR-EM", "Power"}),
    (re.compile(r"\b(route|routing|nanoroute|ecoroute|detour|congestion|overflow|hotspot)\b", re.I), {"route", "PnR"}),
    (re.compile(r"\b(floorplan|macro|channel|blockage|region|fence|halo)\b", re.I), {"floorplan", "PnR"}),
    (re.compile(r"\b(powerplan|pg|stripe|ring|via pillar|globalnetconnect|derive\s*pg)\b", re.I), {"powerplan", "Power"}),
    (re.compile(r"\b(eco|post-mask|spare|repeater|buffer|upsize|swap)\b", re.I), {"eco", "ECO"}),
    (re.compile(r"\b(tcl|script|dbget|get_db|set_db)\b", re.I), {"tcl", "Tcl-Scripting", "tool-scripting"}),
]

CODE_RE = re.compile(r"\b[A-Z]{2,}[A-Z0-9]*[-.][A-Z0-9*_.:-]+(?:[-.][A-Z0-9*_.:-]+)*\b")
COMMAND_RE = re.compile(r"(?<![A-Za-z0-9_])(?:set|get|add|delete|remove|create|check|verify|report|eco|opt|route|place|ccopt|db|get_db|set_db|globalNetConnect|global|detail|refine|load|write|read|save|restore)[A-Za-z0-9_]*(?![A-Za-z0-9_])")
TOKEN_RE = re.compile(r"[A-Za-z0-9_.*:-]+|[\u4e00-\u9fff]{2,}")

COMMAND_PREFIXES = (
    "set",
    "get",
    "add",
    "delete",
    "remove",
    "create",
    "check",
    "verify",
    "report",
    "eco",
    "opt",
    "route",
    "place",
    "ccopt",
    "db",
    "global",
    "detail",
    "refine",
    "load",
    "write",
    "read",
    "save",
    "restore",
)

KNOWN_COMMAND_NAMES = {
    "ccopt_design",
    "checkRoute",
    "dbget",
    "detailRoute",
    "ecoRoute",
    "globalDetailRoute",
    "globalNetConnect",
    "globalRoute",
    "loadViolationReport",
    "optDesign",
    "placeDesign",
    "refinePlace",
    "report_clock_timing",
    "report_timing",
    "restoreDesign",
    "routeDesign",
    "setNanoRouteMode",
    "setRouteMode",
    "set_analysis_mode",
    "set_ccopt_mode",
}

COMMAND_STOPWORDS = {
    "add",
    "check",
    "create",
    "delete",
    "detail",
    "eco",
    "get",
    "global",
    "load",
    "opt",
    "place",
    "read",
    "remove",
    "report",
    "restore",
    "route",
    "routing",
    "save",
    "set",
    "setup",
    "write",
}


def norm(value: Any) -> str:
    return str(value or "").lower()


def norm_list(values: Any) -> set[str]:
    if not isinstance(values, list):
        return {norm(values)} if values else set()
    return {norm(item) for item in values if str(item).strip()}


def load_index(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_terms(query: str) -> tuple[list[str], list[str]]:
    strong = []
    for pattern in (CODE_RE, COMMAND_RE):
        for match in pattern.findall(query):
            if match not in strong:
                strong.append(match)

    tokens = []
    for token in TOKEN_RE.findall(query):
        token = token.strip()
        if len(token) < 2:
            continue
        if token not in tokens:
            tokens.append(token)
        token_l = token.lower()
        if (
            token_l.startswith(("set", "get", "add", "delete", "remove", "create", "check", "verify", "report", "eco", "ccopt"))
            or "_" in token
            or re.search(r"[a-z][A-Z]", token)
        ) and token not in strong:
            strong.append(token)
    return strong, tokens


def looks_like_command(value: str) -> bool:
    command = value.strip("`'\".,;:()[]{}")
    if not command:
        return False
    if command in KNOWN_COMMAND_NAMES:
        return True

    command_l = command.lower()
    known_l = {item.lower() for item in KNOWN_COMMAND_NAMES}
    if command_l in known_l or command_l in COMMAND_STOPWORDS:
        return command_l in known_l
    if len(command) < 4 or command.startswith("-"):
        return False

    prefix_match = command_l.startswith(tuple(prefix.lower() for prefix in COMMAND_PREFIXES))
    if "_" in command and prefix_match:
        return True
    if re.search(r"[a-z][A-Z]", command) and prefix_match:
        return True
    return False


def extract_candidate_commands(*texts: str, limit: int = 12) -> list[str]:
    candidates: list[str] = []
    for text in texts:
        for match in COMMAND_RE.findall(text or ""):
            command = match.strip("`'\".,;:()[]{}")
            if not looks_like_command(command):
                continue
            if command not in candidates:
                candidates.append(command)
            if len(candidates) >= limit:
                return candidates
    return candidates


def inferred_tags(query: str, tools: list[str]) -> set[str]:
    tags: set[str] = set()
    for tool in tools:
        tags.update(TOOL_TAGS.get(tool.lower(), set()))
    for regex, mapped in SYMPTOM_TAGS:
        if regex.search(query):
            tags.update(mapped)
    return {norm(tag) for tag in tags}


def passes_filters(doc: dict[str, Any], tags: set[str], flow: set[str], knowledge: set[str], tools: set[str]) -> bool:
    doc_tags = norm_list(doc.get("tags"))
    doc_flow = norm_list(doc.get("flow_stage"))
    doc_knowledge = norm_list(doc.get("knowledge_area"))
    hay = " ".join([norm(doc.get("title")), norm(doc.get("path")), norm(doc.get("source_path"))])

    if tags and not (tags & doc_tags):
        return False
    if flow and not (flow & doc_flow):
        return False
    if knowledge and not (knowledge & doc_knowledge):
        return False
    if tools:
        tool_match = False
        for tool in tools:
            tool_tags = TOOL_TAGS.get(tool, {tool})
            if {norm(tag) for tag in tool_tags} & (doc_tags | doc_knowledge | doc_flow):
                tool_match = True
            if tool in hay:
                tool_match = True
            if tool == "innovus" and doc.get("kind") == "innovus-flow":
                tool_match = True
        if not tool_match:
            return False
    return True


def find_snippet(text: str, terms: list[str], width: int = 280) -> str:
    text = re.sub(r"\s+", " ", html.unescape(text or "")).strip()
    if not text:
        return ""
    lower = text.lower()
    positions = [lower.find(term.lower()) for term in terms if term and lower.find(term.lower()) >= 0]
    pos = min(positions) if positions else 0
    start = max(0, pos - width // 3)
    end = min(len(text), start + width)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet


def score_doc(doc: dict[str, Any], query: str, strong: list[str], tokens: list[str], auto_tags: set[str]) -> tuple[float, list[str]]:
    title = norm(doc.get("title"))
    path = norm(doc.get("path"))
    source = norm(doc.get("source_path"))
    text = norm(doc.get("text"))
    tags = norm_list(doc.get("tags")) | norm_list(doc.get("flow_stage")) | norm_list(doc.get("knowledge_area"))
    matched: list[str] = []
    score = 0.0
    exact_title_hit = False

    query_lower = query.lower().strip()
    if query_lower and query_lower in title:
        score += 1200
        exact_title_hit = True
        matched.append(query)

    for term in strong:
        term_l = term.lower()
        if term_l in title:
            score += 1000
            exact_title_hit = True
            matched.append(term)
        if term_l in path or term_l in source:
            score += 300
            matched.append(term)
        if term_l in text:
            score += 220 + min(text.count(term_l), 5) * 20
            matched.append(term)

    for token in tokens:
        token_l = token.lower()
        if token_l in title:
            score += 260
            matched.append(token)
        if token_l in tags:
            score += 160
            matched.append(token)
        if token_l in path or token_l in source:
            score += 90
            matched.append(token)
        if token_l in text:
            score += 25 + min(text.count(token_l), 8) * 6
            matched.append(token)

    for tag in auto_tags:
        if tag in tags:
            score += 65
            matched.append(tag)

    kind = doc.get("kind")
    if kind == "innovus-flow" and (
        "innovus" in auto_tags
        or any(term.lower().startswith(("set", "add", "verify", "report", "ccopt")) for term in strong)
    ):
        score += 180
        if any(term.lower() in title or term.lower() in text for term in strong):
            score += 650
    if kind == "tag-index":
        score *= 0.55

    weak_flags = {"empty", "attachment_placeholder", "needs-review"}
    if not exact_title_hit and weak_flags & tags:
        score -= 120 if "empty" in tags else 70

    score += math.log1p(len(str(doc.get("text") or ""))) * 0.8
    unique_matched = []
    for item in matched:
        if item not in unique_matched:
            unique_matched.append(item)
    return score, unique_matched[:16]


def search(index: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    strong, tokens = extract_terms(args.query)
    tools = {tool.lower() for tool in args.tool}
    auto_tags = inferred_tags(args.query, list(tools))

    filter_tags = {norm(tag) for tag in args.tag}
    filter_flow = {norm(item) for item in args.flow_stage}
    filter_knowledge = {norm(item) for item in args.knowledge_area}

    docs = index.get("documents", [])
    filtered = [
        doc
        for doc in docs
        if passes_filters(doc, filter_tags, filter_flow, filter_knowledge, tools)
    ]
    candidates = filtered if filtered else docs

    results = []
    terms_for_snippet = strong + tokens
    for doc in candidates:
        score, matched = score_doc(doc, args.query, strong, tokens, auto_tags)
        if score <= 0 and not matched:
            continue
        snippet = find_snippet(str(doc.get("text", "")), terms_for_snippet)
        result = {
            "title": doc.get("title", ""),
            "path": doc.get("path", ""),
            "score": round(score, 2),
            "flow_stage": doc.get("flow_stage", []),
            "knowledge_area": doc.get("knowledge_area", []),
            "tags": doc.get("tags", []),
            "source_path": doc.get("source_path", ""),
            "kind": doc.get("kind", ""),
            "matched_terms": matched,
            "candidate_commands": extract_candidate_commands(args.query, str(doc.get("title", "")), snippet),
            "snippet": snippet,
        }
        results.append(result)

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[: args.top]


def emit_text(results: list[dict[str, Any]]) -> None:
    for idx, item in enumerate(results, 1):
        print(f"{idx}. {item['title']}")
        print(f"   path: {item['path']}")
        print(f"   score: {item['score']} kind: {item['kind']}")
        print(f"   flow_stage: {', '.join(item['flow_stage']) if item['flow_stage'] else '-'}")
        print(f"   knowledge_area: {', '.join(item['knowledge_area']) if item['knowledge_area'] else '-'}")
        print(f"   tags: {', '.join(item['tags']) if item['tags'] else '-'}")
        if item["source_path"]:
            print(f"   source_path: {item['source_path']}")
        print(f"   matched_terms: {', '.join(item['matched_terms']) if item['matched_terms'] else '-'}")
        if item.get("candidate_commands"):
            print(f"   candidate_commands: {', '.join(item['candidate_commands'])}")
        if item["snippet"]:
            print(f"   snippet: {item['snippet']}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the local IC backend document index.")
    parser.add_argument("--index", required=True, help="Path to JSON index built by build_index.py.")
    parser.add_argument("--query", required=True, help="Issue, error code, command, or symptom to search.")
    parser.add_argument("--tag", action="append", default=[], help="Restrict to a document tag. Repeatable.")
    parser.add_argument("--flow-stage", action="append", default=[], help="Restrict to a flow_stage value. Repeatable.")
    parser.add_argument("--knowledge-area", action="append", default=[], help="Restrict to a knowledge_area value. Repeatable.")
    parser.add_argument("--tool", action="append", default=[], help="Restrict/boost by tool name, e.g. innovus, calibre, redhawk.")
    parser.add_argument("--top", type=int, default=8, help="Number of results.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    index_path = Path(args.index)
    if not index_path.exists():
        print(f"error: index not found: {index_path}", file=sys.stderr)
        return 2

    results = search(load_index(index_path), args)
    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        emit_text(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
