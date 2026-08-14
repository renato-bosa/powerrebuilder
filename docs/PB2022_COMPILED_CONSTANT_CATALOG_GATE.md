# PB2022 global value buffer and typed constant catalog gate

## Scope and result

This gate retains the compiled object's global value buffer and exposes
constant declarations as typed evidence. It does **not** replace literals with
symbolic names, alter `powerscript_like`, or add equivalences to the
known-source oracle.

The implementation now preserves, for every compiled constant declaration:

- declaring object type (or global scope);
- constant name and PowerBuilder type;
- raw four-byte value or buffer offset;
- conservatively decoded typed value.

Supported typed values in this gate are signed and unsigned integral values,
booleans, UTF-16 strings, and characters. Unsupported representations remain
explicitly `unresolved(raw)`; they are never guessed.

## String-buffer proof

A unit fixture proves that a string constant's high-bit-marked offset is
masked and resolved as a null-terminated UTF-16LE value in the retained global
buffer. Odd or out-of-range offsets remain unresolved.

The integration test
`crates/adapters/tests/pfcapsrv_constant_catalog.rs` reads only the compiled
OpenSourcePFC 2022 `pfcapsrv.pbl`. It does not open or index the matching
exported source. The compiled artifact independently yielded:

| Object | Constant | Raw offset | Decoded value |
|---|---|---:|---|
| `pfc_n_cst_lvsrv_datasource` | `cache_id` | `0x800000F0` | `pfc listview` |
| `pfc_n_cst_lvsrv_datasource` | `is_pfckey` | `0x80000170` | `pfc_lvi_key` |
| `pfc_n_cst_error` | `database` | `0x80000056` | `database` |
| `pfc_n_cst_error` | `ics_database` | `0x80000056` | `database` |
| `pfc_n_cst_error` | `file` | `0x80000068` | `file` |
| `pfc_n_cst_error` | `ics_file` | `0x80000068` | `file` |

Across `pfcapsrv`, 552 compiled constant declarations were recovered. All 42
string constants decoded successfully. Four non-string declarations remain
explicitly unresolved: one `double` and three `decimal` constants whose value
slots point to representations not interpreted by this gate.

## Typed resolution contract

`CompiledConstantCatalog::resolve` requires an exact declaring type, an exact
PowerBuilder type reference, and an exact decoded value. Its result is one of:

- `zero`: no candidate exists in that compiled type and value domain;
- `unique`: exactly one compiled declaration matches;
- `ambiguous`: multiple aliases match, with all candidates retained.

The synthetic test proves all three states and also proves that equal numeric
values of different PB types do not mix. The compiled-only integration test
then proves:

- a unique lookup for `cache_id`;
- an ambiguous lookup for `database`/`ics_database`;
- a zero-result lookup for a string absent from the compiled catalog.

The catalog intentionally performs no inheritance expansion yet. This keeps
the evidence boundary precise before deciding how constants should be exposed
to the renderer or oracle.

## Three-corpus regression run

Report schema v9 adds `compiled_constants` evidence and summary counts. The
three public corpora were regenerated without changing rendering or oracle
rules:

| Corpus | Functions compared | Verified | Normalized equality | Safe canonicalization | Constants | String constants |
|---|---:|---:|---:|---:|---:|---:|
| `exmmain` | 17 | 7 | 6 | 1 | 0 | 0 |
| `appexmfe` | 163 | 103 | 101 | 2 | 0 | 0 |
| `pfcapsrv` | 1,693 | 385 | 324 | 61 | 552 | 42 |
| **Total** | **1,873** | **495** | **431** | **64** | **552** | **42** |

SHA-256 comparison of every v8 and v9 preview found 0 differences in 1,873
files. Therefore `function_reconstruction = verified` remains 495/1,873
(26.43%), with zero regressions and zero accidental promotions.

Reproduced reports:

- `pb2022-analysis/whole-function-v9-exmmain/decode-report.json`;
- `pb2022-analysis/whole-function-v9-appexmfe/decode-report.json`;
- `pb2022-analysis/whole-function-v9-pfcapsrv/decode-report.json`.

## Decision boundary

This gate establishes recoverability, not presentation policy. No symbolic
substitution should be enabled until we decide separately:

1. how exact-owner and inherited catalogs enter expression context;
2. whether unique symbols belong in decompiler output, annotations, or both;
3. how the oracle should treat a compiled symbol and its literal as equivalent
   without learning names from the known source;
4. how ambiguous aliases remain visible without selecting an invented original
   spelling.
