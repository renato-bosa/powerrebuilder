# PB2022 v10 semantic decision gate

## Scope and method

This gate is analysis-only. It does not change semantic rules,
`powerscript_like`, or the decoder.

Inputs:

- `whole-function-v10-exmmain/decode-report.json`;
- `whole-function-v10-appexmfe/decode-report.json`;
- `whole-function-v10-pfcapsrv/decode-report.json`;
- `replicacao-snapshot-v10/decode-report.json`.

For known-source mismatches, the analyzer replays superficial normalization,
the current safe canonicalization, and the current exact-owner/unique-value
compiled-symbol canonicalization before recording the first remaining
divergence. As a control, it independently reproduced all 24/24 v10
`compiled_symbol_equivalence` promotions.

Each rule-complete but unverified function is assigned exactly one first
demonstrable mismatch family. This is a diagnostic classification, not a claim
that every mismatch is a behavioral error.

## 1. Known-source fidelity

| Corpus | Compared | Rule-complete | Verified | Complete but not verified | Rule-incomplete |
|---|---:|---:|---:|---:|---:|
| `exmmain` | 17 | 17 | 7 | 10 | 0 |
| `appexmfe` | 163 | 163 | 103 | 60 | 0 |
| `pfcapsrv` | 1,693 | 844 | 409 | 435 | 849 |
| **Total** | **1,873** | **1,024** | **519** | **505** | **849** |

The 519 verified functions comprise 431 normalized matches, 64 safe
canonicalization matches, and 24 compiled-symbol matches.

### First demonstrable mismatch

| Family | Functions | Representative source -> reconstruction | Interpretation |
|---|---:|---|---|
| `structured_if_not_recovered` | 116 | `if checked = true then` -> `if not checked = true then` plus `goto` | CFG is valid, but the structured source guard/branch was not recovered. |
| `implicit_this_event_receiver` | 112 | `TriggerEvent(this, "constructor")` -> `TriggerEvent("constructor")` | One local spelling difference; all 112 bodies become equal if this proven receiver equivalence is admitted by the oracle. |
| `event_return_scaffolding` | 74 | `call super::clicked` -> `long ancestorReturnValue` plus message/return scaffolding | Compiler/runtime event-return protocol remains visible. |
| `compiled_symbol_resolution_boundary` | 72 | `return FAILURE` -> `return -1` | Current exact-owner/unique-value oracle cannot prove the remaining symbol spelling. |
| `compiler_temporary_or_declaration_placement` | 37 | source statement -> synthetic `n_tr sqlca`, `n_msg ::message`, global, or selector declaration | Compiler temporaries or declaration placement precede the first source statement. |
| `source_initializer_not_preserved` | 25 | `boolean lb_initialload = true` -> `boolean lb_initialload` | The declaration is present, but the source initializer is absent from the reconstruction/P-code view. |
| `choose_case_lowering` | 19 | `choose case ...` -> synthetic `\u0001caseN` selector and branches | `choose` remains lowered control flow. |
| `array_marker_not_preserved` | 10 | `item[] = {m_table}` -> `item = {m_table}` | Array marker is missing at a use site. |
| `array_or_grouped_declaration_form` | 9 | `string a[10], b[10]` -> split/partial declaration | Current safe grouped-declaration rule deliberately excludes these array/custom-type forms. |
| `receiver_qualification_or_member_mapping` | 7 | `ilv_parent.view = ...` -> `parent.parent.ilv_parent.view = ...` | Receiver qualification or member/enum mapping differs. |
| `compiled_accessor_not_collapsed` | 6 | `dw.object.col[row]` -> `__get_attribute_item(...)` | Compiled accessor remains exposed. |
| `ancestor_dispatch_spelling` | 5 | `call transaction::create` -> `call super::create` | Ancestor dispatch spelling differs. |
| `source_super_call_absent_from_pcode` | 5 | `call super::pfc_deleteitem` -> next return statement | The source super call is absent from the observed reconstruction. |
| `other_statement_mapping` | 4 | mixed isolated statement differences | No larger family is demonstrated yet. |
| `return_expression_mapping` | 3 | `return super::of_remove(...)` -> `return of_remove(...)` | Return receiver/dispatch differs. |
| `powerbuilder_quote_escape_equivalence` | 1 | source single-quoted `"` -> reconstructed `"~\""` form | Analyzer proves equal resulting literal; current Rust comparator does not yet recognize this escape spelling. |
| **Total** | **505** | | |

For the 72 compiled-symbol boundary cases, an independent catalog check finds:

