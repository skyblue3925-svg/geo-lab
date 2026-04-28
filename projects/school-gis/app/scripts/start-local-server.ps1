param(
  [int]$Port = 8787,
  [int]$MaxPort = 8805
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Test-PortAvailable {
  param(
    [Parameter(Mandatory = $true)]
    [int]$PortToCheck
  )

  $listener = $null
  try {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $PortToCheck)
    $listener.Start()
    return $true
  } catch {
    return $false
  } finally {
    if ($listener) {
      $listener.Stop()
    }
  }
}

function Resolve-AvailablePort {
  param(
    [Parameter(Mandatory = $true)]
    [int]$RequestedPort,
    [Parameter(Mandatory = $true)]
    [int]$UpperBound
  )

  for ($candidate = $RequestedPort; $candidate -le $UpperBound; $candidate++) {
    if (Test-PortAvailable -PortToCheck $candidate) {
      return $candidate
    }
  }

  throw "No available port found between $RequestedPort and $UpperBound."
}

$localSgisEnvFile = Join-Path $PSScriptRoot "sgis-local-env.ps1"
if (Test-Path $localSgisEnvFile) {
  . $localSgisEnvFile
  Write-Host "Loaded local SGIS environment from scripts/sgis-local-env.ps1" -ForegroundColor Cyan
} else {
  Write-Host "SGIS local env file not found. Local SGIS proxy will stay disabled unless env vars are already set." -ForegroundColor Yellow
}

$resolvedPort = Resolve-AvailablePort -RequestedPort $Port -UpperBound $MaxPort
if ($resolvedPort -ne $Port) {
  Write-Host "Port $Port is already in use. Starting School GIS local server at http://127.0.0.1:$resolvedPort/ instead." -ForegroundColor Yellow
} else {
  Write-Host "Starting School GIS local server at http://127.0.0.1:$resolvedPort/" -ForegroundColor Green
}

Write-Host "If Kakao Map is enabled, register this exact origin in Kakao JavaScript SDK domains: http://127.0.0.1:$resolvedPort" -ForegroundColor Cyan

node scripts/dev-static-server.mjs $resolvedPort
