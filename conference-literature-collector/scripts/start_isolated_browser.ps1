param(
    [string]$ProxyServer = $env:LIT_BROWSER_PROXY,
    [string]$Browser = $env:LIT_BROWSER,
    [int]$CdpPort = 0,
    [string]$SessionFile = "logs\browser_session.json",
    [switch]$Visible,
    [switch]$KeepExistingSession
)

$ErrorActionPreference = "Stop"

if (-not $ProxyServer) { $ProxyServer = "http://127.0.0.1:7890" }
if (-not $Browser) { $Browser = "edge" }
if ($env:LIT_CDP_PORT -and $CdpPort -eq 0) { $CdpPort = [int]$env:LIT_CDP_PORT }
if ($env:LIT_VISIBLE_BROWSER -eq "1") { $Visible = $true }

function Test-PortFree {
    param([int]$Port)
    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($listener) { $listener.Stop() }
    }
}

function Get-FreePort {
    if ($CdpPort -gt 0) {
        if (-not (Test-PortFree $CdpPort)) { throw "Requested CDP port $CdpPort is already in use." }
        return $CdpPort
    }
    for ($p = 9333; $p -lt 9433; $p++) {
        if (Test-PortFree $p) { return $p }
    }
    throw "No free CDP port found in 9333-9432."
}

function Find-BrowserPath {
    param([string]$Name)
    $edgeCandidates = @(
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe"
    )
    $chromeCandidates = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
    )
    $candidates = if ($Name -eq "chrome") { $chromeCandidates + $edgeCandidates } else { $edgeCandidates + $chromeCandidates }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    throw "Could not find Edge or Chrome executable."
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $SessionFile) | Out-Null

if ((Test-Path -LiteralPath $SessionFile) -and -not $KeepExistingSession) {
    $existing = Get-Content -LiteralPath $SessionFile -Raw | ConvertFrom-Json
    if ($existing.pid -and (Get-Process -Id $existing.pid -ErrorAction SilentlyContinue)) {
        throw "Existing isolated browser session is still running with PID $($existing.pid). Stop it first or pass -KeepExistingSession."
    }
}

$port = Get-FreePort
$browserPath = Find-BrowserPath $Browser
$profileRoot = Join-Path (Resolve-Path ".").Path "logs\browser_profiles"
$userDataDir = Join-Path $profileRoot ("lit-" + (Get-Date -Format "yyyyMMdd-HHmmss") + "-$port")
New-Item -ItemType Directory -Force -Path $userDataDir | Out-Null

$args = @(
    "--remote-debugging-port=$port",
    "--user-data-dir=$userDataDir",
    "--proxy-server=$ProxyServer",
    "--no-first-run",
    "--disable-default-apps",
    "--disable-background-networking",
    "about:blank"
)
if (-not $Visible) {
    $args = @("--headless=new") + $args
}

$startParams = @{
    FilePath = $browserPath
    ArgumentList = $args
    PassThru = $true
}
if (-not $Visible) { $startParams.WindowStyle = "Hidden" }
$process = Start-Process @startParams
Start-Sleep -Milliseconds 800

$session = [ordered]@{
    pid = $process.Id
    cdp_port = $port
    proxy_server = $ProxyServer
    user_data_dir = $userDataDir
    browser_path = $browserPath
    visible = [bool]$Visible
    started_at = (Get-Date).ToString("o")
    command_args = $args
}
$session | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $SessionFile -Encoding UTF8
$session | ConvertTo-Json -Depth 5
