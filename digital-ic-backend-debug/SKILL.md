---
name: digital-ic-backend-debug
description: Diagnose digital IC backend/PnR issues using local wiki, flow notes, and manuals. Use for timing, CTS, routing, floorplan, power, IR/EM, DRC/LVS, ECO, tool errors, or Tcl failures; use innovus-command-lookup for one named command's syntax.
---

# Digital IC Backend Debug

Use this skill to turn a backend issue report into an evidence-backed diagnostic answer. Search the local Wiki first, confirm any concrete Innovus command against the local manual, cite the documents used, and separate document-supported conclusions from inference.

## Quick Start

Resolve paths once before running a helper. `<BACKEND_DEBUG_DIR>` is the
directory containing this `SKILL.md`; replace it with the loader-provided
absolute path. Resolve `<IC_PYTHON>` to a real Python interpreter and require
`"<IC_PYTHON>" -X utf8 -c "import sys"` to pass.

Resolve the Wiki root in this order: an explicit user path,
`IC_BACKEND_ROOT`, the current directory when it contains `source_map.csv` or
`innovus/innovus_manual.txt`, then the platform Desktop `IC-Backend` folder.
Verify the selected root before use; never reuse a username or Desktop path
copied from an example.

```powershell
$skillRoot = (Resolve-Path -LiteralPath '<BACKEND_DEBUG_DIR>').Path
$wikiCandidates = @(
  $env:IC_BACKEND_ROOT,
  (Get-Location).Path,
  (Join-Path ([Environment]::GetFolderPath('Desktop')) 'IC-Backend')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$wikiRoot = $wikiCandidates | Where-Object {
  (Test-Path -LiteralPath (Join-Path $_ 'source_map.csv')) -or
  (Test-Path -LiteralPath (Join-Path $_ 'innovus\innovus_manual.txt'))
} | Select-Object -First 1
if (-not $wikiRoot) { throw 'IC Backend Wiki root was not found; provide it explicitly or set IC_BACKEND_ROOT.' }
$wikiRoot = (Resolve-Path -LiteralPath $wikiRoot).Path
$indexPath = Join-Path $wikiRoot '.codex\ic_backend_doc_index.json'
```

If the index is missing or stale, build it:

```powershell
& '<IC_PYTHON>' -X utf8 (Join-Path $skillRoot 'scripts\build_index.py') --repo-root $wikiRoot --out $indexPath --include-tags --include-innovus
```

Encoding note: the Wiki markdown and `source_map.csv` are UTF-8. If Chinese looks garbled in a Windows shell, check the shell or capture path before assuming the JSON bytes are broken. The builder now reads source files as strict UTF-8/UTF-8-SIG and writes UTF-8 JSON, so a real encoding problem fails fast instead of silently producing damaged metadata.

Search it:

```powershell
& '<IC_PYTHON>' -X utf8 (Join-Path $skillRoot 'scripts\search_docs.py') --index $indexPath --query "postCTS timing突然变差" --top 8
```

Confirm Innovus commands before recommending them:

```powershell
& '<IC_PYTHON>' -X utf8 (Join-Path $skillRoot 'scripts\confirm_innovus_commands.py') --repo-root $wikiRoot --command setNanoRouteMode --command ecoRoute --format json
```

If another copy of the Wiki is active, pass that path as `--repo-root` and write the index inside that workspace.

## Diagnostic Workflow

1. Extract strong signals from the user request:
   - Tool: Innovus, ICC2, PT/PrimeTime, StarRC, Calibre, RedHawk, Tempus.
   - Flow stage: design import, floorplan, powerplan, placement, CTS/postCTS, route/postRoute, extraction, STA/signoff, ECO, chipfinish.
   - Error/rule/command: examples include `IMPCCOPT-1304`, `VIA4.EN.12`, `M2.S*`, `setNanoRouteMode`, `ecoRoute`.
   - Symptom words: setup/hold, transition, congestion, short/open, LVS mismatch, IR drop, EM, floating pin, no clock tree.
2. Read `references/tag-routing.md` when you need tag hints or query expansion for a noisy or underspecified issue.
3. Run 2-3 focused searches:
   - Exact error/rule/command search.
   - Tag-aware search using likely stage, tool, and knowledge tags.
   - Cross-check search for a related cause or command if the fix is risky.
