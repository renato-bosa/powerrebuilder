# Opcode Documentation Organization

As of June 2025, the opcode documentation has been reorganized from 9 scattered files into 3 focused documents:

## Current Documentation (3 files)

### 1. `opcode_discovery_guide.md`
- **Purpose**: Comprehensive guide for the automated opcode discovery pipeline
- **Content**: Tool usage, configuration, best practices, troubleshooting
- **Merged from**: OPCODE_DISCOVERY_TOOLS.md + opcode_discovery_automation.md

### 2. `opcode_reference.md` 
- **Purpose**: Authoritative reference of all 583 verified PowerBuilder opcodes
- **Content**: Complete opcode listing with hex values, names, lengths, and metadata
- **Status**: Maintained as-is, this is the primary reference

### 3. `issues/pcode_extraction_debug_report.md`
- **Purpose**: Active bug report for P-code detection logic issue
- **Content**: Documents why .fun files aren't being created during extraction
- **Status**: Moved to issues/ directory as it requires fixing

## Archived Documentation (5 files)

Historical documents moved to `archive/opcode_history/`:

1. **OPCODE_FIX_SUMMARY.md** - Chronicles the discovery of incorrect opcode mappings
2. **opcode_analysis_report.md** - Detailed technical analysis of opcode mapping issues
3. **opcode_analysis_summary.md** - Executive summary of the analysis findings
4. **opcode_remediation_plan.md** - Original plan before reference implementations were found
5. **opcode_discovery_lessons.md** - Post-mortem on failed pattern-matching approach

## Why This Organization?

1. **Clarity**: Users now have just 2 main documents to consult (guide + reference)
2. **History Preserved**: Important lessons learned are archived but accessible
3. **Active Issues Visible**: Bug reports are clearly separated in issues/
4. **Reduced Redundancy**: Overlapping content has been consolidated

## For New Contributors

- Start with `opcode_discovery_guide.md` to understand the tools
- Reference `opcode_reference.md` for the complete opcode list
- Check `issues/` for known bugs that need fixing
- Browse `archive/opcode_history/` for context on past decisions