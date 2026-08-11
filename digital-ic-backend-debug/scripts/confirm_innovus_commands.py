from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def locate_manual(repo_root: Path) -> Path:
    candidates = [
        repo_root / "innovus" / "innovus_manual.txt",
        repo_root / "innovus_manual.txt",
        repo_root / "docs" / "innovus_manual.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = list(repo_root.rglob("innovus_manual.txt"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Cannot find innovus_manual.txt under {repo_root}")


def locate_repo_extractor(repo_root: Path) -> Path | None:
    candidate = repo_root / "innovus" / "tools" / "extract_innovus_command.py"
    return candidate if candidate.exists() else None


def is_heading(lines: list[str], idx: int, command: str) -> bool:
    if idx < 0 or idx + 1 >= len(lines):
        return False
    return normalize_line(lines[idx]) == command and command in normalize_line(lines[idx + 1])


def is_probable_command_heading(lines: list[str], idx: int) -> bool:
    current = normalize_line(lines[idx])
    nxt = normalize_line(lines[idx + 1]) if idx + 1 < len(lines) else ""
    if not current or " " in current or len(current) < 2:
        return False
    return current in nxt


def find_heading(lines: list[str], command: str) -> int:
    for idx in range(len(lines) - 1):
        if is_heading(lines, idx, command):
            return idx
    raise ValueError(f"Command heading not found: {command}")


def find_next_heading(lines: list[str], start_idx: int) -> int:
    for idx in range(start_idx + 1, len(lines) - 1):
        if lines[idx].strip() and is_probable_command_heading(lines, idx):
            return idx
    return len(lines)


