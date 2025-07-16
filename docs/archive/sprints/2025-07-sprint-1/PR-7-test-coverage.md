# PR #7: Improve Test Coverage for Critical Path

## Summary
- Add tests for critical pipeline modules
- Target minimum 20% coverage (up from 7%)
- Focus on extract, parse, decompile core functionality
- Use new testing infrastructure (Syrupy, Hypothesis, Nox)

## Problem
Current test coverage is critically low at 7%, making it difficult to ensure changes don't break functionality.

## Solution
Implement comprehensive tests for critical path modules using modern testing tools.

## Test Implementation Plan

### 1. Extraction Module Tests
```python
# test_extraction_core.py
def test_pbd_header_parsing():
    """Test PBD header parsing with various formats."""
    
def test_entry_extraction():
    """Test extraction of different entry types."""
    
@given(binary_data())
def test_binary_parsing_robustness(data):
    """Property-based test for binary parsing."""
```

### 2. Parser Module Tests
```python
# test_parser_core.py
@pytest.mark.parametrize("pb_file", get_sample_files())
def test_parse_powerbuilder_files(pb_file):
    """Test parsing of real PowerBuilder files."""
    
def test_grammar_loading():
    """Test all grammars load successfully."""
```

### 3. Decompiler Module Tests
```python
# test_decompiler_core.py
def test_opcode_decoding():
    """Test opcode decoding for known sequences."""
    
def test_instruction_formatting():
    """Test instruction formatting output."""
```

### 4. Snapshot Tests with Syrupy
```python
# test_snapshots.py
def test_ast_snapshot(snapshot):
    """Test AST generation consistency."""
    ast = parse_file("sample.srw")
    assert ast == snapshot
    
def test_decompiler_snapshot(snapshot):
    """Test decompiler output consistency."""
    output = decompile_pcode("sample.fun")
    assert output == snapshot
```

## Coverage Targets
- Extract module: 30% → 50%
- Parse module: 15% → 40%  
- Decompile module: 0% → 30%
- Model module: 20% → 40%
- Overall: 7% → 20%

## Test Infrastructure Setup
1. Configure Syrupy for snapshot testing
2. Set up Hypothesis for property-based tests
3. Configure Nox for multi-version testing
4. Add coverage reporting to CI

## Estimated Time: 5 points (1-2 days)

## Branch: `test/improve-critical-coverage`