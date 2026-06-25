param(
    [string]$SessionFile = "logs\browser_session.json",
    [switch]$RemoveProfile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SessionFile)) {
    Write-Output "No isolated browser session file found: $SessionFile"
    exit 0
}

$session = Get-Content -LiteralPath $SessionFile -Raw | ConvertFrom-Json
$processIds = @()

if ($session.user_data_dir) {
    $escapedProfile = [regex]::Escape([string]$session.user_data_dir)
    $matched = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match $escapedProfile }
    $processIds += @($matched | Select-Object -ExpandProperty ProcessId)
}
if ($session.pid) { $processIds += [int]$session.pid }
$processIds = @($processIds | Where-Object { $_ } | Select-Object -Unique)

foreach ($procId in $processIds) {
    $process = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
try { Wait-Process -Id $procId -Timeout 5 -ErrorAction SilentlyContinue } catch {}
        Write-Output "Stopped isolated browser PID $procId."
    }
}

if (-not $processIds) {
    Write-Output "No isolated browser process was running."
}

if ($RemoveProfile -and $session.user_data_dir -and (Test-Path -LiteralPath $session.user_data_dir)) {
    $resolved = (Resolve-Path -LiteralPath $session.user_data_dir).Path
    $allowed = (Resolve-Path -LiteralPath "logs\browser_profiles").Path
    if (-not $resolved.StartsWith($allowed, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove profile outside logs\browser_profiles: $resolved"
    }
    for ($attempt = 1; $attempt -le 8; $attempt++) {
        try {
            Remove-Item -LiteralPath $resolved -Recurse -Force -ErrorAction Stop
            Write-Output "Removed isolated browser profile $resolved."
            break
        } catch {
            if ($attempt -eq 8) { throw }
            Start-Sleep -Milliseconds (250 * $attempt)
        }
    }
}
