# PB2022 v11 semantic decision gate

## Scope and method

This gate is analysis-only. It does not change the decoder, semantic rules,
CFG reconstruction, or `powerscript_like`.

Inputs:

- `whole-function-v11-exmmain/decode-report.json`;
- `whole-function-v11-appexmfe/decode-report.json`;
- `whole-function-v11-pfcapsrv/decode-report.json`;
- `replicacao-snapshot-v11/decode-report.json`.

The known-source comparison replays the v11 oracle, including safe semantic
canonicalization and unique compiled-symbol equivalence. The control check
reproduced all 24/24 functions currently verified through
`compiled_symbol_equivalence`.

Unresolved items are separated into three classes:

1. `direct_rule_absent`: the decoder explicitly reports
   `semantic rule not implemented`;
2. `artifact_or_metadata_resolution_gap`: the operation is known, but a
   function, enum, member, or local-variable description cannot be resolved;
3. `dependent_stack_or_context_failure`: a later consumer has no value,
   receiver, lvalue, call result, or branch condition available.

This third class is a symptom count, not a count of independent rules.

## 1. Coverage of `replicacao.pbd`

Current v11 status:

- 304 functions/P-code regions;
- 245 `semantically_complete` and 59 incomplete functions;
- 23,306 instructions, 22,760 supported (97.657%);
- 546 unresolved occurrences in 63 exact opcode/mnemonic/reason groups.

### Unresolved kind

| Kind | Occurrences | Functions |
|---|---:|---:|
| Direct semantic rule absent | 365 | 59 |
| Dependent stack/context failure | 169 | 32 |
| Artifact/metadata resolution gap | 12 | 1 |
| **Total** | **546** | **59** |

All 59 incomplete target functions contain at least one direct missing rule.
There is no target function whose incompleteness is explained only by a
downstream stack/context symptom. The first observed blocker is a direct rule
in 58 functions and a metadata gap in one function
(`replicacao.apl: event open(string commandline)`).

The 12 metadata occurrences are all `PUSH_LOCAL_VAR` (`0x01AA`) indexes 24,
25, 26, 35, and 38 outside the currently decoded local-variable table.

### Direct semantic families

| Family | Occurrences | Functions | First direct blocker | Sole direct family | Stack/context failures in affected functions |
|---|---:|---:|---:|---:|---:|
| SQL and embedded SQL | 221 | 32 | 26 | 15 | 81 |
| Typed call protocol | 36 | 13 | 3 | 3 | 86 |
| Exception handling | 30 | 9 | 3 | 3 | 23 |
| `INCR_*` | 27 | 16 | 12 | 5 | 63 |
| `DUP_STACKED_LVALUE` | 25 | 7 | 5 | 4 | 52 |
| `ADDASSIGN_*` | 14 | 2 | 2 | 1 | 2 |
| Unknown PB2022 opcode | 5 | 4 | 3 | 3 | 16 |
| `MOD_*` | 3 | 3 | 3 | 0 | 11 |
| `INT` intrinsic | 2 | 2 | 0 | 0 | 4 |
| `ARRAY_BOUND_INFO` | 1 | 1 | 1 | 1 | 2 |
| `CREATE_USING` | 1 | 1 | 1 | 1 | 2 |
| **Total direct** | **365** | | | | |

`Sole direct family` means that no other direct semantic family is absent in
that function. It is only an upper bound on immediate completion: metadata or
dependent failures may still remain. Stack/context co-occurrences overlap
between families and therefore must not be summed.

### Direct gaps by exact opcode

