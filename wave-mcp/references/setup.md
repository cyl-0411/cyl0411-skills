# Local setup and maintenance

Resolve the local layout before maintenance. Prefer `CODEX_HOME`; otherwise use
the current user's `.codex` directory. The WSL distribution is a configured
value, while the Linux home and Windows-to-WSL source path are discovered at
runtime:

```powershell
$waveCodexRoot = if ($env:CODEX_HOME) {
  $env:CODEX_HOME
} else {
  Join-Path $env:USERPROFILE '.codex'
}
$waveCodexRoot = (Resolve-Path -LiteralPath $waveCodexRoot).Path
$waveSourceRoot = (Resolve-Path -LiteralPath (Join-Path $waveCodexRoot 'vendor_imports\wave-mcp')).Path
$waveDistro = if ($env:WAVE_MCP_WSL_DISTRO) { $env:WAVE_MCP_WSL_DISTRO } else { '<WAVE_WSL_DISTRO>' }
$waveLinuxHome = (wsl.exe -d $waveDistro -- sh -lc 'printf %s "$HOME"').Trim()
$waveRuntime = "$waveLinuxHome/.local/opt/wave-mcp/.venv"
$waveSourceWsl = (wsl.exe -d $waveDistro -- wslpath -a $waveSourceRoot).Trim()
if (-not $waveLinuxHome -or -not $waveSourceWsl) { throw 'Unable to resolve wave-mcp WSL paths.' }
```

The currently installed upstream is `Tencent/wave-mcp` version `0.1.1`; the
optional VCD converter is normally `vcd2fst` from GTKWave.

## Codex MCP configuration

The global `<CODEX_HOME>/config.toml` entry should resolve the Linux home inside
WSL rather than embedding a username. Substitute the configured distribution at
configuration time:

```toml
[mcp_servers.wave-mcp]
command = "wsl.exe"
args = ["-d", "<WAVE_WSL_DISTRO>", "--", "bash", "-lc", "exec \"$HOME/.local/opt/wave-mcp/.venv/bin/wave-mcp\""]
startup_timeout_sec = 120
tool_timeout_sec = 300
```

No persistent approval override is configured. Codex's default MCP approval
policy remains in effect.

## Verification

Run these from Windows PowerShell:

```powershell
wsl.exe -d $waveDistro -- "$waveRuntime/bin/python" -c "import wave_mcp,pylibfst,pyslang; print(wave_mcp.__version__)"
wsl.exe -d $waveDistro -- "$waveRuntime/bin/wave-mcp" query --list
codex mcp list
```

Expected results are wave-mcp `0.1.1`, 27 tools, and an enabled `wave-mcp`
entry. Restart Codex after changing MCP configuration.

## Updating

Pull the source clone, review upstream changes, then reinstall it into the
existing isolated environment:

```powershell
git -C $waveSourceRoot pull --ff-only
wsl.exe -d $waveDistro -- "$waveRuntime/bin/python" -m pip install --upgrade $waveSourceWsl
```

Re-run the verification commands and the upstream static-analysis example
before relying on a new version.
