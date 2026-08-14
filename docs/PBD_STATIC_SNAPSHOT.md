# Static PBD snapshot

The static snapshot is a read-only human view over an existing
`decode-report.json`. It does not run decompilation, add semantic rules, or
rewrite `powerscript_like`.

## Generate

From the repository root on Windows PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_static_snapshot.ps1 `
  -ReportPath C:\path\to\decode-report.json `
  -OutputPath C:\path\to\pbd-explorer.html
```

The result is one self-contained HTML file. It embeds the report and has no
external resources or server dependency, so it can be opened directly in a
browser.

## Views

- object and function navigation, search, and filters;
- the report's exact `powerscript_like`, including `/* unresolved ... */` and
  `goto` output;
- P-code instruction rows and existing operand/debug evidence;
- existing CFG blocks, edges, validation, and exception-region records;
- unresolved instructions, reconstructed `if` and `try/catch` records,
  declarations, variables, and other semantic evidence already present in the
  report;
- compiled constants as separate object-level evidence, classified as
  `unique` or `ambiguous` only by the compiled catalog already in the report.

The compiled-constant view does not associate a constant with a function and
does not substitute a symbolic name into `powerscript_like`.

## Current `replicacao.pbd` snapshot

The generated file is:

```text
pb2022-analysis/replicacao-snapshot-v10/replicacao-explorer.html
```

It contains report v10 data for 70 objects and 304 P-code regions/functions.
The reported instruction coverage is 96.86%, with 239
`semantically_complete` previews and 304 valid CFG records. These are report
coverage/status values, not claims that the target has been verified against a
known source.
