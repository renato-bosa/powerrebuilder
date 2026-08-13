param(
    [string]$WorkspaceRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$ReportGeneration = "v6",
    [string]$JsonOut
)

$ErrorActionPreference = "Stop"

function Remove-PowerBuilderComments([string]$Source) {
    $output = [Text.StringBuilder]::new()
    $stringDelimiter = [char]0
    $lineComment = $false
    $blockComment = $false
    for ($index = 0; $index -lt $Source.Length; $index++) {
        $current = $Source[$index]
        $next = if ($index + 1 -lt $Source.Length) { $Source[$index + 1] } else { [char]0 }
        if ($lineComment) {
            if ($current -eq "`n") {
                $lineComment = $false
                [void]$output.Append($current)
            }
        } elseif ($blockComment) {
            if ($current -eq '*' -and $next -eq '/') {
                $blockComment = $false
                $index++
            } elseif ($current -eq "`n") {
                [void]$output.Append($current)
            }
        } elseif ($stringDelimiter -ne [char]0) {
            [void]$output.Append($current)
            if ($current -eq '~' -and $index + 1 -lt $Source.Length) {
                [void]$output.Append($next)
                $index++
            } elseif ($current -eq $stringDelimiter) {
                $stringDelimiter = [char]0
            }
        } elseif ($current -in @('"', "'")) {
            $stringDelimiter = $current
            [void]$output.Append($current)
        } elseif ($current -eq '/' -and $next -eq '/') {
            $lineComment = $true
            $index++
        } elseif ($current -eq '/' -and $next -eq '*') {
            $blockComment = $true
            $index++
        } else {
            [void]$output.Append($current)
        }
    }
    $output.ToString()
}

function Join-PowerBuilderContinuations([string]$Source) {
    $output = [Text.StringBuilder]::new()
    $stringDelimiter = [char]0
    $escaped = $false
    $continuation = $false
    foreach ($character in $Source.ToCharArray()) {
        if ($continuation) {
            if ([char]::IsWhiteSpace($character)) { continue }
            $continuation = $false
        }
        if ($stringDelimiter -ne [char]0) {
            [void]$output.Append($character)
            if ($escaped) {
                $escaped = $false
            } elseif ($character -eq '~') {
                $escaped = $true
            } elseif ($character -eq $stringDelimiter) {
                $stringDelimiter = [char]0
            }
        } elseif ($character -in @('"', "'")) {
            $stringDelimiter = $character
            [void]$output.Append($character)
        } elseif ($character -eq '&') {
            $continuation = $true
        } else {
            [void]$output.Append($character)
        }
    }
    $output.ToString()
}

function Split-PowerBuilderStatements([string]$Source) {
    $statements = [Collections.Generic.List[string]]::new()
    $current = [Text.StringBuilder]::new()
    $stringDelimiter = [char]0
    $escaped = $false
    foreach ($character in $Source.ToCharArray()) {
        if ($stringDelimiter -ne [char]0) {
            [void]$current.Append($character)
            if ($escaped) {
                $escaped = $false
            } elseif ($character -eq '~') {
                $escaped = $true
            } elseif ($character -eq $stringDelimiter) {
                $stringDelimiter = [char]0
            }
        } elseif ($character -in @('"', "'")) {
            $stringDelimiter = $character
            [void]$current.Append($character)
        } elseif ($character -in @("`n", "`r", ';')) {
            if ($current.ToString().Trim()) { $statements.Add($current.ToString()) }
            [void]$current.Clear()
        } else {
            [void]$current.Append($character)
        }
    }
    if ($current.ToString().Trim()) { $statements.Add($current.ToString()) }
    $statements.ToArray()
}

function Normalize-PowerBuilderType([string]$Word) {
    switch ($Word.ToLowerInvariant()) {
        "int" { "integer" }
        "bool" { "boolean" }
        "unsignedinteger" { "uint" }
        "unsignedlong" { "ulong" }
        "character" { "char" }
        default { $Word.ToLowerInvariant() }
    }
}

