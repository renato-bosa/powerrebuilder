# 100% Accuracy Improvement Plan for PowerBuilder Pipeline

## Executive Summary
This document outlines a systematic approach to achieve 100% accuracy in PowerBuilder file extraction and parsing, addressing:
- 806 DataWindow syntax extraction failures
- DAT block corruption issues
- Parsing errors with unexpected tokens and EOF conditions

## Current State Analysis

### Failure Statistics
- **Total DataWindow Failures**: 806 files (approximately 15-20% of all DataWindow objects)
- **DAT Block Corruptions**: Affects multiple PBD files with size mismatches
- **Parse Entry Failures**: Incomplete extraction leading to missing objects

### Root Causes Identified
1. **Magic Number Misinterpretation**: 0x444F4D76 being read as size value
2. **Binary/Text Content Mixing**: DataWindows with embedded images or special formatting
3. **Incomplete File Type Handling**: Different DataWindow suffixes need specialized parsing
4. **Header Structure Variations**: Different PowerBuilder versions use different formats

## Phase 1: Enhanced Binary Detection and Classification (Week 1)

### 1.1 Implement Advanced File Type Detection
```python
# Priority: HIGH
# Location: common/object_type_detector.py

- Enhance binary content detection algorithm
- Add magic number recognition for all DataWindow variants
- Implement file suffix-based classification system
- Create specialized parsers for each DataWindow type
```

### 1.2 DataWindow Type Classification System
```
File Suffix → Parser Strategy:
- _sql    → SQL-focused parser with loose syntax requirements
- _ex     → External DataWindow parser with reference resolution
- _ds     → DataStore parser with data-centric approach
- _dddw   → DropDown parser with list handling
- _rpt    → Report parser with formatting preservation
```

### 1.3 Testing Strategy
- Create test suite with failing DataWindow samples
- Validate each parser against its specific file type
- Achieve 100% detection rate for file types

## Phase 2: DAT Block Corruption Resolution (Week 2)

### 2.1 Magic Number Handler
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

### 2.2 Implement Recovery Mechanisms
- **Partial Block Recovery**: Extract valid data before corruption
- **Header Reconstruction**: Rebuild corrupted headers using patterns
- **Size Inference**: Calculate actual size from content patterns
- **Boundary Detection**: Find next valid object boundary

### 2.3 Testing Strategy
- Test against all 806 failing DataWindow files
- Validate recovered data integrity
- Ensure no data loss during recovery

## Phase 3: Advanced DataWindow Syntax Parser (Week 3)

### 3.1 Multi-Format Parser Implementation
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

### 3.2 Binary Content Handling
- **Image Extraction**: Separate embedded images from syntax
- **Binary Markers**: Identify and preserve binary sections
- **Mixed Content Parser**: Handle interleaved text/binary data
- **Encoding Detection**: Auto-detect character encodings

### 3.3 SQL Statement Parser Enhancement
- Handle multi-line SQL with proper escaping
- Support stored procedure definitions
- Parse complex JOIN statements
- Handle database-specific syntax variations

### 3.4 Testing Strategy
- Create corpus of complex DataWindow files
- Test each enhancement against real-world failures
- Validate SQL extraction accuracy

## Phase 4: Grammar Parser Improvements (Week 4)

### 4.1 PowerBuilder Grammar Enhancements
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

### 4.2 EOF Handling Improvements
- Implement partial parse recovery
- Add statement completion heuristics
- Create fallback parsing modes
- Generate meaningful error reports

### 4.3 Token Error Recovery
- Implement token suggestion system
- Add context-aware error correction
- Create token recovery strategies
- Build comprehensive token database

### 4.4 Testing Strategy
- Test against all files with parse errors
- Validate grammar coverage
- Ensure backward compatibility

## Phase 5: Integration and Validation (Week 5)

### 5.1 Pipeline Integration
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

### 5.2 Comprehensive Testing Suite
```python
# Location: tests/test_100_percent_accuracy/

test_cases = {
    "test_all_failed_datawindows": validate_806_files,
    "test_dat_corruption_recovery": validate_dat_recovery,
    "test_parse_error_resolution": validate_parsing,
    "test_binary_content_handling": validate_binary_extraction,
    "test_sql_extraction_accuracy": validate_sql_parsing
}
```

### 5.3 Performance Optimization
- Parallel processing for large files
- Caching for repeated patterns
- Memory-efficient streaming parsers
- Progress tracking and reporting

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

## Monitoring and Reporting

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

## Conclusion

This plan provides a systematic approach to achieving 100% accuracy in PowerBuilder file processing. By addressing each failure type with specialized solutions and comprehensive testing, we can eliminate all parsing errors and data corruption issues.

The modular approach ensures that improvements can be implemented incrementally while maintaining system stability. Regular testing and validation ensure that we achieve our accuracy goals without compromising performance or data integrity.