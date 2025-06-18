#!/usr/bin/env python3
"""Add type stub files for better type checking."""

from pathlib import Path
from typing import List


def create_type_stub(module_path: Path, stub_content: str) -> None:
    """Create a .pyi stub file."""
    stub_path = module_path.with_suffix('.pyi')
    stub_path.write_text(stub_content)
    print(f"Created stub: {stub_path}")


def generate_common_stubs() -> None:
    """Generate stub files for common module."""
    
    # common/types.pyi
    types_stub = '''"""Type definitions for PowerBuilder type system."""

from typing import Any, Dict, Optional, List, Union
from enum import Enum

class TypeCategory(Enum):
    BASIC: str = "basic"
    ARRAY: str = "array"
    CUSTOM: str = "custom"
    STRUCTURE: str = "structure"
    ENUM: str = "enum"

class BasicType:
    name: str
    category: TypeCategory
    
    def __init__(self, name: str, category: TypeCategory = TypeCategory.BASIC) -> None: ...

class ArrayType:
    name: str
    element_type: BasicType
    dimensions: List[int]
    
    def __init__(self, name: str, element_type: BasicType, dimensions: Optional[List[int]] = None) -> None: ...

class CustomType:
    name: str
    base_type: Optional[str]
    
    def __init__(self, name: str, base_type: Optional[str] = None) -> None: ...

class TypeRegistry:
    @staticmethod
    def register(name: str, type_info: Dict[str, Any]) -> None: ...
    
    @staticmethod
    def get(name: str) -> Optional[Dict[str, Any]]: ...
    
    @staticmethod
    def is_registered(name: str) -> bool: ...
'''
    create_type_stub(Path("common/types.py"), types_stub)
    
    # common/progress.pyi
    progress_stub = '''"""Progress tracking type stubs."""

from typing import Any, Optional, Protocol, List
from rich.progress import Progress, Task

class ProgressCallback(Protocol):
    def __call__(self, current: int, total: int, message: str = "") -> None: ...

class ProgressTracker:
    progress: Progress
    tasks: dict[str, Task]
    
    def __init__(self) -> None: ...
    def start_task(self, task_id: str, description: str, total: int) -> None: ...
    def update_task(self, task_id: str, advance: int = 1, message: Optional[str] = None) -> None: ...
    def complete_task(self, task_id: str) -> None: ...
'''
    create_type_stub(Path("common/progress.py"), progress_stub)


def fix_import_issues() -> None:
    """Fix common import issues."""
    # Fix the types.py shadow issue
    problem_file = Path("reference/decompilers/powerbuilder-decompile/pbd/types.py")
    if problem_file.exists():
        # Rename to avoid shadowing
        new_name = problem_file.parent / "pbd_types.py"
        problem_file.rename(new_name)
        print(f"Renamed {problem_file} to {new_name}")
        
        # Update imports
        for py_file in problem_file.parent.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "from .types import" in content or "import types" in content:
                    content = content.replace("from .types import", "from .pbd_types import")
                    content = content.replace("import types", "import pbd_types")
                    py_file.write_text(content)
                    print(f"Updated imports in {py_file}")
            except Exception as e:
                print(f"Error updating {py_file}: {e}")


def add_py_typed_marker() -> None:
    """Add py.typed marker for PEP 561 compliance."""
    modules = ["common", "extract", "parse", "decompile", "generate", "model"]
    
    for module in modules:
        module_path = Path(module)
        if module_path.exists() and module_path.is_dir():
            py_typed = module_path / "py.typed"
            if not py_typed.exists():
                py_typed.touch()
                print(f"Added py.typed to {module}")


def create_mypy_config() -> None:
    """Create a more lenient mypy configuration for gradual typing."""
    config = '''# Gradual typing configuration for mypy

[mypy]
python_version = 3.13
warn_return_any = True
warn_unused_configs = True

# Start with less strict settings
disallow_untyped_defs = False
disallow_incomplete_defs = False
check_untyped_defs = True
disallow_untyped_decorators = False
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = False
warn_no_return = True
warn_unreachable = True
strict_equality = False

# Allow gradual typing
allow_untyped_globals = True
allow_redefinition = True

# Ignore missing imports
ignore_missing_imports = True

# Per-module options for stricter checking
[mypy-common.*]
disallow_untyped_defs = True

[mypy-model.ast.*]
disallow_untyped_defs = True

[mypy-tests.*]
ignore_errors = True

# Third party
[mypy-lark.*]
ignore_missing_imports = True

[mypy-psutil.*]
ignore_missing_imports = True

[mypy-rich.*]
ignore_missing_imports = True
'''
    
    Path("mypy.ini").write_text(config)
    print("Created gradual typing mypy.ini configuration")


def main():
    """Main entry point."""
    print("Setting up type checking infrastructure...")
    
    # Fix import shadow issues
    print("\n1. Fixing import issues...")
    fix_import_issues()
    
    # Create type stubs
    print("\n2. Creating type stubs...")
    generate_common_stubs()
    
    # Add py.typed markers
    print("\n3. Adding py.typed markers...")
    add_py_typed_marker()
    
    # Create gradual mypy config
    print("\n4. Creating gradual mypy configuration...")
    create_mypy_config()
    
    print("\nType checking setup complete!")
    print("Run 'mypy . --config-file=mypy.ini' for gradual type checking")


if __name__ == "__main__":
    main()