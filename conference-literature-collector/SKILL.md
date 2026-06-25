---
name: conference-literature-collector
description: >-
  Collect conference proceedings literature end to end: scrape official program and DBLP/Crossref metadata, download ACM/IEEE PDFs through an isolated per-task browser proxy, record missing papers, screen quantum/QEC candidates, archive yearly PDFs, and produce Chinese research reports. Use when the user asks to collect ASP-DAC/DAC/ICCAD/DATE or similar conference papers, download full texts with local institutional access, organize missing-paper spreadsheets, or find QEC/quantum simulator related work.
---

# Conference Literature Collector

Use this skill for conference-scale literature collection where the output is a local paper library plus metadata, download logs, candidate screening, and related-work notes.

## Safety First

Before any publisher or logged-in browser download, use the isolated-browser workflow in [references/browser-proxy-isolation.md](references/browser-proxy-isolation.md).

Never change global proxy state for this skill:

- Do not edit Windows system proxy, WinHTTP proxy, browser global settings, or registry proxy keys.
- Do not edit `C:\Users\CYL04\.codex\.env` for proxy setup.
- Do not edit `web-access/config.env` for paper downloading.
- Do not attach proxy settings to the user's daily browser process.

The default is a hidden Edge or Chrome instance with a task-specific user data directory, task-specific CDP port, and `--proxy-server` passed only to that process.

## Workflow

1. Create a project root with `papers/`, `metadata/`, `reports/`, `logs/`, and `tools/`.
2. Collect metadata from the official conference program first, then enrich with DBLP, DOI, ACM/IEEE, Crossref, or publisher pages.
3. Write a full paper index to `metadata/papers.json` and `metadata/papers.csv`.
4. Download PDFs only through authorized routes: publisher access with the user's institution or logged-in isolated browser, open versions such as arXiv/author pages/institutional repositories/Unpaywall, and no paywall bypassing or credential extraction.
5. Record every paper in `logs/download_report.csv` with status, source URL, local path, and failure reason.
6. Screen quantum/QEC candidates with [references/qec-screening.md](references/qec-screening.md).
7. Generate reports for candidates, related work, archive layout, and missing-paper summaries.

For ASP-DAC 2023-2026, use [references/aspdac-workflow.md](references/aspdac-workflow.md) and the bundled scripts directly.

## Bundled Scripts

- `scripts/aspdac_multiyear_pipeline.py`: collect ASP-DAC 2023-2025 metadata and QEC candidate reports.
- `scripts/publisher_cdp_downloader_bg.js`: download ACM/IEEE PDFs through a CDP browser, using `CDP_PORT`, `METADATA_FILE`, `ONLY_IDS`, `MAX`, and related environment variables.
- `scripts/generate_qec_brief.py`: generate structured QEC paper briefs from local metadata and extracted text.
- `scripts/combine_qec_years.py`: combine yearly QEC candidate outputs.
- `scripts/build_asp_dac_archive.mjs`: build the desktop `ASP-DAC` archive, missing workbook, and QEC copy set.
- `scripts/start_isolated_browser.ps1`: start a hidden per-task browser with isolated proxy settings.
- `scripts/stop_isolated_browser.ps1`: stop only the browser process recorded by the isolated session file.

## Handoff To Other Skills

- Use `web-access` for general web browsing and page inspection when a task does not need a dedicated proxy-isolated publisher browser.
- Use `read-qec-paper` after this skill identifies or downloads a QEC paper that needs single-paper deep reading.
- Use spreadsheet or document skills only for final artifact formatting when the requested output is `.xlsx`, `.docx`, or `.pptx`.

## Output Contract

For a full collection task, produce:

- `metadata/papers.json`
- `metadata/papers.csv`
- `logs/download_report.csv`
- `reports/quantum_candidates.md`
- `reports/qec_simulator_related_work.md`
- `papers/*.pdf`

For archive tasks, produce a year-organized PDF directory, a missing-paper workbook, and a `QEC/README.md` summary that marks missing full text explicitly.

