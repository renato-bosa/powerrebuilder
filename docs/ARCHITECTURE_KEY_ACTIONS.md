# PowerRebuilder Architecture - Key Actions Required

## 1. Fix Circular Dependency Between Parse and Model

**Issue**: Circular imports found:
- `src/parse/library.py:19` imports `from src.model.ast.serialization`
- `src/model/coordinator.py:26` imports `from src.parse.ast_to_model`

**Solution Options**:

### Option A: Move AST to Common Module (Recommended)
```bash
# Create new AST module in common
mkdir -p src/common/ast
mv src/model/ast/* src/common/ast/

# Update imports
find src -name "*.py" -exec sed -i '' 's/from src\.model\.ast/from src.common.ast/g' {} \;
find src -name "*.py" -exec sed -i '' 's/import src\.model\.ast/import src.common.ast/g' {} \;
```

### Option B: Move ast_to_model to Model Module
```bash
# Move the file
mv src/parse/ast_to_model.py src/model/transformers/

# Update imports
find src -name "*.py" -exec sed -i '' 's/from src\.parse\.ast_to_model/from src.model.transformers.ast_to_model/g' {} \;
```

## 2. Clean Up Unused Imports

**Issue**: 217 unused imports, especially STRING_TABLE_OFFSET imported in 30+ files

**Action**:
```bash
# Remove all unused imports automatically
ruff check --select F401 --fix src/

# Remove blank lines with whitespace
ruff check --select W293 --fix src/
```

## 3. Remove Dead Code

**Issue**: Vulture found numerous unused variables and unreachable code

**Key Areas**:
- `src/parse/visitors/transformer.py` - 100+ unused variables
- `src/extract/pbd/structures/node.py:562` - unreachable code after return
- `src/extract/utils/version.py:216` - unreachable code after if

**Action**:
```bash
# Generate detailed dead code report
vulture src/ --min-confidence 90 > dead_code_report.txt

# Review and remove confirmed dead code
# (Manual review required to avoid removing intentionally unused code)
```

## 4. Reorganize Project Structure

**Current Issues**:
- Test files in root directory
- Configuration files mixed with code
- Old modules in archive still imported

**Action**:
```bash
# Move test files
mv test_*.py tests/
mv diagnose_*.py tools/debug/
mv debug_*.py tools/debug/
mv analyze_*.py tools/analysis/
mv trace_*.py tools/debug/
mv verify_*.py tools/verification/
mv check_*.py tools/verification/
mv find_*.py tools/analysis/

# Move config files
mkdir -p config
mv .importlinter config/importlinter.ini

# Clean up archive references
find src -name "*.py" -exec grep -l "from archive\." {} \; | xargs rm -f
```

## 5. Implement Clean Architecture

### Create Contract Interfaces
```python
# src/contracts/pipeline.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class PipelineStage(ABC):
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        pass
```

### Update Each Module to Use Contracts
```python
# src/extract/coordinator.py
from src.contracts.pipeline import PipelineStage

class ExtractCoordinator(PipelineStage):
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
        pass
```

## 6. Fix Test Suite

**Current State**: ~45% passing (90 out of 200 tests)

**Key Issues**:
1. Missing test fixtures
2. Hardcoded paths
3. Integration tests need real PBD files

**Actions**:
```bash
# Create proper test fixtures
mkdir -p tests/fixtures/sample_pbd_files
mkdir -p tests/fixtures/expected_outputs

# Fix import paths in tests
find tests -name "*.py" -exec sed -i '' 's/from model\./from src.model./g' {} \;
find tests -name "*.py" -exec sed -i '' 's/from parse\./from src.parse./g' {} \;

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html
```

## 7. Implement P-code Detection Fix

**Issue**: P-code detection only finding 10 bytes due to complex file structure

**Action**: Implement proper PowerBuilder object file format parser
```python
# src/extract/pbd/formats/object_format.py
class PowerBuilderObjectFormat:
    """Parser for PowerBuilder object file format"""
    
    def parse_header(self, data: bytes) -> ObjectHeader:
        # Parse object header structure
        pass
    
    def find_code_sections(self, data: bytes) -> List[CodeSection]:
        # Find all P-code sections in object
        pass
    
    def extract_metadata(self, data: bytes) -> ObjectMetadata:
        # Extract strings, resources, etc.
        pass
```

## Implementation Priority

1. **Immediate** (Day 1):
   - Fix circular dependency (#1)
   - Clean up unused imports (#2)
   - Move test files to proper locations (#4)

2. **Short-term** (Week 1):
   - Remove dead code (#3)
   - Implement contract interfaces (#5)
   - Fix failing tests (#6)

3. **Medium-term** (Week 2-3):
   - Complete project reorganization (#4)
   - Implement P-code detection fix (#7)
   - Add comprehensive integration tests

## Monitoring Progress

Track progress with these metrics:
- Import health: `ruff check --select F,W src/ | wc -l`
- Test coverage: `pytest --cov=src --cov-report=term-missing`
- Circular dependencies: `lint-imports` (after fixing config)
- Dead code: `vulture src/ --min-confidence 90 | wc -l`

## Expected Outcomes

After implementing these changes:
- No circular dependencies
- Clean module boundaries
- 80%+ test coverage
- Proper P-code extraction
- Maintainable architecture ready for scaling