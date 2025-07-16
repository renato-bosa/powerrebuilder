# CLAUDE.md - Project State and Instructions

## Migration Status (2025-07-14)

### ✅ Completed:
1. **Directory Reorganization** - Successfully moved to src/ structure
   - Achieved ~48% file reduction (close to 50% target)
   - Preserved git history using git mv
   - Organized into clean src/ hierarchy

2. **File Consolidation** - Merged 11 files into 4 unified modules:
   - `src/extract/pbd/reader.py` - Merged file operations, PE scanning, resource utils
   - `src/extract/pbd/extractors/binary.py` - Merged string, image, and resource extractors
   - `src/parse/parser/powerbuilder.py` - Merged unified and enhanced parsers
   - `src/decompile/reconstruction/formatter.py` - Merged output and simple formatters

3. **Test Consolidation** - Achieved 90% reduction in test files:
   - From 40+ test files to 4 comprehensive test files
   - tests/test_extract.py, test_parse.py, test_decompile.py, test_generate.py

4. **Import Fixes** - Fixed all import paths for new structure
   - Main CLI (`python main.py --help`) runs successfully
   - Updated pyproject.toml and mypy.ini for new paths
   - Fixed circular import issues throughout codebase

### ✅ Additional Fixes Applied:
1. **Implemented All Missing Classes**:
   - `TypeConverter` - PowerBuilder to target language type conversion
   - `DatabaseOperationFormatter` - SQL formatting for different databases
   - `DesignSystemConverter` - UI theme conversion
   - `TemplateValidator` - Template validation logic
   - `LibraryManager` - Library management implementation
   - `TypeResolver` - Type resolution implementation
   - `SpecialOpcodeFormatter` - Special opcode formatting
   - `PBConstructorCall` and `PBMethodCall` - AST nodes for method calls

2. **Fixed Opcode Decoder**:
   - Restored actual opcode definitions from analysis
   - Fixed decoder logic for proper instruction handling
   - Implemented comprehensive opcode mapping

3. **Documentation Updated**:
   - Created comprehensive ARCHITECTURE.md
   - Updated QUICK_REFERENCE.md
   - Added BUG_REFERENCE.md
   - Created IMPLEMENTATION_SUMMARY.md

4. **Restored Missing Modules**:
   - Copied essential modules from archive back to src/
   - Fixed all import references
   - Ensured all coordinators have required dependencies

### 📊 Current Test Suite Status:
- **Total Tests**: ~200
- **Passing**: ~45% (90 tests)
- **Main Blockers**: 
  - Missing test fixtures and sample data
  - Some complex integration tests need refactoring
  - Pipeline tests require actual PowerBuilder files

### 🔧 Known Minor Issues:
1. Some integration tests require actual PowerBuilder sample files
2. A few edge cases in opcode decoding need verification
3. Some template generation tests need mock data updates

## Important Notes:
- Always use `jj` (jujutsu) for git operations
- Main entry point: `python main.py`
- All code now under `src/` directory
- Tests consolidated under `tests/`
- Use `uv` for Python dependency management

## Running the Project:

### CLI Commands:
```bash
# Run the CLI
python main.py --help

# Run specific stages in correct order:
python main.py extract <pbl_file> <output_dir>        # Extracts .fun files
python main.py decompile <pcode_dir> <output_dir>     # Converts .fun to .sru
python main.py parse <source_dir> <output_dir>        # Converts .sru to AST
python main.py model <ast_dir> <output_dir>           # Builds semantic models
python main.py generate <model_dir> <output_dir>      # Generates modern code

# Run full pipeline (runs all stages in correct order)
python main.py all <input_dir> <output_dir>
```

## Pipeline Order (CRITICAL):
The pipeline MUST run in this exact order:
1. **Extract** → produces .fun files (P-code)
2. **Decompile** → converts .fun to .sru (PowerBuilder source)
3. **Parse** → converts .sru to AST JSON
4. **Model** → converts AST to semantic models
5. **Generate** → produces Python/Dart from models

**Note**: Decompile MUST run before Parse because Parse requires PowerBuilder source code (.sru files), not P-code (.fun files).

### Running Tests:
```bash
# Run all tests
pytest tests/

# Run specific test modules
pytest tests/test_extract.py
pytest tests/test_parse.py
pytest tests/test_decompile.py
pytest tests/test_generate.py

# Run with coverage
pytest --cov=src tests/
```

### Development Setup:
```bash
# Install dependencies with uv
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"

# Run type checking
mypy src/

# Run linting
ruff check src/
```

## Project Structure:
```
powerrebuilder/
├── src/
│   ├── common/         # Shared utilities and types
│   ├── extract/        # PBL/PBD extraction
│   ├── parse/          # PowerScript parsing
│   ├── decompile/      # P-code decompilation
│   ├── model/          # AST and data models
│   └── generate/       # Code generation
├── tests/              # Test suite
├── docs/               # Documentation
├── archive/            # Old modules (for reference)
└── main.py            # CLI entry point
```