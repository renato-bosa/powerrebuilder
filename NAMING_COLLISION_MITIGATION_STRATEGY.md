# PowerRebuilder Naming Collision Mitigation Strategy

## Executive Summary

The analysis reveals **126 naming collisions** across the PowerRebuilder codebase that would prevent successful module flattening. The most critical issues involve:

1. **Pipeline-related classes** (PipelineMetrics, PipelineStage) with 5-6 collisions each
2. **Exception hierarchy duplicates** between `core.exception_hierarchy` and `core.exceptions`
3. **Common utility functions** duplicated between `common.utils` and its submodules
4. **Interface definitions** scattered across `contracts`, `core`, and module-specific locations

## Critical Collision Categories

### 1. Pipeline Architecture (CRITICAL - 11 collisions)
These are foundational classes used throughout the system:

- **PipelineMetrics** (6 occurrences) - Used in async coordinators and pipeline modes
- **PipelineStage** (5 occurrences) - Core pipeline abstraction
- **IPipelineStage/IPipelineCoordinator** (3 occurrences each) - Interface definitions

**Recommended Solution:**
```python
# Consolidate to single definitions in core.pipeline module:
core.pipeline.PipelineMetrics
core.pipeline.PipelineStage
core.pipeline.interfaces.IPipelineStage
core.pipeline.interfaces.IPipelineCoordinator

# Remove duplicates from:
# - common.pipeline.*
# - contracts.interfaces
# - */async_coordinator.py files
```

### 2. Exception Hierarchy (HIGH - 40+ duplicates)
Every exception is duplicated between `core.exception_hierarchy` and `core.exceptions`:

**Recommended Solution:**
```python
# Keep only core.exceptions module
# Remove core.exception_hierarchy entirely
# Ensure all imports use: from core.exceptions import XError
```

### 3. Common Utilities (MEDIUM - 15 collisions)
Functions duplicated between `common.utils` and submodules:

- String utilities: `camel_to_snake`, `snake_to_camel`, `truncate`, `pluralize`
- File utilities: `read_file_safe`, `normalize_path`, `ensure_directory`
- Collection utilities: `merge_dicts`, `chunk_list`, `filter_dict`

**Recommended Solution:**
```python
# Remove re-exports from common.utils
# Keep only in specialized submodules:
from common.utils.strings import camel_to_snake
from common.utils.files import normalize_path
from common.utils.collections import merge_dicts
```

### 4. Module-Specific Patterns

#### Extract Module
- **ResourceExtractionManager** (3 occurrences in pbd submodule)
- **StringResourceExtractor**, **EnhancedImageExtractor** (2 each)

**Solution:** Prefix with specific extractor type:
```python
extract.pbd.PbdResourceManager
extract.pbd.PbdStringExtractor
extract.pbd.PbdImageExtractor
```

#### Generate Module
- **Generator classes** duplicated between coordinators and implementations
- **Converter classes** with similar names across flutter/data/utils

**Solution:** Use role-specific prefixes:
```python
generate.coordinators.FlutterGeneratorCoordinator
generate.generators.FlutterCodeGenerator
generate.converters.flutter.FlutterWidgetConverter
```

#### Model Module
- **AST expression classes** duplicated between ast and expressions packages
- **PB-specific nodes** duplicated between entities and visitor patterns

**Solution:** Consolidate AST nodes:
```python
model.ast.expressions.*  # All expression nodes
model.ast.nodes.*       # All other AST nodes
model.entities.*        # High-level entity models only
```

## Recommended Refactoring Steps

### Phase 1: Critical Infrastructure (Week 1)
1. **Consolidate Pipeline Classes**
   - Move all pipeline definitions to `core.pipeline`
   - Update all async_coordinator files
   - Remove duplicates from common and contracts

2. **Fix Exception Hierarchy**
   - Delete `core.exception_hierarchy.py`
   - Ensure `core.exceptions.py` has all definitions
   - Update all imports

### Phase 2: Common Utilities (Week 2)
1. **Remove common.utils re-exports**
   - Keep utilities only in their specialized submodules
   - Update all imports to use specific paths
   - Add deprecation warnings to common.utils

2. **Consolidate Security Classes**
   - Merge PathValidator implementations
   - Consolidate security errors
   - Create single security module

### Phase 3: Module-Specific (Week 3-4)
1. **Extract Module**
   - Rename PBD-specific classes with Pbd prefix
   - Consolidate extractor base classes
   - Remove duplicate manager classes

2. **Generate Module**
   - Distinguish coordinators from generators
   - Prefix converter classes by target
   - Consolidate template engines

3. **Model Module**
   - Merge AST expression duplicates
   - Consolidate visitor pattern nodes
   - Create clear entity/AST separation

### Phase 4: Interface Consolidation (Week 5)
1. **Merge Interface Definitions**
   - Keep interfaces in their logical modules
   - Remove contracts.interfaces duplicates
   - Update all type hints

2. **Create Import Guidelines**
   - Document standard import patterns
   - Create import linter rules
   - Add to CI/CD pipeline

## Import Pattern Recommendations

### Bad (Current State):
```python
from common.utils import camel_to_snake  # Re-exported
from contracts.interfaces import IPipelineStage  # Duplicate
from core.exceptions import ValidationError  # One of two copies
```

### Good (Target State):
```python
from common.utils.strings import camel_to_snake  # Direct import
from core.pipeline.interfaces import IPipelineStage  # Single source
from core.exceptions import ValidationError  # Only copy
```

## Automation Tools

### 1. Collision Detector (Already Created)
- `analyze_naming_collisions.py` - Identifies all collisions

### 2. Import Updater (To Create)
```python
# Tool to automatically update imports after renames
python update_imports.py --mapping collision_fixes.json
```

### 3. Safe Rename Script (To Create)
```python
# Tool to rename with automatic import updates
python safe_rename.py OldClassName NewClassName --module src.extract.pbd
```

## Success Metrics

1. **Zero naming collisions** when running collision detector
2. **All tests passing** after each refactoring phase
3. **Successful flat import**: `from powerrebuilder import ClassName` works without ambiguity
4. **No circular imports** after flattening

## Risk Mitigation

1. **Create comprehensive test suite** before starting
2. **Use feature branches** for each refactoring phase
3. **Run collision detector** after each change
4. **Maintain backward compatibility** with deprecation warnings
5. **Update documentation** as changes are made

## Timeline

- **Week 1**: Critical infrastructure (Pipeline, Exceptions)
- **Week 2**: Common utilities consolidation
- **Week 3-4**: Module-specific refactoring
- **Week 5**: Interface consolidation and testing
- **Week 6**: Documentation and import migration tools

Total estimated effort: **6 weeks** with 1-2 developers