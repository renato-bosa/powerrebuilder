param(
    [string]$WorkspaceRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$ReportGeneration = "v10",
    [string]$JsonOut = (Join-Path $WorkspaceRoot "pb2022-analysis\v10-decision-gate-data.json")
)

$ErrorActionPreference = "Stop"

# Reuse the source/body normalization used by the earlier mismatch gate without
# executing that script's report-specific analysis section.
$helperPath = Join-Path $PSScriptRoot "analyze_forward_single_arm_mismatches.ps1"
$helperText = [IO.File]::ReadAllText($helperPath, [Text.Encoding]::UTF8)
$helperStart = $helperText.IndexOf('function Remove-PowerBuilderComments', [StringComparison]::Ordinal)
$analysisMarker = '$analysisRoot = Join-Path $WorkspaceRoot "pb2022-analysis"'
$analysisStart = $helperText.IndexOf($analysisMarker, [StringComparison]::Ordinal)
if ($helperStart -lt 0 -or $analysisStart -lt 0) { throw "Could not locate helper boundary in $helperPath" }
Invoke-Expression $helperText.Substring($helperStart, $analysisStart - $helperStart)

function Get-FirstDirectDifference([string[]]$Source, [string[]]$Reconstructed) {
    $limit = [Math]::Min($Source.Count, $Reconstructed.Count)
    $index = 0
    while ($index -lt $limit -and $Source[$index] -eq $Reconstructed[$index]) { $index++ }
    [pscustomobject]@{
        index = $index
        source = if ($index -lt $Source.Count) { $Source[$index] } else { $null }
        reconstructed = if ($index -lt $Reconstructed.Count) { $Reconstructed[$index] } else { $null }
    }
}

function Get-ControlKeywords([string[]]$Statements) {
    @($Statements | Where-Object {
        $_ -match '^(if|elseif|else$|endif$|choosecase|case|endchoose|for|next$|do$|loop|try$|catch|finally$|endtry$)' -or
        $_ -match '\bgoto\b'
    })
}

function New-CompiledConstantAnalysisContext($Entry, $Region) {
    $types = @{}
    $shadowed = @{}
    $add = {
        param($Variable, [bool]$AlwaysShadow)
        if ($null -eq $Variable -or [string]::IsNullOrEmpty($Variable.name)) { return }
        $name = $Variable.name.ToLowerInvariant()
        $null = $types[$name] = [string]($Variable.type_name)
        if ($AlwaysShadow -or -not [bool]$Variable.is_constant) { $null = $shadowed[$name] = $true }
    }
    $objectDefinition = @($Entry.object_definitions | Where-Object {
        $_.type_name -ieq $Region.object_type_name
    } | Select-Object -First 1)
    if ($objectDefinition.Count) {
        foreach ($property in @($objectDefinition[0].properties)) { & $add $property $false }
    }
    foreach ($variable in @($Region.global_variables)) { & $add $variable $false }
    foreach ($variable in @($Region.variables)) { & $add $variable $false }
    foreach ($parameter in @($Region.definition.parameters)) { & $add $parameter $true }
    return [pscustomobject]@{
        owner = ([string]$Region.object_type_name).ToLowerInvariant()
        types = $types
        shadowed = $shadowed
    }
}

function Get-CompiledConstantLiteral($Constant) {
    switch ([string]($Constant.value.kind)) {
        "signed_integer" { return ([string]($Constant.value.value)).ToLowerInvariant() }
        "unsigned_integer" { return ([string]($Constant.value.value)).ToLowerInvariant() }
        "boolean" { return ([string]($Constant.value.value)).ToLowerInvariant() }
        "string" {
            $value = [string]($Constant.value.value)
            if ($value -match '[\x00-\x1F~''"]') { return $null }
            return '"' + $value.ToLowerInvariant() + '"'
        }
        default { return $null }
    }
}

function Get-CompiledConstantValueKey($Constant) {
    "$($Constant.owner_type_name.ToLowerInvariant())|$($Constant.type_ref)|$($Constant.value.kind)|$($Constant.value.value)"
}

