param(
  [switch]$Fast
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
  $Python = "python"
}

Push-Location $RepoRoot
try {
  if ($Fast) {
    & $Python -m pytest `
      projects\terrain-lab\tests\test_geomorphic_engine_force_fields.py `
      projects\terrain-lab\tests\test_geomorphic_engine_presets.py `
      projects\terrain-lab\tests\test_physics_lab_metadata.py `
      -q
  } else {
    & $Python -m pytest projects\terrain-lab\tests -q
  }
  exit $LASTEXITCODE
} finally {
  Pop-Location
}
