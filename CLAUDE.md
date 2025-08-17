# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PowerRebuilder is a Python-based reverse engineering toolkit that converts legacy PowerBuilder applications into modern web applications. It uses a **sequential five-stage pipeline** to transform PowerBuilder PBL/PBD files into Flutter, React, or Python-based applications.

## Common Development Commands

### Setup and Installation
```bash
# Install runtime dependencies (using uv package manager)
make install
# or
uv sync

# Install all dependencies including dev
make dev
# or
uv sync --dev
```

### Running the Application
```bash
# Show CLI help
python main.py --help
# or
uv run sime-finch --help

# Run complete pipeline (all stages)
python main.py all input/ output/

# Run individual stages (must be run in order)
python main.py extract input/myapp.pbl output/extracted/
python main.py decompile output/extracted/ output/decompiled/
python main.py parse output/decompiled/ output/parsed/
python main.py model output/parsed/ output/models/
python main.py generate output/models/ output/generated/
```

### Testing
```bash
# Run all tests
make test
# or
uv run pytest

# Run specific test module
uv run pytest tests/unit/extract/

# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test categories
uv run pytest -m "not slow"  # Skip slow tests
uv run pytest -m security    # Only security tests
uv run pytest -m integration # Only integration tests

# Run a single test
uv run pytest tests/unit/extract/test_extract.py::test_specific_function

# Run tests in parallel
uv run pytest -n auto
```

### Code Quality
```bash
# Run linter
make lint
# or
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Format code
make format
# or
uv run ruff format .

# Type checking
make type-check
# or
uv run mypy src/

# Check for dead code
uv run vulture src/ config/vulture_whitelist.py
```

### Performance and Profiling
```bash
# Run performance benchmarks
python scripts/performance_benchmark.py

# Profile CPU usage
python scripts/profile_cpu.py

# Profile memory usage
python scripts/profile_memory.py

# Run comprehensive test suite with performance analysis
python scripts/run_comprehensive_tests.py --performance
```

## Pipeline Architecture

The PowerRebuilder pipeline processes files through **five sequential stages**:

### 1. Extract Stage
- **Input**: PowerBuilder PBL/PBD binary files
- **Output**: P-code files (`.fun` extension) containing compiled bytecode
- **Key Module**: `src/extract/`
- **Purpose**: Decompresses and extracts compiled P-code from PowerBuilder archives

### 2. Decompile Stage (MUST run before Parse)
- **Input**: P-code files (`.fun`) from Extract stage
- **Output**: PowerBuilder source files (`.sru`, `.srw`, `.srm` extensions)
- **Key Module**: `src/decompile/`
- **Purpose**: Reconstructs PowerBuilder source code from P-code bytecode
- **Critical**: Parse cannot process P-code directly - it needs the source code this stage produces

### 3. Parse Stage
- **Input**: PowerBuilder source files (`.sru`) from Decompile stage
- **Output**: Abstract Syntax Tree (AST) in JSON format
- **Key Module**: `src/parse/`
- **Purpose**: Builds structured AST representation using Lark grammar parser
- **Grammar**: Located in `src/parse/grammar/`

### 4. Model Stage
- **Input**: AST JSON from Parse stage
- **Output**: Semantic models (typed Python objects)
- **Key Module**: `src/model/`
- **Purpose**: Transforms AST into semantic models with resolved dependencies

### 5. Generate Stage
- **Input**: Semantic models from Model stage
- **Output**: Modern application code (Flutter/Dart, Python/Litestar, React/Vue)
- **Key Module**: `src/generate/`
- **Purpose**: Produces modern web applications using Jinja2 templates
- **Templates**: Located in `src/generate/templates/`

## Key Architecture Concepts

### Sequential Processing
The pipeline stages **must run in order**. Each stage depends on the output of the previous stage:
- Extract produces P-code → Decompile needs P-code
- Decompile produces source → Parse needs source
- Parse produces AST → Model needs AST
- Model produces semantic models → Generate needs models

### Performance Features
- **Streaming Processing**: Handle large files without loading entirely into memory
- **Parallel Execution**: Process multiple files concurrently within each stage
- **Circuit Breakers**: Prevent cascading failures
- **Resource Limits**: Control memory and CPU usage
- **Caching**: Cache results between runs for faster processing

### Security Features
- **Path Traversal Protection**: Validates all file paths
- **Resource Limiting**: Prevents DoS through resource exhaustion
- **Input Validation**: Sanitizes filenames and content
- **Zip Bomb Protection**: Detects malicious compression
- **Audit Logging**: Tracks security events

