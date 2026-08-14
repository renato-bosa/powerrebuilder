# PB 2022 typed numeric constant gate

## Scope

This gate implements only `PUSH_CONST_DEC` (`0x0036`) and
`PUSH_CONST_DOUBLE` (`0x0038`) as typed producers for the existing expression
stack. It does not change CFG reconstruction, source-oracle canonicalization,
constant declarations, call handling, or any other opcode family.

The v10 `pfcapsrv` report supplies 440 occurrences in functions with matching
PB 2022 source: 309 decimal records in 58 functions and 131 double records in
47 functions (91 functions in the union). The compiled records were read from
the extracted PBL entries at each validated function's `stack_buffer_offset`;
the source was used only as an oracle, never as decoder input.

## Empirical PB 2022 representation

Both instructions carry a 32-bit little-endian offset assembled from their two
16-bit operand words. The offset addresses the function stack buffer rather
than containing the number inline.

| Opcode | Observed compiled representation | Known-source evidence |
|---|---|---|
| `PUSH_CONST_DEC` | 16-byte record. Bytes 0..6 are a little-endian magnitude; bytes 7..13 are zero in all 309 observations; byte 14 is sign (`0` in 305 records, `1` in 4); byte 15 is scale (`0..14`). | Magnitude/scale reproduce literals including `10.0`, `0.393700787`, and `100.000`. The only four sign-1 records reproduce exactly `-1.5372`, `-0.4986`, `-0.9689`, and `-0.2040` in `of_xyz2rgb`. |
| `PUSH_CONST_DOUBLE` | 8-byte IEEE-754 binary64, little-endian. All 131 records are in bounds and finite; all offsets are 8-byte aligned. | The bit patterns reproduce the constants used by the known source, including `1`, `2`, `255`, `1440`, and binary64 pi. `of_twipsperpixelx/y` reconstruct `1440 / ...`; `of_deg2rad` reconstructs the compiled value of the source constant `PI` as the round-trippable literal `3.141592653589793`. |

The decimal result preserves the compiled scale. This is why a record for
`-0.2040` remains `-0.2040`, while a scale-zero record is emitted as an integer
spelling. Double rendering uses Rust's shortest round-trippable binary64
spelling. These are semantic values, not guesses at the original typography.

### Conservative rejection boundary

The implementation leaves the instruction unresolved when any of these
conditions holds:

- the referenced record falls outside the function stack buffer;
- a decimal record has nonzero bytes 7..13, sign other than `0/1`, scale above
  14, or negative zero;
- a double record is non-finite or negative zero.

These exclusions intentionally describe states absent from the 440-observation
oracle. The implementation does not generalize beyond the demonstrated PB 2022
layout merely because a broader representation would be plausible.

The two pushed expressions carry `decimal` or `double` type evidence in the
existing expression stack. No symbolic spelling is substituted and
`powerscript_like` receives only the recovered numeric literal.

## v10 to v11 results

### Known-source corpora

| Corpus | Direct constants resolved | Dependent stack/context failures resolved | Complete functions | Function reconstruction verified |
|---|---:|---:|---:|---:|
| `exmmain` | 0 | 0 | 17 -> 17 | 7 -> 7 |
| `appexmfe` | 0 | 0 | 163 -> 163 | 103 -> 103 |
| `pfcapsrv` | 440 in 91 functions | 678 in 67 functions | 844 -> 880 (**+36**) | 409 -> 436 (**+27**) |
| **Total** | **440** | **678** | **1,024 -> 1,060** | **519 -> 546** |

Across all 1,873 known-source functions, semantic-rule completeness rises from
54.67% to 56.59%, while whole-function verification rises from 27.71% to
29.15%. Instruction semantic coverage rises from 86.459% to 87.357%.

All 27 new whole-function verifications are decimal cases: 26 functions contain
one `PUSH_CONST_DEC`, and `of_getfilesize` contains two. They comprise 26
measurement-conversion functions plus `pfc_n_cst_filesrvunicode.of_getfilesize`.
Their verification basis is `safe_semantic_canonicalization`; no rule-incomplete
function is counted as verified.

The six newly complete functions whose relevant compiled constants are double
records remain normal source mismatches. Examples include `of_deg2rad` and
`of_rad2deg`, where the compiled artifact retains binary64 pi but not the source
identifier `PI`. This gate correctly improves semantic coverage without
claiming unproved whole-function equivalence.

There are no remaining unresolved `PUSH_CONST_DEC` or `PUSH_CONST_DOUBLE`
records in the known-source corpora, no newly introduced unresolved
instructions, no completeness regressions, and no verification regressions.

### `replicacao.pbd`

| Metric | v10 | v11 | Change |
|---|---:|---:|---:|
| Direct typed-constant failures | 41 | 0 | -41 |
| Dependent stack/context failures removed | - | 145 in 15 functions | -145 |
| Total unresolved instructions | 732 | 546 | -186 |
| Supported instructions | 22,574 / 23,306 | 22,760 / 23,306 | +186 |
| Semantic instruction coverage | 96.859% | 97.657% | +0.798 pp |
| Semantically complete functions | 239 / 304 | 245 / 304 | **+6** |

The 41 direct occurrences are 16 decimal records and 25 double records across
20 functions. All satisfy the independently established known-source
invariants; none remains unresolved.

The six newly complete target functions are:

- `gf_centerwindow.gf_centerwindow`;
- `gf_centerwindow_resp.gf_centerwindow_resp`;
- `n_runandwait.of_set_options`;
- `w_replicacao.of_center`;
- `u_progressbar.constructor`;
- `u_progressbar.of_setposition`.

Because `replicacao.pbd` has no matching source, these promotions mean
`semantically_complete`, not `function_reconstruction = verified`.

## Reproduction

The comparison is reproducible with:

```powershell
& 'C:\Users\loja1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  scripts\analyze_typed_numeric_gate.py
```

It compares the v10/v11 reports for all three known-source corpora and the
target, reports direct and cascade removals separately, and lists completeness
and verification promotions/regressions.

The generated reports are outside the Git repository under:

- `pb2022-analysis/whole-function-v11-exmmain/`;
- `pb2022-analysis/whole-function-v11-appexmfe/`;
- `pb2022-analysis/whole-function-v11-pfcapsrv/`;
- `pb2022-analysis/replicacao-snapshot-v11/`.
