# PR #4: Implement Critical Stub Classes

## Summary
- Implement missing AST node classes (PBConstructorCall, PBMethodCall)
- Enhance core system stubs (LibraryManager, TypeResolver)
- Add minimal implementations to unblock pipeline
- Create comprehensive test coverage

## Problem
Several critical classes are defined as stubs or missing entirely, causing import errors and pipeline failures.

## Solution
Implement minimal working versions of all critical stub classes with proper interfaces and basic functionality.

## Implementation Details

### AST Node Classes

#### PBConstructorCall
```python
@dataclass
class PBConstructorCall(PBNode):
    """Represents a constructor call in PowerBuilder."""
    class_name: str
    arguments: list[Expression] = field(default_factory=list)
    is_super: bool = False  # For super() calls
    
    def validate(self, context: dict[str, Any] | None = None) -> bool:
        """Validate constructor call."""
        return bool(self.class_name)
```

#### PBMethodCall
```python
@dataclass
class PBMethodCall(PBNode):
    """Represents a method call in PowerBuilder."""
    object: Expression | None = None  # Object instance or class
    method_name: str = ""
    arguments: list[Expression] = field(default_factory=list)
    is_static: bool = False
    is_dynamic: bool = False  # For dynamic method invocation
    
    def validate(self, context: dict[str, Any] | None = None) -> bool:
        """Validate method call."""
        return bool(self.method_name)
```

### Core System Classes

#### LibraryManager Enhancement
```python
class LibraryManager:
    """Manages PowerBuilder library files."""
    
    def __init__(self, library_paths: List[Path] = None):
        self.library_paths = library_paths or []
        self.symbols = {}
        self.loaded_libraries = set()
        
    def load_library(self, library_path: Path) -> bool:
        """Load a library file and extract symbols."""
        if library_path in self.loaded_libraries:
            return True
        self.loaded_libraries.add(library_path)
        logger.info(f"Loaded library: {library_path}")
        return True
        
    def resolve_symbol(self, symbol_name: str) -> Optional[Any]:
        """Resolve a symbol across all loaded libraries."""
        return self.symbols.get(symbol_name)
```

## Test Plan
- [ ] Unit tests for each new class
- [ ] Integration tests with parser
- [ ] Verify no import errors
- [ ] Run full pipeline with stub implementations
- [ ] Performance benchmarks

## File Locations
- `src/model/entities/__init__.py` - AST nodes
- `src/parse/library.py` - LibraryManager
- `src/parse/type_resolution.py` - TypeResolver
- Test files in corresponding test directories

## Estimated Time: 70 hours (2-3 weeks)

## Implementation Priority
1. PBConstructorCall & PBMethodCall (Critical)
2. LibraryManager (High)
3. TypeResolver enhancements (Medium)
4. Other stubs as needed (Low)

## Branch: `feat/implement-critical-stubs`