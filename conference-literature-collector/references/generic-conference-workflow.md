# Generic Conference Workflow

## Project Layout

Use one task root. Multiple venues and years share the same normalized schema:

```text
<PROJECT_ROOT>/
  papers/
  metadata/collection.json
  metadata/papers.json
  metadata/papers.csv
  reports/
  logs/download_report.csv
  tools/
```

Do not derive the root from a fixed desktop location. For multi-venue tasks, use
distinct `collection` values or one child root per collection.

## Source Priority

1. Official conference program or proceedings for title, authors, session, paper
   ID, abstract, keywords, venue, and year.
2. DBLP/Crossref for DOI, pages, bibliographic identifiers, and missing authors.
3. Publisher pages for electronic-edition and PDF URLs.
4. Open repositories or author/institution pages for legal full-text alternatives.

Keep provenance URLs. Do not silently replace an official field with a fuzzy match.

## Normalized Record

Core fields are `collection`, `conference`, `venue_slug`, `year`, `paper_id`,
`title`, `authors`, `abstract`, `keywords`, `session_id`, `session_title`, `pages`,
`publisher`, `doi`, `doi_url`, `ee_url`, `official_url`, and `citation_pdf_url`.

`collection` defaults to `<venue_slug><year>` but can be supplied explicitly.
`paper_id` may fall back to DOI or a stable generated ID. Never merge records from
different collections by paper ID alone.

```powershell
python -X utf8 "<SKILL_DIR>\scripts\normalize_conference_metadata.py" `
  --input "<RAW_JSON_OR_CSV>" --root "<PROJECT_ROOT>" `
  --conference "<CONFERENCE_NAME>" --year <YEAR>
```

## Topic Screening

Topic screening is optional and user-defined. Record the query, inclusion criteria,
exclusion criteria, and evidence fields in `metadata/collection.json`; write results
to `reports/topic_candidates.md`. Domain references are profiles, not global filters.

## Adapter Rule

A conference-specific adapter may parse a known official site, but its output must
conform to this schema. Unsupported years or changed page structures fall back to
generic web collection plus normalization rather than being forced through a preset.
