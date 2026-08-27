---
name: conference-literature-collector
description: >-
  Collect proceedings literature for any named conference, workshop, symposium, venue, or year range. Build normalized metadata from official programs and bibliographic sources, download authorized PDFs through an isolated task browser, record missing papers, apply optional topic screening, and produce local archives and research reports. Use for single- or multi-venue conference paper collection, full-text acquisition, metadata cleanup, topic-focused screening, and year-organized proceedings libraries.
---

# Conference Literature Collector

Use this skill for conference-scale literature collection where the output is a
local paper library plus normalized metadata, download logs, optional topic
screening, and research notes. Never assume a particular conference, year range,
topic, publisher, or desktop path.

## Required Scope

Resolve the conference or venue name, year or year range, project root, known
official sources, optional topic criteria, and requested outputs from the request.
Multiple venues are allowed. If a value cannot be discovered safely, use a
task-local project root and record the assumption in `metadata/collection.json`.

## Safety First

Before any publisher or logged-in browser download, use the isolated-browser workflow in [references/browser-proxy-isolation.md](references/browser-proxy-isolation.md).

Never change global proxy state for this skill:

- Do not edit Windows system proxy, WinHTTP proxy, browser global settings, or registry proxy keys.
- Do not edit the user's global `$CODEX_HOME/.env` for proxy setup.
- Do not edit `web-access/config.env` for paper downloading.
- Do not attach proxy settings to the user's daily browser process.

The default is a hidden Edge or Chrome instance with a task-specific user data directory, task-specific CDP port, and `--proxy-server` passed only to that process.

## Workflow

Read [references/generic-conference-workflow.md](references/generic-conference-workflow.md), then:

1. Create a project root with `papers/`, `metadata/`, `reports/`, `logs/`, and `tools/`.
2. Collect metadata from official program/proceedings sources first, then enrich with DBLP, DOI, Crossref, or publisher pages without overwriting stronger official fields with guesses.
3. Normalize raw JSON or CSV through `scripts/normalize_conference_metadata.py` to create the full paper index.
4. Download PDFs only through authorized routes: publisher access with the user's institution or logged-in isolated browser, open versions such as arXiv/author pages/institutional repositories/Unpaywall, and no paywall bypassing or credential extraction.
5. Record every paper in `logs/download_report.csv` with status, source URL, local path, and failure reason.
6. Apply topic screening only when requested. Write `reports/topic_candidates.md`; [references/qec-screening.md](references/qec-screening.md) is one optional profile, not the default.
7. Generate only the requested candidate, related-work, archive, and missing-paper reports.

Conference-specific parsers are adapters. Use one only when its venue and supported
years match the task. For the optional ASP-DAC preset, read
[references/aspdac-workflow.md](references/aspdac-workflow.md).

## Bundled Scripts

- `scripts/normalize_conference_metadata.py`: normalize arbitrary conference JSON or CSV into the standard metadata and initial download log.
- `scripts/publisher_cdp_downloader_bg.js`: download ACM, IEEE, or publisher-exposed PDFs through a CDP browser; configure metadata, logs, and papers paths with environment variables.
- `scripts/start_isolated_browser.ps1`: start a hidden per-task browser with isolated proxy settings.
- `scripts/stop_isolated_browser.ps1`: stop only the browser process recorded by the isolated session file.
- `scripts/aspdac_multiyear_pipeline.py` and `build_asp_dac_archive*.mjs`: optional ASP-DAC preset tools, not generic entry points.
- `scripts/combine_collections.py`: combine normalized metadata from any named collections into one Markdown matrix.
- `scripts/generate_topic_brief.py`: generate an optional topic brief from metadata plus a user-supplied JSON configuration; no venue, year, paper ID, or topic is built in.

## Handoff To Other Skills

- Use `web-access` for general web browsing and page inspection when a task does not need a dedicated proxy-isolated publisher browser.
- Use `read-qec-paper` only after optional QEC screening identifies or downloads a paper that needs single-paper deep reading.
- Use spreadsheet or document skills only for final artifact formatting when the requested output is `.xlsx`, `.docx`, or `.pptx`.

## Output Contract

Every normalized collection produces:

- `metadata/collection.json`
- `metadata/papers.json`
- `metadata/papers.csv`
- `logs/download_report.csv`

PDF tasks also produce `papers/*.pdf`. Screening and report files are conditional
on the requested topic and output format; no QEC-specific report is mandatory.
