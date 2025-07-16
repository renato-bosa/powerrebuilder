# PR #2: Fix Opcode Definition Lookup Issues

## Summary
- Fix opcode lookup logic that incorrectly reports opcodes as unknown
- Remove unnecessary fallbacks to unknown_opcodes module
- Consolidate opcode lookup into single path

## Problem
The decoder incorrectly falls back to unknown opcodes even when opcodes are properly defined in OPCODE_TABLE. All opcodes (0x00-0x246) are actually present, but lookup logic is flawed.

## Solution
1. Remove fallback to `get_unknown_opcode_info` in decoder.py
2. Fix import statements to use correct opcode module
3. Consolidate opcode lookup logic
4. Add comprehensive tests

## Implementation Details

### Fix 1: Remove unknown opcode fallback
```python
# In decoder.py lines 320-337
# Remove:
from src.decompile.opcodes.unknown_opcodes import get_unknown_opcode_info
opcode_info = get_unknown_opcode_info(opcode)

# Keep only:
opcode_info = get_opcode_info(opcode)
if not opcode_info:
    opcode_info = OpcodeInfo(f"UNKNOWN_{opcode:02X}", opcode, 0, "Unknown opcode")
```

### Fix 2: Consolidate lookup logic
```python
def get_opcode_info_consolidated(opcode: int, version: Optional[str] = None) -> OpcodeInfo:
    """Single source of truth for opcode lookup."""
    # Check main table first
    if opcode in OPCODE_TABLE:
        return OPCODE_TABLE[opcode]
    
    # Check version-specific if provided
    if version and version in VERSION_SPECIFIC_OPCODES:
        if opcode in VERSION_SPECIFIC_OPCODES[version]:
            return VERSION_SPECIFIC_OPCODES[version][opcode]
    
    # Only return unknown if truly not found
    return OpcodeInfo(f"UNKNOWN_{opcode:02X}", opcode, 0, "Unknown opcode")
```

## Test Plan
- [ ] Verify all reported "unknown" opcodes are found in OPCODE_TABLE
- [ ] Run decompiler on test files and verify no UNKNOWN_ opcodes
- [ ] Add unit tests for all opcodes from logs
- [ ] Regression test existing functionality

## Verification Script
```python
# Test that all opcodes reported as unknown are actually defined
test_opcodes = [0x19, 0x1A, 0x1B, 0x1E, 0x8A, 0x8B, 0x90, 0xC4, 0xC5, 0xC6, 0xC7, 0xDC, 0xEA, 0xEB, 0xED]
for op in test_opcodes:
    info = get_opcode_info(op)
    assert info is not None, f"Opcode 0x{op:02X} should be defined"
```

## Estimated Time: 9-13 hours

## Branch: `fix/opcode-lookup-issues`