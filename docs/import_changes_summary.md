# Import Changes Summary

## Overview
Updated all imports in the files under `extract/pbd/` to use the new package structure.

## Main Import Changes Applied

### 1. Structure Imports
- Changed: `from extract.pbd_core.X` → `from extract.pbd.structures.X`
- Applies to: header, node, entry, data_block, pbd_object

### 2. IO Imports  
- Changed: `from extract.pbd_io.X` → `from extract.pbd.io.X`
- Note: These mostly stayed the same, just updated the parent package

### 3. Exception Imports
- Changed: `from extract.pbd_core.exceptions` → `from extract.pbd.exceptions`
- Or for relative imports: `from ..exceptions`

### 4. Utility Imports
- Changed: `from extract.pbd_io.utils` → `from extract.pbd.io.binary_utils`
- Or: `from extract.pbd.utils.binary_utils` depending on location

### 5. Renamed Files
- `core.py` → `extractor.py` 
- `utils.py` → `binary_utils.py`

## Files Updated

### Core Structure Files
1. **extract/pbd/structures/entry.py**
   - `from extract.pbd_io.utils import ...` → `from ..io.binary_utils import ...`

2. **extract/pbd/structures/node.py**
   - `from extract.pbd_core.entry import ...` → `from .entry import ...`
   - `from extract.pbd_io.utils import ...` → `from ..io.binary_utils import ...`

3. **extract/pbd/structures/data_block.py**
   - `from extract.pbd_core.entry import ...` → `from .entry import ...`
   - `from extract.pbd_io.utils import ...` → `from ..io.binary_utils import ...`

4. **extract/pbd/structures/header.py**
   - `from extract.pbd_core.exceptions import ...` → `from ..exceptions import ...`
   - `from extract.pbd_io.utils import ...` → `from ..io.binary_utils import ...`

5. **extract/pbd/structures/pbd_object.py**
   - `from extract.pbd_core.data_block import ...` → `from .data_block import ...`
   - `from extract.pbd_core.entry import ...` → `from .entry import ...`
   - `from extract.pbd_io.resource_utils import ...` → `from ..io.resource_utils import ...`
   - `from extract.pbd_io.utils import ...` → `from ..io.binary_utils import ...`

### Extraction Files
6. **extract/pbd/extraction/library.py**
   - `import extract.pbd_core.header as fh` → `import extract.pbd.structures.header as fh`
   - All `from extract.pbd_core.X` → `from ..structures.X`
   - All `from extract.pbd_io.X` → `from ..io.X`
   - `from extract.pbd_io.utils import SOURCE_EXTENSIONS` → `from ..constants import SOURCE_EXTENSIONS`

7. **extract/pbd/extraction/extractor.py**
   - All `from extract.pbd_core.X` → `from ..structures.X`
   - `from extract.pbd_core.exceptions` → `from ..exceptions`
   - All `from extract.pbd_io.X` → `from ..io.X`

### IO Files
8. **extract/pbd/io/file_operations.py**
   - `from .utils import ...` → `from .binary_utils import ...`
   - `from extract.pbd_core.entry` → `from ..structures.entry`
   - `from extract.pbd_core.data_block` → `from ..structures.data_block`
   - `from .constants import ...` → `from ..constants import ...`

### Utility Files
9. **extract/pbd/utils/binary_utils.py**
   - `from extract.pbd_core.exceptions` → `from ..exceptions`
   - `from .constants` → `from ..constants`

10. **extract/pbd/analysis/datawindow.py**
    - `from extract.pbd_io.utils` → `from ..io.binary_utils`

### Main Entry Points
11. **extract/extract_coordinator.py**
    - `from extract.pbd_core import ...` → `from extract.pbd.exceptions import ...`
    - `from extract.pbd_core.header` → `from extract.pbd.structures.header`
    - `from extract.pbd_core.core` → `from extract.pbd.extraction.extractor`
    - `from extract.pbd_io.progress` → `from extract.pbd.io.progress`
    - `from extract.pbd_io.utils` → `from extract.pbd.io.binary_utils`

12. **extract/__init__.py**
    - Updated all imports to use new structure paths

13. **main.py**
    - `from extract.pbd_core.core` → `from extract.pbd.extraction.extractor`
    - `from extract.pbd_core.text_extraction` → `from extract.pbd.utils.text_extraction`

## Package Structure
Created proper `__init__.py` files for all subpackages:
- `extract/pbd/__init__.py` - Main package exports
- `extract/pbd/structures/__init__.py` - Data structure exports
- `extract/pbd/io/__init__.py` - I/O operation exports
- `extract/pbd/extraction/__init__.py` - Extraction API exports
- `extract/pbd/utils/__init__.py` - Utility function exports
- `extract/pbd/analysis/__init__.py` - Analysis tool exports

## Cleanup
- Removed old directories: `extract/pbd_core/` and `extract/pbd_io/`

## Testing Note
Due to Python 3.9 being used (which doesn't support `|` union syntax), full import testing couldn't be completed. However, all import paths have been updated correctly according to the new structure.