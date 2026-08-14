# PB2022 compiled-symbol equivalence oracle gate

## Result

The typed constant catalog is now used only by the whole-function
known-source oracle. `powerscript_like` is unchanged. A third verification
basis, `compiled_symbol_equivalence`, is recorded only when a source symbol and
a reconstructed literal reduce to the same value through a `unique` lookup in
compiled metadata.

The comparison order is:

1. normalized equality;
2. safe semantic canonicalization;
3. safe canonicalization plus unique compiled-symbol equivalence.

The third step canonicalizes symbols on either side of the comparison to their
compiled literal. It succeeds only when at least one symbol was replaced and
the complete function bodies then match. It never rewrites the preview.

## Conservative boundary

Resolution requires an exact declaring owner, exact PowerBuilder type, and
exact decoded value. Qualified symbols also require a receiver type recovered
from compiled function/object metadata. Parameters, locals, and non-constant
properties block unqualified replacement when they shadow a constant name.

- `unique` may participate in verification;
- `zero` remains a normal body mismatch;
- `ambiguous` remains a normal body mismatch;
- a different owner remains a mismatch;
- inheritance is not expanded;
- unresolved constant representations are not accepted;
- no symbolic substitution is emitted.

Positive and negative unit tests cover these boundaries, including preservation
of the original `powerscript_like` string.

## Three-corpus differential run

Report schema v10 records the new basis and its independent counter.

| Corpus | v9 verified | v10 verified | Compiled-symbol promotions | Regressions | Changed previous basis |
|---|---:|---:|---:|---:|---:|
| `exmmain` | 7 | 7 | 0 | 0 | 0 |
| `appexmfe` | 103 | 103 | 0 | 0 | 0 |
| `pfcapsrv` | 385 | 409 | 24 | 0 | 0 |
| **Total** | **495** | **519** | **24** | **0** | **0** |

Whole-function verification increased from 495/1,873 (26.43%) to 519/1,873
(27.71%), a gain of 24 functions or 1.28 percentage points. The previous 431
normalized-equality and 64 safe-canonicalization verifications are unchanged.

The 24 promotions are distributed as follows:

| Compiled object | Functions promoted |
|---|---:|
| `pfc_n_cst_metaclass.udo` | 11 |
| `pfc_n_cst_apppreference.udo` | 6 |
| `pfc_n_cst_dwcache.udo` | 4 |
| `pfc_n_cst_lvsrv_datasource.udo` | 2 |
| `pfc_n_cst_tmgmultiple.udo` | 1 |

The families include the application-preference file-type constants, the
metaclass handling-mode constants, DataWindow cache method constants, and the
compiled string constants `CACHE_ID` and `IS_PFCKEY`.

SHA-256 comparison found zero changes in all 1,873 v9/v10 semantic preview
files. This independently confirms that the gain exists only in oracle
evidence.

Reproduced reports:

- `pb2022-analysis/whole-function-v10-exmmain/decode-report.json`;
- `pb2022-analysis/whole-function-v10-appexmfe/decode-report.json`;
- `pb2022-analysis/whole-function-v10-pfcapsrv/decode-report.json`.
