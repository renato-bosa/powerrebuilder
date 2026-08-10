# PowerBuilder 2022 object-format notes

This document records observations separately from confirmed format rules. The
local fixture used for the observations is proprietary and is not committed to
the repository.

## Confirmed container layer

The PBL/PBD container is organized in 512-byte blocks. Directory entries in
`NOD*` blocks point to forward-linked `DAT*` chains. Reassembling the declared
payload bytes from those chains produced byte-identical raw object dumps for all
entries in the PB 2022 R2 fixture.

The `extract` command writes:

- every reconstructed entry as an indexed `.bin` file;
- the first data-block offset and the complete physical block chain;
- the payload size and BLAKE3 hash;
- a `manifest.json` containing the source container metadata.

The output directory must be empty so stale evidence cannot be mistaken for a
current extraction.

```powershell
pbdreforge extract application.pbd --out analysis\raw
```

## Observed object envelopes

Two top-level object envelopes occur in the local PB 2022 R2 fixture:

1. Non-DataWindow objects begin with little-endian object version `0x0153`
   (339). The following fields contain flags/revision `3` and a stable
   object-type code.
2. DataWindow objects begin with the null-terminated ASCII tag `PDW2200`.

The following type-code correlations are consistent across the fixture, but
remain observations until confirmed with independent fixtures:

| Object type | Observed code |
| --- | ---: |
| Function | `0x407D` |
| Structure | `0x407E` |
| Application | `0x4086` |
| Window | `0x408A` |

User objects use several codes, probably reflecting distinct visual and
nonvisual base classes. They must not be collapsed into one format assumption.

The `inspect` command reports the envelope, printable ASCII/UTF-16LE strings,
and string clusters with byte offsets. A string cluster is only a candidate
region; it is not a proven symbol-table or source-code section.

```powershell
pbdreforge inspect application.pbd --out analysis\inspection.json
```

## Compiled-object and P-code validation

The compiled-object parser follows the cursor order in PbdViewer's `PbEntry`
implementation and requires exact consumption of the complete object. It
isolates each function's declared P-code and debug-data regions with checked
offsets and lengths. On the local fixture, all 54 non-DataWindow compiled
objects parsed to their exact end and exposed 304 P-code regions containing
103,036 bytes. The 16 DataWindow objects are recognized but their internal
P-code layout has not been implemented.

The opcode table's operand widths are counts of 16-bit words, not bytes. For PB
11 and newer, the diagnostic scanner uses the 583-entry length profile from
PbdViewer's `PCodeParser110`. PB 2022 uses that profile provisionally because
PbdViewer does not explicitly register object version `0x0153`.

The safe `decode` path scans only the validated regions and stops before an
unknown opcode, because its operand width is not known. It writes a per-region
diagnostic report rather than claiming to have recovered source or a valid IR:

```powershell
pbdreforge decode application.pbd --out analysis\decode
```

For the local fixture, 300 of 304 regions scan exactly to their declared end:
23,105 known instructions and 102,136 of 103,036 P-code bytes are consumed
without guessing. The remaining four regions stop at PB 2022 opcodes `0x0251`
or `0x0253`, whose widths and semantics remain unknown. This is strong evidence
for the region boundaries and the PB11+ length profile, but it is not yet a
semantic decompilation result.

The former whole-object behavior is available only with
`--unsafe-raw-object`; its success count is diagnostic noise and must not be
described as decompilation.

Before a region can be marked as validated P-code, it must have independently
verified boundaries and satisfy at least these checks:

- region offsets and lengths stay within the owning object;
- function/event ownership is known;
- instruction operands remain in bounds;
- branch targets land on instruction boundaries inside the same region;
- unknown-opcode coverage is reported rather than silently accepted;
- control-flow and stack behavior are plausible on a known-source fixture.

## External references

- The PowerBuilder User's Guide states that PBLs contain a header, object
  source, and binary code, and documents UTF-16LE source encoding in PB 10 and
  later: <https://infocenter.sybase.com/help/topic/com.sybase.infocenter.dc00844.1252/pdf/pbug.pdf>
- Appeon's current PBL-folder documentation distinguishes text source files
  from compiled P-code artifacts: <https://docs.appeon.com/pb2025r2/pbug/PBL_folder2.html>
- Appeon's ORCA documentation describes source and embedded binary components
  as separate import inputs: <https://docs.appeon.com/pb2025r2/orca_guide/XREF_73854_PBORCA.html>
- A community PBL format note describes `NOD*` directory blocks and forward-
  linked `DAT*` chains: <https://gist.github.com/tom-wolfe/a417bbee2e07098212aefdcee2b41ff2>
- PbdViewer's compiled-object cursor and versioned P-code length tables are the
  direct structural reference used by the experimental parser:
  <https://github.com/Hucxy/PbdViewer>

None of these references documents the PB 2022 opcode additions or guarantees
that the PB11 length profile remains unchanged. Semantics must be established
experimentally against controlled fixtures whose source is known.