- 61 values with indistinguishable aliases, including the `DATABASE`/`FILE`
  pair and color aliases;
- 8 names unique once the compiled declaring owner is reached, but outside the
  current exact-owner context (inheritance/owner propagation);
- 3 names absent from the available compiled catalog (`FAILURE` twice and
  `NO_ACTION`).

The 61 ambiguous and 3 absent cases must not be promoted under the current
policy. The 8 unique inherited-owner cases are a possible later oracle gate,
not evidence for symbol substitution in output.

## 2. Coverage of `replicacao.pbd`

Current target status:

- 304 functions/P-code regions;
- 239 `semantically_complete` and 65 incomplete functions;
- 23,306 instructions, 22,574 supported (96.86%);
- 732 unresolved occurrences in 91 exact opcode/mnemonic/reason groups;
- 406 direct `semantic rule not implemented` occurrences;
- 326 dependent stack/context failures.

Dependent failures are kept visible but are not treated as 326 independent
semantic rules. Many are consequences of an earlier missing producer, call,
SQL operation, or typed value.

### Family distribution

| Family | Target occurrences | Target functions | Known-fixture occurrences | Known-fixture functions | Oracle situation |
|---|---:|---:|---:|---:|---|
| dependent stack/context failures | 326 | 41 | 7,130 | 779 | Source exists, but these are often downstream symptoms. |
| SQL and embedded SQL | 221 | 32 | 0 | 0 | High target impact; no public known-source occurrence for these exact opcodes. |
| numeric/compound operations | 46 | 21 | 318 | 175 | Strong known-source corpus. |
| typed numeric constants | 41 | 20 | 440 | 91 | Strong known-source corpus and small producer rules. |
| call protocol | 36 | 13 | 134 | 54 | Known-source corpus exists; stack/metadata risk is higher. |
| exception handling | 30 | 9 | 0 | 0 | Existing try/catch oracle does not cover these target `POP_TRY`/`THROW_EXCEPTION` occurrences. |
| lvalue/array/creation | 27 | 9 | 93 | 40 | Known-source corpus exists; mixed semantics. |
| unknown PB2022 opcodes | 5 | 4 | 0 | 0 | No source-backed oracle for `0x0251`/`0x0253`. |

### Direct gaps by opcode

| Opcode | Mnemonic | Occurrences | Functions | Known fixture occurrence/function count |
|---|---|---:|---:|---:|
| `0x0010` | `DBSELECT` | 60 | 22 | 0 / 0 |
| `0x01CE` | `ENTER_EMBEDDED` | 38 | 3 | 0 / 0 |
| `0x01CF` | `EXIT_EMBEDDED` | 38 | 3 | 0 / 0 |
| `0x0119` | `DUP_STACKED_LVALUE` | 25 | 7 | 90 / 37 |
| `0x0038` | `PUSH_CONST_DOUBLE` | 25 | 11 | 131 / 47 |
| `0x000E` | `DBFETCH` | 18 | 3 | 0 / 0 |
| `0x00F6` | `INCR_INT` | 16 | 9 | 222 / 119 |
| `0x0036` | `PUSH_CONST_DEC` | 16 | 9 | 309 / 58 |
| `0x01E8` | `THROW_EXCEPTION` | 16 | 3 | 0 / 0 |
| `0x000C` | `DBUPDATE` | 15 | 8 | 0 / 0 |
| `0x01BE` | `CLASS_CALL_DEC` | 14 | 5 | 44 / 26 |
| `0x014D` | `DOTFUNCCALL_DOUBLE` | 14 | 8 | 59 / 34 |
| `0x01E6` | `POP_TRY` | 14 | 6 | 0 / 0 |
| `0x0107` | `ADDASSIGN_ULONG` | 13 | 1 | 5 / 5 |
| `0x0008` | `DBSTOP` | 13 | 8 | 0 / 0 |
| `0x0009` | `DBCLOSE` | 10 | 3 | 0 / 0 |
| `0x00F8` | `INCR_LONG` | 9 | 9 | 50 / 40 |
| `0x01C3` | `DBEXECUTEIMMED` | 8 | 3 | 0 / 0 |
| `0x000A` | `DBOPEN` | 8 | 1 | 0 / 0 |
| `0x01CB` | `FREE_INV_METH_ARGS` | 7 | 2 | 0 / 0 |
| `0x000B` | `DBDELETE` | 6 | 3 | 0 / 0 |
| `0x000F` | `DBINSERT` | 5 | 4 | 0 / 0 |
| `0x0253` | `PB2022_OP_0253` | 3 | 2 | 0 / 0 |
| `0x000D` | `DBEXECUTE` | 2 | 2 | 0 / 0 |
| `0x0189` | `INT` | 2 | 2 | 9 / 6 |
| `0x01D5` | `MOD_DOUBLE` | 2 | 2 | 3 / 3 |
| `0x0251` | `PB2022_OP_0251` | 2 | 2 | 0 / 0 |
| `0x0104` | `ADDASSIGN_INT` | 1 | 1 | 20 / 18 |
| `0x01B7` | `ARRAY_BOUND_INFO` | 1 | 1 | 3 / 3 |
| `0x01C8` | `CREATE_USING` | 1 | 1 | 0 / 0 |
| `0x014E` | `DOTFUNCCALL_DEC` | 1 | 1 | 31 / 22 |
| `0x00FA` | `INCR_DEC` | 1 | 1 | 0 / 0 |
| `0x00F9` | `INCR_ULONG` | 1 | 1 | 0 / 0 |
| `0x01D3` | `MOD_LONG` | 1 | 1 | 9 / 7 |