| Opcode | Mnemonic | Occurrences | Functions | Family |
|---|---|---:|---:|---|
| `0x0010` | `DBSELECT` | 60 | 22 | SQL |
| `0x01CE` | `ENTER_EMBEDDED` | 38 | 3 | SQL |
| `0x01CF` | `EXIT_EMBEDDED` | 38 | 3 | SQL |
| `0x0119` | `DUP_STACKED_LVALUE` | 25 | 7 | lvalue |
| `0x000E` | `DBFETCH` | 18 | 3 | SQL |
| `0x00F6` | `INCR_INT` | 16 | 9 | increment |
| `0x01E8` | `THROW_EXCEPTION` | 16 | 3 | exception |
| `0x000C` | `DBUPDATE` | 15 | 8 | SQL |
| `0x01BE` | `CLASS_CALL_DEC` | 14 | 5 | call protocol |
| `0x014D` | `DOTFUNCCALL_DOUBLE` | 14 | 8 | call protocol |
| `0x01E6` | `POP_TRY` | 14 | 6 | exception |
| `0x0107` | `ADDASSIGN_ULONG` | 13 | 1 | add-assign |
| `0x0008` | `DBSTOP` | 13 | 8 | SQL |
| `0x0009` | `DBCLOSE` | 10 | 3 | SQL |
| `0x00F8` | `INCR_LONG` | 9 | 9 | increment |
| `0x01C3` | `DBEXECUTEIMMED` | 8 | 3 | SQL |
| `0x000A` | `DBOPEN` | 8 | 1 | SQL |
| `0x01CB` | `FREE_INV_METH_ARGS` | 7 | 2 | call protocol |
| `0x000B` | `DBDELETE` | 6 | 3 | SQL |
| `0x000F` | `DBINSERT` | 5 | 4 | SQL |
| `0x0253` | `PB2022_OP_0253` | 3 | 2 | unknown |
| `0x000D` | `DBEXECUTE` | 2 | 2 | SQL |
| `0x0189` | `INT` | 2 | 2 | intrinsic |
| `0x01D5` | `MOD_DOUBLE` | 2 | 2 | modulo |
| `0x0251` | `PB2022_OP_0251` | 2 | 2 | unknown |
| `0x0104` | `ADDASSIGN_INT` | 1 | 1 | add-assign |
| `0x01B7` | `ARRAY_BOUND_INFO` | 1 | 1 | array bound |
| `0x01C8` | `CREATE_USING` | 1 | 1 | creation |
| `0x014E` | `DOTFUNCCALL_DEC` | 1 | 1 | call protocol |
| `0x00FA` | `INCR_DEC` | 1 | 1 | increment |
| `0x00F9` | `INCR_ULONG` | 1 | 1 | increment |
| `0x01D3` | `MOD_LONG` | 1 | 1 | modulo |

### Dependent stack/context symptoms

The largest dependent groups are:

| Mnemonic/cause | Occurrences | Functions |
|---|---:|---:|
| `POP_N_TIMES`: call cleanup has no call result | 40 | 16 |
| `ASSIGN_STRING`: value missing | 24 | 6 |
| `CAT_STRING`: right operand missing | 24 | 6 |
| `ASSIGN_DEC`: value missing | 15 | 5 |
| `ASSIGN_INT`: value missing | 9 | 5 |
| `CNV_DOUBLE_TO_INT`: expression stack empty | 8 | 4 |
| `JUMPFALSE`: condition stack empty | 7 | 7 |
| `LVALUE_EXPR`: statement-expression stack empty | 7 | 3 |
| `STORE_RETURN_VAL`: return-value stack empty | 7 | 4 |
| `ASSIGN_LONG`: value missing | 4 | 3 |
| Remaining 16 exact groups | 24 | — |
| **Total dependent** | **169** | **32** |

The complete 63-row target matrix, including exact reason and function count,
is generated as `pb2022-analysis/v11-decision-gate-target-unresolved.csv`.

## 2. First blockers in known-source fixtures

`exmmain` and `appexmfe` remain fully rule-complete. All 813 incomplete
known-source functions are in `pfcapsrv`.

Across those 813 functions there are:

- 895 direct missing-rule occurrences in 296 functions;
- 5,782 artifact/metadata gaps in 689 functions;
- 9,062 dependent stack/context symptoms in 748 functions.

The first observed blocker is an artifact/metadata resolution gap in 649
functions and a direct missing rule in 164. It is never initially a downstream
stack/context symptom. In 517 functions there is no direct missing semantic
rule at all: every one contains both a metadata-resolution blocker and later
stack/context failures. Those 517 must not be presented as candidates for a
new opcode rule.

### Remaining direct families supported by known source

