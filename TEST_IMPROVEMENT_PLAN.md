# Test Coverage Improvement Plan for SIME Finch

## Current State
- **Line Coverage**: 1% (Critical)
- **File Coverage**: ~51% (54/106 source files have tests)
- **Test Files**: 85 (but most aren't running due to import errors)

## Root Causes
1. **Import Errors**: Module reorganization broke most test imports
2. **Configuration Issues**: pytest.ini restricts which tests run
3. **Outdated APIs**: Tests expect old interfaces that changed
4. **Missing Dependencies**: Some modules referenced in tests don't exist

## Improvement Strategy

### Phase 1: Fix Existing Tests (Week 1)
**Goal**: Get from 1% to 30% coverage by fixing what we have

#### 1.1 Auto-fix Import Errors
```bash
# Run the automated fixer
python scripts/maintenance/fix_test_coverage.py --fix-imports

# Verify fixes
python scripts/maintenance/fix_test_coverage.py --analyze
```

#### 1.2 Update pytest Configuration
Edit `pyproject.toml`:
```toml
[tool.pytest.ini_options]
# Remove or expand testpaths to include all tests
testpaths = ["tests"]
# Remove --maxfail=1 to see all failures
addopts = "-ra --strict-markers --strict-config --cov --cov-branch --cov-report=term-missing --cov-report=html"
```

#### 1.3 Fix API Changes
Common fixes needed:
- Change `error.details` to `error.context` in error handling tests
- Update import paths for moved classes
- Fix references to removed modules

### Phase 2: Test Critical Components (Week 2)
**Goal**: Get from 30% to 60% coverage by testing core functionality

#### 2.1 Coordinator Tests (Highest Priority)
Create tests for each coordinator:
```python
# tests/test_coordinators/test_extract_coordinator.py
import pytest
from pathlib import Path
from extract.extract_coordinator import ExtractCoordinator

class TestExtractCoordinator:
    def test_extract_single_file(self, tmp_path, sample_pbd):
        coordinator = ExtractCoordinator()
        result = coordinator.extract_file(sample_pbd, tmp_path)
        assert result.success
        assert (tmp_path / "extracted").exists()
        
    def test_extract_directory(self, tmp_path, pbd_directory):
        coordinator = ExtractCoordinator()
        result = coordinator.extract_directory(pbd_directory, tmp_path)
        assert result.success
        assert result.file_count > 0
        
    def test_error_handling(self, tmp_path):
        coordinator = ExtractCoordinator()
        with pytest.raises(FileNotFoundError):
            coordinator.extract_file(Path("nonexistent.pbd"), tmp_path)
```

#### 2.2 Integration Tests
Create end-to-end tests:
```python
# tests/test_integration/test_full_pipeline.py
class TestFullPipeline:
    def test_pbd_to_web_app(self, sample_pbd, tmp_path):
        """Test complete transformation from PBD to web application."""
        # Extract
        extract_dir = tmp_path / "extracted"
        extract_result = run_extraction(sample_pbd, extract_dir)
        assert extract_result.success
        
        # Parse
        parse_dir = tmp_path / "parsed"
        parse_result = run_parsing(extract_dir, parse_dir)
        assert parse_result.success
        
        # Decompile
        decompile_dir = tmp_path / "decompiled"
        decompile_result = run_decompilation(extract_dir, decompile_dir)
        assert decompile_result.success
        
        # Generate
        generate_dir = tmp_path / "generated"
        generate_result = run_generation(parse_dir, decompile_dir, generate_dir)
        assert generate_result.success
        assert (generate_dir / "backend" / "models").exists()
        assert (generate_dir / "frontend" / "src").exists()
```

### Phase 3: Comprehensive Coverage (Week 3-4)
**Goal**: Get from 60% to 80% coverage

#### 3.1 Module-Specific Tests

**Extract Module** (Currently 36.4%):
```python
# Priority files to test:
- extract/pbd_core/library.py
- extract/pbd_core/entry.py  
- extract/pbd_core/node.py
- extract/pbd_io/scanner.py
- extract/pbd_io/pe_scanner.py
```

**Model Module** (Currently 51.9%):
```python
# Priority files to test:
- model/entities/pb_application.py
- model/entities/pb_function.py
- model/entities/pb_event.py
- model/ast/arrays.py
- model/ast/control.py
```

**Parse Module** (Currently 58.8%):
```python
# Priority files to test:
- parse/parse_coordinator.py
- parse/grammar.py
- parse/visitors/transformer.py
```

#### 3.2 Test Quality Improvements

1. **Property-based Testing** for parsers:
```python
from hypothesis import given, strategies as st

class TestParser:
    @given(st.text(alphabet=string.printable))
    def test_parser_handles_any_input(self, input_text):
        """Parser should handle any input without crashing."""
        result = parse_string(input_text)
        assert result is not None  # May fail, but shouldn't crash
```

2. **Parameterized Tests** for multiple scenarios:
```python
@pytest.mark.parametrize("file_type,expected_parser", [
    ("window.srw", WindowParser),
    ("userobject.sru", UserObjectParser),
    ("menu.srm", MenuParser),
])
def test_file_type_detection(file_type, expected_parser):
    parser = get_parser_for_file(file_type)
    assert isinstance(parser, expected_parser)
```

3. **Fixture Improvements**:
```python
# tests/conftest.py
@pytest.fixture(scope="session")
def sample_files():
    """Provide various sample PowerBuilder files."""
    return {
        "window": Path("tests/fixtures/sample_window.srw"),
        "datawindow": Path("tests/fixtures/sample_datawindow.dwo"),
        "pbd": Path("tests/fixtures/sample.pbd"),
    }
```

### Phase 4: Continuous Improvement
**Goal**: Maintain 80%+ coverage

#### 4.1 CI/CD Integration
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[test]"
      - run: pytest --cov --cov-fail-under=80
      - uses: codecov/codecov-action@v3
```

#### 4.2 Test Documentation
Create `tests/README.md`:
```markdown
# Testing Guide

## Running Tests
- All tests: `pytest`
- Specific module: `pytest tests/test_parse/`
- With coverage: `pytest --cov`
- Verbose: `pytest -vv`

## Writing Tests
1. One test file per source file
2. Use descriptive test names
3. Test both success and failure cases
4. Use fixtures for common setup
5. Mock external dependencies

## Coverage Goals
- New code: 90% minimum
- Overall: 80% minimum
- Critical paths: 100%
```

## Quick Start Commands

```bash
# 1. Fix all import errors automatically
python scripts/maintenance/fix_test_coverage.py --fix-imports

# 2. Run tests incrementally to find remaining issues
python scripts/maintenance/fix_test_coverage.py --run-tests

# 3. Generate coverage report
pytest --cov --cov-report=html
open htmlcov/index.html

# 4. Create test templates for missing tests
python scripts/maintenance/fix_test_coverage.py --create-templates

# 5. Run specific test file with verbose output
pytest tests/test_model/test_ast_nodes.py -vv

# 6. Run tests with failure details
pytest -vv --tb=short -x
```

## Metrics & Tracking

### Weekly Goals
- Week 1: 1% → 30% (Fix existing tests)
- Week 2: 30% → 60% (Test critical components)
- Week 3: 60% → 75% (Fill major gaps)
- Week 4: 75% → 80% (Polish and maintain)

### Success Criteria
1. All coordinators have >90% coverage
2. Integration tests pass for full pipeline
3. No untested exception handlers
4. CI enforces 80% coverage minimum

## Resources
- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Priority Order
1. Fix imports (automated)
2. Fix pytest configuration  
3. Test coordinators (5 files)
4. Add integration tests (2-3 comprehensive tests)
5. Test Extract module (increase from 36% to 70%)
6. Test Model module (increase from 52% to 70%)
7. Test remaining modules
8. Add property-based tests
9. Set up CI/CD enforcement

This plan will systematically improve test coverage from 1% to 80%+ over 4 weeks.