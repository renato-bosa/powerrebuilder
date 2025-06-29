# 100% Accuracy Improvement Plan for PowerBuilder Pipeline - Complete Guide

## Executive Summary

The PowerBuilder pipeline currently experiences significant extraction failures affecting approximately 15-20% of DataWindow objects. This document outlines a comprehensive solution to achieve 100% accuracy in PowerBuilder file extraction and parsing.

### Current Challenge
- **806 DataWindow files** fail to extract properly (15-20% failure rate)
- **2,405 DAT block corruptions** causing incomplete extractions
- **160 parse entry failures** preventing proper file processing

### Root Causes Identified
1. **Magic Number Confusion**: The value 0x444F4D76 (1146094070) is being misinterpreted as a file size rather than recognized as a DataWindow header marker
2. **Binary/Text Mixing**: DataWindow files containing embedded images or binary data fail standard text extraction
3. **File Type Variations**: Different DataWindow suffixes (_sql, _ex, _ds, etc.) require specialized handling
4. **Legacy Format Support**: Older PowerBuilder versions use different syntax structures

## Solution Architecture

### Phase 1: Enhanced Binary Detection and Classification (Week 1)

#### Implementation Goals
- Enhance binary content detection algorithm
- Add magic number recognition for all DataWindow variants
- Implement file suffix-based classification system
- Create specialized parsers for each DataWindow type

#### DataWindow Type Classification System
```
File Suffix → Parser Strategy:
- _sql    → SQL-focused parser with loose syntax requirements
- _ex     → External DataWindow parser with reference resolution
- _ds     → DataStore parser with data-centric approach
- _dddw   → DropDown parser with list handling
- _rpt    → Report parser with formatting preservation
```

#### Location: `common/object_type_detector.py`
```python
# Priority: HIGH
# Enhance binary content detection algorithm
# Add magic number recognition for all DataWindow variants
# Implement file suffix-based classification system
# Create specialized parsers for each DataWindow type
```

### Phase 2: DAT Block Corruption Resolution (Week 2)

#### Implementation Goals
- Fix magic number misinterpretation in `extract/pbd/structures/data_block.py`
- Implement partial block recovery for corrupted data
- Add boundary detection for valid object sections

#### Magic Number Handler
```python
# Priority: CRITICAL
# Location: extract/pbd/structures/data_block.py

KNOWN_MAGIC_NUMBERS = {
    0x444F4D76: "DATAWINDOW_HEADER",  # "vMOD" in little-endian
    0x4F424A44: "OBJECT_DESCRIPTOR",
    # Add more as discovered
}

def validate_dat_size(declared_size, file_size, offset):
    if declared_size in KNOWN_MAGIC_NUMBERS:
        return handle_magic_number(declared_size)
    if declared_size + offset > file_size:
        return search_for_next_valid_header(offset)
```

#### Recovery Mechanisms
- **Partial Block Recovery**: Extract valid data before corruption
- **Header Reconstruction**: Rebuild corrupted headers using patterns
- **Size Inference**: Calculate actual size from content patterns
- **Boundary Detection**: Find next valid object boundary

### Phase 3: Advanced DataWindow Syntax Parser (Week 3)

#### Multi-Format Parser Implementation
```python
# Priority: HIGH
# Location: decompile/analysis/datawindow_extractor.py

class EnhancedDataWindowExtractor:
    def extract_syntax(self, data: bytes) -> tuple[str, bool]:
        # Try multiple extraction strategies
        strategies = [
            self._extract_standard_syntax,
            self._extract_binary_embedded_syntax,
            self._extract_compressed_syntax,
            self._extract_legacy_format,
            self._extract_with_error_recovery
        ]
        
        for strategy in strategies:
            result, success = strategy(data)
            if success:
                return result, True
                
        # If all fail, use deep inspection
        return self._deep_binary_inspection(data)
```

#### Binary Content Handling
- **Image Extraction**: Separate embedded images from syntax
- **Binary Markers**: Identify and preserve binary sections
- **Mixed Content Parser**: Handle interleaved text/binary data
- **Encoding Detection**: Auto-detect character encodings

#### SQL Statement Parser Enhancement
- Handle multi-line SQL with proper escaping
- Support stored procedure definitions
- Parse complex JOIN statements
- Handle database-specific syntax variations

### Phase 4: Grammar Parser Improvements (Week 4)

#### PowerBuilder Grammar Enhancements
```python
# Location: parse/grammar/powerbuilder.lark

# Add error recovery rules
error_recovery: _NEWLINE* "!" _NEWLINE*
              | unexpected_token _NEWLINE*

# Add lookahead for ambiguous constructs
statement: assignment_statement
         | if_statement  
         | LOOKAHEAD(2) method_call
         | property_access

# Handle incomplete constructs
incomplete_block: block_start ~_NEWLINE*
```

#### Error Handling Improvements
- Implement partial parse recovery
- Add statement completion heuristics
- Create fallback parsing modes
- Generate meaningful error reports
- Implement token suggestion system
- Add context-aware error correction

### Phase 5: Integration and Validation (Week 5)

