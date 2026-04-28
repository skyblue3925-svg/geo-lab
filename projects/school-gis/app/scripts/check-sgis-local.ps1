param(
  [int]$Port = 8788,
  [string]$Year = "2023",
  [string]$AdmCd = "",
  [string]$LowSearch = "1"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$localSgisEnvFile = Join-Path $PSScriptRoot "sgis-local-env.ps1"
if (Test-Path $localSgisEnvFile) {
  . $localSgisEnvFile
  Write-Host "Loaded local SGIS environment from scripts/sgis-local-env.ps1" -ForegroundColor Cyan
} else {
  Write-Host "scripts/sgis-local-env.ps1 not found." -ForegroundColor Yellow
  Write-Host "Copy scripts/sgis-local-env.example.ps1 to scripts/sgis-local-env.ps1 and fill your SGIS keys first." -ForegroundColor Yellow
}

if (-not $env:SGIS_CONSUMER_KEY -or -not $env:SGIS_CONSUMER_SECRET) {
  throw "SGIS_CONSUMER_KEY / SGIS_CONSUMER_SECRET are missing. Fill scripts/sgis-local-env.ps1 first."
}

$query = @{
  year = $Year
  lowSearch = $LowSearch
}
if ($AdmCd) {
  $query.admCd = $AdmCd
}

$queryString = ($query.GetEnumerator() | ForEach-Object {
  "{0}={1}" -f [System.Uri]::EscapeDataString($_.Key), [System.Uri]::EscapeDataString([string]$_.Value)
}) -join "&"

$job = Start-Job -ScriptBlock {
  param($WorkingRoot, $SelectedPort, $ConsumerKey, $ConsumerSecret, $ApiBaseUrl)
  Set-Location $WorkingRoot
  $env:SGIS_CONSUMER_KEY = $ConsumerKey
  $env:SGIS_CONSUMER_SECRET = $ConsumerSecret
  if ($ApiBaseUrl) {
    $env:SGIS_API_BASE_URL = $ApiBaseUrl
  }
  & "C:\Program Files\nodejs\node.exe" "scripts/dev-static-server.mjs" $SelectedPort
} -ArgumentList $root, $Port, $env:SGIS_CONSUMER_KEY, $env:SGIS_CONSUMER_SECRET, $env:SGIS_API_BASE_URL

try {
  Start-Sleep -Seconds 2
  $url = "http://127.0.0.1:$Port/api/sgis/population?$queryString"
  Write-Host "Checking $url" -ForegroundColor Green
  try {
    $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 20 -ErrorAction Stop
  } catch {
    if ($_.Exception.Response) {
      $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
      $errorBody = $reader.ReadToEnd()
      Write-Host ""
      Write-Host "Local SGIS proxy returned an error:" -ForegroundColor Red
      Write-Host $errorBody
      throw
    }

    throw
  }

  $featureCount = @($response.boundary.features).Count
  $rowCount = @($response.statsRows).Count

  Write-Host ""
  Write-Host "Local SGIS proxy is working." -ForegroundColor Green
  Write-Host "year       : $($response.year)"
  Write-Host "admCd      : $($response.admCd)"
  Write-Host "lowSearch  : $($response.lowSearch)"
  Write-Host "boundaries : $featureCount"
  Write-Host "statsRows  : $rowCount"
} finally {
  Stop-Job $job -ErrorAction SilentlyContinue | Out-Null
  Receive-Job $job -Keep -ErrorAction SilentlyContinue | Out-Null
}
