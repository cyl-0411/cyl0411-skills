# PPT Master Troubleshooting

## Python command is not found or imports fail

Resolve `<PPT_PYTHON>` once as described in `SKILL.md`. On Codex Desktop, prefer
the bundled workspace Python. Verify it with:

```text
"<PPT_PYTHON>" -X utf8 -c "import pptx, lxml, PIL"
```

Do not assume a platform-specific Python alias exists. Install `requirements.txt` into the
selected interpreter only when the bundled runtime is unavailable or incomplete.
Use `-X utf8` for every command; otherwise Unicode quality-check diagnostics can
fail in a legacy Windows console.

## Layout overflow

Run `svg_quality_checker.py` against `svg_output/`, fix every error on the
reported page, and rerun the checker before finalization. Avoid shrinking all
text globally; repair the offending layout or reduce local content density.

## Blank or broken images

Confirm each resource listed in `spec_lock.md` exists under the project `images/`
directory. Browser preview may not display EMF/WMF assets; verify those in the
exported PPTX. For bitmap assets, check the generated SVG reference before running
`finalize_svg.py`.

More command-specific checks are in
[`scripts/docs/troubleshooting.md`](../scripts/docs/troubleshooting.md).

## Export errors

Run the pipeline one command at a time: `total_md_split.py`, `finalize_svg.py`,
then `svg_to_pptx.py`. Keep the first failing command's full output. Validate the
project with `project_manager.py validate <project_path>` before retrying.

## Optional tools are missing

Pandoc, LibreOffice, Inkscape, FFmpeg, image providers, and narration providers
are feature-specific dependencies. Their absence does not block the basic
Markdown/SVG/PPTX pipeline; install or configure them only for the feature that
needs them.
