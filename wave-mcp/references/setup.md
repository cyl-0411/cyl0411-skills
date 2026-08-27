# Local setup and maintenance

This workstation uses the following verified layout:

- WSL distribution: `IC-EDA` (Rocky Linux 8.10, x86_64)
- Runtime: `/home/ray/.local/opt/wave-mcp/.venv`
- Source clone: `C:\Users\CYL04\.codex\vendor_imports\wave-mcp`
- Installed upstream: `Tencent/wave-mcp` version `0.1.1`
- Optional VCD converter: `/usr/bin/vcd2fst` from GTKWave 3.3.118

## Codex MCP configuration

The global `C:\Users\CYL04\.codex\config.toml` contains:

```toml
[mcp_servers.wave-mcp]
command = "wsl.exe"
args = ["-d", "IC-EDA", "--", "/home/ray/.local/opt/wave-mcp/.venv/bin/wave-mcp"]
startup_timeout_sec = 120
tool_timeout_sec = 300
```

No persistent approval override is configured. Codex's default MCP approval
policy remains in effect.

## Verification

Run these from Windows PowerShell:

```powershell
wsl -d IC-EDA -- /home/ray/.local/opt/wave-mcp/.venv/bin/python -c "import wave_mcp,pylibfst,pyslang; print(wave_mcp.__version__)"
wsl -d IC-EDA -- /home/ray/.local/opt/wave-mcp/.venv/bin/wave-mcp query --list
codex mcp list
```

Expected results are wave-mcp `0.1.1`, 27 tools, and an enabled `wave-mcp`
entry. Restart Codex after changing MCP configuration.

## Updating

Pull the source clone, review upstream changes, then reinstall it into the
existing isolated environment:

```powershell
git -C C:\Users\CYL04\.codex\vendor_imports\wave-mcp pull --ff-only
wsl -d IC-EDA -- /home/ray/.local/opt/wave-mcp/.venv/bin/python -m pip install --upgrade /mnt/c/Users/CYL04/.codex/vendor_imports/wave-mcp
```

Re-run the verification commands and the upstream static-analysis example
before relying on a new version.