function Resolve-CompiledConstantToken([string]$Token, $Catalog, $Context) {
    $segments = @($Token -split '\.')
    $name = $segments[-1].ToLowerInvariant()
    if ($segments.Count -eq 1) {
        if ($Context.shadowed.ContainsKey($name)) { return $null }
        $owner = $Context.owner
    } else {
        $qualifier = $segments[-2].ToLowerInvariant()
        if ($Context.types.ContainsKey($qualifier)) {
            $owner = ([string]$Context.types[$qualifier]).ToLowerInvariant()
        } else {
            $owner = (($segments[0..($segments.Count - 2)] -join '.').ToLowerInvariant())
            if (-not $Catalog.owners.ContainsKey($owner)) { return $null }
        }
    }
    $nameKey = "$owner|$name"
    [object[]]$named = if ($Catalog.by_name.ContainsKey($nameKey)) { $Catalog.by_name[$nameKey] } else { @() }
    if (($null -eq $named -or $named.Count -eq 0) -and $segments.Count -eq 1) {
        $nameKey = "|$name"
        [object[]]$named = if ($Catalog.by_name.ContainsKey($nameKey)) { $Catalog.by_name[$nameKey] } else { @() }
    }
    if ($named.Count -ne 1) { return $null }
    $constant = $named[0]
    $valueKey = Get-CompiledConstantValueKey $constant
    [object[]]$candidates = $Catalog.by_value[$valueKey]
    if ($candidates.Count -ne 1) { return $null }
    Get-CompiledConstantLiteral $constant
}

function ConvertTo-CompiledSymbolCanonicalStatement([string]$Statement, $Catalog, $Context) {
    $output = [Text.StringBuilder]::new()
    $index = 0
    $delimiter = [char]0
    $escaped = $false
    while ($index -lt $Statement.Length) {
        $character = $Statement[$index]
        if ($delimiter -ne [char]0) {
            [void]$output.Append($character)
            if ($escaped) { $escaped = $false }
            elseif ($character -eq '~') { $escaped = $true }
            elseif ($character -eq $delimiter) { $delimiter = [char]0 }
            $index++
            continue
        }
        if ($character -in @('"', "'")) {
            $delimiter = $character
            [void]$output.Append($character)
            $index++
            continue
        }
        if (-not ([char]::IsLetter($character) -or $character -eq '_')) {
            [void]$output.Append($character)
            $index++
            continue
        }
        $start = $index
        $index++
        while ($index -lt $Statement.Length) {
            $candidate = $Statement[$index]
            if ([char]::IsLetterOrDigit($candidate) -or $candidate -eq '_') {
                $index++
            } elseif ($candidate -eq '.' -and $index + 1 -lt $Statement.Length -and
                ([char]::IsLetter($Statement[$index + 1]) -or $Statement[$index + 1] -eq '_')) {
                $index += 2
                while ($index -lt $Statement.Length -and
                    ([char]::IsLetterOrDigit($Statement[$index]) -or $Statement[$index] -eq '_')) { $index++ }
            } else { break }
        }
        $token = $Statement.Substring($start, $index - $start)
        $literal = if ($index -lt $Statement.Length -and $Statement[$index] -eq '(') {
            $null
        } else {
            Resolve-CompiledConstantToken $token $Catalog $Context
        }
        [void]$output.Append($(if ($null -ne $literal) { $literal } else { $token }))
    }
    $output.ToString()
}

function ConvertTo-CompiledSymbolCanonicalBody([string[]]$Statements, $Catalog, $Context) {
    @($Statements | ForEach-Object { ConvertTo-CompiledSymbolCanonicalStatement $_ $Catalog $Context })
}

function Test-PowerBuilderDeclaration([string]$Statement) {
    $Statement -match '^(any|blob|boolean|byte|char|date|datetime|decimal|double|integer|long|real|string|time|uint|ulong|n_[a-z0-9_]+|w_[a-z0-9_]+|u_[a-z0-9_]+|datawindow|datastore|powerobject)'
}

