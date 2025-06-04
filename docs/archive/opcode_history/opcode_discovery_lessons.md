# Opcode Discovery: Lessons Learned

## The Journey

### Phase 1: Pattern-Based Discovery (Failed Approach)

- We analyzed binary P-code files looking for patterns
- Created an automated pipeline to iteratively guess opcode meanings
- Achieved "100% coverage" by assigning names to every byte value
- Thought we understood opcodes like:
  - 0xE4 = LOAD
  - 0xE8 = STORE
  - 0xC4 = CONST_0
  - 0xD4 = JUMP

### Phase 2: Validation Revealed the Truth

- Stack imbalance: 386 instead of 0
- No decompilation output
- Illogical instruction sequences
- Realized we were just pattern matching without understanding

### Phase 3: Found Reference Implementations

- Located existing decompilers:
  - pbdviewer (C#): 101 opcodes
  - powerbuilder-decompile (Python): 583 opcodes
- Extracted and compared with our guesses

## The Shocking Results

**Zero overlap between our guessed opcodes and the real ones!**

- Our guesses: 145 opcodes (0x0-0xFF range)
- Verified: 583 opcodes (0x0-0x246 range)
- Common opcodes: 0
- Our most common patterns: UNKNOWN (41), VARIANT (39), SPECIAL (15)
- Real most common patterns: CNV (96 conversions), PUSH (58), equality ops (21)

## What We Got Wrong

1. **Opcode values**: We thought opcodes were single bytes (0-255). Real opcodes go up to 0x246 (582).

2. **Opcode meanings**: Our pattern-based names were completely wrong:
   - We saw "VARIANT_80" - Real: "ASSIGN_INT"
   - We saw "CONST" patterns - Real: Complex type conversions
   - We saw "MARKER" bytes - Real: Actual operations

3. **Instruction lengths**: We guessed based on patterns. Real lengths are defined by the opcode specification.

4. **String detection**: We thought UTF-8 sequences were unknown opcodes. They were just embedded strings.

## Key Insights

1. **Reverse engineering without ground truth is guesswork**: No amount of pattern analysis can reveal the true semantics of opcodes.

2. **Existing work matters**: Instead of reinventing the wheel, we should have searched for existing implementations first.

3. **Validation is crucial**: Our "100% coverage" meant nothing without proper validation.

4. **Real opcodes tell a story**:
   - 96 type conversion opcodes (CNV_*) show PowerBuilder's type system complexity
   - 58 PUSH variants show different data sources
   - Separate opcodes for each data type operation (ADD_INT, ADD_LONG, ADD_DOUBLE, etc.)

## The Real Opcode Structure

From the verified opcodes, we can see PowerBuilder P-code is:

- **Strongly typed**: Separate opcodes for each type (INT, LONG, DOUBLE, DEC, etc.)
- **Stack-based**: PUSH/POP operations, stack manipulation
- **Object-oriented**: DOT operations, method calls, object creation
- **Database-aware**: Dedicated DB* opcodes for SQL operations
- **Rich in conversions**: 96 CNV_* opcodes for type conversions

## Next Steps

1. **Use the verified opcodes**: Replace our entire opcode system with the reference implementation
2. **Study the implementations**: Learn from how they decode and decompile
3. **Test with real programs**: Create simple PowerBuilder programs and verify the decoding
4. **Build on proven foundations**: Don't reinvent what already exists

## The Silver Lining

While our approach failed, we:

- Built a robust extraction pipeline
- Created good analysis tools
- Learned valuable lessons about reverse engineering
- Now have access to real, working implementations

The journey wasn't wasted - it led us to the right solution.
