# PR #6: Re-enable Disabled Test Files

## Summary
- Fix 5 disabled test files
- Resolve missing dependencies and import errors
- Update test fixtures for new structure
- Ensure all tests can run (even if failing)

## Problem
Several test files were disabled during migration due to:
- Missing dependencies
- Import errors
- Complex dependency chains
- Outdated test fixtures

## Disabled Tests to Fix
1. `test_generate/test_python.py`
2. `test_generate/test_system_functions_template.py`
3. `test_100_percent_accuracy/test_enhanced_extraction.py`
4. Others identified during investigation

## Solution
1. Update import paths in test files
2. Create missing test fixtures
3. Mock complex dependencies where needed
4. Update test assertions for new behavior

## Implementation Details

### Fix Import Paths
```python
# Old imports
from generate.converters.python import PythonConverter

# New imports
from src.generate.converters.python import PythonConverter
```

### Add Missing Fixtures
```python
# Create test fixtures for missing classes
@pytest.fixture
def mock_library_manager():
    from src.parse.library import LibraryManager
    return LibraryManager()
```

### Mock Complex Dependencies
```python
# Mock external dependencies
@patch('src.extract.pbd.reader.PBDReader')
def test_extraction(mock_reader):
    mock_reader.return_value.read.return_value = test_data
```

## Test Plan
- [ ] Run pytest with all tests enabled
- [ ] Document which tests still fail
- [ ] Create issues for failing tests
- [ ] Ensure no import errors
- [ ] Verify test discovery works

## Estimated Time: 5 points (1 day)

## Branch: `fix/enable-disabled-tests`