# SIME Finch Quick Reference

## Installation

```bash
pip install -r requirements.txt
```

## Basic Usage

### Convert a Single File

```python
from common.pipeline_coordinator import PipelineCoordinator

pipeline = PipelineCoordinator("input/", "output/")
result = pipeline.process_file("window.srw", "output/")
```

### Convert a Project

```python
result = pipeline.process_directory("pb_project/")
```

### Command Line

```bash
python main.py convert --input pb_project/ --output flutter_app/
```

## Common Tasks

### Extract PBL Files

```python
from extract.extract_coordinator import extract_pbls
files = extract_pbls(["app.pbl"], "extracted/")
```

### Parse PowerBuilder Code

```python
from parse.parse_coordinator import PowerBuilderParser
parser = PowerBuilderParser()
ast = parser.parse("global function integer test()\nreturn 1\nend function")
```

### Generate Flutter Code

```python
from generate.flutter import FlutterGenerator
gen = FlutterGenerator("templates/", "output/")
gen.generate_screen(window_ast)
```

## Object Types

| PowerBuilder | Flutter/Dart |
|--------------|--------------|
| Window | Screen (StatefulWidget) |
| UserObject | Widget |
| DataWindow | DataTable + Model |
| Menu | AppBar/Drawer |
| Function | Method |
| Structure | Model Class |
| Application | MaterialApp |

## Type Mappings

| PowerBuilder | Dart |
|--------------|------|
| integer | int |
| long | int |
| decimal | double |
| string | String |
| boolean | bool |
| date | DateTime |
| time | DateTime |
| blob | Uint8List |
| char | String |
| any | dynamic |

## File Extensions

- `.srw` - Window
- `.sru` - User Object
- `.srf` - Function
- `.srs` - Structure
- `.srm` - Menu
- `.sra` - Application
- `.srd` - DataWindow
- `.pbl` - PowerBuilder Library
- `.pbd` - PowerBuilder Dynamic Library

## Error Recovery

Enable recovery for corrupted files:

```python
from extract.extract_coordinator import extract_with_recovery

result = extract_with_recovery(
    "corrupted.pbl",
    "recovered/",
    recovery_options={'aggressive': True}
)
```

## Debugging

### Enable Verbose Logging

```python
from common.logging_config import configure_pipeline_logging
configure_pipeline_logging(verbose=True, log_file="debug.log")
```

### Check Parse Errors

```python
try:
    ast = parser.parse_file("file.srw")
except ParseError as e:
    print(f"Line {e.line}, Column {e.column}: {e.message}")
```

## Performance

### Enable Parallel Processing

```python
pipeline = PipelineCoordinator(
    "input/", "output/",
    options={'parallel_processing': True, 'max_workers': 4}
)
```

### Run Benchmarks

```bash
python benchmarks/run_benchmarks.py
```

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Module Tests

```bash
pytest tests/test_extract/
pytest tests/test_parse/
pytest tests/test_generate/
```

### Check Coverage

```bash
pytest --cov=. --cov-report=html
```

## Common Issues

### ImportError

Add project root to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Type Checking

Run mypy with gradual typing:
```bash
mypy . --config-file=mypy.ini
```

### Memory Issues

For large projects, increase memory:
```python
pipeline = PipelineCoordinator(
    "input/", "output/",
    options={'batch_size': 10, 'memory_limit': '4GB'}
)
```