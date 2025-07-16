# Pipeline Sequential Execution Update

## Summary of Changes

The PowerRebuilder pipeline has been successfully updated to run stages sequentially instead of in parallel. The pipeline now follows this order:

1. **Extract** → Produces .fun files from PBL/PBD archives
2. **Decompile** → Converts .fun files to .sru source files  
3. **Parse** → Processes .sru files into Abstract Syntax Trees (ASTs)
4. **Model** → Converts ASTs into structured model objects (NEW STAGE)
5. **Generate** → Produces Python/Dart code from model objects

## Files Modified

### 1. `/src/common/pipeline/pipeline_coordinator.py`
- Updated module docstring to reflect sequential execution
- Modified stage directories to follow sequential flow
- Added `model_dir` for the new Model stage
- Updated `_init_stages()` to:
  - Set decompiler input to extracted directory
  - Set parser input to decompiled directory
  - Added ModelCoordinator initialization
  - Set modeler input to parsed directory
  - Set generator input to model directory
- Reordered stage execution in `process_files()`:
  - Extract → Decompile → Parse → Model → Generate
- Added `_run_model_stage()` method
- Added `_save_model_summary()` and `_load_model_summary()` methods
- Updated `_run_parse_stage()` to read from decompiled directory
- Updated `_run_decompile_stage()` to output .sru files
- Updated `_run_generate_stage()` to read from model summary
- Updated checkpoint recovery to include model stage
- Removed `run_parallel_stages()` method

### 2. `/main.py`
- Updated 'all' command docstring to reflect sequential execution
- Replaced manual pipeline execution with PipelineCoordinator usage
- Added configuration for all pipeline stages including model
- Simplified error handling and results display
- Removed ~150 lines of manual pipeline code

### 3. `/src/generate/coordinator.py`
- Added `generate_from_model()` method to GenerateCoordinator
- Added `generate_screen_from_model()` method to FlutterGenerator
- Added `_generate_simple_layout()` helper method

## Key Benefits

1. **Sequential Data Flow**: Each stage now properly feeds into the next
   - Decompiler reads .fun files and produces .sru files
   - Parser reads .sru files and produces AST JSON
   - Model stage converts ASTs to structured models
   - Generator reads models to produce final code

2. **Model Stage Addition**: New intermediate stage between Parse and Generate
   - Provides better abstraction and separation of concerns
   - Enables more sophisticated code generation
   - Makes the pipeline more maintainable

3. **Simplified Execution**: The 'all' command now uses PipelineCoordinator
   - Cleaner code with better error handling
   - Checkpoint/recovery support built-in
   - Consistent progress tracking

4. **Better Error Recovery**: Sequential execution makes debugging easier
   - Clear stage boundaries
   - Each stage output can be inspected
   - Checkpoint system tracks progress through stages

## Configuration Updates

The pipeline now accepts configuration for all stages:

```python
config = {
    'extract': {
        'preserve_structure': True,
        'extract_resources': True,
        'enable_byte_recovery': enable_byte_recovery,
    },
    'decompile': {
        'debug_mode': debug,
    },
    'parse': {
        'strict_mode': False,
        'resolve_imports': True,
    },
    'model': {},  # Model stage configuration
    'generate': {
        'target_framework': 'flutter',
        'null_safety': True,
        'generate_tests': False,
    },
    'cleanup_temp': False,
    'auto_recover_checkpoint': True,
}
```

## Usage

The pipeline is now used through the PipelineCoordinator:

```bash
# Run the full sequential pipeline
python main.py all

# Or with specific input/output directories
python main.py all --pbl-input-dir /path/to/pbls --base-output-dir /path/to/output
```

## Next Steps

1. Implement the actual ModelCoordinator class in `/src/model/coordinator.py`
2. Update tests to reflect sequential execution
3. Add integration tests for the complete pipeline
4. Document the Model stage data structures
5. Optimize stage transitions for better performance