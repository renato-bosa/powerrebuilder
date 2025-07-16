# API Reference

## CLI Commands

### Main Command
```bash
python main.py [OPTIONS] COMMAND [ARGS]...
```

**Options:**
- `--loglevel [DEBUG|INFO|WARNING|ERROR|CRITICAL]`: Set logging level (default: INFO)
- `--traceback/--no-traceback`: Show full traceback on error (default: false)
- `--version`: Show version

### Extract Commands

#### extract files
Extract PowerBuilder source and P-code from PBL/PBD files.

```bash
python main.py extract files [OPTIONS] [INPUT_DIR] [OUTPUT_DIR]
```

**Arguments:**
- `INPUT_DIR`: Directory containing PBL/PBD files (default: input)
- `OUTPUT_DIR`: Directory to write extracted files (default: data/output/current/extracted)

**Options:**
- `--debug`: Enable debug logging
- `--enable-byte-recovery`: Enable byte-level recovery for corrupted files
- `--unicode`: Use unicode mode for extraction

#### extract to-text
Convert PowerBuilder binary files to readable text format.

```bash
python main.py extract to-text [OPTIONS] INPUT_FILE
```

**Options:**
- `-o, --output PATH`: Output text file path
- `-s, --stdout`: Also print to stdout

#### extract inspect
Inspect PBD file structure.

```bash
python main.py extract inspect [FILES]...
```

#### extract hexdump
View hexdump of PowerBuilder files.

```bash
python main.py extract hexdump [FILES]...
```

### Parse Command
Parse PowerBuilder source files into Abstract Syntax Trees.

```bash
python main.py parse [INPUT_DIR] [OUTPUT_DIR]
```

**Arguments:**
- `INPUT_DIR`: Directory with extracted PB source files (default: data/output/current/extracted)
- `OUTPUT_DIR`: Directory for parsed AST data (default: data/output/current/parsed)

### Decompile Command
Decompile PowerBuilder P-code files to high-level pseudocode.

```bash
python main.py decompile [INPUT_DIR] [OUTPUT_DIR]
```

**Arguments:**
- `INPUT_DIR`: Directory with extracted P-code files (default: data/output/current/extracted)
- `OUTPUT_DIR`: Directory for decompiled code (default: data/output/current/decompiled)

### Generate Command
Generate modern application code from parsed and decompiled data.

```bash
python main.py generate [OPTIONS]
```

**Options:**
- `--parsed-dir PATH`: Directory containing parsed AST files
- `--decompiled-dir PATH`: Directory containing decompiled functions

### Schema Command
Extract and document database schema from PowerBuilder code.

```bash
python main.py schema [OPTIONS]
```

**Options:**
- `--project-dir PATH`: PowerBuilder project directory (default: .)
- `-o, --output-dir PATH`: Output directory for schema documentation
- `-f, --format [markdown|html|json]`: Output format (default: markdown)
- `--include-flows/--no-flows`: Include data flow analysis

### All Command
Run the full pipeline: extract, parse, decompile, generate.

```bash
python main.py all [OPTIONS]
```

**Options:**
- `--pbl-input-dir PATH`: Input directory with PBL/PBD files
- `--base-output-dir PATH`: Base directory for all output
- `--debug`: Enable debug logging
- `--enable-byte-recovery`: Enable byte-level recovery

### Performance Commands

#### extract-streaming
Extract PBD files using streaming for better memory efficiency.

```bash
python main.py extract-streaming [OPTIONS] INPUT_PATH OUTPUT_PATH
```

**Options:**
- `--streaming/--no-streaming`: Use streaming extraction (default: enabled)
- `--async/--sync`: Use async extraction
- `--chunk-size INT`: Chunk size for streaming (default: 8192)

#### all-parallel
Run full pipeline with performance optimizations.

```bash
python main.py all-parallel [OPTIONS] INPUT_PATH OUTPUT_PATH
```

**Options:**
- `--target [flutter|python|typescript]`: Target language (default: flutter)
- `--parallel/--sequential`: Run stages in parallel (default: enabled)
- `--async/--sync`: Use async pipeline
- `--cache/--no-cache`: Enable AST caching (default: enabled)
- `--streaming/--no-streaming`: Use streaming (default: enabled)

### Utility Commands

#### clean-output
Clean specific output directories.

```bash
python main.py clean-output [OPTIONS] [TARGET_DIR]
```