def clean_block(block: str) -> str:
    cleaned: list[str] = []
    for raw in block.splitlines():
        line = raw.replace("\u200b", "").rstrip()
        stripped = line.strip()
        if "Last Updated in July 2017" in line:
            continue
        if stripped == "Innovus Text Command Reference":
            continue
        if "Commands and Global Variables" in stripped:
            continue
        if stripped.endswith("Commands") and "Reference" not in stripped:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def extract_with_repo_tool(extractor: Path, manual: Path, command: str) -> str | None:
    try:
        completed = subprocess.run(
            [sys.executable, str(extractor), str(manual), command],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return clean_block(completed.stdout)


def extract_with_internal_parser(manual: Path, command: str) -> str:
    lines = manual.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = find_heading(lines, command)
    end = find_next_heading(lines, start)
    return clean_block("\n".join(lines[start:end]))


def is_syntax_line(line: str, previous: str) -> bool:
    stripped = line.strip()
    prev = previous.rstrip()
    if not stripped:
        return False
    if stripped.startswith(("[", "]", "-", "{", "|")):
        return True
    if prev.endswith(("|", "{", "[", "\\")):
        return True
    if prev.count("[") > prev.count("]"):
        return True
    if re.match(r"^[A-Za-z0-9_{}|:.,\" ]+\]?$", stripped) and prev.endswith("|"):
        return True
    return False


def split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections = {"syntax": [], "summary": [], "parameters": [], "examples": []}
    state = "syntax"
    syntax_seen = False
    previous = ""

    for raw in lines[2:]:
        stripped = raw.strip()
        lower = stripped.lower()
        if lower == "parameters":
            state = "parameters"
            previous = raw
            continue
        if lower == "examples":
            state = "examples"
            previous = raw
            continue
        if lower.startswith("related topic"):
            break

        if state == "syntax":
            if is_syntax_line(raw, previous):
                sections["syntax"].append(stripped)
                syntax_seen = True
                previous = raw
                continue
            if syntax_seen and stripped:
                state = "summary"

        if state == "summary":
            if stripped:
                sections["summary"].append(stripped)
        elif state == "parameters":
            if stripped:
                sections["parameters"].append(raw.rstrip())
        elif state == "examples":
            if stripped:
                sections["examples"].append(raw.rstrip())
        previous = raw

    return sections


def compact_summary(lines: list[str], max_chars: int = 700) -> str:
    text = re.sub(r"\s+", " ", " ".join(lines)).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def extract_options(text: str, limit: int = 80) -> list[str]:
    options: list[str] = []
    for match in re.findall(r"(?<!\w)-[A-Za-z][A-Za-z0-9_]*", text):
        if match not in options:
            options.append(match)
        if len(options) >= limit:
            break
    return options


def extract_examples(lines: list[str], command: str, limit: int = 8) -> list[str]:
    examples: list[str] = []
    command_start = re.compile(r"^(set|get|report|check|verify|eco|route|global|detail|opt|ccopt|load|add|delete|remove|create|refine|place|restore)[A-Za-z0-9_]*\b")
    for raw in lines:
        stripped = normalize_line(raw)
        if not stripped:
            continue
        if command_start.match(stripped):
            examples.append(stripped)
        if len(examples) >= limit:
            break
    return examples


def parse_entry(command: str, block: str, manual: Path, source: str) -> dict[str, Any]:
    lines = block.splitlines()
    sections = split_sections(lines)
    syntax = "\n".join(sections["syntax"]).strip()
    syntax_text = "\n".join(sections["syntax"])
    return {
        "command": command,
        "manual_found": True,
        "syntax": syntax,
        "summary": compact_summary(sections["summary"]),
        "key_options": extract_options(syntax_text),
        "examples": extract_examples(sections["examples"], command),
        "source_path": manual.as_posix(),
        "source": source,
        "warnings": [
            "Manual source is the local Innovus Text Command Reference; verify version-sensitive defaults against the user's installed Innovus build."
        ],
    }


def confirm_command(repo_root: Path, command: str) -> dict[str, Any]:
    manual = locate_manual(repo_root)
    extractor = locate_repo_extractor(repo_root)
    block = extract_with_repo_tool(extractor, manual, command) if extractor else None
    source = "repo-extractor" if block else "internal-parser"
    try:
        if not block:
            block = extract_with_internal_parser(manual, command)
        return parse_entry(command, block, manual, source)
    except Exception as exc:  # noqa: BLE001 - CLI should report structured failure for any parser issue.
        return {
            "command": command,
            "manual_found": False,
            "syntax": "",
            "summary": "",
            "key_options": [],
            "examples": [],
            "source_path": manual.as_posix(),
            "source": source,
            "warnings": [
                f"{exc}",
                "Do not present this command as manual-confirmed. It may be a Tcl helper, db query shortcut, project proc, or a command absent from this manual.",
            ],
        }


def commands_from_search_json(path: Path) -> list[str]:
    raw = path.read_bytes()
    text = ""
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if not text:
        text = raw.decode("utf-8", errors="replace")
    data = json.loads(text)
    commands: list[str] = []
    items = data if isinstance(data, list) else data.get("results", [])
    for item in items:
        for command in item.get("candidate_commands", []):
            if command not in commands:
                commands.append(command)
    return commands


def emit_text(results: list[dict[str, Any]]) -> None:
    for item in results:
        status = "手册确认" if item["manual_found"] else "未在手册中确认"
        print(f"{item['command']} - {status}")
        print(f"  source_path: {item['source_path']}")
        if item["syntax"]:
            print("  syntax:")
            for line in item["syntax"].splitlines():
                print(f"    {line}")
        if item["key_options"]:
            print(f"  key_options: {', '.join(item['key_options'])}")
        if item["summary"]:
            print(f"  summary: {item['summary']}")
        if item["examples"]:
            print("  examples:")
            for example in item["examples"]:
                print(f"    {example}")
        if item["warnings"]:
            print("  warnings:")
            for warning in item["warnings"]:
                print(f"    {warning}")
        print()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Confirm Innovus command syntax from local innovus_manual.txt.")
    parser.add_argument("--repo-root", default=".", help="Path to IC_Backend_WIKI root.")
    parser.add_argument("--command", action="append", default=[], help="Exact Innovus command name. Repeatable.")
    parser.add_argument("--from-search-json", help="Read candidate_commands from a search_docs.py JSON result file.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    commands = list(args.command)
    if args.from_search_json:
        for command in commands_from_search_json(Path(args.from_search_json)):
            if command not in commands:
                commands.append(command)
    if not commands:
        print("error: provide at least one --command or --from-search-json", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root).resolve()
    try:
        results = [confirm_command(repo_root, command) for command in commands]
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        emit_text(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