4. Open the top Markdown documents that support the answer. Prefer original article Markdown over generated HTML.
5. Extract candidate Innovus commands from the request and search results. Use the `candidate_commands` field from `search_docs.py` as hints, then add obvious commands from the opened documents.
6. Before giving any concrete Innovus command or option, run `scripts/confirm_innovus_commands.py` against `innovus/innovus_manual.txt`.
7. Answer as a diagnosis, not as a blind snippet dump.

## Innovus Command Evidence

Read `references/innovus-command-policy.md` when the answer includes Innovus command syntax, options, or Tcl snippets.

Use these evidence labels:

- `手册确认`: The command heading and syntax/options were found in `innovus/innovus_manual.txt`.
- `Wiki/项目案例出现但手册未确认`: The command appears in Wiki or flow notes, but not as a manual-confirmed command entry.
- `推断建议需确认版本`: The command is inferred from similar cases or common flow practice and must be checked by the user in their Innovus version.

Do not present a command as manual-confirmed unless `confirm_innovus_commands.py` found it. If a command is a Tcl helper, db query shortcut, project proc, or unavailable in the manual, say that explicitly.

## Search Guidance

- Prefer exact strings for error codes, DRC/LVS rules, and command names.
- Use `--tool` for known tools, such as `--tool innovus`, `--tool calibre`, or `--tool redhawk`.
- Use `--tag`, `--flow-stage`, and `--knowledge-area` when the symptom is broad.
- Treat documents tagged `empty`, `attachment_placeholder`, or `needs-review` as weak evidence unless the title exactly matches the issue.
- For Innovus command usage, search `innovus_flow_commands` for flow context, then confirm exact syntax/options in `innovus_manual.txt`.
- Do not index the full manual into the Wiki search path; use it only for command confirmation to avoid drowning case retrieval.

## Answer Template

Use this shape unless the user asked for something narrower:

```markdown
**问题归类**
一句话归类工具、阶段和问题类型。

**最可能原因**
- 文档明确支持的原因。
- 基于相似案例的推断，明确写“推断”。

**建议检查**
- 需要用户在工具/report/log 中确认的检查项。
- 可给出命令或 Tcl 片段，但必须标注命令证据等级。

**修复思路**
- 先给低风险检查和局部修复。
- 再给可能影响全局 QoR/DRC/timing 的操作，并标注风险。

**Innovus 指令（手册确认）**
- `command ...`：用途、关键语法/option、适用阶段、风险说明。证据：`手册确认` 或其他证据等级。

**相关文档引用**
- `title` - `path`

**风险与待确认项**
- 缺少的工具版本、阶段、error/rule 原文、report 片段或 design state。
```

## Evidence Rules

- Cite every substantive fix idea with at least one document title/path.
- Cite every manual-confirmed Innovus command with `innovus/innovus_manual.txt`; include flow note paths only as usage context.
- Do not present forum-style article content as a foundry rule unless the article itself quotes the rule; say it is a case-based suggestion.
- When documents disagree or only show a similar case, say so.
- If no strong hit is found, state that the local Wiki did not contain a direct match and provide a conservative next diagnostic step.

## Common Commands

Build a fresh index:

```powershell
& '<IC_PYTHON>' -X utf8 (Join-Path $skillRoot 'scripts\build_index.py') --repo-root $wikiRoot --out $indexPath --include-tags --include-innovus
```

Search by issue:

```powershell
& '<IC_PYTHON>' -X utf8 (Join-Path $skillRoot 'scripts\search_docs.py') --index $indexPath --query "VIA4.EN.12 DRC怎么修" --top 8
```

Search with filters:

```powershell
& '<IC_PYTHON>' -X utf8 (Join-Path $skillRoot 'scripts\search_docs.py') --index $indexPath --query "instance没有供上电" --tool redhawk --knowledge-area IR-EM --top 8
```

Confirm commands from the manual:

```powershell
& '<IC_PYTHON>' -X utf8 (Join-Path $skillRoot 'scripts\confirm_innovus_commands.py') --repo-root $wikiRoot --command loadViolationReport --command dbget --format text
```
