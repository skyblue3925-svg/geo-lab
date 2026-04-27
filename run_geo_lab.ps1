param(
    [int]$Port = 8501,
    [switch]$KillPortOwner,
    [switch]$BootstrapVenv,
    [string]$PythonVersion = "3.13"
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$requirements = Join-Path $root 'requirements.txt'

function Test-VenvPython {
    param([string]$PythonPath)

    if (-not (Test-Path $PythonPath)) {
        return $false
    }

    try {
        & $PythonPath -c "import sys; print(sys.executable)" | Out-Null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Initialize-Venv {
    param(
        [string]$RootPath,
        [string]$Version,
        [string]$PythonPath,
        [string]$RequirementsPath
    )

    Write-Host "Bootstrapping virtualenv with Python $Version ..."
    & py -$Version -m venv (Join-Path $RootPath '.venv')
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create .venv with py -$Version"
    }

    & $PythonPath -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip in .venv"
    }

    & $PythonPath -m pip install -r $RequirementsPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install requirements into .venv"
    }
}

if (-not (Test-VenvPython $python)) {
    if ($BootstrapVenv) {
        Initialize-Venv -RootPath $root -Version $PythonVersion -PythonPath $python -RequirementsPath $requirements
    }
    else {
        throw "Virtualenv is missing or broken: $python`nRun '.\run_geo_lab.ps1 -BootstrapVenv' to recreate it."
    }
}

if ($KillPortOwner) {
    $lines = netstat -ano | Select-String ":$Port\s+.*LISTENING\s+\d+$"
    foreach ($line in $lines) {
        $parts = ($line.ToString() -replace '\s+', ' ').Trim().Split(' ')
        $ownerPid = [int]$parts[-1]
        if ($ownerPid -gt 0) {
            Stop-Process -Id $ownerPid -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Milliseconds 700
}

Start-Process -FilePath $python -ArgumentList @('-m', 'streamlit', 'run', 'app.py', "--server.port=$Port") -WorkingDirectory $root | Out-Null

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $resp = Invoke-WebRequest -UseBasicParsing "http://localhost:$Port" -TimeoutSec 1
        if ($resp.StatusCode -ge 200) {
            $ready = $true
            break
        }
    }
    catch {
    }
    Start-Sleep -Milliseconds 500
}

if ($ready) {
    Write-Host "Geo-lab server started: http://localhost:$Port"
}
else {
    Write-Host "Server process started. Open: http://localhost:$Port"
}