function Get-FirstMismatchFamily($Row) {
    $source = [string]$Row.first_source
    $reconstructed = [string]$Row.first_reconstructed
    $sourceOnly = @($Row.source_only) -join ' || '
    $reconstructedOnly = @($Row.reconstructed_only) -join ' || '
    $allReconstructed = @($Row.oracle_canonical_reconstructed) -join ' || '
    $caseMarker = [string][char]1 + 'case'

    if ($source -match '^triggerevent\(this,' -and $reconstructed -match '^triggerevent\(') {
        return 'implicit_this_event_receiver'
    }
    if ($reconstructed -match 'ancestorreturnvalue|^n_msg(?:::)?message$' -or
        (($reconstructedOnly -match 'ancestorreturnvalue|::message\.returnvalue') -and
            $source -match '^(callsuper::|call[a-z0-9_]+::)')) {
        return 'event_return_scaffolding'
    }
    if ($reconstructed.Contains($caseMarker) -or $source -match '^choosecase') {
        return 'choose_case_lowering'
    }
    if ($source -match '^if' -and $reconstructed -match '^if' -and
        $allReconstructed -match '\bgoto') {
        return 'structured_if_not_recovered'
    }
    if (($source -match '\b(invo_constants|lnvo_constants)\.' -and $reconstructed -match '\d') -or
        ($source -match '^return[a-z_][a-z0-9_]*$' -and $reconstructed -match '^return-?\d+$') -or
        ($source -match '\bcst_[a-z0-9_]+' -and $reconstructed -match '\d') -or
        ($source -match 'is_msgsrc=(database|file)then' -and $reconstructed -match '="(database|file)"then')) {
        return 'compiled_symbol_resolution_boundary'
    }
    if ((Test-PowerBuilderDeclaration $source) -and (Test-PowerBuilderDeclaration $reconstructed)) {
        if ($source -match '=' -and $reconstructed -notmatch '=') {
            return 'source_initializer_not_preserved'
        }
        if ($source -match ',' -or ($source -match '\[\]' -and $reconstructed -notmatch '\[\]')) {
            return 'array_or_grouped_declaration_form'
        }
    }
    if (($source -match '\[\]' -and $reconstructed -notmatch '\[\]') -or
        ($source -match 'item\[\]' -and $reconstructed -match '^item=')) {
        return 'array_marker_not_preserved'
    }
    if ($reconstructed -match '__get_attribute_item|getclassdefinition\(\)|getis(userdefined|systemtype)|getsystemfunction') {
        return 'compiled_accessor_not_collapsed'
    }
    if ($reconstructed -match '\bparent\.' -and $source -notmatch '\bparent\.') {
        return 'receiver_qualification_or_member_mapping'
    }
    if ($source -match '^callsuper::' -and $reconstructed -match '^returnof_') {
        return 'source_super_call_absent_from_pcode'
    }
    if (($source -match '^call[a-z0-9_]+::' -and $reconstructed -match '^callsuper::') -or
        ($source -match '^callsuper::' -and $reconstructed -match '^callsuper::')) {
        return 'ancestor_dispatch_spelling'
    }
    if (Test-PowerBuilderDeclaration $reconstructed) {
        return 'compiler_temporary_or_declaration_placement'
    }
    if (@($Row.source_only).Count -eq 0 -and @($Row.reconstructed_only).Count -eq 0) {
        return 'powerbuilder_quote_escape_equivalence'
    }
    if ($null -eq $Row.first_source -or $null -eq $Row.first_reconstructed) {
        return 'extra_or_missing_statement'
    }
    if ($source -match '^return' -and $reconstructed -match '^return') {
        return 'return_expression_mapping'
    }
    if ($source -match '^if' -or $source -match '^(else|endif|for|do|loop|choosecase|case)') {
        return 'other_control_flow_mismatch'
    }
    if ($source -match '\(' -or $reconstructed -match '\(') {
        return 'call_or_receiver_mapping'
    }
    return 'other_statement_mapping'
}

