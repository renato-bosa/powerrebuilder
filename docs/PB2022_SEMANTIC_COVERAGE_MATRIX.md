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

## Array semantics result

The next known-source batch implemented array indexing, `LowerBound` and
`UpperBound`, unbounded array-list construction, indexed member lvalues, and
the non-emitting bound/array transformation opcodes around them. The operand
layouts continue to come from the validated PB 11+ / PB 2022 VM width table;
only their expression-stack meaning was added.

| Corpus | Before arrays | After arrays | Complete previews |
| --- | ---: | ---: | ---: |
| `replicacao.pbd` | 22,315 / 23,306 (95.75%) | 22,424 / 23,306 (96.22%) | 235 / 304 |
| OpenSourcePFC `appexmfe` | 5,624 / 5,812 (96.77%) | 5,775 / 5,812 (99.36%) | 156 / 163 |
| OpenSourcePFC `exmmain` | 400 / 400 (100.00%) | 400 / 400 (100.00%) | 17 / 17 |

The generated `appexmfe` preview now reproduces all three array forms used as
the oracle:

- `this.Item[UpperBound(this.item)+1]=this.m_tree`
- `this.Item[]={this.m_table}`
- `la_args[1] = ...`

These correspond respectively to `UPPERBOUND` plus
`CALC_UNBOUNDED_ARRAY_BOUND` / `DOT_FLD_UPDATE_INDEX_RP`,
`BUILD_UNBOUNDED_ARRAYLIST`, and `CALC_SIMPLE_ARRAY_BOUND` / `INDEX_LV`.
The comparison is semantic and case-insensitive; formatting and redundant
qualification such as `this.` or `parent.` are not required to be byte-for-byte
identical to the exported source.

At this checkpoint, seven of 163 `appexmfe` previews remained incomplete.
Their 37 unresolved occurrences were concentrated in `LOWER`, `DOT_ANY`,
cleanup after calls, `HALT`, and two apparent shared/global resolutions.

## Known-source closure result

The remaining `appexmfe` cases established five additional rules:

- `LOWER` is the unary PowerScript `lower(...)` intrinsic.
- `PUSH_SHARED_VAR` `0x01AB` is non-emitting reference bookkeeping despite
  its historical mnemonic; the reference implementation records `pb_empty`
  and a `0 -> 0` stack effect.
- `HALT` mode `0` renders `halt close`, as confirmed by the fixture; mode `1`
  is the complementary `halt` form from the two-form PowerScript grammar.
- `DOT_ANY` performs ordinary member access while preserving a dynamic value.
- Compiler-generated menu separator type names such as `m_-` are valid type
  descriptor strings, even though ordinary member-name recovery remains
  conservatively restricted.

| Corpus | Before closure | After closure | Complete previews |
| --- | ---: | ---: | ---: |
| `replicacao.pbd` | 22,424 / 23,306 (96.22%) | 22,453 / 23,306 (96.34%) | 236 / 304 |
| OpenSourcePFC `appexmfe` | 5,775 / 5,812 (99.36%) | 5,812 / 5,812 (100.00%) | 163 / 163 |
| OpenSourcePFC `exmmain` | 400 / 400 (100.00%) | 400 / 400 (100.00%) | 17 / 17 |

`appexmfe` is now exhausted as an opcode-semantic oracle: every structurally
validated region is semantically complete under the current preview model.
Further target progress requires either a new known-source fixture overlapping
the remaining families or dedicated handling of embedded SQL, transactions,
and exception/control-flow regions.

## Expanded transaction and exception fixture

The local OpenSourcePFC `pfcapsrv` library provides the next known-source
oracle. It contains 108 compiled-object envelopes and 1,693 validated P-code
regions, including explicit transaction statements and three `try` blocks with
two typed catches each.

| Corpus | Instructions | Supported baseline | Coverage | Complete previews |
| --- | ---: | ---: | ---: | ---: |
| OpenSourcePFC `pfcapsrv` | 118,278 | 99,701 | 84.29% | 814 / 1,693 |

The first aligned function is
`pfc_n_cst_security.of_scanwindow(window aw_win)`. Its source and P-code
establish that `DBROLLBACK` and `DBCOMMIT` consume the transaction expression
already on the stack and render respectively as `rollback using ...` and
`commit using ...`.

| Corpus | Before transactions | After transactions | Complete previews |
| --- | ---: | ---: | ---: |
| `replicacao.pbd` | 22,453 / 23,306 (96.34%) | 22,495 / 23,306 (96.52%) | 239 / 304 |
| OpenSourcePFC `pfcapsrv` | 99,701 / 118,278 (84.29%) | 99,703 / 118,278 (84.30%) | 814 / 1,693 |
| OpenSourcePFC `appexmfe` | 5,812 / 5,812 (100.00%) | 5,812 / 5,812 (100.00%) | 163 / 163 |
| OpenSourcePFC `exmmain` | 400 / 400 (100.00%) | 400 / 400 (100.00%) | 17 / 17 |

