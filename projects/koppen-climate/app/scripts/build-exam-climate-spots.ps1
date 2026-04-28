param(
  [Parameter(Mandatory = $true)]
  [string]$InputPath,

  [Parameter(Mandatory = $true)]
  [string]$OutputJsonPath,

  [string]$OutputModulePath,

  [string]$OutputReviewPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $InputPath)) {
  throw "Input PPTX not found: $InputPath"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

$codePattern = "Af|Am|Aw|As|BW|BS|Cs|Cw|Cfa|Cfb|Cfc|Csa|Csb|Df|Dw|ET\(H\)|ET|EF|AH"
$namedRegex = "^(?<name>.+?)\s*(?<code>$codePattern)\s+(?<dates>\d{6}(?:\s+\d{6})*)$"
$orphanRegex = "^(?<code>$codePattern)\s+(?<dates>\d{6}(?:\s+\d{6})*)$"

function Ensure-ParentDirectory([string]$Path) {
  $parent = Split-Path -Parent $Path
  if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent | Out-Null
  }
}

function Normalize-Text([string]$Text) {
  $normalized = ($Text -replace "\s+", " ").Trim()
  $normalized = $normalized -replace "\s+\)", ")"
  $normalized = $normalized -replace "\(\s+", "("
  return $normalized.Trim()
}

function Get-UnicodeLiteral([int[]]$CodePoints) {
  return -join ($CodePoints | ForEach-Object { [char]$_ })
}

function Normalize-Name([string]$Name) {
  $normalized = Normalize-Text $Name
  $normalized = $normalized -replace "\s+\(", "("
  $nameOverrides = @{
    (Get-UnicodeLiteral @(48652, 47532, 49752)) = (Get-UnicodeLiteral @(48652, 47420, 49472))
    (Get-UnicodeLiteral @(48292, 53216, 48260)) = (Get-UnicodeLiteral @(48180, 53216, 48260))
    (Get-UnicodeLiteral @(54000, 48307, 44256, 50896)) = (Get-UnicodeLiteral @(54000, 48288, 53944, 44256, 50896))
  }
  if ($nameOverrides.ContainsKey($normalized)) {
    return $nameOverrides[$normalized]
  }
  return $normalized
}

function Normalize-ExamCode([string]$DisplayName, [string]$ExamCode) {
  $normalizedCode = Normalize-Text $ExamCode
  $codeOverrides = @{
    "케이프타운" = "Cs"
  }
  if ($codeOverrides.ContainsKey($DisplayName)) {
    return $codeOverrides[$DisplayName]
  }
  return $normalizedCode
}

function Should-IgnoreText([string]$Text) {
  return $false
}

function Parse-DateList([string]$RawDates) {
  [string[]]$values = @(
    $RawDates.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries) |
      Sort-Object -Unique
  )
  return ,$values
}

function Get-ShapeTextRuns($Shape, $NamespaceManager) {
  return @(
    $Shape.SelectNodes(".//a:t", $NamespaceManager) |
      ForEach-Object { $_.InnerText } |
      Where-Object { $_ -and $_.Trim() }
  )
}

function Parse-SlideShapes([string]$SlideName, [string]$XmlText) {
  [xml]$xml = $XmlText
  $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
  $ns.AddNamespace("p", "http://schemas.openxmlformats.org/presentationml/2006/main")
  $ns.AddNamespace("a", "http://schemas.openxmlformats.org/drawingml/2006/main")

  $rows = New-Object System.Collections.Generic.List[object]
  $shapeIndex = 0
  foreach ($shape in $xml.SelectNodes("//p:sp", $ns)) {
    $shapeIndex++
    $text = Normalize-Text ((Get-ShapeTextRuns $shape $ns) -join " ")
    if (-not $text -or (Should-IgnoreText $text)) {
      continue
    }

    $rows.Add([pscustomobject]@{
        slide = $SlideName
        shapeIndex = $shapeIndex
        x = [int]$shape.spPr.xfrm.off.x
        y = [int]$shape.spPr.xfrm.off.y
        text = $text
      })
  }

  return @($rows.ToArray())
}

function Merge-OrphanShape($Orphan, $Records) {
  $candidates = @(
    $Records | Where-Object {
      $_.examCode -eq $Orphan.code `
      -and $_.sourceSlide -eq $Orphan.slide `
      -and $_.y -le $Orphan.y `
      -and ($Orphan.y - $_.y) -le 350000 `
      -and [math]::Abs($Orphan.x - $_.x) -le 1500000
    }
  )

  if (-not $candidates) {
    return $null
  }

  return $candidates |
    Sort-Object @{
      Expression = {
        ($Orphan.y - $_.y) + ([math]::Abs($Orphan.x - $_.x) / 4)
      }
    } |
    Select-Object -First 1
}