function Get-UnresolvedFamily([string]$Mnemonic, [string]$Reason) {
    if ($Reason -notmatch 'semantic rule not implemented') { return 'dependent_stack_or_context_failure' }
    if ($Mnemonic -match '^DB' -or $Mnemonic -in @('ENTER_EMBEDDED', 'EXIT_EMBEDDED')) { return 'sql_and_embedded_sql' }
    if ($Mnemonic -in @('THROW_EXCEPTION', 'POP_TRY')) { return 'exception_handling' }
    if ($Mnemonic -match '^PUSH_CONST_(DEC|DOUBLE)$') { return 'typed_numeric_constants' }
    if ($Mnemonic -match '^(CLASS_CALL|DOTFUNCCALL|FREE_INV_METH_ARGS)') { return 'call_protocol' }
    if ($Mnemonic -match '^(INCR_|ADDASSIGN_|MOD_)' -or $Mnemonic -eq 'INT') { return 'numeric_and_compound_operations' }
    if ($Mnemonic -in @('DUP_STACKED_LVALUE', 'ARRAY_BOUND_INFO', 'CREATE_USING')) { return 'lvalue_array_and_creation' }
    if ($Mnemonic -match '^PB2022_OP_') { return 'unknown_pb2022_opcode' }
    return 'other_direct_semantic_gap'
}

$analysisRoot = Join-Path $WorkspaceRoot "pb2022-analysis"
$knownRows = [Collections.Generic.List[object]]::new()
$compiledSymbolVerifiedChecked = 0
$compiledSymbolVerifiedReproduced = 0
$compiledSymbolValidationRows = [Collections.Generic.List[object]]::new()
$knownUnresolvedRows = [Collections.Generic.List[object]]::new()
foreach ($corpus in @("exmmain", "appexmfe", "pfcapsrv")) {
    $reportPath = Join-Path $analysisRoot "whole-function-$ReportGeneration-$corpus\decode-report.json"
    $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
    $compiledConstants = @($report.entries | ForEach-Object { @($_.compiled_constants) })
    $compiledOwners = @{}
    $compiledByName = @{}
    $compiledByValue = @{}
    foreach ($constant in $compiledConstants) {
        $owner = $constant.owner_type_name.ToLowerInvariant()
        if ($owner) { $null = $compiledOwners[$owner] = $true }
        $nameKey = "$owner|$($constant.name.ToLowerInvariant())"
        $compiledByName[$nameKey] = if ($compiledByName.ContainsKey($nameKey)) {
            @($compiledByName[$nameKey]) + @($constant)
        } else {
            @($constant)
        }
        $valueKey = Get-CompiledConstantValueKey $constant
        $compiledByValue[$valueKey] = if ($compiledByValue.ContainsKey($valueKey)) {
            @($compiledByValue[$valueKey]) + @($constant)
        } else {
            @($constant)
        }
    }
    $compiledCatalog = [pscustomobject]@{
        constants = $compiledConstants
        owners = $compiledOwners
        by_name = $compiledByName
        by_value = $compiledByValue
    }
    foreach ($entry in $report.entries) {
        foreach ($region in $entry.pcode_regions) {
            $preview = $region.semantic_preview
            foreach ($unresolved in @($preview.unresolved)) {
                $knownUnresolvedRows.Add([pscustomobject]@{
                    corpus = $corpus
                    function_id = "$corpus::$($entry.name)::$($region.region_index)::$($preview.signature)"
                    opcode = [int]$unresolved.opcode
                    mnemonic = $unresolved.mnemonic
                    reason = $unresolved.reason
                })
            }
            if (-not $preview.evidence.semantic_rules_complete) { continue }
            $isCompiledSymbolValidation =
                $preview.evidence.function_comparison.verification_basis -eq "compiled_symbol_equivalence"
            if ($preview.evidence.function_reconstruction -eq "verified" -and
                -not $isCompiledSymbolValidation) { continue }
            $source = @(Get-NormalizedSourceBody $preview.evidence.function_comparison.source_reference)
            $reconstructed = @(Get-NormalizedPreviewBody $preview.powerscript_like)
            $canonicalSource = @(ConvertTo-SafeCanonicalBody $source)
            $canonicalReconstructed = @(ConvertTo-SafeCanonicalBody $reconstructed)
            $constantContext = New-CompiledConstantAnalysisContext $entry $region
            $oracleSource = @(ConvertTo-CompiledSymbolCanonicalBody $canonicalSource $compiledCatalog $constantContext)
            $oracleReconstructed = @(ConvertTo-CompiledSymbolCanonicalBody $canonicalReconstructed $compiledCatalog $constantContext)
            if ($isCompiledSymbolValidation) {
                $compiledSymbolVerifiedChecked++
                $reproduced = ($oracleSource.Count -eq $oracleReconstructed.Count -and
                    (Compare-Object $oracleSource $oracleReconstructed -SyncWindow 0).Count -eq 0)
                if ($reproduced) {
                    $compiledSymbolVerifiedReproduced++
                }
                $compiledSymbolValidationRows.Add([pscustomobject]@{
                    corpus = $corpus
                    entry = $entry.name
                    signature = $preview.signature
                    reproduced = $reproduced
                    source = $oracleSource
                    reconstructed = $oracleReconstructed
                })
                continue
            }
            $difference = Get-LcsDifference $oracleSource $oracleReconstructed
            $first = Get-FirstDirectDifference $oracleSource $oracleReconstructed
            $row = [pscustomobject]@{
                corpus = $corpus
                entry = $entry.name
                region_index = $region.region_index
                signature = $preview.signature
                source_reference = $preview.evidence.function_comparison.source_reference
                source_statement_count = $source.Count
                reconstructed_statement_count = $reconstructed.Count
                common_prefix_count = $first.index
                first_source = $first.source
                first_reconstructed = $first.reconstructed
                source_only = @($difference.SourceOnly)
                reconstructed_only = @($difference.ReconstructedOnly)
                source_control = @(Get-ControlKeywords $oracleSource)
                reconstructed_control = @(Get-ControlKeywords $oracleReconstructed)
                reconstructed_ifs = @($preview.reconstructed_ifs).Count
                try_catch_structures = @($preview.try_catch_structures).Count
                source = $source
                reconstructed = $reconstructed
                safe_canonical_source = $canonicalSource
                safe_canonical_reconstructed = $canonicalReconstructed
                oracle_canonical_source = $oracleSource
                oracle_canonical_reconstructed = $oracleReconstructed
            }
            $row | Add-Member -NotePropertyName first_mismatch_family -NotePropertyValue (Get-FirstMismatchFamily $row)
            $knownRows.Add($row)
        }
    }
}

