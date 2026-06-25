# Browser Proxy Isolation

Use this reference before any publisher download or task that requires changing browser proxy behavior.

## Contract

Launch a dedicated browser process for the current literature task. Put proxy configuration only on that process command line. Never change global operating system, Codex, or user-browser proxy settings.

Forbidden actions:

- Editing Windows system proxy, WinHTTP proxy, registry proxy keys, or Internet Options.
- Editing `C:\Users\CYL04\.codex\.env`.
- Editing `C:\Users\CYL04\.codex\skills\web-access\config.env`.
- Reusing the user's daily Chrome or Edge process after changing its proxy flags.
- Killing browser processes that were not started by this task.

## Start

From the project root:

```powershell
powershell -ExecutionPolicy Bypass -File ".\skills\conference-literature-collector\scripts\start_isolated_browser.ps1"
```

Useful overrides:

```powershell
$env:LIT_BROWSER_PROXY = "http://127.0.0.1:7890"
$env:LIT_BROWSER = "edge"
$env:LIT_CDP_PORT = "9333"
$env:LIT_VISIBLE_BROWSER = "1"
powershell -ExecutionPolicy Bypass -File ".\skills\conference-literature-collector\scripts\start_isolated_browser.ps1"
```

The script writes `logs/browser_session.json` with `pid`, `cdp_port`, `proxy_server`, `user_data_dir`, and `browser_path`.

## Download

Use the recorded `cdp_port` when running browser download scripts:

```powershell
$session = Get-Content ".\logs\browser_session.json" | ConvertFrom-Json
$env:CDP_PORT = [string]$session.cdp_port
node ".\skills\conference-literature-collector\scripts\publisher_cdp_downloader_bg.js"
```

If publisher access needs a login, first retry via institution/IP access. If login is still required, rerun the start script with `LIT_VISIBLE_BROWSER=1`, let the user log into the isolated browser profile, and then continue. This preserves isolation while allowing cookies to remain only in the task profile.

## Stop

Stop only the recorded process:

```powershell
powershell -ExecutionPolicy Bypass -File ".\skills\conference-literature-collector\scripts\stop_isolated_browser.ps1"
```

Keep the task profile when the user may need to reuse the login. Delete it only when the task is complete and no future publisher access is expected.
