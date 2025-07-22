# PowerRebuilder Tools Directory

This directory contains development tools, analysis scripts, and maintenance utilities for the PowerRebuilder project.

## Directory Structure

### 📊 `/analysis/`
Scripts for analyzing codebase health, extraction results, and project metrics.

**Key scripts:**
- `project_status_report.py` - Generate comprehensive project status
- `code_quality_check.py` - Check code quality metrics
- `analyze_extraction_results.py` - Analyze PBD extraction outcomes
- `get_test_stats.py` - Get test suite statistics
- `learn_from_extracted.py` - Learn patterns from extracted code

### 🐛 `/debug/`
Debugging tools for troubleshooting P-code extraction and decompilation issues.

**Key scripts:**
- `pcode_extractor.py` - Extract and analyze P-code from PBD files
- `pbd_analyzer.py` - Deep analysis of PBD file structure
- `debug_pcode_pipeline.py` - Debug the P-code processing pipeline
- `analyze_fun_file.py` - Analyze .fun file contents
- `final_decoder_summary.py` - Summary of decoder implementation

### 🔧 `/maintenance/`
Maintenance scripts for project cleanup, organization, and development setup.

**Key scripts:**
- `consolidate_project.py` - Project-wide file consolidation
- `organize_test_files.py` - Organize test files into subdirectories
- `cleanup_project.py` - Clean up temporary and generated files
- `setup_dev.sh` - Development environment setup
- `dev-tools.py` - Interactive development tools menu

### 🔄 `/migration/`
Scripts for code migration and import fixes.

**Key scripts:**
- `fix_imports.py` - Fix import statements after reorganization
- `fix_base_imports.py` - Fix base module imports

### 🎯 `/opcodes/`
Tools for PowerBuilder opcode discovery, extraction, and validation.

**Subdirectories:**
- `discovery/` - Opcode discovery pipeline
- `extraction/` - Extract opcodes from various sources
- `generation/` - Generate opcode reference files
- `validation/` - Validate opcode implementations

### 🚀 `/pipeline/`
Scripts for testing and running the complete PowerRebuilder pipeline.

**Key scripts:**
- `test_comprehensive_pipeline.py` - Run comprehensive pipeline tests
- `root_test_full_pipeline.py` - Test full pipeline from root
- `test_pcode_detection_logic.py` - Test P-code detection

### ✅ `/verification/`
Scripts for verifying extraction and conversion correctness.

**Key scripts:**
- `verify_extraction_issue.py` - Verify specific extraction issues
- `check_multiple_nodes.py` - Check for multiple node issues

## Usage Examples

### Running Analysis
```bash
# Generate project status report
python tools/analysis/project_status_report.py

# Check code quality
python tools/analysis/code_quality_check.py

# Get test statistics
python tools/analysis/get_test_stats.py
```

### Debugging Issues
```bash
# Analyze a PBD file
python tools/debug/pbd_analyzer.py path/to/file.pbd

# Extract P-code for analysis
python tools/debug/pcode_extractor.py path/to/file.pbd

# Debug the pipeline
python tools/debug/debug_pcode_pipeline.py
```

### Maintenance Tasks
```bash
# Run project consolidation
python tools/maintenance/consolidate_project.py --phase 1

# Clean up project
python tools/maintenance/cleanup_project.py

# Set up development environment
./tools/maintenance/setup_dev.sh
```

### Pipeline Testing
```bash
# Run comprehensive pipeline test
python tools/pipeline/test_comprehensive_pipeline.py

# Test P-code detection
python tools/pipeline/test_pcode_detection_logic.py
```

## Adding New Tools

When adding new tools:
1. Place in the appropriate subdirectory based on purpose
2. Include a module docstring explaining the tool's purpose
3. Add command-line argument parsing for usability
4. Update this README with the new tool

## Tool Guidelines

- Tools should be self-contained and runnable from any directory
- Use absolute paths or make paths relative to project root
- Include `--help` output for all scripts
- Add appropriate error handling and user feedback
- Consider adding dry-run options for destructive operations