#### Pipeline Integration
```python
# Location: main.py / pipeline configuration

class EnhancedPipeline:
    def __init__(self):
        self.binary_detector = EnhancedBinaryDetector()
        self.dat_recovery = DATBlockRecovery()
        self.dw_extractor = EnhancedDataWindowExtractor()
        self.parser = ImprovedGrammarParser()
        
    def process_with_recovery(self, file_path):
        # Multi-stage processing with fallbacks
        stages = [
            self.standard_processing,
            self.recovery_processing,
            self.deep_inspection_processing
        ]
```

## Implementation Guide

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

Update `extract/pbd/structures/data_block.py`:
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

Create validation script `scripts/validation/validate_extraction.py`:
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

Run progressive integration tests:
```bash
# Test individual components
pytest tests/test_100_percent_accuracy/test_binary_detection.py -v
pytest tests/test_100_percent_accuracy/test_dat_recovery.py -v
pytest tests/test_100_percent_accuracy/test_datawindow_parser.py -v

# Run full pipeline test
uv run python main.py all --test-mode
```

### Step 7: Performance Optimization

Add caching and parallel processing:
```python
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor

@lru_cache(maxsize=1000)
def detect_file_type(file_header: bytes) -> str:
    """Cache file type detection for performance"""
    # Implementation

def process_files_parallel(file_list):
    with ProcessPoolExecutor() as executor:
        results = executor.map(process_single_file, file_list)
    return list(results)
```

## Testing Framework

### Unit Tests
```python
# For each component
def test_binary_detection():
    assert detector.is_binary(known_binary_file) == True
    assert detector.get_type(datawindow_file) == "datawindow"

def test_dat_recovery():
    corrupted = load_corrupted_dat()
    recovered = recovery.process(corrupted)
    assert recovered.is_valid()
```

### Integration Tests
```python
def test_full_pipeline():
    for failed_file in all_806_failures:
        result = pipeline.process(failed_file)
        assert result.success == True
        assert result.data_integrity == 100
```

### Validation Tests
- Compare extracted content with known good outputs
- Validate SQL syntax with database parsers
- Ensure visual elements are preserved
- Check cross-references remain intact

## Implementation Schedule

### Week 1: Binary Detection & Classification
- [ ] Implement enhanced object type detector
- [ ] Create DataWindow classifier
- [ ] Build test framework
- [ ] Achieve 100% type detection

### Week 2: DAT Block Recovery
- [ ] Implement magic number handler
- [ ] Create recovery mechanisms
- [ ] Test against corrupted files
- [ ] Validate data integrity

### Week 3: DataWindow Parser Enhancement
- [ ] Build multi-strategy parser
- [ ] Implement binary handling
- [ ] Enhance SQL extraction
- [ ] Test complex scenarios

### Week 4: Grammar Improvements
- [ ] Enhance PowerBuilder grammar
- [ ] Implement error recovery
- [ ] Add EOF handling
- [ ] Complete grammar testing

### Week 5: Integration & Validation
- [ ] Integrate all components
- [ ] Run comprehensive tests
- [ ] Optimize performance
- [ ] Document improvements

## Success Metrics

### Primary Goals
- **100% DataWindow Extraction**: All 806 failing files parsed successfully
- **Zero DAT Corruption Errors**: All corruption handled gracefully
- **100% Parse Success**: No unexpected token or EOF errors

### Secondary Goals
- **Performance**: < 10% increase in processing time
- **Data Integrity**: 100% validation of extracted content
- **Maintainability**: Comprehensive test coverage

### Validation Checklist
- [ ] All 806 DataWindow files extract successfully
- [ ] No DAT block corruption errors
- [ ] No parse entry failures  
- [ ] No unexpected token errors
- [ ] Performance degradation < 10%
- [ ] All existing tests still pass
- [ ] Memory usage remains stable

## Risk Mitigation

### Technical Risks
1. **Unknown File Formats**: May discover new PowerBuilder versions
   - Mitigation: Extensible parser architecture
   
2. **Performance Impact**: Recovery mechanisms may slow processing
   - Mitigation: Parallel processing and caching
   
3. **Data Loss**: Aggressive parsing might lose information
   - Mitigation: Multiple validation stages

### Implementation Risks
1. **Regression**: New code might break existing functionality
   - Mitigation: Comprehensive regression testing
   
2. **Complexity**: System might become too complex
   - Mitigation: Modular design with clear interfaces

### Rollback Plan
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

## Monitoring and Reporting

### Testing Commands
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

### Progress Dashboard
```
Week 1: Binary Detection    [####----] 50%
Week 2: DAT Recovery       [--------] 0%
Week 3: DW Parser          [--------] 0%
Week 4: Grammar            [--------] 0%
Week 5: Integration        [--------] 0%

Files Fixed: 0/806
Success Rate: 0%
```

### Daily Reports
- Files successfully parsed
- New failure patterns discovered
- Performance metrics
- Test coverage statistics

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

## Conclusion

This comprehensive plan addresses all identified failure patterns through a systematic, testable approach. The modular design ensures safe implementation while the extensive testing framework validates our progress toward 100% accuracy. The solution not only fixes current issues but provides a robust foundation for handling future PowerBuilder format variations.

By addressing each failure type with specialized solutions and comprehensive testing, we can eliminate all parsing errors and data corruption issues. The implementation ensures that improvements can be made incrementally while maintaining system stability.