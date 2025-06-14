# 100% Accuracy Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing the improvements needed to achieve 100% accuracy in PowerBuilder extraction and parsing. Based on our analysis, we have identified 806 DataWindow extraction failures and various parsing errors that need to be addressed.

## Current Status
- **Failed DataWindow Extractions**: 806 files
- **DAT Block Corruptions**: 2,405 instances  
- **Parse Entry Errors**: 160 instances
- **Primary Failure Pattern**: Magic number 0x444F4D76 misinterpreted as size

## Implementation Steps

### Step 1: Set Up Testing Infrastructure
```bash
# Run failure analysis
uv run python scripts/analysis/analyze_failed_datawindows.py

# Run baseline tests
uv run python tests/test_100_percent_accuracy/test_framework.py
```

### Step 2: Integrate Enhanced DataWindow Extractor

1. **Update imports in `decompile/analysis/datawindow_extractor.py`:**
```python
from decompile.analysis.enhanced_datawindow_extractor import EnhancedDataWindowExtractor
```

2. **Replace current extraction logic:**
```python
# In extract_syntax method
extractor = EnhancedDataWindowExtractor()
syntax, success = extractor.extract_syntax(data, filename)
```

### Step 3: Implement DAT Block Recovery

1. **Update `extract/pbd/structures/data_block.py`:**
```python
KNOWN_MAGIC_NUMBERS = {
    0x444F4D76: "DATAWINDOW_HEADER",  # Most common corruption
    0x4F424A44: "OBJECT_DESCRIPTOR",
}

def read_with_recovery(self, stream, offset, file_size):
    # Check for magic number misinterpretation
    if self.data_length in KNOWN_MAGIC_NUMBERS:
        return self._handle_magic_number(stream, offset)
    
    # Validate size bounds
    if self.data_length + offset > file_size:
        return self._search_next_valid_header(stream, offset)
```

### Step 4: Enhance Grammar Parser

1. **Add error recovery to `parse/grammar/powerbuilder.lark`:**
```lark
// Add at the top of grammar file
@recover = true
@propagate_positions = true

// Add error recovery rules
error_recovery: _NEWLINE* "!" _NEWLINE*
              | unexpected_token _recover_to_newline

_recover_to_newline: /[^\n]*/ _NEWLINE
```

2. **Update parser configuration in `parse/base_parser.py`:**
```python
parser = Lark(
    grammar,
    parser='earley',  # More robust than LALR
    propagate_positions=True,
    maybe_placeholders=True,
    on_error=self._handle_parse_error  # Custom error handler
)
```

### Step 5: Create Validation Suite

1. **Create validation script `scripts/validation/validate_extraction.py`:**
```python
def validate_all_extractions():
    """Validate that all 806 failed files now extract successfully"""
    failed_files = load_failed_files_list()
    success_count = 0
    
    for file_path in failed_files:
        result = extract_with_new_system(file_path)
        if result.success:
            success_count += 1
            
    accuracy = (success_count / len(failed_files)) * 100
    print(f"Extraction accuracy: {accuracy:.2f}%")
    return accuracy == 100.0
```

### Step 6: Integration Testing

1. **Run progressive integration tests:**
```bash
# Test individual components
pytest tests/test_100_percent_accuracy/test_binary_detection.py -v
pytest tests/test_100_percent_accuracy/test_dat_recovery.py -v
pytest tests/test_100_percent_accuracy/test_datawindow_parser.py -v

# Run full pipeline test
uv run python main.py all --test-mode
```

2. **Monitor progress:**
```bash
# Check progress report
cat docs/100_percent_accuracy_progress.md
```

### Step 7: Performance Optimization

1. **Add caching for repeated patterns:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def detect_file_type(file_header: bytes) -> str:
    """Cache file type detection for performance"""
    # Implementation
```

2. **Implement parallel processing:**
```python
from concurrent.futures import ProcessPoolExecutor

def process_files_parallel(file_list):
    with ProcessPoolExecutor() as executor:
        results = executor.map(process_single_file, file_list)
    return list(results)
```

## Validation Checklist

- [ ] All 806 DataWindow files extract successfully
- [ ] No DAT block corruption errors
- [ ] No parse entry failures  
- [ ] No unexpected token errors
- [ ] Performance degradation < 10%
- [ ] All existing tests still pass
- [ ] Memory usage remains stable

## Testing Commands

```bash
# Run all accuracy tests
uv run pytest tests/test_100_percent_accuracy/ -v

# Run specific failure scenarios
uv run python tests/test_100_percent_accuracy/test_framework.py

# Validate against production data
uv run python scripts/validation/validate_extraction.py

# Run full pipeline with monitoring
uv run python main.py all --verbose --log-failures
```

## Monitoring Progress

The following metrics should reach 100%:
- DataWindow extraction success rate
- DAT block parsing success rate  
- Grammar parsing success rate
- Overall pipeline success rate

Use the progress dashboard:
```bash
# Generate current progress report
uv run python tests/test_100_percent_accuracy/test_framework.py

# View report
cat docs/100_percent_accuracy_progress.md
```

## Rollback Plan

If issues arise during implementation:

1. **Component-level rollback:**
   - Each enhancement is isolated and can be disabled
   - Use feature flags for gradual rollout

2. **Maintain backward compatibility:**
   - Keep original extraction methods as fallback
   - Log when fallback is used for analysis

3. **Performance monitoring:**
   - Track extraction times
   - Set alerts for > 20% performance degradation

## Success Criteria

The implementation is successful when:
1. All 806 failed DataWindow files extract successfully
2. Zero DAT corruption errors in logs
3. Zero parsing errors for valid PowerBuilder files
4. Performance impact < 10%
5. All regression tests pass

## Next Steps After Implementation

1. **Documentation:**
   - Update technical documentation
   - Create troubleshooting guide
   - Document new extraction strategies

2. **Maintenance:**
   - Set up monitoring for new failure patterns
   - Create automated alerts for accuracy drops
   - Schedule regular validation runs

3. **Future Improvements:**
   - Machine learning for pattern recognition
   - Support for new PowerBuilder versions
   - Performance optimization for large files