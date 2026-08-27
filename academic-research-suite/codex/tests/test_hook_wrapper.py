from __future__ import annotations

import json
import subprocess
from pathlib import Path


CODEX_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = CODEX_ROOT / "scripts" / "ars_codex_hook.mjs"
MANIFEST_PATH = CODEX_ROOT / "full-runtime-manifest.json"


def test_announce_reports_canonical_aliases_without_slashes() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    result = subprocess.run(
        ["node", str(HOOK_PATH), "announce"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["name"] == manifest["adapter"]["name"]
    assert "ars-plan" in payload["aliases"]
    assert "ars-reviewer" in payload["aliases"]
    assert all(not alias.startswith("/") for alias in payload["aliases"])
    assert len(payload["aliases"]) == len(set(payload["aliases"]))


def test_cli_announce_does_not_echo_environment_values(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-should-not-appear")

    result = subprocess.run(
        ["node", str(HOOK_PATH), "announce"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "sk-test-should-not-appear" not in result.stdout
    payload = json.loads(result.stdout)
    assert payload["hooks"] == "opt-in with ARS_CODEX_HOOKS=1"
