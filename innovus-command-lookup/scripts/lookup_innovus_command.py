from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def is_probable_command_heading(lines: list[str], idx: int) -> bool:
    cur = normalize_line(lines[idx])
    nxt = normalize_line(lines[idx + 1]) if idx + 1 < len(lines) else ""
    if not cur or " " in cur or len(cur) < 2:
        return False
    return cur in nxt


def is_heading(lines: list[str], idx: int, command: str) -> bool:
    if idx < 0 or idx + 1 >= len(lines):
        return False
    return normalize_line(lines[idx]) == command and command in normalize_line(lines[idx + 1])


def find_heading(lines: list[str], command: str) -> int:
    for i in range(len(lines) - 1):
        if is_heading(lines, i, command):
            return i
    raise ValueError(f"Command heading not found: {command}")


def find_next_heading(lines: list[str], start_idx: int) -> int:
    for i in range(start_idx + 1, len(lines) - 1):
        if lines[i].strip() and is_probable_command_heading(lines, i):
            return i
    return len(lines)


def clean_block(block: str) -> str:
    cleaned: list[str] = []
    for raw in block.splitlines():
        line = raw.replace("\u200b", "").rstrip()
        stripped = line.strip()
        if not stripped:
            cleaned.append("")
            continue
        if "Last Updated in July 2017" in line:
            continue
        if stripped == "Innovus Text Command Reference":
            continue
        if stripped.endswith("Commands") and "Reference" not in stripped:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def locate_manual(root: Path) -> Path:
    candidates = [
        root / "innovus_manual.txt",
        root / "docs" / "innovus_manual.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = list(root.rglob("innovus_manual.txt"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Cannot find innovus_manual.txt under {root}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Extract one Innovus command entry from innovus_manual.txt")
    parser.add_argument("root", help="Project directory containing innovus_manual.txt")
    parser.add_argument("command", help="Exact Innovus command name")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manual = locate_manual(root)
    lines = manual.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = find_heading(lines, args.command)
    end = find_next_heading(lines, start)
    print(clean_block("\n".join(lines[start:end])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
