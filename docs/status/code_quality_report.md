# Code Quality Analysis Report

## Memory Management
✅ Positive: 222 | ⚠️  Warnings: 0 | 🚨 Critical: 0

### Positive
- `main.py:228`: Uses context manager for resource management
- `main.py:354`: Uses context manager for resource management
- `decompile/decompile_coordinator.py:53`: Uses context manager for resource management
- `decompile/decompile_coordinator.py:162`: Uses context manager for resource management
- `decompile/decompile_coordinator.py:212`: Uses context manager for resource management
- `decompile/decompile_coordinator.py:246`: Uses context manager for resource management
- `parse/library.py`: Uses pooling/caching
- `parse/grammar.py`: Uses pooling/caching
- `parse/base_parser.py:134`: Uses context manager for resource management
- `parse/pb_preprocessor.py:240`: Uses context manager for resource management
- ... and 212 more

## Security
✅ Positive: 29 | ⚠️  Warnings: 0 | 🚨 Critical: 5

### Critical
- `scripts/analysis/code_quality_check.py`: Potential SQL injection vulnerability
- `scripts/analysis/code_quality_check.py`: Potential SQL injection vulnerability
- `scripts/opcodes/validation/compare_decompilers.py`: Potential SQL injection vulnerability
- `tests/test_parse/test_parser.py`: Potential hardcoded secret
- `parse/visitors/sql_transformer.py`: Potential SQL injection vulnerability

### Positive
- `tests/test_validation.py`: Contains validation/sanitization logic
- `tests/test_validators.py`: Contains validation/sanitization logic
- `tests/test_type_system.py`: Contains validation/sanitization logic
- `common/__init__.py`: Contains validation/sanitization logic
- `common/types.py`: Contains validation/sanitization logic
- `common/datawindow_utils.py`: Contains validation/sanitization logic
- `extract/pbd/io/resource_utils.py`: Contains validation/sanitization logic
- `extract/pbd/utils/binary_utils.py`: Contains validation/sanitization logic
- `model/utils/config.py`: Contains validation/sanitization logic
- `model/utils/validators.py`: Contains validation/sanitization logic
- ... and 19 more

## Error Handling
✅ Positive: 95 | ⚠️  Warnings: 9 | 🚨 Critical: 0

### Warning
- `parse/debug.py`: Contains 1 bare except clauses
- `tests/test_extract.py`: Contains 1 bare except clauses
- `extract/pbd/structures/entry.py`: Contains 1 bare except clauses
- `extract/pbd/utils/text_extraction.py`: Contains 1 bare except clauses
- `scripts/maintenance/pbd_inspector.py`: Contains 2 bare except clauses
- `scripts/debug/analyze_pcode_patterns.py`: Contains 2 bare except clauses
- `scripts/debug/debug_pcode_detection_detailed.py`: Contains 3 bare except clauses
- `scripts/debug/debug_first_opcode.py`: Contains 1 bare except clauses
- `scripts/debug/parse_pcode_text.py`: Contains 1 bare except clauses

### Positive
- `main.py`: Uses logging
- `decompile/decompile_coordinator.py`: Uses logging
- `parse/library.py`: Uses logging
- `parse/library.py`: Uses type hints for optional/result types
- `parse/pseudocode_transformer.py`: Uses logging
- `parse/grammar.py`: Uses logging
- `parse/grammar.py`: Uses type hints for optional/result types
- `parse/debug.py`: Uses logging
- `parse/parse_coordinator.py`: Uses logging
- `parse/sql_parser.py`: Uses logging
- ... and 85 more

### Info
- `main.py`: Contains 9 try/except blocks
- `decompile/decompile_coordinator.py`: Contains 4 try/except blocks
- `parse/library.py`: Contains 2 try/except blocks
- `parse/pseudocode_transformer.py`: Contains 1 try/except blocks
- `parse/grammar.py`: Contains 3 try/except blocks
- `parse/base_parser.py`: Contains 3 try/except blocks
- `parse/pb_preprocessor.py`: Contains 2 try/except blocks
- `parse/debug.py`: Contains 1 try/except blocks
- `parse/interactive.py`: Contains 6 try/except blocks
- `parse/parse_coordinator.py`: Contains 5 try/except blocks
- ... and 56 more

## Concurrency
✅ Positive: 0 | ⚠️  Warnings: 1 | 🚨 Critical: 0

### Warning
- `scripts/analysis/code_quality_check.py`: Global variable in concurrent context