| Direct family | Occurrences | Functions | First direct blocker | Sole direct family | Representative source-backed case |
|---|---:|---:|---:|---:|---|
| `INCR_*` | 272 | 154 | 139 | 103 | `of_resetupdate`, `of_getobjects` |
| Typed member access (`DOT_DEC`, etc.) | 156 | 24 | 21 | 15 | `of_xyz2rgb` |
| Typed call protocol | 143 | 62 | 57 | 55 | `of_setitemattributes` |
| `DUP_STACKED_LVALUE` | 90 | 37 | 7 | 7 | `of_getkeyvalue` |
| `INDEX_ANY` family | 50 | 7 | 1 | 0 | array/`any` indexing |
| `ADDASSIGN_*` | 44 | 38 | 18 | 11 | `of_getargs` |
| `MOD_*` | 40 | 29 | 13 | 4 | `of_isleapyear` |
| Intrinsic/unary operations | 32 | 20 | 14 | 8 | `UPPER`, `NEGATE`, `SQRT` |
| Array shape transforms | 22 | 19 | 11 | 6 | bounded/unbounded transforms |
| Other compound assignments | 15 | 7 | 1 | 0 | `SUBASSIGN_*`, `MULTASSIGN_*` |
| `INT` intrinsic | 9 | 6 | 1 | 1 | numeric conversion |
| `DECR_*` | 8 | 8 | 5 | 3 | decrement statements |
| Unknown PB2022 opcodes | 6 | 3 | 3 | 3 | `0x0249`, `0x024A`, `0x0254`, `0x0261` |
| `ARRAY_BOUND_INFO` | 3 | 3 | 3 | 3 | file-date helpers |
| Generic `ASSIGN` | 3 | 3 | 0 | 0 | generic assignment form |
| `PUSH_CONST_FLOAT` | 2 | 2 | 2 | 2 | typed float literal |

The exact known-source support for opcodes that also occur in the target is:

| Target family | Exact known occurrences | Known functions |
|---|---:|---:|
| `INCR_*` | 272 | 154 |
| Typed call protocol | 134 | 54 |
| `DUP_STACKED_LVALUE` | 90 | 37 |
| `ADDASSIGN_INT/ULONG` | 25 | 22 |
| `MOD_LONG/DOUBLE` | 12 | 10 |
| `INT` | 9 | 6 |
| `ARRAY_BOUND_INFO` | 3 | 3 |
| SQL, exceptions, `CREATE_USING`, target `0x0251/0x0253` | 0 | 0 |

Family-level similarity must not be mistaken for opcode-level evidence. The
unknown opcodes found in known fixtures are not `0x0251` or `0x0253`.

## 3. Rule-complete but not verified

| Corpus | Functions | Rule-complete | Verified | Complete, not verified | Rule-incomplete |
|---|---:|---:|---:|---:|---:|
| `exmmain` | 17 | 17 | 7 | 10 | 0 |
| `appexmfe` | 163 | 163 | 103 | 60 | 0 |
| `pfcapsrv` | 1,693 | 880 | 436 | 444 | 813 |
| **Total** | **1,873** | **1,060** | **546** | **514** | **813** |

The 546 verified functions comprise 431 normalized matches, 91 safe semantic
canonicalization matches, and 24 compiled-symbol matches.

### First demonstrable mismatch after the v11 oracle

| Family | v11 functions | Change from v10 |
|---|---:|---:|
| Structured `if` not recovered | 118 | +2 |
| Implicit `this` event receiver | 112 | 0 |
| Event-return scaffolding | 74 | 0 |
| Compiled-symbol resolution boundary | 72 | 0 |
| Compiler temporary/declaration placement | 39 | +2 |
| Source initializer not preserved | 25 | 0 |
| `choose case` lowering | 19 | 0 |
| Array marker not preserved | 10 | 0 |
| Array/grouped declaration form | 9 | 0 |
| Return-expression mapping | 8 | +5 |
| Receiver qualification/member mapping | 7 | 0 |
| Compiled accessor not collapsed | 6 | 0 |
| Ancestor dispatch spelling | 5 | 0 |
| Source super call absent from P-code | 5 | 0 |
| Other statement mapping | 4 | 0 |
| PowerBuilder quote-escape equivalence | 1 | 0 |
| **Total** | **514** | **+9** |

The 36 functions made rule-complete by v11 split into 27 newly verified and 9
new complete-but-unverified cases. No new mismatch family appeared:

- 5 entered `return_expression_mapping` (the measure/color conversion
  functions that now reconstruct their decimal/double expressions);