$targetPath = Join-Path $analysisRoot "replicacao-snapshot-$ReportGeneration\decode-report.json"
$target = Get-Content -LiteralPath $targetPath -Raw | ConvertFrom-Json
$targetRows = [Collections.Generic.List[object]]::new()
foreach ($entry in $target.entries) {
    foreach ($region in $entry.pcode_regions) {
        $preview = $region.semantic_preview
        if ($preview.semantically_complete) { continue }
        $functionId = "$($entry.name)::$($region.region_index)::$($preview.signature)"
        foreach ($unresolved in @($preview.unresolved)) {
            $targetRows.Add([pscustomobject]@{
                function_id = $functionId
                entry = $entry.name
                region_index = $region.region_index
                signature = $preview.signature
                opcode = [int]$unresolved.opcode
                opcode_hex = ('0x{0:X4}' -f [int]$unresolved.opcode)
                mnemonic = $unresolved.mnemonic
                reason = $unresolved.reason
                offset = $unresolved.offset
            })
        }
    }
}

$knownMismatchFamilies = @(
    $knownRows | Group-Object first_mismatch_family | Sort-Object Count -Descending | ForEach-Object {
        $group = @($_.Group)
        [pscustomobject]@{
            family = $_.Name
            functions = $group.Count
            corpora = @($group.corpus | Sort-Object -Unique)
            examples = @($group | Select-Object -First 3 | ForEach-Object {
                [pscustomobject]@{
                    corpus = $_.corpus
                    entry = $_.entry
                    signature = $_.signature
                    source = $_.first_source
                    reconstructed = $_.first_reconstructed
                }
            })
        }
    }
)

$knownUnresolvedIndex = @{}
foreach ($knownUnresolved in $knownUnresolvedRows) {
    $key = "$($knownUnresolved.opcode)|$($knownUnresolved.mnemonic)"
    if (-not $knownUnresolvedIndex.ContainsKey($key)) {
        $knownUnresolvedIndex[$key] = [pscustomobject]@{
            occurrences = 0
            functions = @{}
            corpora = @{}
        }
    }
    $stats = $knownUnresolvedIndex[$key]
    $stats.occurrences++
    $null = $stats.functions[$knownUnresolved.function_id] = $true
    $null = $stats.corpora[$knownUnresolved.corpus] = $true
}

