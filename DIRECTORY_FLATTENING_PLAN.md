# Directory Flattening Plan for PowerRebuilder

## Executive Summary

This plan identifies opportunities to reduce directory depth and consolidate files in the PowerRebuilder codebase. The analysis found 7 target directories that can be flattened, potentially reducing directory count by 6 and improving import paths.

## Flattening Opportunities

### 1. decompile/utils/ (1 file)

**Current Structure:**
```
src/decompile/utils/
└── version.py
```

**Proposed Action:** Move `version.py` to parent directory
```
src/decompile/version.py
```

**Changes Required:**
- Move file: `src/decompile/utils/version.py` → `src/decompile/version.py`
- Update imports:
  - From: `from src.decompile.utils.version import VersionDetector`
  - To: `from src.decompile.version import VersionDetector`
- Remove empty directory: `src/decompile/utils/`

**Risk Assessment:** LOW
- Single file with minimal external dependencies
- Clear import pattern to update

### 2. parse/utils/ (2 files)

**Current Structure:**
```
src/parse/utils/
├── __init__.py
└── loader.py
```

**Proposed Action:** Move `loader.py` to parent directory
```
src/parse/loader.py  # renamed from loader.py to grammar_loader.py for clarity
```

**Changes Required:**
- Rename and move: `src/parse/utils/loader.py` → `src/parse/grammar_loader.py`
- Update imports:
  - From: `from src.parse.utils.loader import ...`
  - To: `from src.parse.grammar_loader import ...`
- Remove directory: `src/parse/utils/`

**Risk Assessment:** LOW
- Only 2 files, one is just __init__.py
- Renaming adds clarity to the file's purpose

### 3. parse/error_recovery/ (2 files)

**Current Structure:**
```
src/parse/error_recovery/
├── __init__.py
└── strategy.py
```

**Proposed Action:** Move `strategy.py` to parent directory
```
src/parse/recovery_strategy.py
```

**Changes Required:**
- Rename and move: `src/parse/error_recovery/strategy.py` → `src/parse/recovery_strategy.py`
- Update imports:
  - From: `from src.parse.error_recovery.strategy import ...`
  - To: `from src.parse.recovery_strategy import ...`
- Remove directory: `src/parse/error_recovery/`

**Risk Assessment:** LOW
- Simple structure with clear purpose
- Renamed file maintains clarity

### 4. decompile/visualization/ (2 files)

**Current Structure:**
```
src/decompile/visualization/
├── __init__.py
└── visualizer.py
```

**Proposed Action:** Move `visualizer.py` to parent directory
```
src/decompile/cfg_visualizer.py
```

**Changes Required:**
- Rename and move: `src/decompile/visualization/visualizer.py` → `src/decompile/cfg_visualizer.py`
- Update imports:
  - From: `from src.decompile.visualization.visualizer import ...`
  - To: `from src.decompile.cfg_visualizer import ...`
- Remove directory: `src/decompile/visualization/`

**Risk Assessment:** LOW
- Single functional file
- Renamed to clarify it's for Control Flow Graph visualization

### 5. generate/mappings/ (2 files)

**Current Structure:**
```
src/generate/mappings/
├── __init__.py
└── powerbuilder_flutter_mapping.json
```

**Proposed Action:** Move JSON file to parent directory
```
src/generate/powerbuilder_flutter_mapping.json
```

**Changes Required:**
- Move: `src/generate/mappings/powerbuilder_flutter_mapping.json` → `src/generate/powerbuilder_flutter_mapping.json`
- Update code that loads this JSON file (path references)
- Remove directory: `src/generate/mappings/`

**Risk Assessment:** LOW
- Non-code file (JSON data)
- Easy to update path references

### 6. common/utils/ (4 files) - CONDITIONAL

**Current Structure:**
```
src/common/utils/
├── __init__.py
├── collections.py
├── files.py
└── strings.py
```

**Proposed Action:** Keep as-is or merge into parent
```
Option A: Keep directory (4 related utility files)
Option B: Move all to src/common/ with prefixed names:
  - collections.py → collection_utils.py
  - files.py → file_utils.py  
  - strings.py → string_utils.py
```