function Normalize-PowerBuilderStatement([string]$Statement) {
    $output = [Text.StringBuilder]::new()
    $word = [Text.StringBuilder]::new()
    $stringDelimiter = [char]0
    $characters = $Statement.ToCharArray()
    $flushWord = {
        if ($word.Length -gt 0) {
            [void]$output.Append((Normalize-PowerBuilderType $word.ToString()))
            [void]$word.Clear()
        }
    }
    for ($index = 0; $index -lt $characters.Length; $index++) {
        $character = $characters[$index]
        if ($stringDelimiter -eq [char]0 -and $character -in @('"', "'")) {
            & $flushWord
            $stringDelimiter = $character
            [void]$output.Append('"')
        } elseif ($stringDelimiter -ne [char]0) {
            if ($character -eq '~' -and $index + 1 -lt $characters.Length -and
                $characters[$index + 1] -eq $stringDelimiter) {
                [void]$output.Append($stringDelimiter)
                $index++
            } elseif ($character -eq $stringDelimiter) {
                $stringDelimiter = [char]0
                [void]$output.Append('"')
            } else {
            [void]$output.Append(([string]$character).ToLowerInvariant())
            }
        } elseif ([char]::IsLetterOrDigit($character) -or $character -eq '_' -or [int]$character -eq 1) {
            [void]$word.Append(([string]$character).ToLowerInvariant())
        } else {
            & $flushWord
            if (-not [char]::IsWhiteSpace($character)) { [void]$output.Append($character) }
        }
    }
    & $flushWord
    $output.ToString().Replace("this.", "")
}

function Normalize-PowerBuilderBody([string]$Body) {
    $withoutComments = Remove-PowerBuilderComments $Body
    $joined = Join-PowerBuilderContinuations $withoutComments
    $statements = @(
        Split-PowerBuilderStatements $joined |
            ForEach-Object { Normalize-PowerBuilderStatement $_ } |
            Where-Object { $_ }
    )
    while ($statements.Count -gt 0 -and $statements[-1] -eq "return") {
        $statements = if ($statements.Count -gt 1) {
            @($statements[0..($statements.Count - 2)])
        } else {
            @()
        }
    }
    @($statements)
}

function Find-FirstSemicolon([string]$Line) {
    $stringDelimiter = [char]0
    $escaped = $false
    for ($index = 0; $index -lt $Line.Length; $index++) {
        if ($stringDelimiter -ne [char]0) {
            if ($escaped) {
                $escaped = $false
            } elseif ($Line[$index] -eq '~') {
                $escaped = $true
            } elseif ($Line[$index] -eq $stringDelimiter) {
                $stringDelimiter = [char]0
            }
        } elseif ($Line[$index] -in @('"', "'")) {
            $stringDelimiter = $Line[$index]
        } elseif ($Line[$index] -eq ';') {
            return $index
        }
    }
    -1
}

$sourceFileCache = @{}
function Get-NormalizedSourceBody([string]$SourceReference) {
    $path = $SourceReference -replace ':\d+$', ''
    if (-not $sourceFileCache.ContainsKey($path)) {
        $sourceFileCache[$path] = @(Get-Content -LiteralPath $path)
    }
    $lines = $sourceFileCache[$path]
    $start = [int]([regex]::Match($SourceReference, ':(\d+)$').Groups[1].Value) - 1
    $header = $lines[$start].TrimStart()
    $body = [Text.StringBuilder]::new()
    if ($header.StartsWith("on ", [StringComparison]::OrdinalIgnoreCase)) {
        $terminator = "end on"
    } else {
        $semicolon = Find-FirstSemicolon $header
        if ($semicolon -lt 0) { throw "Source header has no semicolon: $SourceReference" }
        $inlineBody = $header.Substring($semicolon + 1)
        if ($inlineBody) { [void]$body.AppendLine($inlineBody) }
        $lowerHeader = $header.Substring(0, $semicolon).ToLowerInvariant()
        $terminator = if ($lowerHeader.StartsWith("event ")) {
            "end event"
        } elseif ($lowerHeader.Contains("function")) {
            "end function"
        } else {
            "end subroutine"
        }
    }
    for ($index = $start + 1; $index -lt $lines.Count; $index++) {
        if ($lines[$index].Trim().Equals($terminator, [StringComparison]::OrdinalIgnoreCase)) {
            break
        }
        [void]$body.AppendLine($lines[$index])
    }
    @(Normalize-PowerBuilderBody $body.ToString())
}

function Get-NormalizedPreviewBody([string]$Preview) {
    $lines = @(($Preview -replace "`r", '') -split "`n")
    $body = if ($lines.Count -gt 2) { $lines[1..($lines.Count - 2)] -join "`n" } else { "" }
    @(Normalize-PowerBuilderBody $body)
}

