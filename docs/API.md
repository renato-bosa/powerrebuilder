# SIME Finch API Documentation

This document provides comprehensive API documentation for all public interfaces in the SIME Finch PowerBuilder reverse engineering system.

## Table of Contents

1. [Pipeline Coordinator](#pipeline-coordinator)
2. [Extraction API](#extraction-api)
3. [Parsing API](#parsing-api)
4. [Code Generation API](#code-generation-api)
5. [Model Classes](#model-classes)
6. [Utility Functions](#utility-functions)

## Pipeline Coordinator

### Class: `PipelineCoordinator`

Main entry point for PowerBuilder to Flutter conversion.

```python
from common.pipeline_coordinator import PipelineCoordinator

coordinator = PipelineCoordinator(
    input_dir="path/to/pb/files",
    output_dir="path/to/output"
)
```

#### Methods

##### `process_directory(directory: str) -> dict`

Process all PowerBuilder files in a directory.

**Parameters:**
- `directory` (str): Path to directory containing PowerBuilder files

**Returns:**
- `dict`: Result dictionary with keys:
  - `status` (str): 'success', 'partial_success', or 'failed'
  - `stages` (dict): Results from each pipeline stage
  - `statistics` (dict): Conversion statistics
  - `errors` (list): List of errors encountered

**Example:**
```python
result = coordinator.process_directory("/path/to/pb/project")
if result['status'] == 'success':
    print(f"Converted {result['statistics']['total_files']} files")
```

##### `process_file(file_path: str, output_dir: str) -> dict`

Process a single PowerBuilder file.

**Parameters:**
- `file_path` (str): Path to PowerBuilder file
- `output_dir` (str): Output directory for generated files

**Returns:**
- `dict`: Processing result

## Extraction API

### Function: `extract_pbls`

Extract PowerBuilder library files.

```python
from extract.extract_coordinator import extract_pbls

extracted_files = extract_pbls(
    pbl_files=["app.pbl", "windows.pbl"],
    output_dir="extracted/"
)
```

**Parameters:**
- `pbl_files` (list[str]): List of PBL/PBD file paths
- `output_dir` (str): Output directory
- `show_progress` (bool): Show progress bar (default: True)
- `enable_recovery` (bool): Enable corrupted file recovery (default: True)

**Returns:**
- `list[str]`: List of extracted file paths

### Function: `extract_with_recovery`

Extract with enhanced error recovery.

```python
from extract.extract_coordinator import extract_with_recovery

result = extract_with_recovery(
    file_path="corrupted.pbl",
    output_dir="recovered/",
    recovery_options={
        'aggressive': True,
        'reconstruct_headers': True
    }
)
```

## Parsing API

### Class: `PowerBuilderParser`

Parse PowerBuilder source code to AST.

```python
from parse.parse_coordinator import PowerBuilderParser

parser = PowerBuilderParser()
ast = parser.parse_file("window.srw")
```

#### Methods

##### `parse_file(file_path: str) -> ParseResult`

Parse a PowerBuilder source file.

**Parameters:**
- `file_path` (str): Path to source file

**Returns:**
- `ParseResult`: Object containing:
  - `ast`: Abstract syntax tree
  - `object_type`: Type of PowerBuilder object
  - `metadata`: Additional parsing metadata

##### `parse(source_code: str, object_type: str = None) -> ParseResult`

Parse PowerBuilder source code string.

**Parameters:**
- `source_code` (str): PowerBuilder source code
- `object_type` (str): Optional object type hint

### Class: `DataWindowParser`

Specialized parser for DataWindow syntax.

```python
from parse.parse_coordinator import DataWindowParser

dw_parser = DataWindowParser()
dw_definition = dw_parser.parse_datawindow(dw_syntax)
```

## Code Generation API

### Class: `FlutterGenerator`

Generate Flutter code from PowerBuilder AST.

```python
from generate.flutter import FlutterGenerator

generator = FlutterGenerator(
    template_dir="templates/",
    output_dir="flutter_app/"
)
```

#### Methods

##### `generate_screen(window_ast: Window) -> str`

Generate Flutter screen from window AST.

**Parameters:**
- `window_ast` (Window): Window AST node

**Returns:**
- `str`: Path to generated screen file

##### `generate_widget(user_object_ast: UserObject) -> str`

Generate Flutter widget from user object.

##### `generate_model(structure_ast: Structure) -> str`

Generate Dart model class from structure.

### Class: `ModelGenerator`

Generate backend models and services.

```python
from generate.generate_coordinator import ModelGenerator

model_gen = ModelGenerator(
    template_dir="templates/backend/",
    output_dir="backend/"
)
```

## Model Classes

### Window

Represents a PowerBuilder window.

```python
from model.ast import Window

window = Window(
    name="w_main",
    title="Main Window",
    width=800,
    height=600,
    controls=[],
    events=[],
    methods=[]
)
```

**Attributes:**
- `name` (str): Window name
- `title` (str): Window title
- `width` (int): Width in pixels
- `height` (int): Height in pixels
- `controls` (list[Control]): Child controls
- `events` (list[Event]): Event handlers
- `methods` (list[Function]): Window methods

### DataWindow

Represents a PowerBuilder DataWindow.

```python
from model.pb_datawindow import DataWindow

dw = DataWindow(
    name="d_employee",
    columns=[],
    sql="SELECT * FROM employee",
    presentation_style="grid"
)
```

**Attributes:**
- `name` (str): DataWindow name
- `columns` (list[DataWindowColumn]): Column definitions
- `sql` (str): SQL SELECT statement
- `presentation_style` (str): Display style

### Function

Represents a function or method.

```python
from model.ast import Function

func = Function(
    name="calculate",
    return_type=Type("integer"),
    parameters=[],
    body=Block([])
)
```

## Utility Functions

### Type Conversion

```python
from generate.converters.type_converter import TypeConverter

converter = TypeConverter()
dart_type = converter.convert_type("integer")  # Returns "int"
```

### Expression Conversion

```python
from generate.converters.expression_converter import ExpressionConverter

expr_converter = ExpressionConverter()
dart_expr = expr_converter.convert_expression("a + b * 2")
```

### Progress Tracking

```python
from common.progress import ProgressTracker

tracker = ProgressTracker()
tracker.start_task("extraction", "Extracting files", total=100)
tracker.update_task("extraction", advance=10)
tracker.complete_task("extraction")
```

## Error Handling

All API functions may raise the following exceptions:

- `ExtractError`: Extraction failures
- `ParseError`: Parsing failures
- `GenerateError`: Code generation failures
- `PipelineError`: General pipeline failures

Example error handling:

```python
from extract.exceptions import ExtractError
from parse.exceptions import ParseError

try:
    result = coordinator.process_file("app.pbl")
except ExtractError as e:
    print(f"Extraction failed: {e}")
except ParseError as e:
    print(f"Parsing failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Configuration

### Logging

```python
from common.logging_config import configure_pipeline_logging

configure_pipeline_logging(
    verbose=True,
    log_file="conversion.log",
    max_message_length=500
)
```

### Pipeline Options

```python
coordinator = PipelineCoordinator(
    input_dir="input/",
    output_dir="output/",
    options={
        'strict_parsing': False,
        'enable_recovery': True,
        'parallel_processing': True,
        'max_workers': 4
    }
)
```

## Examples

### Complete Conversion Example

```python
from common.pipeline_coordinator import PipelineCoordinator
from common.logging_config import configure_pipeline_logging

# Configure logging
configure_pipeline_logging(verbose=True)

# Create pipeline
pipeline = PipelineCoordinator(
    input_dir="powerbuilder_project/",
    output_dir="flutter_output/"
)

# Run conversion
result = pipeline.process_directory("powerbuilder_project/")

# Check results
if result['status'] == 'success':
    print("Conversion successful!")
    print(f"Files converted: {result['statistics']['total_files']}")
    print(f"Output directory: flutter_output/")
else:
    print("Conversion failed or partially failed")
    for error in result.get('errors', []):
        print(f"Error: {error}")
```

### Custom Processing Example

```python
from extract.extract_coordinator import extract_pbls
from parse.parse_coordinator import PowerBuilderParser
from generate.flutter import FlutterGenerator

# Step 1: Extract
files = extract_pbls(["app.pbl"], "temp/")

# Step 2: Parse
parser = PowerBuilderParser()
asts = {}
for file in files:
    result = parser.parse_file(file)
    asts[file] = result.ast

# Step 3: Generate
generator = FlutterGenerator("templates/", "output/")
for file, ast in asts.items():
    if ast.object_type == "window":
        generator.generate_screen(ast)
    elif ast.object_type == "datawindow":
        generator.generate_datawindow_widget(ast)
```

## Version Information

- API Version: 1.0.0
- PowerBuilder Support: 6.x - 12.5
- Flutter Support: 3.x
- Dart SDK: 3.x

## Support

For issues or questions:
- GitHub Issues: https://github.com/sime-finch/issues
- Documentation: https://sime-finch.readthedocs.io