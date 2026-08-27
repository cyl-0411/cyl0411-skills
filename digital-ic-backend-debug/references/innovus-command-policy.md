# Innovus Command Policy

Use this reference whenever a diagnostic answer includes concrete Innovus commands, options, or Tcl snippets.

## Evidence Priority

1. `innovus/innovus_manual.txt`: authoritative source for command existence, syntax, parameters, defaults, and examples.
2. `innovus/docs/innovus_flow_commands/*.md`: flow context and practical ordering notes.
3. `docs/articles/*.md`: case-based evidence from the local Wiki.
4. Inference from similar cases: lowest confidence; label clearly.

Do not use flow notes or Wiki articles as proof that an option exists. They can justify when a command is useful, but exact syntax and option names must come from the manual.

## Required Labels

- `手册确认`: `scripts/confirm_innovus_commands.py` found the command heading in `innovus_manual.txt`.
- `Wiki/项目案例出现但手册未确认`: The command appears in local docs but the manual lookup did not find it.
- `推断建议需确认版本`: The recommendation is inferred and must be checked in the user's installed Innovus version.

## Answer Rules

- Before recommending an Innovus command, run:

```powershell
& '<IC_PYTHON>' -X utf8 (Join-Path $skillRoot 'scripts\confirm_innovus_commands.py') --repo-root $wikiRoot --command <command> --format json
```

Resolve `$skillRoot`, `$wikiRoot`, and `<IC_PYTHON>` using the root
`SKILL.md` path-resolution preflight before running this command.

- Preserve exact command and option spelling from the manual.
- Mention that the local manual is an Innovus Text Command Reference generated from the local `innovus_manual.txt`; version-sensitive defaults should be checked against the user's installed Innovus build.
- If a snippet includes Tcl, db accessors, or project helper procs that the manual does not contain, mark them as not manual-confirmed instead of silently dropping them.
- Keep quoted manual text short. Summarize long parameter descriptions in your own words.

## Common Interpretation

- `手册确认` supports command syntax and option existence.
- `innovus_flow_commands` supports flow stage, typical order, and practical context.
- Wiki articles support observed symptoms, likely causes, and case-specific repairs.
- A Calibre/RedHawk/PrimeTime command should not be labeled as Innovus manual-confirmed; cite its local article context instead.