function Get-LcsDifference([string[]]$Source, [string[]]$Reconstructed) {
    $sourceCount = $Source.Count
    $reconstructedCount = $Reconstructed.Count
    $lengths = [int[,]]::new($sourceCount + 1, $reconstructedCount + 1)
    for ($left = $sourceCount - 1; $left -ge 0; $left--) {
        for ($right = $reconstructedCount - 1; $right -ge 0; $right--) {
            $lengths[$left, $right] = if ($Source[$left] -eq $Reconstructed[$right]) {
                1 + $lengths[($left + 1), ($right + 1)]
            } else {
                $skipSource = $lengths[($left + 1), $right]
                $skipReconstructed = $lengths[$left, ($right + 1)]
                [Math]::Max($skipSource, $skipReconstructed)
            }
        }
    }
    $sourceOnly = [Collections.Generic.List[string]]::new()
    $reconstructedOnly = [Collections.Generic.List[string]]::new()
    $left = 0
    $right = 0
    while ($left -lt $sourceCount -and $right -lt $reconstructedCount) {
        if ($Source[$left] -eq $Reconstructed[$right]) {
            $left++
            $right++
        } else {
            $skipSource = $lengths[($left + 1), $right]
            $skipReconstructed = $lengths[$left, ($right + 1)]
            if ($skipSource -ge $skipReconstructed) {
            $sourceOnly.Add($Source[$left])
            $left++
            } else {
                $reconstructedOnly.Add($Reconstructed[$right])
                $right++
            }
        }
    }
    while ($left -lt $sourceCount) { $sourceOnly.Add($Source[$left]); $left++ }
    while ($right -lt $reconstructedCount) { $reconstructedOnly.Add($Reconstructed[$right]); $right++ }
    [pscustomobject]@{
        SourceOnly = @($sourceOnly)
        ReconstructedOnly = @($reconstructedOnly)
        Matched = $lengths[0, 0]
    }
}

function Get-ControlShape([string[]]$Statements) {
    [pscustomobject]@{
        Ifs = @($Statements | Where-Object { $_ -match '^(if|elseif).+then$' }).Count
        Elses = @($Statements | Where-Object { $_ -eq 'else' -or $_ -match '^elseif' }).Count
        EndIfs = @($Statements | Where-Object { $_ -eq 'endif' }).Count
        ChooseMarkers = @($Statements | Where-Object { $_ -match '^(choosecase|case|endchoose)' }).Count
        Gotos = @($Statements | Where-Object { $_ -match 'goto' }).Count
    }
}

function ConvertTo-SafeCanonicalBody([string[]]$Statements) {
    $expanded = [Collections.Generic.List[string]]::new()
    foreach ($statement in $Statements) {
        if ($statement -match '^if(.+)then(.+)$') {
            $expanded.Add("if$($Matches[1])then")
            $expanded.Add($Matches[2])
            $expanded.Add("endif")
            continue
        }
        if ($statement -match '^(any|blob|boolean|byte|char|date|datetime|decimal|double|integer|long|real|string|time|uint|ulong)([a-z_][a-z0-9_]*),([a-z_][a-z0-9_,]*)$') {
            $typeName = $Matches[1]
            $expanded.Add("$typeName$($Matches[2])")
            foreach ($name in $Matches[3] -split ',') { $expanded.Add("$typeName$name") }
            continue
        }
        $expanded.Add($statement)
    }
    @($expanded | ForEach-Object {
        $statement = $_
        if ($statement -match '^if.*then$') {
            $statement = $statement.Replace('(', '').Replace(')', '')
        } elseif ($statement -match '^return\((.*)\)$') {
            $statement = "return$($Matches[1])"
        } elseif ($statement -match '^destroy\((.*)\)$') {
            $statement = "destroy$($Matches[1])"
        }
        $statement
    })
}

function Get-StatementKinds([string[]]$Statements) {
    $kinds = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($statement in $Statements) {
        if ($statement -match '^(if|elseif).+then$') { [void]$kinds.Add("condition_expression"); continue }
        if ($statement -match '^(else|endif|choosecase|case|endchoose)' -or $statement -match 'goto') {
            [void]$kinds.Add("control_flow")
            continue
        }
        if ($statement -match '^return') { [void]$kinds.Add("return_expression"); continue }
        if ($statement -match '(^|=)create\b' -or $statement -match '^destroy\b') {
            [void]$kinds.Add("object_lifecycle")
            continue
        }
        if ($statement -match '=') { [void]$kinds.Add("assignment"); continue }
        if ($statement -match '\(' -or $statement -match '\bevent\b' -or $statement -match '^call') {
            [void]$kinds.Add("call_or_event")
            continue
        }
        if ($statement -match '^[a-z_][a-z0-9_]*(\[\])?[a-z_][a-z0-9_]*(\[.*\])?$') {
            [void]$kinds.Add("declaration")
            continue
        }
        [void]$kinds.Add("other_statement")
    }
    @($kinds | Sort-Object)
}