The complete 91-row matrix, including exact dependent-failure reasons,
function counts, examples, and known-fixture overlap, is generated as
`pb2022-analysis/v10-decision-gate-data.target-unresolved.csv`.

## Candidate ranking

The ranking separates proven whole-function gain from merely available oracle
coverage.

| Rank | Candidate | Proven/potential fixture gain | `replicacao` impact | Confidence | Size/risk | Decision |
|---:|---|---|---|---|---|---|
| 1 | Safe oracle equivalence for implicit `this` in `TriggerEvent` | **112 guaranteed**; each body has exactly this one difference | Same emitted form occurs in 22 target functions; no coverage change | High | XS / low | Best fidelity-only gate. It must not rewrite `powerscript_like`. |
| 2 | `PUSH_CONST_DEC` + `PUSH_CONST_DOUBLE` | 440 occurrences in 91 known-source functions; exact verified gain not yet guaranteed | **41 occurrences / 20 functions**; 6 target functions have no other direct unimplemented family | High | S / low-medium | **Recommended next true semantic gate.** |
| 3 | Classify and admit a conservative subset of residual structured `if` | Up to 116 complete mismatches, but no single rule has yet been proven for all | `goto` appears in 134 target functions, including 54 incomplete | Medium | M-L / medium-high | Do a pattern sub-gate first; do not implement all 116 as one rule. |
| 4 | Increment/modulo/compound numeric operations | 318 occurrences in 175 known-source functions | 46 / 21; 5 target functions have no other direct family | Medium-high | M / medium | Strong follow-up after typed constants. |
| 5 | Lvalue/array/creation primitives | 93 / 40 known-source | 27 / 9; 4 target functions have no other direct family | Medium | M / medium | Split `DUP_STACKED_LVALUE` from creation/array-bound work before implementation. |
| 6 | Typed call protocol | 134 / 54 known-source | 36 / 13; always co-occurs with another target direct family | Medium | L / high | Defer until typed producers reduce stack cascades. |
| 7 | Unique compiled constants through owner/inheritance context | **8 guaranteed candidates** under the existing unique-only policy | No measurable semantic-coverage gain in the target | High | M / medium | Oracle-only later gate; keep 61 ambiguous and 3 absent cases as mismatch. |
| 8 | SQL/embedded SQL | No matching known-source opcode occurrence | **221 / 32**, the largest target-only impact | Low without a new oracle | L / high | Do not choose next unless a PB2022 source/binary SQL fixture is added. |
| 9 | `POP_TRY`/`THROW_EXCEPTION` | No matching known-source opcode occurrence | 30 / 9 | Low-medium | M-L / high | Existing exception fixtures are insufficient for these exact operations. |
| 10 | `0x0251`/`0x0253` | None | 5 / 4 | Low | Unknown / high | Keep deferred pending a source-backed oracle. |

There is also one guaranteed comparator-only cleanup for PowerBuilder quote
escaping. It is real but too small to determine the next semantic family.

## Recommendation

If the immediate objective is the primary metric
`function_reconstruction = verified`, the smallest high-confidence gate is the
implicit-`this` oracle equivalence, with a demonstrated gain of 112 functions
and no output rewrite.

If the objective is to resume semantic coverage of `replicacao.pbd`, choose
typed numeric constants (`PUSH_CONST_DEC` and `PUSH_CONST_DOUBLE`). They have
the best current combination of target impact, known-source oracle density,
small implementation surface, and low structural risk. Re-run all three
corpora afterward and measure actual verified promotions before selecting the
next family.
