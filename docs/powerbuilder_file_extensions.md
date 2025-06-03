# PowerBuilder File Extensions Reference

## Source Code File Extensions

Based on the codebase analysis, here are the PowerBuilder file extensions and their meanings:

### Primary Source Files (.sr* series)
- **.sra** - Application object (PowerBuilder Application)
- **.srw** - Window object
- **.sru** - User object (User-defined Object) 
- **.srm** - Menu object
- **.srf** - Function object
- **.srd** - DataWindow object
- **.srs** - Structure object
- **.srq** - Query object
- **.srj** - Project object (Java-related)
- **.srp** - Pipeline object
- **.srx** - User object (extension)

### P-Code File Extensions (Compiled)
When PowerBuilder source files are compiled into P-code, they follow this mapping pattern:
- **.srf** → **.fun** (Function P-code)
- **.sr[a,w,u,m,d,s,q,j,p,x]** → **.[same base]f** (e.g., .sru → .srf, .srw → .srf)

Example mappings:
- `mywindow.srw` → `mywindow.srf` (P-code)
- `myfunction.srf` → `myfunction.fun` (P-code)
- `myuserobject.sru` → `myuserobject.srf` (P-code)

### Library Files
- **.pbl** - PowerBuilder Library (source code library)
- **.pbd** - PowerBuilder Dynamic library (compiled library)
- **.pbr** - PowerBuilder Resource file
- **.pbg** - PowerBuilder Generation file
- **.pbt** - PowerBuilder Target file
- **.pbw** - PowerBuilder Workspace file

### Other Extensions (Less Common)
- **.udo** - User Defined Object (older format, less common)
- **.win** - Window file (older format, less common)

## File Type Mappings in Code

From `parse/constants.py`:
```python
FILE_EXTENSIONS: dict[str, FileType] = {
    "srw": FileType.WINDOW,
    "sru": FileType.USER_OBJECT,
    "srf": FileType.FUNCTION,
    "srm": FileType.MENU,
    "srs": FileType.STRUCTURE,
    "srq": FileType.QUERY,
    "sra": FileType.APPLICATION,
    "srd": FileType.DATAWINDOW,
    "pbt": FileType.PROJECT,
    "pbl": FileType.LIBRARY,
    "pbd": FileType.LIBRARY,
}
```

From `extract/pbd_io/utils.py`:
```python
SOURCE_EXTENSIONS = {
    ".srd", ".srs", ".srw", ".sru", ".srf", ".srm", ".srx", ".srj", ".srp", ".srq", ".sra",
}
```

## P-Code Generation Logic

From `extract/pbd_io/file_operations.py`:
```python
def save_pcode_file(obj_name: str, text: str, output_path: str | Path) -> None:
    # Create pcode filename
    if safe_base.lower().endswith(".srf"):
        pcode_name = safe_base[:-4] + ".fun"
    else:
        # .sru, .srw, etc.
        pcode_name = safe_base[:-1] + "f"
```

This shows that:
1. Function objects (.srf) compile to .fun files
2. All other source files compile to P-code by replacing the last character with 'f'

## Notes

1. The .udo and .win extensions appear to be older PowerBuilder formats that are less commonly used in modern versions.

2. When PowerBuilder compiles source code into P-code within PBD files, the P-code retains information about the original source file extension but is stored in a binary format.

3. The extraction process in this codebase can save both the original source format and the P-code format when extracting from PBD files.