### Error Recovery
- **Graceful Degradation**: Continue processing other files if one fails
- **Retry Mechanisms**: Automatic retry with exponential backoff
- **Checkpoint/Resume**: Can resume processing from last checkpoint
- **Detailed Error Reporting**: Comprehensive error messages with context

## Important Implementation Notes

### P-code Detection
The decompiler uses a tiered approach to detect P-code boundaries:
1. **HighPerformancePCodeDetector**: Fast pattern matching for common cases
2. **TieredPCodeDetector**: More sophisticated detection for edge cases
3. Located in `src/decompile/pcode/`

### PowerBuilder Object Types
Common PowerBuilder object types handled:
- `.fun` - Functions (compiled P-code)
- `.dwo` - DataWindow objects
- `.udo` - User objects
- `.win` - Windows
- `.mnu` - Menus
- `.str` - Structures

### AST Node Types
Key AST nodes defined in `src/model/ast/`:
- Functions, methods, events
- Variables, parameters, properties
- Control structures (if, for, while, case)
- SQL statements (SELECT, INSERT, UPDATE, DELETE)
- UI elements (windows, controls, menus)

### Dependency Injection
The codebase previously used dependency injection but this has been removed. Direct imports are now used throughout.

### Logging Configuration
- Configured in `src/core/logging.py`
- Use `--loglevel DEBUG` for detailed debugging
- Pipeline-specific logging with structured output
- Separate loggers for each module

## Common Development Patterns

### Adding a New Opcode
1. Add opcode definition to `src/decompile/opcodes/opcodes.py`
2. Implement handler in `src/decompile/reconstruction/enhanced_reconstructor.py`
3. Add tests in `tests/unit/decompile/test_opcodes.py`

### Adding a New AST Node Type
1. Define node in appropriate file under `src/model/ast/`
2. Add visitor method in `src/model/visitors/`
3. Update parser grammar if needed in `src/parse/grammar/`
4. Add serialization support in `src/model/ast/serialization.py`

### Adding a New Code Generator
1. Create new coordinator in `src/generate/coordinators/`
2. Implement converter in `src/generate/converters/`
3. Add templates in `src/generate/templates/`
4. Register in factory in `src/generate/factory.py`

## Testing Guidelines

### Test Structure
- Unit tests: `tests/unit/` - Test individual components
- Integration tests: `tests/integration/` - Test module interactions
- Fixtures: `tests/fixtures/` - Sample PowerBuilder files
- Benchmarks: `tests/benchmarks/` - Performance tests

### Test Markers
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.security` - Security-related tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.skip_ci` - Skip in CI environment

### Running Focused Tests
```bash
# Test a specific module
uv run pytest tests/unit/decompile/ -v

# Test with specific marker
uv run pytest -m "not slow" -v

# Test with pattern matching
uv run pytest -k "test_pcode" -v
```

## Debugging Tips

### Enable Debug Logging
```bash
python main.py --loglevel DEBUG extract input/ output/
```

### Profile Performance
```bash
# CPU profiling
python -m cProfile -o profile.stats main.py all input/ output/

# Memory profiling
python scripts/profile_memory.py
```

### Inspect Intermediate Output
Each stage creates output that can be inspected:
- Extract: Check `.fun` files in hex editor
- Decompile: Review `.sru` source files
- Parse: Examine `.json` AST files
- Model: Use debugger to inspect model objects
- Generate: Review generated code files

### Common Issues
1. **"Parse failed" errors**: Usually means Decompile didn't run or failed
2. **Memory errors**: Enable streaming with `--streaming` flag
3. **Slow processing**: Use parallel processing with `--parallel --workers 8`
4. **Permission errors**: Check file permissions and path security settings

## Performance Optimization

### For Large Projects
```bash
python main.py all large_app/ output/ \
  --streaming \
  --parallel --workers 8 \
  --max-memory 1GB \
  --chunk-size 1MB
```

### Caching Between Runs
Results are cached by default. To clear cache:
```bash
python scripts/cache_manager.py --clear
```

### Resource Limits
Configure in `config.yaml`:
```yaml
security:
  resource_limits:
    max_file_size: 104857600  # 100MB
    max_memory: 2147483648    # 2GB
    max_cpu_percent: 80
```

## Key File Locations

- Main entry point: `main.py`
- Pipeline coordinators: `src/*/coordinator.py`
- Configuration: `config/`
- Documentation: `docs/`
- Tests: `tests/`
- Scripts: `scripts/`
- Grammar files: `src/parse/grammar/`
- Templates: `src/generate/templates/`