# PB2022 differential `if` experiment

Date: 2026-08-13

## Scope and decision

Rust remains the primary implementation. The experimental PbdViewer clone is
kept as a reproducible second implementation and differential oracle; no code
or opcode heuristics were transferred from it into Rust.

This experiment was deliberately limited to the smallest `if` pattern that can
be checked against matching PB2022 source. It does not implement generic CFG
structuring, `else`, `else if`, `choose case`, or loops.

## Reproducible checkpoints and inputs

- Rust baseline: commit `387838e`, reports `whole-function-v3-*`.
- Experimental PbdViewer: branch `experiment/pb2022-decision-gate`, commit
  `262286d`, reports `pbdviewer-analysis/v4-*`.
- New Rust reports: `whole-function-v6-exmmain`,
  `whole-function-v6-appexmfe`, and `whole-function-v6-pfcapsrv`.
- Target-only evidence: PbdViewer
  `pbdviewer-analysis/target-replicacao-v1` and Rust
  `semantic-preview-known-source-v25-single-if-runtime`.
- Public PB2022 binaries and exported source are the three OpenSourcePFC
  corpora already recorded in the decode-report metadata.

The PbdViewer clone remains unchanged after its experimental checkpoint.

## Re-audit of the PbdViewer-exclusive corpus

The occurrence-aware join confirms the original total: 65 functions are
whole-source verified by PbdViewer while the baseline Rust report marks them as
normalized-body mismatches.

A stricter second classification, which removes line and block comments before
looking for control-flow markers, corrects one detail in the decision-gate
report:

| Known-source family | Count |
| --- | ---: |
| `if` / `else` | 46 |
| `choose case` | 1 |
| No structured-control marker | 18 |
| Total | 65 |

The earlier 47/17 split was a coarse-classification false positive. The extra
case is `w_frame.pfc_pretoolbar(n_cst_toolbarattrib)`, whose executable source
has no `if`. This correction does not change the 65-function differential or
the architectural decision.

The 46 confirmed `if`/`else` functions have these source/CFG shapes. Columns
show source `if` count, source `else` count, basic blocks, conditional branches,
unconditional jump edges, and fallthrough edges.

| Functions | `if` | `else` | Blocks | Branches | Jumps | Fallthrough | Interpretation |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 36 | 1 | 0 | 4 | 1 | 2 | 1 | Single guard arm ending in `return`; both source paths use the compiler return epilogue |
| 3 | 1 | 1 | 5 | 1 | 3 | 1 | Forward `if/else` with returning arms |
| 2 | 3 | 0 | 8 | 3 | 4 | 3 | Three sequential/nested guards |
| 2 | 2 | 0 | 6 | 2 | 3 | 2 | Two sequential/nested guards |
| 1 | 1 | 0 | 3 | 1 | 0 | 2 | Single linear arm falling through to its join |
| 1 | 2 | 0 | 5 | 2 | 2 | 2 | Two guards with a shared continuation |
| 1 | 1 | 1 | 4 | 1 | 1 | 2 | Classic assignment diamond |

Representative known-source oracles are:

- `n_tr.of_begin()`: one forward guard whose arm returns;
- `w_examplemain.ue_statusbarrbuttonup(...)`: one forward arm that falls
  through;
- `pfc_n_cst_filesrvunicode.of_filerename(...)`: an explicit `if/else`, kept
  out of scope;
- `pfc_n_cst_list.of_setsorted(...)`: multiple guards, kept out of scope.

PbdViewer's `ParseIfElse` performs broad post-processing: a forward false
branch becomes `if`, a forward jump before its target is interpreted as
`else`, and a later pass folds `else if`. That treatment explains its advantage
on this corpus, but it is broader than the rule admitted into Rust.

## Admitted Rust rule

The serialized pattern is named `forward_single_arm_v1`. It is accepted only
when all of these invariants hold:

1. the minimal CFG is valid and the function has no exception region;
2. the function contains exactly one conditional branch and it is a forward
   PB2022 `JUMPFALSE`;
