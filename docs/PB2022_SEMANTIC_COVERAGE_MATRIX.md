# PB 2022 semantic coverage matrix

This note records the baseline used to prioritize semantic work after the
structural PB 2022 parser reached exact region boundaries. Counts are dynamic
occurrences in the generated decode reports, not distinct opcode values.

## Baseline corpus

| Corpus | Instructions | Supported | Coverage | Complete previews |
| --- | ---: | ---: | ---: | ---: |
| `replicacao.pbd` | 23,306 | 19,370 | 83.11% | 162 / 304 |
| OpenSourcePFC `appexmfe` | 5,812 | 5,325 | 91.62% | 127 / 163 |
| OpenSourcePFC `exmmain` | 400 | 400 | 100.00% | 17 / 17 |

The `exmmain` result validates a small, fully supported subset. It does not
imply that all PB 2022 semantic families are covered. The larger `appexmfe`
fixture remains the primary known-source oracle before adding another public
fixture.

## Highest-impact unresolved families

`First` counts regions where the mnemonic is the earliest unresolved
instruction. This distinguishes likely causes from failures that occur only
after the expression stack has already been cleared.

| Mnemonic | Target | Target first | `appexmfe` | `appexmfe` first |
| --- | ---: | ---: | ---: | ---: |
| `POP_N_TIMES` | 489 | 0 | 38 | 0 |
| `LVALUE_EXPR` | 270 | 0 | 27 | 0 |
| `CAT_STRING` | 260 | 0 | 15 | 0 |
| `POP_POP` | 217 | 15 | 6 | 1 |
| `POP_FREE` | 183 | 1 | 13 | 1 |
| `CLASS_CALL` | 182 | 0 | 5 | 0 |
| `ASSIGN_STRING` | 176 | 0 | 5 | 0 |
| `FREE_REF_PAK_N` | 175 | 40 | 36 | 8 |
| `JUMPFALSE` | 174 | 0 | 26 | 0 |
| `DOTFUNCCALL` | 118 | 0 | 8 | 0 |
| `PUSH_LOCAL_VAR_DEC` | 88 | 3 | 0 | 0 |
| `PUSH_LOCAL_GLOBREF_LV` | 73 | 5 | 0 | 0 |
| `LEN_STRING` | 69 | 6 | 3 | 1 |
| `ISNULL` | 62 | 18 | 18 | 10 |
| `DBSELECT` | 60 | 9 | 0 | 0 |
| `PUSH_GLOBAL_VAR` | 40 | 6 | 35 | 8 |
| `PUSH_LOCAL_GLOBREF_DEC` | 36 | 0 | 0 | 0 |
| `PUSH_RESULT` | 24 | 2 | 1 | 1 |
| `PUSH_LOCAL_GLOBREF_RP` | 17 | 1 | 3 | 2 |

At baseline, `replicacao.pbd` has 3,936 unresolved instruction occurrences.
Only 1,713 are direct `semantic rule not implemented` results; the remaining
2,223 are mostly missing-operand and empty-stack cascades. For that reason,
raw frequency is not the implementation order.

## Implementation order

1. Typed local and referenced-global producers.
2. Null, length, string, decimal, and other scalar expressions.
3. Non-emitting native temporary/reference bookkeeping.
4. Calls and assignments after their operands remain available.
5. Embedded SQL and transaction operations.
6. Exception regions and structured control flow.

The next public fixture should be selected only after the existing
known-source overlap is exhausted. It should include exported source plus a
matching PB 2022 binary with embedded SQL, cursors, transactions, and
`try`/`catch` blocks.

## First causal batch result

The first implementation batch added typed local/reference producers,
`IsNull`/`Len` and related unary intrinsics, non-emitting native temporary
bookkeeping, and compiler-generated child-control creation. The latter is
opcode `PUSH_GLOBAL_VAR` (`0x002D`), identified as `pb_create` by the reference
implementation and confirmed against exported PB window/control creation
source.

| Corpus | Baseline | After batch | Complete previews |
| --- | ---: | ---: | ---: |
| `replicacao.pbd` | 19,370 / 23,306 (83.11%) | 22,315 / 23,306 (95.75%) | 222 / 304 |
| OpenSourcePFC `appexmfe` | 5,325 / 5,812 (91.62%) | 5,624 / 5,812 (96.77%) | 149 / 163 |
| OpenSourcePFC `exmmain` | 400 / 400 (100.00%) | 400 / 400 (100.00%) | 17 / 17 |

Known-source comparison confirms expressions such as
`IsNull(gnv_app.inv_debug)` and `Len(ls_id)` without adding fixture-specific
names. On the target, 2,945 additional instruction occurrences became
supported even though the batch directly implemented far fewer opcodes. This
confirms that the previous deficit was dominated by expression-stack cascades.