### Info
- `decompile/decompile_coordinator.py`: Uses concurrency feature: lock
- `decompile/__init__.py`: Uses concurrency feature: lock
- `parse/pseudocode_transformer.py`: Uses concurrency feature: lock
- `parse/transaction_parser.py`: Uses concurrency feature: lock
- `tests/test_pbd_extraction_simple.py`: Uses concurrency feature: lock
- `tests/test_pbd_extraction.py`: Uses concurrency feature: lock
- `tests/test_validators.py`: Uses concurrency feature: lock
- `common/exceptions.py`: Uses concurrency feature: lock
- `model/__init__.py`: Uses concurrency feature: lock
- `generate/generate_coordinator.py`: Uses concurrency feature: lock
- ... and 57 more

## Database Io
✅ Positive: 57 | ⚠️  Warnings: 0 | 🚨 Critical: 0

### Positive
- `decompile/decompile_coordinator.py`: Implements pagination
- `parse/sql_parser.py`: Implements pagination
- `tests/test_pbd_extraction_simple.py`: Implements pagination
- `tests/test_pbd_extraction.py`: Implements pagination
- `tests/test_pbd_fixtures.py`: Implements pagination
- `model/source.py`: Implements pagination
- `extract/extract_coordinator.py`: Implements pagination
- `extract/pbd/analysis/symbol_table.py`: Implements pagination
- `extract/pbd/analysis/datawindow.py`: Implements pagination
- `extract/pbd/structures/header.py`: Implements pagination
- ... and 47 more

## Code Organization
✅ Positive: 28 | ⚠️  Warnings: 128 | 🚨 Critical: 0

### Warning
- `main.py:315`: Function 'all' is 69 lines (consider splitting)
- `main.py:395`: Function 'clean_output' is 58 lines (consider splitting)
- `decompile/decompile_coordinator.py:301`: Function 'main' is 52 lines (consider splitting)
- `decompile/decompile_coordinator.py:41`: Function 'decompile_pbd' is 62 lines (consider splitting)
- `decompile/decompile_coordinator.py:105`: Function '_decompile_object' is 73 lines (consider splitting)
- `decompile/decompile_coordinator.py:180`: Function '_extract_datawindow' is 80 lines (consider splitting)
- `parse/pseudocode_transformer.py:186`: Function 'function_def' is 53 lines (consider splitting)
- `parse/transaction_parser.py:56`: Function 'parse_transaction_statement' is 81 lines (consider splitting)
- `parse/transaction_parser.py:139`: Function 'parse_transaction_block' is 69 lines (consider splitting)
- `parse/grammar.py:73`: Function 'load_grammar' is 52 lines (consider splitting)
- ... and 118 more

### Positive
- `parse/sql_parser.py`: Uses dependency injection pattern
- `common/pipeline.py`: Uses dependency injection pattern
- `common/exceptions.py`: Uses dependency injection pattern
- `common/exceptions.py`: Uses dependency injection pattern
- `common/exceptions.py`: Uses dependency injection pattern
- `common/exceptions.py`: Uses dependency injection pattern
- `model/ui.py`: Uses dependency injection pattern
- `model/ui.py`: Uses dependency injection pattern
- `model/ui.py`: Uses dependency injection pattern
- `model/ui.py`: Uses dependency injection pattern
- ... and 18 more

## Performance
✅ Positive: 244 | ⚠️  Warnings: 0 | 🚨 Critical: 0

### Positive
- `main.py`: Uses list comprehensions
- `decompile/decompile_coordinator.py`: Uses list comprehensions
- `decompile/__init__.py`: Uses list comprehensions
- `parse/library.py`: Uses list comprehensions
- `parse/constants.py`: Uses list comprehensions
- `parse/pseudocode_transformer.py`: Uses list comprehensions
- `parse/transaction_parser.py`: Uses list comprehensions
- `parse/__init__.py`: Uses list comprehensions
- `parse/grammar.py`: Uses list comprehensions
- `parse/base_parser.py`: Uses list comprehensions
- ... and 234 more

## Monitoring
✅ Positive: 70 | ⚠️  Warnings: 0 | 🚨 Critical: 0

### Positive
- `main.py`: Uses structured logging
- `decompile/decompile_coordinator.py`: Uses structured logging
- `parse/library.py`: Uses structured logging
- `parse/pseudocode_transformer.py`: Uses structured logging
- `parse/grammar.py`: Uses structured logging
- `parse/debug.py`: Uses structured logging
- `parse/parse_coordinator.py`: Uses structured logging
- `parse/sql_parser.py`: Uses structured logging
- `tests/test_pbd_fixtures.py`: Uses structured logging
- `common/datawindow_utils.py`: Uses structured logging
- ... and 60 more