function Get-RootCauseFamily(
    [string[]]$SourceOnly,
    [string[]]$ReconstructedOnly,
    [bool]$StructuralResidual,
    [string]$PrimaryFamily
) {
    $sourceText = $SourceOnly -join " || "
    $reconstructedText = $ReconstructedOnly -join " || "
    if ($SourceOnly.Count -eq 0 -and $ReconstructedOnly.Count -eq 0) {
        return "single_quote_literal_normalization"
    }
    if ($reconstructedText -match '__get_attribute_item') {
        return "datawindow_attribute_lowering"
    }
    if ($reconstructedText -match 'getclassdefinition\(\)') {
        return "classdefinition_accessor_mapping"
    }
    if ($reconstructedText -match 'ancestorreturnvalue') {
        return "compiler_scaffolding_not_collapsed"
    }
    if ($sourceText -match 'invo_constants\.color_' -or
        $sourceText -match 'cst_filetype_(reg|ini|xml)' -or
        (($sourceText -match '=database' -or $sourceText -match '=file') -and
            $reconstructedText -match '="(database|file)"')) {
        return "symbolic_constant_elided"
    }
    if (($sourceText -match '^(long|boolean)[a-z0-9_]+=(0|false)( \|\| |$)' -and
            $ReconstructedOnly.Count -gt 0) -or
        ($sourceText -match '^callsuper::' -and $ReconstructedOnly.Count -eq 0)) {
        return "source_construct_optimized_away"
    }
    if ($StructuralResidual -and
        @($SourceOnly | Where-Object { $_ -match '^if.+then.+' }).Count -gt 0) {
        return "inline_if_vs_block_form"
    }
    if ($PrimaryFamily -eq "condition_expression") {
        return "equivalent_expression_spelling"
    }
    if ($sourceText -match '^[a-z_][a-z0-9_]+[a-z_][a-z0-9_]+,[a-z_][a-z0-9_]+$') {
        return "grouped_vs_split_declaration"
    }
    "unclassified"
}

function Get-PostSafeFormBlocker(
    [string[]]$SourceOnly,
    [string[]]$ReconstructedOnly,
    [bool]$SafeFormEquivalent,
    [string]$RootCauseFamily
) {
    if ($SafeFormEquivalent) { return "resolved_by_safe_form_canonicalization" }
    $sourceText = $SourceOnly -join " || "
    $reconstructedText = $ReconstructedOnly -join " || "
    if ($RootCauseFamily -eq "symbolic_constant_elided" -or
        (($sourceText -match '(\bcache_id\b|\bis_pfckey\b|returnfailure)') -and
            $reconstructedText -match '("pfc listview"|"pfc_lvi_key"|-1)')) {
        return "symbolic_constant_elided"
    }
    $RootCauseFamily
}

