
# Migration Summary Report

## Statistics
- File movements: 194
- File merges: 4
- File deletions: 19
- Errors encountered: 1

## Movements
- extract/extract_coordinator.py → src/extract/coordinator.py
- extract/pbd/io/scanner.py → src/extract/pbd/scanner.py
- extract/pbd/structures/header.py → src/extract/pbd/structures/header.py
- extract/pbd/structures/entry.py → src/extract/pbd/structures/entry.py
- extract/pbd/structures/data_block.py → src/extract/pbd/structures/data_block.py
- extract/pbd/structures/pbd_object.py → src/extract/pbd/structures/object.py
- extract/pbd/extraction/extractor.py → src/extract/pbd/extractors/base.py
- extract/pbd/extraction/unified_resource_extractor.py → src/extract/pbd/extractors/resource.py
- extract/pbd/recovery/enhanced_recovery.py → src/extract/pbd/recovery/checkpoint.py
- extract/pbd/structures/data_corruption_fix.py → src/extract/pbd/recovery/corruption.py
... and 184 more

## Merges Required
- src/extract/pbd/reader.py: merge 3 files
- src/extract/pbd/extractors/binary.py: merge 3 files
- src/parse/parser/powerbuilder.py: merge 2 files
- src/decompile/reconstruction/formatter.py: merge 2 files

## Deletions
- extract/pbd/structures/enhanced_data_block.py
- extract/pbd/structures/enhanced_entry_parser.py
- extract/pbd/extraction/library.py
- extract/pbd/extraction/resource_catalog.py
- extract/pbd/formatters/
- extract/pbd/analysis/
- parse/interactive.py
- parse/debug.py
- parse/library.py
- parse/ast_to_model.py
... and 9 more

## Errors
Command failed: git mv tests/fixtures/__init__.py tests/fixtures/__init__.py
Error: fatal: can not move directory into itself, source=tests/fixtures/__init__.py, destination=tests/fixtures/__init__.py


## Next Steps
1. Review and complete file merges
2. Run tests to ensure nothing is broken
3. Update documentation
4. Clean up any remaining empty directories
