# ARS-Codex Hook Pack

The hook pack is disabled by default. It is only eligible for installation when
the user explicitly opts in with:

```bash
export ARS_CODEX_FULL_RUNTIME=1
export ARS_CODEX_HOOKS=1
```

In Windows PowerShell, use:

```powershell
$env:ARS_CODEX_FULL_RUNTIME = '1'
$env:ARS_CODEX_HOOKS = '1'
```

`hooks.json` contains one read-only SessionStart announcement hook. It calls the
Node-native `codex/scripts/ars_codex_hook.mjs` wrapper, so it has no Python-path
dependency and does not read `ARS_PYTHON` or `VIRTUAL_ENV`. The hook prints adapter
metadata and command aliases only. It does not read environment variables, print
secrets, access the network, or write files.

Before installing the source hook pack, replace `__ARS_DIR__` in `hooks.json`
with the absolute directory containing the root `SKILL.md`. Keep the quotes so
paths containing spaces remain valid.

Before installing or copying this hook pack into a Codex hook configuration, run:

```text
<ARS_PYTHON> -X utf8 "<ARS_DIR>/codex/scripts/ars_codex_quality_gates.py" hook-safety
```

Claude Code hooks in `ars/hooks/hooks.json` remain vendored upstream metadata.
They are not installed by this Codex adapter.
