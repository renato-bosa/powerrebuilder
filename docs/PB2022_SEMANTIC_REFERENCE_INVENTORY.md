# PB 2022 semantic reference inventory

Last updated: 2026-08-12

This inventory defines the evidence and reuse boundary for the next semantic
work. It covers exceptions, embedded SQL, structured control flow, and
DataWindow objects. It is intentionally a planning artifact: no decoder or
semantic rule was changed while producing it.

The central distinction is:

- a known opcode name is not proof of its semantics;
- an implementation in an older decompiler is not proof that its numeric
  opcode mapping is valid for PB 2022;
- plausible output is not validation unless a matching compiled binary and
  exported source are available.

## Evidence scale

| Grade | Meaning |
| --- | --- |
| A | Matching PB 2022 binary and exported source, with exact P-code boundaries |
| B | PB 2022 binary evidence plus independently recovered runtime operand widths, but no source |
| C | Older implementation or format reference whose behavior is useful after version mapping is verified |
| D | Model, stub, heuristic, or synthetic fixture; useful for design only |

`Supported` in a semantic preview means that the current linear interpreter
accepted the instruction. It does not mean that the original structured
PowerScript was recovered.

## Pinned reference bases

| Reference | Revision and license | What is actually present | Reuse rule |
| --- | --- | --- | --- |
| [Hucxy/PbdViewer](https://github.com/Hucxy/PbdViewer/tree/b46fd3e42b8f26ed18a547b9e4bec47f96530a86) | `b46fd3e42b8f26ed18a547b9e4bec47f96530a86`, MIT | Versioned compiled-object/P-code parsing, stack semantics for exceptions and SQL, and post-processing heuristics for `try`, `choose`, loops, `if`, `exit`, and `continue` | Reuse algorithms and invariants. Do not copy switch-case numbers without applying its version remapping. It supports object versions only through `0x014E`/334, not PB 2022 `0x0152`/`0x0153`. |
| [sijms/PowerBuilder-decompile](https://github.com/sijms/PowerBuilder-decompile/tree/5a7b9b05a400ddef8515dbf74e6fcd51a2e741a4) | `5a7b9b05a400ddef8515dbf74e6fcd51a2e741a4`, MIT | A 583-opcode table, several executable stack handlers, SQL statement metadata parsing, and goto-style branches | Strongest older reference for raw opcode IDs and operand counts shared with the current table. Handlers are incomplete and output is not a structured decompilation oracle. |
| Archived PowerRebuilder Python | Current repository history/archive, Apache-2.0 | Opcode catalogs, immutable PowerScript statement models, partial CFG/SSA experiments, source parsers, and DataWindow placeholders | Reuse the domain vocabulary and test ideas. Do not revive the archived binary-decompilation pipeline as an implementation: important parts are stubs, simplified heuristics, or missing imports. |
| [OpenSourcePFC 2022](https://github.com/OpenSourcePFCLibraries/2022/tree/19b7ec2f8353ce9ad8fb22fd0897ef4dadb71eea) | `19b7ec2f8353ce9ad8fb22fd0897ef4dadb71eea`, MIT | Matching PBLs and exported source for `appexmfe` and `pfcapsrv` | Primary grade-A semantic oracle. |

The checked-in [opcode reference](../data/reference/opcode_reference.yaml) was
derived largely from PowerBuilder-decompile, but it is provenance, not an
oracle. For example, it currently records `PUSH_TRY` as a one-word instruction
with no handler, while the pinned upstream table and the PB 2022 runtime both
give it two operand words. The version-specific runtime width table used by
the scanner is authoritative for framing.

## Current corpus and relevant occurrences

Counts below are dynamic instruction occurrences in the latest reports, not
distinct opcodes. `Unresolved` includes direct missing rules and stack
cascades. Structured-flow counts therefore need a separate interpretation:
accepted jumps are still rendered as gotos.

| Corpus | Exceptions | SQL/embedded | Branches | DataWindows | Oracle quality |
| --- | ---: | ---: | ---: | ---: | --- |
| `replicacao.pbd` | 72 total, 72 unresolved, 9 regions | 263 total, 221 unresolved, 36 regions | 1,677 total, 30 unresolved, 234 regions | 16 `PDW2200` objects | B: target has no source |
| OpenSourcePFC `pfcapsrv` | 12 total, 12 unresolved, 3 regions | 2 transaction instructions, both supported | 15,027 total, 1,948 unresolved, 1,499 regions | 13 `PDW2100` objects | A for the three exception functions, transactions, control-flow source, and 13 `.srd` pairs |
| OpenSourcePFC `appexmfe` | 0 | 0 | 272 total, all accepted, 48 regions | 5 `PDW2100` objects | A for control flow and five `.srd` pairs |
| OpenSourcePFC `exmmain` | 0 | 0 | Included in its 400 fully accepted instructions | 0 | A, but small |

The target's current overall baseline remains 22,495/23,306 accepted
instructions (96.52%) and 239/304 complete linear previews. `appexmfe` and
`exmmain` are at 100% under that same linear-preview definition. Neither
number measures structured-source equivalence.

## Summary gap and reuse matrix

| Family | Current Rust | PbdViewer opportunity | PowerBuilder-decompile opportunity | Archived Python opportunity | PB old to PB 2022 risk | Best available oracle | Recommended gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Exceptions | Framing is exact; no semantic rules; no exception-region IR | Stack behavior and `try`/catch/finally post-processing | Raw IDs/widths agree for `0x01E5`-`0x01E8`, but handlers are absent | `TryBlock`/`ThrowStatement` domain models only | Medium: core IDs appear stable, but PbdViewer uses a remapped dispatch namespace and its finally mapping conflicts with the raw 583 table | Three PB 2022 PFC functions with two typed catches each; target adds throw-only evidence | Reproduce all three PFC sources semantically before enabling target-wide exception output |
| Embedded SQL | Only commit/rollback are implemented; SQL metadata buffers are not exposed as a model | Most complete stack recipes, cursor/procedure declaration enrichment, direct SQL reconstruction | Parses `StmtInfo`, SQL strings, parameters, and implements common direct SQL handlers | Good statement data classes; binary recovery is absent | Low/medium for core IDs and widths; high for metadata layouts and late variants | Grade A only for commit/rollback; target gives grade B coverage for the wider family | Retain/parse statement metadata, then obtain or construct a PB 2022 source/binary SQL fixture before claiming correctness |
| Structured control flow | Linear text interpreter emits `goto`; separate CFG/SSA modules are simplified and not wired to this preview | Useful pattern recognizers for `if`, `choose`, `for`, `do`, `exit`, `continue`, and exception cleanup | Resolves labels but emits goto-style text only | Useful AST vocabulary; CFG and SSA algorithms are placeholders | Low for basic jump IDs/widths; medium for compiler idioms across versions | Strong and broad PFC/appexmfe source pairs | Build and validate a real CFG first; then structure one construct at a time against source |
| DataWindow | Detects `PDW2100`/`PDW2200` envelope and stops; no internal layout | Explicitly declines parsing `.dwo` and says it must be exported through the PB interface | Recognizes the `.dwo` type but has no DataWindow parser | Extraction is a string-search/DAT-marker heuristic and is unsafe at object-payload level | High: public pairs are `PDW2100`, target is `PDW2200` | 18 exact public PBL/`.srd` pairs for `PDW2100`; 16 target `PDW2200` objects without source | Treat as a separate binary-format project; infer `PDW2100` first, then differential-map `PDW2200` |

## Exceptions

### Observed PB 2022 instructions

| Opcode | Mnemonic | PB 2022 operand words | Target count | PFC count | Current status | Evidence/opportunity |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| `0x01E5` | `PUSH_TRY` | 2 | 14 | 3 | Unresolved | Operands behave as catch-entry and end-region offsets. The pinned PowerBuilder-decompile table also says two operands. |
| `0x01E6` | `POP_TRY` | 0 | 28 | 3 | Unresolved | Terminates/removes an exception handler; multiple target occurrences may represent path-specific compiler scaffolding. |
| `0x01E7` | `CATCH_EXCEPTION` | 0 | 14 | 6 | Unresolved | PbdViewer turns a typed exception expression on the stack into a catch clause, then restructures the following conditional branch. |
| `0x01E8` | `THROW_EXCEPTION` | 0 | 16 | 0 | Unresolved | PbdViewer pops and emits the thrown expression. PB 2022 source-pair validation is still absent. |

The grade-A PFC oracle consists of these three functions in
`pfc_n_cst_apppreference.udo`:

- `of_restore(integer, string, string, string, ref string, string)`;
- `of_save(integer, string, string, string, string)`;
- `of_restore(string, string, string, ref string, string)`.

Each compiled region has one `PUSH_TRY`, two `CATCH_EXCEPTION` instructions,
and one `POP_TRY`, matching source with `PBDOM_Exception` and
`PBXRuntimeError` catches. The first function's `PUSH_TRY` operands are
`456, 616`, for example, and both land on valid instruction boundaries.

PbdViewer contributes useful behavior but not directly usable raw numbers.
Its PB 11 parser maps raw opcodes `<=408` unchanged, `409..416` by `+1`,
`417..419` by `+2`, and later opcodes by `+3` before dispatching into its PB 9
switch. Its switch cases 485-490 therefore cannot be read as PB 11/PB 2022
raw opcode IDs. This is especially important around finally handling, where
PbdViewer's normalized `EnterFinally`/`LeaveFinally` cases overlap raw IDs
that the 583-entry table names `GOSUB`/`RETURN_SUB` or other exception
instructions after remapping.

### Exception gaps

1. Introduce explicit exception regions and handler edges instead of emitting
   four isolated statements.
2. Establish whether `PUSH_TRY` offsets are absolute byte offsets for every
   PB 2022 function and define whether the second offset is exclusive.
3. Recover the typed catch variable from the expression stack and metadata.
4. Model the extra `POP_TRY` paths seen in the target without assuming a
   one-to-one correspondence with source `end try`.
5. Validate `THROW_EXCEPTION` using a new source/binary pair.
6. Obtain a PB 2022 `finally` fixture before assigning semantics to
   `GOSUB`/`RETURN_SUB` or any apparent finally pattern.

### Exception tests/oracles

| Test | Available now | Acceptance criterion |
| --- | --- | --- |
| Width/framing | Yes, runtime-derived 615-entry PB 2022 table | All regions still end exactly; both `PUSH_TRY` targets are instruction boundaries |
| Source equivalence for typed catches | Yes, three PFC functions | Same try body, catch order, exception type/name, and post-try continuation |
| Throw | Target binary only | Keep output explicitly unverified until a matching source fixture exists |
| Finally | No | Do not implement from PbdViewer numbering alone |
| Regression to older versions | Existing scanner/unit suite plus the 583-entry legacy width profile | No change to version-selected widths or old decoder behavior |

## Embedded SQL

### Observed target instructions

| Opcode | Mnemonic | Words | Count | Current status |
| ---: | --- | ---: | ---: | --- |
| `0x0006` | `DBCOMMIT` | 0 | 11 | Implemented and source-validated |
| `0x0007` | `DBROLLBACK` | 0 | 31 | Implemented and source-validated |
| `0x0008` | `DBSTOP` | 0 | 13 | Unresolved; likely transaction disconnect, but no matching PB 2022 source pair |
| `0x0009` | `DBCLOSE` | 0 | 10 | Unresolved |
| `0x000A` | `DBOPEN` | 1 | 8 | Unresolved |
| `0x000B` | `DBDELETE` | 3 | 6 | Unresolved |
| `0x000C` | `DBUPDATE` | 3 | 15 | Unresolved |
| `0x000D` | `DBEXECUTE` | 1 | 2 | Unresolved |
| `0x000E` | `DBFETCH` | 3 | 18 | Unresolved |
| `0x000F` | `DBINSERT` | 3 | 5 | Unresolved |
| `0x0010` | `DBSELECT` | 4 | 60 | Unresolved |
| `0x01C3` | `DBEXECUTEIMMED` | 0 | 8 | Unresolved |
| `0x01CE` | `ENTER_EMBEDDED` | 1 | 38 | Unresolved |
| `0x01CF` | `EXIT_EMBEDDED` | 0 | 38 | Unresolved |

The target contains 263 instructions in this family. Forty-two commit/rollback
occurrences are already handled; 221 remain unresolved. There are no direct
SQL/cursor opcodes in the current `appexmfe` report and only the validated
commit/rollback pair in `pfcapsrv`, so the target frequency is not a semantic
oracle.

PbdViewer contains the broadest reusable recipes:

- transaction operations consume a transaction object;
- open/execute/fetch/close consume cursor, transaction, and parameter values;
- direct insert/update/delete and select recover stored SQL through a cursor
  descriptor in the object's variable buffer;
- prepare, execute immediate, dynamic SQL, and descriptor variants have
  separate stack forms;
- cursor and procedure declarations are enriched after the statement is
  decoded.

PowerBuilder-decompile independently parses a `StmtInfo` record containing
SQL-string location, select-statement indirection, and parameter spans. Its
direct DML/select handlers substitute stack expressions into those spans.
This is strong corroboration for the metadata-first approach, although some
handlers are visibly approximate (`DBFETCH` consumes the remaining stack, for
example) and must not be ported literally.

The current PB 2022 object parser reads but discards the global value buffer
as `_global_value_buffer`. That is the leading candidate for SQL statement
metadata and must be retained and described before the direct DML opcodes can
be implemented soundly. This is a structural prerequisite, not an opcode
exception.

### SQL gaps and oracle plan

1. Preserve the global value/statement buffer in `CompiledObjectLayout` and
   expose evidence offsets in the JSON report.
2. Port only the `StmtInfo`/cursor descriptor parsing concept, with bounds
   checks and PB 2022 observations; do not port global mutable state from the
   Python project.
3. Correlate each target SQL operand with a descriptor and recovered string.
   This can validate layout, not source equivalence.
4. Add a public or locally compiled PB 2022 fixture containing static
   select/insert/update/delete, declared cursor open/fetch/close, execute
   immediate, and disconnect. The fixture must include exported source.
5. Implement one SQL form at a time and compare transaction object, host
   parameters, `into` variables, cursor name, and exact statement kind.

The archived Python `SelectStatement`, `InsertStatement`, `UpdateStatement`,
`DeleteStatement`, `CommitStatement`, and `RollbackStatement` classes are a
useful target IR vocabulary. They are not evidence that the archived pipeline
could recover these statements from a PBD.

## Structured control flow

### Current state

The semantic preview directly translates `JUMPTRUE`, `JUMPFALSE`, and `JUMP`
to `if ... then goto` and `goto`. On the target this affects 1,677 branch
instructions across 234 regions; on `pfcapsrv`, 15,027 across 1,499 regions;
and on the otherwise 100%-accepted `appexmfe`, 272 across 48 regions. The 30
target and 1,948 PFC unresolved branch occurrences are mostly missing-stack
cascades. The much larger quality gap is that all accepted branches remain
unstructured.

The separate Rust CFG currently splits at branch/call families but then adds
only linear edges. Its SSA conversion emits empty definitions and sequential
jump terminators. It is not connected to the PB 2022 semantic-preview stack
state. It should be treated as a scaffold, not as an existing solution.

PbdViewer's post-processor is useful as a catalog of compiler idioms:

- typed catch branches and finally labels;
- `choose case`, including ranges and relational cases;
- `for ... to ... step ...`;
- pre-test and post-test `do while`/`do until` loops;
- `exit` and `continue` inferred from loop boundaries;
- `if`/`elseif`/`else` and removal of redundant gotos;
- indentation after regions are recognized.

These routines destructively rewrite neighboring text lines and assume
specific patterns. Their conditions are valuable regression cases, but a Rust
port should operate on a CFG/region tree rather than mutate strings.
PowerBuilder-decompile adds no structuring advantage: its branch handler only
maps byte offsets to debug line labels and emits goto text.

The archived Python offers good names (`IfStatement`, `ChooseCase`, `ForLoop`,
`WhileLoop`, `DoLoop`, `ExitStatement`, and `ContinueStatement`), but its CFG
connects only explicit branch targets and omits required fallthrough edges.
The archived decoder's `_identify_jump_targets` is empty, and its choose node
is explicitly marked as a stub. The current Rust domain CFG/SSA is similarly
simplified, so neither should be promoted without replacement.

### Required control-flow foundation

1. Build leaders from function entry, branch targets, and fallthrough after
   terminators.
2. Distinguish conditional, unconditional, return, throw, and exception-region
   terminators.
3. Add both target and fallthrough edges where applicable; validate every
   target against the already exact instruction-boundary set.
4. Propagate expression-stack states across edges and reconcile joins. The
   current linear `Vec<Expression>` with text payloads cannot represent
   phi-like merges safely.
5. Derive dominators/post-dominators and natural loops, then construct a
   region tree.
6. Recover constructs incrementally: `if`, `if/else`, pre/post-test loops,
   `for`, `choose`, `exit`/`continue`, and finally exception regions.
7. Keep an explicit goto fallback for irreducible or not-yet-recognized flow.

The source-paired PFC and examples corpus is already sufficient to begin this
work: even `appexmfe`'s 100% linear acceptance contains 272 branches. Tests
must compare normalized structured source, not merely require that every
instruction was consumed.

## DataWindow

### Current evidence

| Corpus | Compiled objects | Tag | Matching exported `.srd` |
| --- | ---: | --- | ---: |
| Target `replicacao.pbd` | 16 | `PDW2200` | 0 |
| OpenSourcePFC `pfcapsrv.pbl` | 13 | `PDW2100` | 13 |
| OpenSourcePFC `appexmfe.pbl` | 5 | `PDW2100` | 5 |

The object inspector correctly classifies these envelopes and deliberately
reports `datawindow_pcode_layout_not_implemented`. A DataWindow object is not
an ordinary compiled-object envelope and should not be sent through the
function-region parser.

None of the three historical codebases supplies a trustworthy parser:

- PbdViewer recognizes `.dwo` but explicitly says DataWindow source can be
  exported through the PowerBuilder interface; it does not decode the body.
- PowerBuilder-decompile maps object type 18 to `.dwo` and has no parser for
  its contents.
- Archived PowerRebuilder searches for strings/`select` in instructions or
  assumes a `DAT*` prefix. At the extracted object-payload layer the PBL
  `DAT*` container block has already been removed, so that assumption is at
  the wrong abstraction level. Its enhanced extractor import is also absent
  from the archive.

### DataWindow opportunity

The 18 public PBL/`.srd` pairs form a strong `PDW2100` differential corpus.
They can be used to identify source-string fragments, length tables, property
records, column definitions, SQL/select data, expression bytecode, and checks
or compression without guessing from the target. The `PDW2200` target then
provides a version-delta corpus, but not a source oracle.

The work should therefore proceed as a separate format track:

1. Produce byte maps and entropy/string inventories for all 18 `PDW2100`
   objects and align them with their `.srd` files.
2. Find fields stable across objects and verify every proposed offset/length
   on all 18, not just one sample.
3. Implement a read-only structural inspector that reports records and raw
   slices before emitting any `.srd` text.
4. Round-trip the recovered `PDW2100` semantics against all 18 exported
   sources using normalized syntax/property ordering.
5. Compare `PDW2100` with the 16 `PDW2200` objects and identify the version
   delta explicitly.
6. Do not claim target DataWindow decompilation until at least one `PDW2200`
   binary/source pair is available.

## PB legacy to PB 2022 delta

| Layer | Legacy evidence | PB 2022 observation | Consequence |
| --- | --- | --- | --- |
| Compiled-object envelope | PbdViewer supports versions through `0x014E` | Public PB 2022 uses `0x0152`; target uses `0x0153` | Cursor order remains useful, but every conditional field must be version-gated and boundary-tested |
| Opcode width table | PB 11+ references contain 583 entries (`0x0000..0x0246`) | Runtime `22.1.0.2819` contains 615 entries (`0x0000..0x0266`); the first 583 widths match exactly | Preserve version-selected tables. Never extend older decoders by silently accepting PB 2022-only IDs |
| Core exception/SQL/jump IDs | PowerBuilder-decompile's raw 583 table | Observed PB 2022 IDs and widths agree for the instructions listed above, including two-word `PUSH_TRY` | Good compatibility evidence, still subject to source-pair semantic tests |
| PbdViewer dispatch IDs | Semantic switch inherited from PB 9, with PB 10/10.5/11 remapping | Not a raw PB 2022 namespace | Copy method behavior only after mapping by mnemonic, operands, and fixture evidence |
| DataWindow envelope | Public PB 2022 fixture contains `PDW2100` | Target contains `PDW2200` | Treat the change as a format boundary until proven otherwise |
| Semantic IR | Older tools primarily mutate strings/stack text | Current PB 2022 preview also remains textual | Exceptions and structured flow require a real region/statement IR; more switch arms alone will not close the gap |

No PB 2022-only opcode (`0x0247..0x0266`) has yet been proven to belong to one
of these four families. Their neutral names must remain neutral until a
known-source sequence or other independent semantic evidence exists.

## Recommended implementation order after this inventory

1. **CFG and exception-region minimum:** implement correct leaders, target and
   fallthrough edges, and explicit exception-region metadata without yet
   attempting all high-level constructs.
2. **Typed try/catch slice:** use the three PFC functions to implement and
   normalize `PUSH_TRY`/`CATCH_EXCEPTION`/`POP_TRY`; keep throw/finally gated
   where the oracle is missing.
3. **General control structuring:** recover `if` and loops first, then
   `choose`, `exit`, and `continue`, using PFC/appexmfe comparisons.
4. **SQL metadata slice:** retain and map statement buffers before adding SQL
   rendering; acquire a PB 2022 SQL source/binary fixture for semantic claims.
5. **DataWindow format track:** analyze the 18 `PDW2100` pairs independently
   and seek a `PDW2200` pair before target emission.

This order avoids two failure modes exposed by the inventory: copying
version-normalized PbdViewer opcode numbers as raw PB 2022 IDs, and adding
textual special cases where the missing layer is actually CFG or binary
metadata.

## Implemented checkpoint: minimal CFG and typed catches

Items 1 and the source-confirmed portion of item 2 were implemented after this
inventory:

- all 304 target functions and all 1,693 `pfcapsrv` functions produce a valid
  minimal semantic CFG;
- all branch destinations and conditional fallthroughs remain explicit;
- 14 target exception regions and three PFC exception regions are represented;
- the three PFC regions reconstruct the two typed catches in the same order as
  their exported PB 2022 source;
- each oracle also compares two normalized, source-derived body fragments, so
  verification is not inferred merely from consuming the scaffolding opcodes;
- the corresponding real PFC functions now have complete rule coverage at
  148/148, 142/142, and 138/138 instructions respectively, without promoting
  them to whole-function source verification;
- `THROW_EXCEPTION` and finally behavior remain gated for lack of a matching
  source oracle.

Coverage and verification are now separate report dimensions. The legacy
`semantically_complete` field remains for compatibility and means only that
the implemented semantic rules consumed the function without unresolved
instructions or residual stack values. Each preview also records structural
decoding, CFG validity, per-construction known-source evidence, whole-function
verification, and future object recompilation status. Whole-function and
recompilation verification default to `not_assessed` and are never inferred
from coverage.

Known-source expectations are supplied through the optional
`--known-source-oracles` decode argument. The first manifest is
[`pfcapsrv_pb2022_known_source_oracles.json`](../data/reference/pfcapsrv_pb2022_known_source_oracles.json).

## Reproducible evidence locations

- Current semantic implementation:
  [`semantic_preview.rs`](../rust/pbd-reforge/crates/adapters/src/pb/semantic_preview.rs)
- Minimal PB-specific control-flow model:
  [`semantic_cfg.rs`](../rust/pbd-reforge/crates/adapters/src/pb/semantic_cfg.rs)
- Formal three-function exception oracle test:
  [`pfcapsrv_exception_oracle.rs`](../rust/pbd-reforge/crates/adapters/tests/pfcapsrv_exception_oracle.rs)
- Versioned operand widths and opcode names:
  [`opcodes.rs`](../rust/pbd-reforge/crates/adapters/src/pb/opcodes.rs)
- PB 2022 compiled-object parser:
  [`compiled_object.rs`](../rust/pbd-reforge/crates/adapters/src/pb/compiled_object.rs)
- Generic CFG and SSA scaffolds deliberately not extended by this slice:
  [`cfg.rs`](../rust/pbd-reforge/crates/domain/src/decode/cfg.rs) and
  [`ssa.rs`](../rust/pbd-reforge/crates/domain/src/decode/ssa.rs)
- Archived semantic vocabulary:
  [`.archive/src-original/domain/powerbuilder/powerscript.py`](../.archive/src-original/domain/powerbuilder/powerscript.py)
- Archived incomplete CFG/DataWindow path:
  [`.archive/src/decompile/unified_decompile.py`](../.archive/src/decompile/unified_decompile.py)
- Existing structural findings:
  [`PB2022_OBJECT_FORMAT_NOTES.md`](PB2022_OBJECT_FORMAT_NOTES.md)
- Existing coverage history:
  [`PB2022_SEMANTIC_COVERAGE_MATRIX.md`](PB2022_SEMANTIC_COVERAGE_MATRIX.md)
