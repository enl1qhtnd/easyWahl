$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$frontendDir = Join-Path $repoRoot 'frontend'
$backendDir = Join-Path $repoRoot 'backend'
$pythonExe = Join-Path $backendDir 'venv\Scripts\python.exe'

function Invoke-Step {
    param(
        [string]$Description,
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description fehlgeschlagen (Exitcode $LASTEXITCODE)."
    }
}

if (-not (Test-Path $frontendDir)) {
    throw "Frontend-Verzeichnis nicht gefunden: $frontendDir"
}

if (-not (Test-Path $backendDir)) {
    throw "Backend-Verzeichnis nicht gefunden: $backendDir"
}

if (-not (Test-Path $pythonExe)) {
    throw "Python-Venv nicht gefunden: $pythonExe"
}

Push-Location $frontendDir
try {
    Invoke-Step "Frontend-Build" { npm.cmd run build }
}
finally {
    Pop-Location
}

Push-Location $backendDir
try {
    Invoke-Step "PyInstaller-Build" { & $pythonExe -m PyInstaller --noconfirm admin_gui.spec }
}
finally {
    Pop-Location
}

$exePath = Join-Path $backendDir 'dist\easyWahl-v1.2.0.exe'
Write-Host "Build abgeschlossen: $exePath"