$zip = [System.IO.Compression.ZipFile]::OpenRead($InputPath)
try {
  $slideEntries = @(
    $zip.Entries |
      Where-Object { $_.FullName -like "ppt/slides/slide*.xml" } |
      Sort-Object FullName
  )

  $fingerprints = @{}
  $allShapes = New-Object System.Collections.Generic.List[object]
  $usedSlides = New-Object System.Collections.Generic.List[string]

  foreach ($entry in $slideEntries) {
    $reader = New-Object System.IO.StreamReader($entry.Open())
    try {
      $xmlText = $reader.ReadToEnd()
    } finally {
      $reader.Dispose()
    }

    $fingerprint = [Convert]::ToBase64String(
      [System.Text.Encoding]::UTF8.GetBytes(
        (
          [regex]::Matches($xmlText, "<a:t>(.*?)</a:t>") |
            ForEach-Object { Normalize-Text $_.Groups[1].Value } |
            Where-Object { $_ }
        ) -join "|"
      )
    )

    if ($fingerprints.ContainsKey($fingerprint)) {
      continue
    }
    $fingerprints[$fingerprint] = $entry.FullName
    $usedSlides.Add($entry.FullName)

    foreach ($shape in (Parse-SlideShapes $entry.FullName $xmlText)) {
      $allShapes.Add($shape)
    }
  }

  $records = New-Object System.Collections.Generic.List[object]
  $unresolvedOrphans = New-Object System.Collections.Generic.List[object]

  foreach ($shape in ($allShapes | Sort-Object y, x)) {
    if ($shape.text -match $namedRegex) {
      $examDates = Parse-DateList $Matches["dates"]
      $displayName = Normalize-Name $Matches["name"]
      $records.Add([pscustomobject]@{
          id = $null
          displayName = $displayName
          rawName = $Matches["name"].Trim()
          examCode = Normalize-ExamCode $displayName $Matches["code"]
          examDates = [string[]]$examDates
          examCount = $examDates.Count
          sourceSlide = $shape.slide
          sourceShapes = @($shape.shapeIndex)
          sourceTexts = @($shape.text)
          x = $shape.x
          y = $shape.y
        })
      continue
    }

    if ($shape.text -match $orphanRegex) {
      $orphan = [pscustomobject]@{
        slide = $shape.slide
        shapeIndex = $shape.shapeIndex
        x = $shape.x
        y = $shape.y
        text = $shape.text
        code = $Matches["code"]
        examDates = Parse-DateList $Matches["dates"]
      }
      $target = Merge-OrphanShape $orphan $records
      if ($target) {
        $target.examDates = [string[]]@($target.examDates + $orphan.examDates | Sort-Object -Unique)
        $target.examCount = $target.examDates.Count
        $target.sourceShapes = @($target.sourceShapes + $orphan.shapeIndex | Sort-Object -Unique)
        $target.sourceTexts = @($target.sourceTexts + $orphan.text | Sort-Object -Unique)
      } else {
        $unresolvedOrphans.Add($orphan)
      }
    }
  }

  $sortedRecords = @(
    $records |
      Sort-Object y, x |
      ForEach-Object -Begin { $index = 0 } -Process {
        $index++
        [pscustomobject]@{
          id = ("exam-spot-{0:d3}" -f $index)
          displayName = $_.displayName
          rawName = $_.rawName
          examCode = $_.examCode
          examDates = $_.examDates
          examCount = $_.examCount
          sourceSlide = $_.sourceSlide
          sourceShapes = $_.sourceShapes
          sourceTexts = $_.sourceTexts
          x = $_.x
          y = $_.y
        }
      }
  )

  $payload = [pscustomobject]@{
    source = $InputPath
    generatedAt = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
    slidesUsed = @($usedSlides.ToArray())
    recordCount = $sortedRecords.Count
    unresolvedOrphanCount = $unresolvedOrphans.Count
    records = $sortedRecords
    unresolvedOrphans = @($unresolvedOrphans.ToArray())
  }

  Ensure-ParentDirectory $OutputJsonPath
  $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputJsonPath -Encoding UTF8

  if ($OutputModulePath) {
    Ensure-ParentDirectory $OutputModulePath
    $moduleBody = @(
      "export const EXAM_CLIMATE_SPOTS = " + ($sortedRecords | ConvertTo-Json -Depth 6) + ";",
      "",
      "export const EXAM_CLIMATE_SPOTS_META = " + (
        [pscustomobject]@{
          source = $InputPath
          generatedAt = $payload.generatedAt
          slidesUsed = $payload.slidesUsed
          unresolvedOrphanCount = $payload.unresolvedOrphanCount
        } | ConvertTo-Json -Depth 4
      ) + ";"
    ) -join [Environment]::NewLine
    Set-Content -LiteralPath $OutputModulePath -Value $moduleBody -Encoding UTF8
  }

  if ($OutputReviewPath) {
    Ensure-ParentDirectory $OutputReviewPath
    $reviewLines = New-Object System.Collections.Generic.List[string]
    $reviewLines.Add("# Exam Climate Spots Review")
    $reviewLines.Add("")
    $reviewLines.Add(("Source: {0}" -f $InputPath))
    $reviewLines.Add(("Generated: {0}" -f $payload.generatedAt))
    $reviewLines.Add(("Records: {0}" -f $payload.recordCount))
    $reviewLines.Add(("Unresolved orphan boxes: {0}" -f $payload.unresolvedOrphanCount))
    $reviewLines.Add("")
    $reviewLines.Add("## Parsed Records")
    $reviewLines.Add("")
    foreach ($record in $sortedRecords) {
      $reviewLines.Add(("- `{0}` | `{1}` | {2}" -f $record.displayName, $record.examCode, ($record.examDates -join ", ")))
    }
    $reviewLines.Add("")
    $reviewLines.Add("## Unresolved Orphans")
    $reviewLines.Add("")
    if ($unresolvedOrphans.Count -eq 0) {
      $reviewLines.Add("- none")
    } else {
      foreach ($orphan in $unresolvedOrphans) {
        $reviewLines.Add(("- slide {0} shape {1} | {2}" -f $orphan.slide, $orphan.shapeIndex, $orphan.text))
      }
    }
    Set-Content -LiteralPath $OutputReviewPath -Value $reviewLines -Encoding UTF8
  }
} finally {
  $zip.Dispose()
}