**Risk Assessment:** MEDIUM
- Multiple files with potentially wide usage
- May benefit from grouping as utilities
- Recommend: KEEP AS-IS (logical grouping of utilities)

### 7. extract/pbd/ (28 files) - NO ACTION

**Current Structure:**
```
src/extract/pbd/
├── 28 Python files
└── 1 YAML file
```

**Proposed Action:** NO FLATTENING - Too many files
- This directory contains a cohesive module with 28 files
- Flattening would pollute the parent directory
- The grouping provides good organization

**Alternative Actions:**
1. Consider breaking into submodules if logical groups exist
2. Review for potential file consolidation opportunities
3. Keep current structure for maintainability

## Implementation Steps

### Phase 1: Low-Risk Moves (Directories with 1-2 files)
1. Move `src/decompile/utils/version.py` → `src/decompile/version.py`
2. Move `src/parse/utils/loader.py` → `src/parse/grammar_loader.py`
3. Move `src/parse/error_recovery/strategy.py` → `src/parse/recovery_strategy.py`
4. Move `src/decompile/visualization/visualizer.py` → `src/decompile/cfg_visualizer.py`
5. Move `src/generate/mappings/powerbuilder_flutter_mapping.json` → `src/generate/powerbuilder_flutter_mapping.json`

### Phase 2: Update Imports
Run the following commands to update imports:
```bash
# Update decompile.utils.version imports
find . -name "*.py" -exec sed -i '' 's/from src.decompile.utils.version/from src.decompile.version/g' {} \;
find . -name "*.py" -exec sed -i '' 's/import src.decompile.utils.version/import src.decompile.version/g' {} \;

# Update parse.utils.loader imports
find . -name "*.py" -exec sed -i '' 's/from src.parse.utils.loader/from src.parse.grammar_loader/g' {} \;
find . -name "*.py" -exec sed -i '' 's/import src.parse.utils.loader/import src.parse.grammar_loader/g' {} \;

# Update parse.error_recovery.strategy imports
find . -name "*.py" -exec sed -i '' 's/from src.parse.error_recovery.strategy/from src.parse.recovery_strategy/g' {} \;
find . -name "*.py" -exec sed -i '' 's/import src.parse.error_recovery.strategy/import src.parse.recovery_strategy/g' {} \;

# Update decompile.visualization.visualizer imports
find . -name "*.py" -exec sed -i '' 's/from src.decompile.visualization.visualizer/from src.decompile.cfg_visualizer/g' {} \;
find . -name "*.py" -exec sed -i '' 's/import src.decompile.visualization.visualizer/import src.decompile.cfg_visualizer/g' {} \;
```

### Phase 3: Remove Empty Directories
```bash
rmdir src/decompile/utils
rmdir src/parse/utils
rmdir src/parse/error_recovery
rmdir src/decompile/visualization
rmdir src/generate/mappings
```

## Expected Benefits

1. **Reduced Directory Depth**: Eliminate 5 unnecessary directory levels
2. **Simpler Import Paths**: Shorter, more direct import statements
3. **Better File Visibility**: Important files not hidden in deep directories
4. **Clearer File Names**: Renamed files indicate their purpose better

## Metrics

- **Directories Removed**: 5
- **Files Moved**: 6 (5 .py files, 1 .json file)
- **Import Statements to Update**: ~10-50 (estimated)
- **Complexity Reduction**: 25% fewer directory levels in affected areas

## Risks and Mitigation

1. **Import Breakage**: Mitigated by systematic find-and-replace
2. **Test Failures**: Run full test suite after each phase
3. **Documentation**: Update any documentation referencing old paths
4. **IDE/Tool Configuration**: May need to update path mappings

## Decision Summary

| Directory | Files | Action | Priority |
|-----------|-------|--------|----------|
| decompile/utils/ | 1 | Flatten | HIGH |
| parse/utils/ | 2 | Flatten | HIGH |
| parse/error_recovery/ | 2 | Flatten | HIGH |
| decompile/visualization/ | 2 | Flatten | HIGH |
| generate/mappings/ | 2 | Flatten | HIGH |
| common/utils/ | 4 | Keep | - |
| extract/pbd/ | 28 | Keep | - |

**Total Directories to Remove**: 5
**Total Files to Move**: 6