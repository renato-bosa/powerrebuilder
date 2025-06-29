# Data Directory Reorganization Report

## Summary
Reorganized input/output data structure to eliminate duplication and improve clarity.

## Previous Structure (Problematic)
```
input/
├── pbd_files/*.pbd          # Source PBD files
├── test_single/*.pbd        # Test files
└── input_single/            # More test files

output/
├── extracted/pbd_files/     # Extracted content (not PBD files)
├── test_extract/            # Test outputs
├── test_wizard/             # More test outputs
├── decompiled/              # Decompiled source
├── model/                   # Model representations
├── parsed/                  # Parsed ASTs
└── logs/                    # Processing logs
```

### Issues:
- Confusing naming (extracted/pbd_files/ didn't contain PBD files)
- Multiple test directories with unclear purposes
- No clear separation between production and test data

## New Structure (Implemented)
```
data/
├── input/
│   └── pbd_files/          # All source PBD files (54 files, ~50MB)
├── output/
│   └── current/            # Current processing results
└── test_data/
    └── fixtures/           # Test fixture files
```

## Migration Actions

### 1. Created New Directory Structure
```bash
mkdir -p data/input/pbd_files
mkdir -p data/output/current  
mkdir -p data/test_data/fixtures
```

### 2. Migrated Files
- Copied 54 PBD files from `input/pbd_files/` to `data/input/pbd_files/`
- Copied test PBD from `input/test_single/` to `data/test_data/fixtures/`

### 3. Updated .gitignore
Added `data/output/current/` to ignore processing outputs while keeping input files and test fixtures in version control.

### 4. Created Migration Tools
- `data/README.md` - Documents the new structure
- `tools/migrate_data_paths.py` - Script to update path references in code

## Next Steps

1. **Run Migration Script**
   ```bash
   python tools/migrate_data_paths.py
   ```

2. **Update Configuration Files**
   - Check for hardcoded paths in JSON/YAML configs
   - Update any pipeline configuration

3. **Clean Up Old Directories**
   After verifying everything works:
   ```bash
   rm -rf input/
   rm -rf output/
   ```

4. **Update Documentation**
   - Update README files that reference old paths
   - Update any user guides or developer documentation

## Benefits
- ✅ Clear separation of input/output/test data
- ✅ No more confusing directory names
- ✅ Easier to understand data flow
- ✅ Better .gitignore management
- ✅ Consistent structure for future development