The larger gain on the target comes from 31 rollback and 11 commit statements;
three additional target previews became complete. `DBSTOP` was deliberately
left unresolved because this fixture does not contain a matching
`disconnect using` statement. The next cross-corpus family with direct source
evidence is exception-region scaffolding: `PUSH_TRY`, `CATCH_EXCEPTION`, and
`POP_TRY`.

## Minimal CFG and known-source exception result

The PB semantic path now builds a deliberately small, PB-specific control-flow
model. It records basic blocks, conditional target and fallthrough edges,
unconditional jumps, exception-dispatch edges, and the handler regions encoded
by `PUSH_TRY`. It does not extend or depend on the repository's generic CFG/SSA
scaffold.

| Corpus | Valid semantic CFGs | Exception regions | Before | After | Complete previews |
| --- | ---: | ---: | ---: | ---: | ---: |
| `replicacao.pbd` | 304 / 304 | 14 in 6 functions | 22,495 / 23,306 (96.52%) | 22,574 / 23,306 (96.86%) | 239 / 304 |
| OpenSourcePFC `pfcapsrv` | 1,693 / 1,693 | 3 in 3 functions | 99,703 / 118,278 (84.30%) | 101,421 / 118,278 (85.75%) | 844 / 1,693 |

The gain covers exception setup, catch dispatch, handler guards, cleanup, and
only the compiler exits found immediately before exception-handler boundaries.
An arbitrary user jump to the same destination is not suppressed as
scaffolding. `THROW_EXCEPTION` remains unresolved because the target supplies
binary evidence but no matching source oracle.

The three `pfc_n_cst_apppreference` functions are the first formal
known-source construction oracles. Their reconstructed exception regions each
contain, in source order:

- `catch (PBDOM_Exception pbde)`;
- `catch (PBXRuntimeError re)`.

A versioned JSON manifest records the catch shapes plus two source-derived,
case/whitespace-normalized body fragments per function. The diagnostic reports
three oracle matches, three verified `try_catch` constructions, six compared
body fragments, and zero mismatches. Oracle-guided, source-confirmed mappings
for `RegistryGet`, `ProfileString`, `RegistrySet`, `SetProfileString`, and the `INDEX_ERR_CHK`
array reduction also close every instruction in the three real functions:
148/148, 142/142, and 138/138. Thus `semantic_rules_complete` is true for all
three. When decode is run only with the construction manifest,
`function_reconstruction` deliberately remains `not_assessed`. This is
intentional: complete rule coverage plus a verified construction is still not
promoted to verified whole-function equivalence.

The report now separates these quality states:

1. `instructions_structurally_decoded`;
2. `control_flow_validated`;
3. `semantic_rules_complete` (also exposed through the legacy
   `semantically_complete` field);
4. explicit `known_source_constructs` evidence;
5. `function_reconstruction`;
6. `object_recompilation`.

The final two remain `not_assessed`. A test also deliberately supplies a
different catch oracle and proves that a semantically complete instruction
slice is marked `mismatch`, not verified.

## Conservative whole-function source comparison

The optional `--known-source-dir` path indexes matching exported PowerBuilder
objects and compares each complete reconstructed function with its known
source body. The comparator is deliberately strict: it ignores comments,
case, whitespace, line continuations, redundant `this.`, a trailing implicit
`return`, and documented type aliases (`int`/`integer`, `bool`/`boolean`,
`uint`/`unsignedinteger`, `ulong`/`unsignedlong`, and `char`/`character`). It
does not treat `goto` output as equivalent to structured `if`/loops, rewrite
expressions, or equate symbolic constants with numeric values.

The first full public-corpus run produced:

| PB 2022 corpus | Functions | Rule-complete | Whole-function verified | Normalized mismatch | Rule-incomplete |
| --- | ---: | ---: | ---: | ---: | ---: |
| OpenSourcePFC `exmmain` | 17 | 17 | 5 (29.41%) | 12 | 0 |
| OpenSourcePFC `appexmfe` | 163 | 163 | 101 (61.96%) | 62 | 0 |
| OpenSourcePFC `pfcapsrv` | 1,693 | 844 | 274 (16.18%) | 570 | 849 |
| **Combined** | **1,873** | **1,024 (54.67%)** | **380 (20.29%)** | **644** | **849** |

There were zero missing source files, missing routines, or ambiguous matches
after accounting for PowerBuilder type aliases, typed events, prototype
sections, and declaration order for repeated control events. Among only the
1,024 rule-complete functions, 380 (37.11%) passed the strict whole-body
comparison.

The 20.29% value is therefore a defensible lower bound for functions confirmed
against known PB 2022 source by this comparator, not a claim that the other
79.71% are wrong. In particular, a normalized mismatch can be caused by
semantically equivalent but differently structured control flow that this
version intentionally refuses to accept. The nontrivial verified sample
`pfc_n_cst_color.of_reset()` matches all 35 assignments in its exported
source, demonstrating that the result is not limited to empty lifecycle
handlers.

The three exception oracle functions remain a useful negative boundary: their
typed `try/catch` constructions and body fragments are source-verified, but
their entire bodies report `normalized_body_mismatch`. Construction-level
confirmation is consequently preserved without being inflated into
whole-function verification.
