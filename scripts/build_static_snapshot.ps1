param(
    [Parameter(Mandatory = $true)]
    [string]$ReportPath,

    [string]$OutputPath
)

$ErrorActionPreference = "Stop"

$resolvedReport = (Resolve-Path -LiteralPath $ReportPath).Path
if (-not $OutputPath) {
    $OutputPath = Join-Path (Split-Path -Parent $resolvedReport) "pbd-snapshot.html"
}
$resolvedOutput = [IO.Path]::GetFullPath($OutputPath)
$templatePath = Join-Path $PSScriptRoot "static-snapshot-template.html"
if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
    throw "Static snapshot template not found: $templatePath"
}

$reportJson = [IO.File]::ReadAllText($resolvedReport, [Text.Encoding]::UTF8)
$null = $reportJson | ConvertFrom-Json
$safeJson = $reportJson.Replace("</", "<\/")
$template = [IO.File]::ReadAllText($templatePath, [Text.Encoding]::UTF8)
$marker = "__DECODE_REPORT_JSON__"
if (-not $template.Contains($marker)) {
    throw "Snapshot template does not contain the data marker"
}

$outputDirectory = Split-Path -Parent $resolvedOutput
if ($outputDirectory -and -not (Test-Path -LiteralPath $outputDirectory)) {
    [IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
}
$html = $template.Replace($marker, $safeJson)
[IO.File]::WriteAllText($resolvedOutput, $html, [Text.UTF8Encoding]::new($false))

Write-Output $resolvedOutput