**Options:**
- `--force`: Actually delete files (without this, only lists)
- `--full-recovery`: Target recovery directory
- `--full-extracted`: Target extracted directory
- `--full-decompiled`: Target decompiled directory
- `--full-parsed`: Target parsed directory
- `--test-outputs`: Clean all test_* directories

#### cache-stats
Display cache statistics.

```bash
python main.py cache-stats [OPTIONS]
```

**Options:**
- `--size INT`: Maximum cache entries (default: 1000)
- `--memory INT`: Maximum cache memory in MB (default: 512)

## Python API

### Extract Module

```python
from src.extract.coordinator import extract_pbls
from src.extract.pbd.extractors.base import extract_pbl

# Extract multiple PBL files
results = extract_pbls(
    input_dir="path/to/pbls",
    output_dir="path/to/output",
    enable_byte_recovery=True
)

# Extract single PBL file
extract_pbl(
    pbl_path="path/to/file.pbl",
    output_dir="path/to/output",
    show_progress=True,
    extract_resources=True
)
```

### Parse Module

```python
from src.parse.coordinator import parse_powerbuilder_directory
from src.parse.parser.powerbuilder import PowerBuilderParser

# Parse directory of source files
parsed_data = parse_powerbuilder_directory(
    input_path="path/to/sources",
    output_path="path/to/output"
)

# Parse single file
parser = PowerBuilderParser()
ast = parser.parse_file("path/to/file.srw")
```

### Decompile Module

```python
from src.decompile.coordinator import decompile_directory
from src.decompile.pcode.decoder import PCodeDecoder

# Decompile directory
decompile_directory(
    input_dir="path/to/pcode",
    output_dir="path/to/output"
)

# Decompile single file
decoder = PCodeDecoder()
result = decoder.decode_file("path/to/file.fun")
```

### Generate Module

```python
from src.generate.coordinator import (
    generate_models,
    generate_services,
    generate_flutter
)

# Generate database models
generate_models("path/to/parsed")

# Generate service layer
generate_services("path/to/parsed", "path/to/decompiled")

# Generate Flutter UI
generate_flutter("path/to/parsed")
```

### Pipeline Module

```python
from src.common.pipeline.pipeline_coordinator import PipelineCoordinator

# Create pipeline coordinator
coordinator = PipelineCoordinator(
    input_dir="path/to/input",
    output_dir="path/to/output",
    config={
        'target': 'flutter',
        'parallel': True,
        'cache': True,
        'streaming': True
    }
)

# Run pipeline
results = coordinator.run()

# Get summary
summary = coordinator.get_summary()
```

## Configuration

### Environment Variables

- `PB_PARSER_ERROR_RECOVERY`: Enable parser error recovery (true/false)
- `PB_PARSER_TYPE`: Parser type (earley/lalr)
- `PB_PARSER_MAX_ERRORS`: Maximum parser errors to collect

### Resource Limits

```python
from src.common.limits import ResourceLimits, ResourceMonitor

# Configure limits
limits = ResourceLimits(
    max_file_size=100 * 1024 * 1024,  # 100MB
    max_memory_usage=2 * 1024 * 1024 * 1024,  # 2GB
    max_files_open=100,
    max_extraction_time=3600  # 1 hour
)

# Monitor resource usage
with ResourceMonitor(limits) as monitor:
    # Your processing code here
    pass
```

### Security Configuration

```python
from src.common.security import SecurityConfig

config = SecurityConfig(
    validate_paths=True,
    sanitize_filenames=True,
    max_path_depth=10,
    allowed_extensions=['.pbl', '.pbd', '.srw', '.sru']
)
```

## Error Handling

All modules use consistent error types:

```python
from src.common.exceptions import (
    ExtractError,
    ParseError,
    DecompileError,
    GenerateError,
    PipelineError
)

try:
    # Your code here
    pass
except ExtractError as e:
    # Handle extraction errors
    pass
except ParseError as e:
    # Handle parsing errors
    pass
```

## Progress Tracking

```python
from src.common.pipeline.progress import PipelineProgress

# Create progress tracker
progress = PipelineProgress(total_steps=5)

# Track progress
progress.start_step("Extracting files", 1)
# ... do work ...
progress.complete_step(1)

# Get progress info
current = progress.get_current_progress()
print(f"Progress: {current['percentage']}%")
```