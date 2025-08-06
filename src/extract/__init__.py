"""Module initialization with lazy loading to reduce import overhead."""

from typing import Any

# Cache for lazy-loaded imports
_import_cache: dict[str, Any] = {}

def __getattr__(name: str) -> Any:
    """Lazy import extraction components on first access."""
    if name in _import_cache:
        return _import_cache[name]
    
    # Define lazy loading mappings
    lazy_imports = {
        "ExtractCoordinator": ("src.extract.coordinator", "ExtractCoordinator"),
        "RESOURCE_EXTENSIONS": ("src.extract.pbd.constants", "RESOURCE_EXTENSIONS"),
        "SOURCE_EXTENSIONS": ("src.extract.pbd.constants", "SOURCE_EXTENSIONS"),
        "is_resource_file": ("src.extract.utils.binary", "is_resource_file"),
        "is_source_file": ("src.extract.utils.binary", "is_source_file"),
        "extract_pbl_file": (".extract", "extract_pbl_file"),
        "extract_with_recovery": (".extract", "extract_with_recovery"),
    }
    
    if name in lazy_imports:
        module_name, attr_name = lazy_imports[name]
        try:
            if module_name.startswith('.'):
                # Relative import
                from . import extract as extract_module
                _import_cache[name] = getattr(extract_module, attr_name)
            else:
                # Absolute import
                import importlib
                module = importlib.import_module(module_name)
                _import_cache[name] = getattr(module, attr_name)
            return _import_cache[name]
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Cannot import {name} from {module_name}: {e}")
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "RESOURCE_EXTENSIONS",
    "SOURCE_EXTENSIONS", 
    "ExtractCoordinator",
    "extract_pbl_file",
    "extract_with_recovery",
    "is_resource_file",
    "is_source_file",
]