$targetUnresolvedGroups = @(
    $targetRows | Group-Object opcode,mnemonic,reason | ForEach-Object {
        $group = @($_.Group)
        $opcode = $group[0].opcode
        $mnemonic = $group[0].mnemonic
        $knownStats = $knownUnresolvedIndex["$opcode|$mnemonic"]
        [pscustomobject]@{
            opcode = $opcode
            opcode_hex = $group[0].opcode_hex
            mnemonic = $mnemonic
            reason = $group[0].reason
            family = Get-UnresolvedFamily $mnemonic $group[0].reason
            occurrences = $group.Count
            functions = @($group.function_id | Sort-Object -Unique).Count
            examples = @($group | Select-Object -First 3 | ForEach-Object {
                "$($_.entry): $($_.signature)"
            })
            known_fixture_occurrences = if ($knownStats) { $knownStats.occurrences } else { 0 }
            known_fixture_functions = if ($knownStats) { $knownStats.functions.Count } else { 0 }
            known_fixture_corpora = if ($knownStats) { @($knownStats.corpora.Keys | Sort-Object) } else { @() }
        }
    } | Sort-Object -Property @{ Expression = 'occurrences'; Descending = $true }, mnemonic, reason
)

$targetUnresolvedFamilies = @(
    $targetRows | ForEach-Object {
        $_ | Add-Member -PassThru -NotePropertyName family -NotePropertyValue (
            Get-UnresolvedFamily $_.mnemonic $_.reason
        )
    } | Group-Object family | Sort-Object Count -Descending | ForEach-Object {
        $group = @($_.Group)
        $mnemonics = @($group | ForEach-Object { "$($_.opcode_hex) $($_.mnemonic)" } | Sort-Object -Unique)
        $knownOccurrences = 0
        $knownFunctions = @{}
        foreach ($targetOpcodeMnemonic in @($group | Select-Object opcode,mnemonic -Unique)) {
            $knownStats = $knownUnresolvedIndex["$($targetOpcodeMnemonic.opcode)|$($targetOpcodeMnemonic.mnemonic)"]
            if ($knownStats) {
                $knownOccurrences += $knownStats.occurrences
                foreach ($functionId in $knownStats.functions.Keys) { $null = $knownFunctions[$functionId] = $true }
            }
        }
        [pscustomobject]@{
            family = $_.Name
            occurrences = $group.Count
            functions = @($group.function_id | Sort-Object -Unique).Count
            opcode_mnemonics = $mnemonics
            known_fixture_occurrences = $knownOccurrences
            known_fixture_functions = $knownFunctions.Count
        }
    }
)

$result = [pscustomobject]@{
    report_generation = $ReportGeneration
    compiled_symbol_verified_checked = $compiledSymbolVerifiedChecked
    compiled_symbol_verified_reproduced = $compiledSymbolVerifiedReproduced
    compiled_symbol_validation = @($compiledSymbolValidationRows)
    known_mismatch_families = $knownMismatchFamilies
    known_complete_not_verified = @($knownRows)
    target_unresolved_families = $targetUnresolvedFamilies
    target_unresolved_groups = $targetUnresolvedGroups
    target_incomplete_unresolved = @($targetRows)
}
$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $JsonOut -Encoding utf8
$csvOut = [IO.Path]::ChangeExtension($JsonOut, '.target-unresolved.csv')
$targetUnresolvedGroups | Select-Object opcode_hex,mnemonic,reason,family,occurrences,functions,
    known_fixture_occurrences,known_fixture_functions,@{ Name = 'known_fixture_corpora'; Expression = { $_.known_fixture_corpora -join ';' } },
    @{ Name = 'examples'; Expression = { $_.examples -join ' | ' } } |
    Export-Csv -LiteralPath $csvOut -NoTypeInformation -Encoding utf8
Write-Output "known_complete_not_verified=$($knownRows.Count)"
Write-Output "compiled_symbol_verified_reproduced=$compiledSymbolVerifiedReproduced/$compiledSymbolVerifiedChecked"
Write-Output "target_incomplete_functions=$(@($targetRows.function_id | Sort-Object -Unique).Count)"
Write-Output "target_unresolved=$($targetRows.Count)"
Write-Output "JSON: $JsonOut"
Write-Output "CSV: $csvOut"
