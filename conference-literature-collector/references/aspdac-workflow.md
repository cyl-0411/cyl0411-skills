# ASP-DAC Workflow

Use this optional preset only for ASP-DAC collection and archive tasks. The bundled
metadata parser currently supports 2023-2025; other years must use the generic
workflow unless the adapter is extended and tested.

## Directory Layout

Create or use one root per year:

```text
<PROJECT_ROOT>/
  papers/
  metadata/
  reports/
  logs/
  tools/
```

For a combined desktop archive, use:

```text
ASP-DAC/
  2023/
  2024/
  2025/
  2026/
  missing_papers.xlsx
  QEC/
    2023/
    2024/
    2025/
    2026/
    README.md
```

## Metadata

Prefer official ASP-DAC program pages for session IDs, titles, authors, abstracts, and keywords. Enrich from DBLP for DOI, pages, BibTeX/RIS, publisher, proceedings title, ISBN, and venue metadata.

Use:

```powershell
python -X utf8 "<SKILL_DIR>\scripts\aspdac_multiyear_pipeline.py" --year 2025 --root "<PROJECT_ROOT>"
```

For any unsupported year, collect official metadata through the generic workflow,
then normalize it to `metadata/papers.json` and `metadata/papers.csv`.

## PDF Download

Start the isolated browser first. Then run:

```powershell
$session = Get-Content ".\logs\browser_session.json" | ConvertFrom-Json
$env:CDP_PORT = [string]$session.cdp_port
$env:METADATA_FILE = "metadata\papers.json"
$env:DOWNLOAD_LOG = "logs\download_report.csv"
node ".\skills\conference-literature-collector\scripts\publisher_cdp_downloader_bg.js"
```

Use `ONLY_IDS`, `MAX`, and `START` for controlled retries. Keep every failed paper in the download log with a failure reason.

## Archive

After yearly folders are populated, build the combined archive:

```powershell
node ".\skills\conference-literature-collector\scripts\build_asp_dac_archive_dry_run.mjs" # safe preview
node ".\skills\conference-literature-collector\scripts\build_asp_dac_archive.mjs" # real archive build
```

Do not include external `related__*.pdf` files in annual ASP-DAC folders. Copy them only when the user explicitly asks for external related work.