3. the branch has exactly the expected taken edge to the join and fallthrough
   edge to one adjacent body block;
4. the body has no other predecessor and contains no nested `if`, visible
   `goto`, exception marker, or unresolved instruction;
5. the body either falls directly into the join or ends in `return` and exits
   through the compiler epilogue.

On acceptance, the low-level `if not CONDITION then goto JOIN` is rendered as
`if CONDITION then`, and `end if` is inserted at `JOIN`. The report records the
branch, body, and join offsets in `reconstructed_ifs`; report schema version was
incremented from 6 to 7.

This rule is semantically conservative. In particular, a real assignment
diamond retains its low-level branch and `goto` in this iteration.

## Whole-function verification result

| Corpus | Functions compared | Baseline verified | New verified | Gain | New mismatches | Rule-incomplete |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `exmmain` | 17 | 5 | 6 | +1 | 11 | 0 |
| `appexmfe` | 163 | 101 | 101 | 0 | 62 | 0 |
| `pfcapsrv` | 1,693 | 274 | 324 | +50 | 520 | 849 |
| **Total** | **1,873** | **380 (20.29%)** | **431 (23.01%)** | **+51** | **593** | **849** |

All 51 newly verified functions have known source containing exactly one `if`,
no `else`, one conditional branch, and the admitted four-block shape. Of the
65 original PbdViewer-exclusive functions, 30 are now verified by Rust; the
other 21 gains come from functions that were not exclusive PbdViewer wins.

There were no `verified -> mismatch` regressions. Semantic instruction
coverage and the 849 rule-incomplete functions are unchanged, so the increase
is specifically in `function_reconstruction = verified`.

The rule was recognized in 196 public-corpus functions. Outcomes were 51
verified, 96 source mismatches, and 48 not assessed because semantic rules were
incomplete; one additional mismatch contains the admitted `if` inside a
`choose` function. Recognition alone is not treated as verification.

## New mismatch distribution and next gate

The 593 complete-but-mismatching functions now classify by known source as:

| Family | Mismatches |
| --- | ---: |
| No recognized structured-control marker | 300 |
| `if` / `else` | 261 |
| `choose case` | 27 |
| Exceptions | 3 |
| Embedded SQL | 2 |

Within the 261 `if`/`else` mismatches, 92 of the largest simple groups already
carry `forward_single_arm_v1` (55 with two epilogue jumps and 37 with one).
Their remaining differences are therefore expression/call/statement fidelity,
not missing `if` structure. The largest not-yet-structured homogeneous group
has two conditional branches (27 functions); simple explicit-`else` groups are
smaller in this corpus.

Recommended next gate: first classify the 96 structured-but-mismatching cases
by normalized statement delta. This should identify the next semantic family
without widening CFG rules. If a structural family is selected after that,
test two non-nested forward single-arm guards against known source before
considering generic diamonds. Do not proceed to `choose` or loops from this
result alone.

## `replicacao.pbd` differential evidence

Both implementations structurally enumerate the same 304 functions. With no
matching source, none of these outputs is promoted to verified.

| Differential state | Functions |
| --- | ---: |
| Complete in both implementations | 215 |
| Complete only in PbdViewer | 41 |
| Complete only in Rust | 24 |
| Incomplete in both | 24 |

PbdViewer reports 256 semantic parses complete; Rust reports 239 semantic
previews complete and recognizes `forward_single_arm_v1` in 18 functions.
Those 18 are evidence candidates only.

All 24 Rust-only completions correspond to PbdViewer failing at opcode
`0x003D` because its experimental run has no PB2022 runtime typedef catalog.
The 41 PbdViewer-only completions concentrate on Rust gaps around embedded SQL
and its stack effects (`ENTER_EMBEDDED`, `EXIT_EMBEDDED`, `DBSELECT`,
`DBFETCH`, string assignment/concatenation, and related bookkeeping). This is
a useful differential locator, not a correctness verdict.