$analysisRoot = Join-Path $WorkspaceRoot "pb2022-analysis"
$rows = [Collections.Generic.List[object]]::new()
foreach ($corpus in @("exmmain", "appexmfe", "pfcapsrv")) {
    $reportPath = Join-Path $analysisRoot "whole-function-$ReportGeneration-$corpus\decode-report.json"
    $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
    foreach ($entry in $report.entries) {
        foreach ($region in $entry.pcode_regions) {
            $preview = $region.semantic_preview
            if (@($preview.reconstructed_ifs).Count -eq 0 -or
                $preview.evidence.function_reconstruction -ne "mismatch") {
                continue
            }
            $source = @(Get-NormalizedSourceBody $preview.evidence.function_comparison.source_reference)
            $reconstructed = @(Get-NormalizedPreviewBody $preview.powerscript_like)
            $difference = Get-LcsDifference $source $reconstructed
            $sourceShape = Get-ControlShape $source
            $reconstructedShape = Get-ControlShape $reconstructed
            $safeCanonicalSource = @(ConvertTo-SafeCanonicalBody $source)
            $safeCanonicalReconstructed = @(ConvertTo-SafeCanonicalBody $reconstructed)
            $safeFormEquivalent =
                $safeCanonicalSource.Count -eq $safeCanonicalReconstructed.Count -and
                (Compare-Object $safeCanonicalSource $safeCanonicalReconstructed -SyncWindow 0).Count -eq 0
            $allDifferent = @($difference.SourceOnly) + @($difference.ReconstructedOnly)
            $kinds = @(Get-StatementKinds $allDifferent)
            $structuralResidual =
                $sourceShape.Ifs -ne $reconstructedShape.Ifs -or
                $sourceShape.Elses -ne $reconstructedShape.Elses -or
                $sourceShape.EndIfs -ne $reconstructedShape.EndIfs -or
                $sourceShape.ChooseMarkers -ne $reconstructedShape.ChooseMarkers -or
                $reconstructedShape.Gotos -gt 0
            $primaryFamily = if ($structuralResidual) {
                "residual_control_flow"
            } elseif ($kinds -contains "condition_expression") {
                "condition_expression"
            } elseif ($kinds.Count -eq 1) {
                $kinds[0]
            } elseif ($kinds -contains "assignment") {
                "mixed_with_assignment"
            } elseif ($kinds -contains "call_or_event") {
                "mixed_with_call_or_event"
            } elseif ($kinds -contains "return_expression") {
                "mixed_with_return"
            } else {
                "mixed_or_other"
            }
            $rootCauseFamily = Get-RootCauseFamily `
                @($difference.SourceOnly) `
                @($difference.ReconstructedOnly) `
                $structuralResidual `
                $primaryFamily
            $postSafeFormBlocker = Get-PostSafeFormBlocker `
                @($difference.SourceOnly) `
                @($difference.ReconstructedOnly) `
                $safeFormEquivalent `
                $rootCauseFamily
            $rows.Add([pscustomobject]@{
                corpus = $corpus
                entry = $entry.name
                function = $region.definition.name
                source_reference = $preview.evidence.function_comparison.source_reference
                source_statements = $source.Count
                reconstructed_statements = $reconstructed.Count
                lcs_matched_statements = $difference.Matched
                source_if_count = $sourceShape.Ifs
                source_else_count = $sourceShape.Elses
                source_choose_markers = $sourceShape.ChooseMarkers
                reconstructed_goto_count = $reconstructedShape.Gotos
                structural_residual = $structuralResidual
                safe_form_equivalent = $safeFormEquivalent
                mismatch_kinds = @($kinds)
                primary_family = $primaryFamily
                root_cause_family = $rootCauseFamily
                post_safe_form_blocker = $postSafeFormBlocker
                source_only = @($difference.SourceOnly)
                reconstructed_only = @($difference.ReconstructedOnly)
            })
        }
    }
}

$ifRows = @($rows | Where-Object { $_.source_choose_markers -eq 0 })
$chooseRows = @($rows | Where-Object { $_.source_choose_markers -gt 0 })
$result = [pscustomobject]@{
    report_generation = $ReportGeneration
    total_structured_mismatches = $rows.Count
    if_family_mismatches = $ifRows.Count
    adjacent_choose_mismatches = $chooseRows.Count
    primary_families = @(
        $ifRows | Group-Object primary_family | Sort-Object Count -Descending |
            ForEach-Object { [pscustomobject]@{ family = $_.Name; count = $_.Count } }
    )
    overlapping_kinds = @(
        $ifRows | ForEach-Object { $_.mismatch_kinds } | Group-Object | Sort-Object Count -Descending |
            ForEach-Object { [pscustomobject]@{ kind = $_.Name; count = $_.Count } }
    )
    root_cause_families = @(
        $ifRows | Group-Object root_cause_family | Sort-Object Count -Descending |
            ForEach-Object { [pscustomobject]@{ family = $_.Name; count = $_.Count } }
    )
    safe_form_equivalent = @($ifRows | Where-Object { $_.safe_form_equivalent }).Count
    post_safe_form_families = @(
        $ifRows | Group-Object post_safe_form_blocker | Sort-Object Count -Descending |
            ForEach-Object { [pscustomobject]@{ family = $_.Name; count = $_.Count } }
    )
    rows = @($rows)
}

$result.primary_families | Format-Table -AutoSize
Write-Output "if_family_mismatches=$($result.if_family_mismatches) adjacent_choose=$($result.adjacent_choose_mismatches)"
Write-Output "Root-cause families:"
$result.root_cause_families | Format-Table -AutoSize
Write-Output "safe_form_equivalent=$($result.safe_form_equivalent)"
Write-Output "After safe-form canonicalization:"
$result.post_safe_form_families | Format-Table -AutoSize
Write-Output "Overlapping statement kinds:"
$result.overlapping_kinds | Format-Table -AutoSize
if ($JsonOut) {
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $JsonOut -Encoding utf8
    Write-Output "JSON: $JsonOut"
}