- 2 entered `compiler_temporary_or_declaration_placement`;
- 2 entered `structured_if_not_recovered`.

This is the intended distinction: consuming all instructions made those nine
functions rule-complete, but did not prove whole-function equivalence.

## 4. Candidate ordering

The ordering below favors target impact, exact known-source density, plausible
cascade reduction, confidence, and implementation risk. Potential completion
is deliberately not reported as guaranteed verification.

| Rank | Candidate | Target impact | Exact known-source density | Cascade evidence | Confidence | Size/risk | Decision |
|---:|---|---|---|---|---|---|---|
| 1 | `INCR_*` only | 27 / 16; first direct in 12; sole direct family in 5 | **272 / 154** | 63 dependent symptoms in affected target functions; 404 in known functions where increment is the sole direct family | High | S-M / medium | **Recommended next semantic gate.** Infer INT/LONG first; keep DEC/ULONG unresolved unless independently demonstrated. |
| 2 | `DUP_STACKED_LVALUE` only | 25 / 7; sole in 4 | 90 / 37 | **44** target dependent symptoms in the four sole-family functions | Medium-high | M / medium-high | Very strong cascade candidate, but lvalue alias/stack behavior is riskier than increment. |
| 3 | Typed call protocol | 36 / 13; sole in 3 | 134 / 54 exact overlap | 86 target co-occurrences, 9 in sole-family functions | Medium-high | L / high | High impact, but receiver, argument, cleanup, and return-value state should remain one later controlled gate. |
| 4 | `ADDASSIGN_*` only | 14 / 2; sole in 1 | 25 / 22 exact overlap | Only 2 target dependent symptoms | High | S-M / medium | Clean isolated measurement, but limited target function gain. Do not mix with increment. |
| 5 | `MOD_*` only | 3 / 3; sole in 0 | 12 / 10 exact overlap | 11 target dependent symptoms, all with another direct family | High | S / low-medium | Useful small rule, but cannot complete a target function alone in current evidence. |
| 6 | `ARRAY_BOUND_INFO` | 1 / 1; sole in 1 | 3 / 3 | 2 dependent symptoms in that target function | Medium-high | S / medium | Small source-backed gate after higher-impact families. |
| 7 | `INT` intrinsic | 2 / 2; sole in 0 | 9 / 6 | 4 target dependent symptoms | High | XS-S / low | Low impact and not currently a root family in the target. |
| 8 | SQL/embedded SQL | **221 / 32** | **0 / 0** | 81 target dependent symptoms | Low without a fixture | L / high | Largest target impact, but blocked by the agreed known-source proof standard. |
| 9 | `POP_TRY`/`THROW_EXCEPTION` | 30 / 9 | 0 / 0 for these exact opcodes | 23 target dependent symptoms | Low-medium | M-L / high | Existing exception oracle does not prove these target forms. |
| 10 | Target `0x0251/0x0253` | 5 / 4 | 0 / 0 exact | 16 target dependent symptoms | Low | Unknown / high | Keep deferred until a source-backed opcode identification exists. |
| 11 | `CREATE_USING` | 1 / 1 | 0 / 0 | 2 dependent symptoms | Low | S-M / medium | Too little evidence for the next gate. |

`DECR_*`, `SUBASSIGN_*`, `MULTASSIGN_*`, typed member access, and the other
known-only families remain separate measurements. They are not folded into the
increment recommendation merely because they are numeric or mutate an lvalue.

There is a separate infrastructure opportunity in artifact/metadata
resolution: 517 known functions have no direct missing semantic rule, and the
largest first blocker is the unresolved PB2022 system-function reference
`0x40D5:356` in 425 functions. It is potentially important for known-corpus
verification but has almost no current target overlap, so it should not be
mixed into the next `INCR_*` semantic gate.

The `TriggerEvent(this, ...)` equivalence remains a valid oracle-only backlog
item affecting 112 complete functions. It is intentionally excluded from the
semantic candidate order because it does not increase decompiler capability.

## Recommendation

Proceed, if selected, with an `INCR_*`-only semantic gate. Use the 154 known
functions to infer stack and lvalue behavior empirically, implement only the
operand forms demonstrated by source, and measure the target and verified
function deltas before considering `ADDASSIGN_*`, `MOD_*`, decrement, or other
compound assignment operations.
