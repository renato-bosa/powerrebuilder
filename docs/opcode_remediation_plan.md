# PowerBuilder P-code Opcode Remediation Plan

## Executive Summary

We achieved 100% opcode coverage through pattern matching and educated guessing, but validation shows our interpretations are incorrect. This plan outlines a systematic approach to properly reverse engineer the P-code format.

## Current State Assessment

### Problems Identified

1. **Stack Imbalance**: Decoded files show stack depth of 386 instead of 0
2. **No Decompilation Output**: `pcode_to_source.py` produces no output
3. **Illogical Patterns**: Excessive NOPs, strange instruction sequences
4. **No Ground Truth**: We have no verified opcode definitions to compare against

### Root Cause

We assigned names to opcodes based on:

- Byte value ranges (e.g., C0-CF = constants)
- Context patterns
- Frequency analysis
- Analogies to other bytecode formats

But we never verified these assumptions against actual PowerBuilder behavior.

## Remediation Strategy

### Phase 1: Establish Ground Truth (Priority: CRITICAL)

#### Step 1.1: Create Simple PowerBuilder Test Programs

**Goal**: Build a corpus of known source → P-code mappings

**Actions**:

1. Set up PowerBuilder development environment (version 10.5 or compatible)
2. Create test programs with isolated features:
   - `test_constants.pb`: Only constant declarations
   - `test_variables.pb`: Variable declarations and assignments
   - `test_arithmetic.pb`: Basic math operations
   - `test_control_flow.pb`: If/else, loops
   - `test_functions.pb`: Function calls and returns
   - `test_strings.pb`: String operations
   - `test_objects.pb`: Object creation and method calls

**Deliverables**:

- PowerBuilder source files (.pb)
- Compiled P-code files (.pbd)
- Mapping document: source line → expected P-code pattern

#### Step 1.2: Find Reference Implementation

**Goal**: Locate existing PowerBuilder decompilers or documentation

**Actions**:

1. Search for open-source PowerBuilder decompilers
2. Look for PowerBuilder VM documentation
3. Check Sybase/SAP archives for P-code specifications
4. Contact PowerBuilder community forums
5. Analyze PowerBuilder runtime DLLs for opcode handlers

**Deliverables**:

- List of reference implementations
- Extracted opcode definitions
- Documentation links

### Phase 2: Systematic Opcode Analysis

#### Step 2.1: Reset Opcode Definitions

**Goal**: Start fresh with only verified opcodes

**Actions**:

1. Create `opcodes_verified.yaml` with empty structure
2. Move current `opcodes.yaml` to `opcodes_guessed.yaml`
3. Implement strict validation for new entries

**Script**: `reset_opcodes.py`

```python
# Pseudocode
def reset_opcodes():
    backup_current_opcodes()
    create_empty_verified_opcodes()
    setup_validation_framework()
```

#### Step 2.2: Trace-Based Analysis

**Goal**: Understand opcodes through execution tracing

**Actions**:

1. Instrument PowerBuilder runtime (if possible)
2. Create execution trace logger
3. Run test programs and capture:
   - Opcode bytes executed
   - Stack state before/after
   - Memory changes
   - Function calls made

**Script**: `trace_analyzer.py`

```python
# Pseudocode
def analyze_trace(source_file, pcode_file, trace_log):
    correlate_source_to_pcode()
    identify_opcode_effects()
    validate_stack_operations()
```

#### Step 2.3: Differential Analysis

**Goal**: Compare similar programs to isolate opcode functions

**Actions**:

1. Create program pairs with single differences
2. Compare resulting P-code
3. Identify which bytes change
4. Infer opcode function from difference

**Example**:

- Program A: `x = 5`
- Program B: `x = 10`
- Difference in P-code reveals constant encoding

### Phase 3: Opcode Verification Framework

#### Step 3.1: Create Verification Test Suite

**Goal**: Automated testing of opcode definitions

**Script**: `verify_opcodes.py`

```python
class OpcodeVerifier:
    def verify_constants(self):
        # Test that constant opcodes produce expected values
        
    def verify_stack_balance(self):
        # Ensure stack operations balance
        
    def verify_control_flow(self):
        # Test jump targets are valid
        
    def verify_decompilation(self):
        # Test that P-code → source produces valid code
```

#### Step 3.2: Implement Behavioral Testing

**Goal**: Verify decompiled code behaves identically to original

**Actions**:

1. Create test harness for PowerBuilder execution
2. Run original P-code, capture output
3. Run decompiled/recompiled code, capture output
4. Compare results

### Phase 4: Iterative Refinement

#### Step 4.1: Priority-Based Discovery

**Goal**: Focus on most common/important opcodes first

**Priority Order**:

1. Constants and literals (needed for any program)
2. Variable load/store (basic data manipulation)
3. Arithmetic operations (computation)
4. Control flow (program logic)
5. Function calls (modularity)
6. Object operations (OOP features)
7. Special/rare opcodes (edge cases)

#### Step 4.2: Community Validation

**Goal**: Leverage PowerBuilder community knowledge

**Actions**:

1. Share findings with PowerBuilder forums
2. Request validation from experienced developers
3. Collaborate on difficult opcodes
4. Build public opcode database

## Implementation Plan

### Week 1-2: Ground Truth Establishment

- Set up PowerBuilder environment
- Create test programs
- Search for references

### Week 3-4: Analysis Framework

- Build trace analyzer
- Create differential analyzer
- Reset opcode definitions

### Week 5-6: Core Opcode Discovery

- Constants and variables
- Basic operations
- Control flow

### Week 7-8: Advanced Opcodes

- Functions and methods
- Objects and classes
- Special cases

### Week 9-10: Verification and Documentation

- Run full test suite
- Document findings
- Create final opcode reference

## Success Criteria

1. **Stack Balance**: All decoded files have stack depth 0 at end
2. **Decompilation**: `pcode_to_source.py` produces valid PowerBuilder code
3. **Behavioral Match**: Decompiled code behaves identically to original
4. **Community Validation**: Opcodes verified by PowerBuilder experts
5. **Documentation**: Complete opcode reference with examples

## Risk Mitigation

1. **No PowerBuilder Access**: Use cloud/VM services, find community members
2. **Encrypted P-code**: Focus on unencrypted samples first
3. **Version Differences**: Document version-specific opcodes
4. **Legal Concerns**: Ensure reverse engineering is for interoperability

## Tools and Scripts Needed

1. `reset_opcodes.py` - Reset opcode definitions
2. `pb_test_generator.py` - Generate PowerBuilder test programs
3. `trace_analyzer.py` - Analyze execution traces
4. `differential_analyzer.py` - Compare P-code differences
5. `verify_opcodes.py` - Automated verification suite
6. `behavioral_tester.py` - Compare program behaviors
7. `opcode_documenter.py` - Generate opcode reference

## Next Immediate Steps

1. **STOP** using current incorrect opcode definitions
2. **CREATE** backup of current work
3. **FIND** PowerBuilder development environment
4. **START** with simplest possible test case
5. **VERIFY** each opcode through testing, not guessing

## Notes for AI Implementation

When implementing this plan:

1. Start with Phase 1 - without ground truth, everything else is guesswork
2. Be systematic - verify each assumption
3. Document everything - sources, tests, results
4. Fail fast - if an opcode doesn't verify, mark it unknown
5. Iterate - build knowledge incrementally

Remember: **No more guessing**. Every opcode definition must be verified through actual PowerBuilder behavior.
