param(
  [Parameter(Mandatory = $true)]
  [string]$InputPath,

  [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $InputPath)) {
  throw "Input PPTX not found: $InputPath"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

$zip = [System.IO.Compression.ZipFile]::OpenRead($InputPath)
try {
  $slides = $zip.Entries |
    Where-Object { $_.FullName -like "ppt/slides/slide*.xml" } |
    Sort-Object FullName

  $lines = New-Object System.Collections.Generic.List[string]
  $lines.Add(("Source: {0}" -f $InputPath))
  $lines.Add(("ExtractedAt: {0}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")))
  $lines.Add("")

  foreach ($slide in $slides) {
    $reader = New-Object System.IO.StreamReader($slide.Open())
    try {
      $xmlText = $reader.ReadToEnd()
    } finally {
      $reader.Dispose()
    }

    $lines.Add(("--- {0} ---" -f $slide.FullName))
    $matches = [regex]::Matches($xmlText, "<a:t>(.*?)</a:t>")
    foreach ($match in $matches) {
      $text = $match.Groups[1].Value.Trim()
      if ($text) {
        $lines.Add($text)
      }
    }
    $lines.Add("")
  }

  if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
      New-Item -ItemType Directory -Path $parent | Out-Null
    }
    $utf8Bom = New-Object System.Text.UTF8Encoding($true)
    [System.IO.File]::WriteAllLines($OutputPath, $lines, $utf8Bom)
  } else {
    $lines
  }
} finally {
  $zip.Dispose()
}
