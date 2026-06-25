#!/usr/bin/env python3
"""Build a cross-year ASP-DAC 2023-2025 QEC related-work summary."""

from __future__ import annotations

import json
from pathlib import Path


YEAR_ROOTS = {
    2025: Path(r"C:\Users\CYL04\Desktop\ASP_DAC_2025"),
    2024: Path(r"C:\Users\CYL04\Desktop\ASP_DAC_2024"),
    2023: Path(r"C:\Users\CYL04\Desktop\ASP_DAC_2023"),
}

OUT_FILE = Path(r"C:\Users\CYL04\Desktop\ASP_DAC_2026\reports\qec_simulator_related_work_2023_2025.md")


def load_candidates(year: int) -> list[dict]:
    path = YEAR_ROOTS[year] / "metadata" / f"aspdac{year}_papers.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [row for row in rows if row.get("is_quantum_candidate")]


def note_for(row: dict) -> tuple[str, str]:
    hay = f"{row.get('title', '')} {row.get('abstract', '')}".lower()
    if row.get("qec_relevance") == "QEC-simulator-core":
        return (
            "high",
            "Directly useful for decoder architecture, syndrome flow, or fault-tolerant execution modeling.",
        )
    if "simulation" in hay:
        return (
            "medium",
            "Useful as a simulator kernel or baseline for quantum-circuit workload modeling, though not a full QEC loop by itself.",
        )
    if "routing" in hay or "oracle synthesis" in hay or "measurements" in hay:
        return (
            "medium",
            "Relevant to front-end compilation, measurement representation, or back-end-aware workload construction.",
        )
    return (
        "low",
        "Quantum-adjacent context; more peripheral to a QEC decoder/architecture simulator.",
    )


def main() -> int:
    rows: list[dict] = []
    for year in sorted(YEAR_ROOTS, reverse=True):
        rows.extend(load_candidates(year))

    lines = [
        "# ASP-DAC 2023-2025 QEC Simulator Related Work",
        "",
        "## Overview",
        "",
        "This matrix focuses on papers from ASP-DAC 2023, 2024, and 2025 that are closest to QEC decoder or architecture simulator design. The ranking is based on official abstracts and metadata, then translated into how much each paper can inform decoder modeling, timing simulation, workload generation, or control-hardware assumptions.",
        "",
        "## Paper Matrix",
        "",
        "| Year | ID | Paper | Relevance bucket | Similarity | Why it matters |",
        "|---|---|---|---|---|---|",
    ]
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            {"QEC-simulator-core": 0, "QEC-adjacent": 1, "quantum-non-QEC": 2}.get(row["qec_relevance"], 9),
            -row["year"],
            row["paper_id"],
        ),
    )
    for row in sorted_rows:
        similarity, note = note_for(row)
        doi = row.get("doi_url") or row.get("official_url") or ""
        paper = f"[{row['title']}]({doi})" if doi else row["title"]
        lines.append(
            f"| {row['year']} | {row['paper_id']} | {paper} | {row['qec_relevance']} | {similarity} | {note} |"
        )

    lines.extend(
        [
            "",
            "## Most Relevant Themes",
            "",
            "- **Decoder-centric core**: `Software Tools for Decoding Quantum Low-Density Parity-Check Codes` and `WIT-Greedy` are the closest papers to the decoder back-end of a QEC simulator.",
            "- **Simulation kernel references**: `Graph Partitioning Approach for Fast Quantum Circuit Simulation` and `PIMutation` are useful for workload execution and state-evolution modeling, even though they are not decoder-system papers.",
            "- **Compiler / mapping adjacency**: `CTQr`, `Back-end-aware Fault-tolerant Quantum Oracle Synthesis`, and measurement-decision-diagram work matter because a realistic simulator needs compiler-generated circuits and measurement representations that reflect hardware constraints.",
            "- **Control-hardware assumptions**: `Towards Multiphase Clocking in Single-Flux Quantum Systems` is more peripheral, but can inform timing and control-electronics assumptions around quantum-system deployment.",
            "",
            "## Design Takeaways for a QEC Simulator",
            "",
            "- The simulator should treat the decoder as a pluggable module with explicit latency, memory, and scheduling interfaces.",
            "- It should separate **circuit evolution / syndrome generation** from **decoder execution / correction feedback**, so simulation and decoder architecture studies can be mixed and matched.",
            "- Front-end circuit generation matters: routing, synthesis, and measurement representation papers suggest the simulator needs a compiler-aware input format rather than only raw parity-check matrices.",
            "- A useful comparison framework should normalize throughput, per-round latency, and problem size across algorithmic decoders and hardware-minded implementations.",
            "",
            "## Research Gaps",
            "",
            "- Across these three ASP-DAC years, there are only a few papers that directly touch QEC decoding hardware or system design; most quantum papers remain compiler, verification, or simulation adjacent.",
            "- There is still a clear opening for an end-to-end simulator that joins syndrome generation, decoder latency modeling, architecture constraints, and workload/resource estimation in one environment.",
            "",
        ]
    )
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_FILE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
