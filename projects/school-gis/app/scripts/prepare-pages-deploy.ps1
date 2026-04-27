param(
  [string]$Destination = "C:\Users\HANSOL\OneDrive\Desktop\Geo-lab\.deploy\school-neighborhood-gis-pages"
)

$ErrorActionPreference = "Stop"

$sourceRoot = Split-Path -Parent $PSScriptRoot
$files = @(
  "index.html",
  "teacher.html",
  "teacher-national.html",
  "_worker.js",
  "app.js",
  "layer-workspace-data.js",
  "layer-workspace-map.js",
  "public-layer-imports.js",
  "sgis-adapter.js",
  "config.js",
  "runtime-config.js",
  "store.js",
  "demo-data.js",
  "national-data.js",
  "styles.css",
  "_headers"
)

$directories = @(
  "application",
  "domain",
  "infrastructure",
  "presentation",
  "functions",
  "sample-layers",
  "vendor"
)

New-Item -ItemType Directory -Force -Path $Destination | Out-Null

Get-ChildItem -LiteralPath $Destination -Force | Remove-Item -Force -Recurse

foreach ($file in $files) {
  Copy-Item -LiteralPath (Join-Path $sourceRoot $file) -Destination (Join-Path $Destination $file) -Force
}

foreach ($directory in $directories) {
  $sourcePath = Join-Path $sourceRoot $directory
  if (Test-Path $sourcePath) {
    Copy-Item -LiteralPath $sourcePath -Destination (Join-Path $Destination $directory) -Recurse -Force
  }
}

Write-Output "Prepared Pages deploy directory: $Destination"
