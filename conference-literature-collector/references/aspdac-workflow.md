# ASP-DAC Workflow

Use this reference for ASP-DAC 2023-2026 style collection and archive tasks.

## Directory Layout

Create or use one root per year:

```text
ASP_DAC_20xx/
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
python ".\skills\conference-literature-collector\scripts\aspdac_multiyear_pipeline.py" --year 2025 --root "C:\Users\CYL04\Desktop\ASP_DAC_2025"
```

For ASP-DAC 2026, use the already collected metadata format if present; otherwise follow the same schema and write `metadata/papers.json` and `metadata/papers.csv`.

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

