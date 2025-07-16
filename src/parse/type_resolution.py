"""Type resolution for PowerBuilder parsing.

This module provides comprehensive type resolution for PowerBuilder code,
including custom types, arrays, inheritance, and cross-library resolution.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple, List
from functools import lru_cache

from src.model.ast.pb_types import (
    PBType, PBBasicType, PBCustomType, PBArrayType, 
    PBDataWindowType, PBTypeRegistry
)
from src.parse.library import LibraryManager

logger = logging.getLogger(__name__)


@dataclass
class ResolutionContext:
    """Context for type resolution."""

    file_path: Path
    resolved_types: Dict[str, PBType] = field(default_factory=dict)
    unresolved_symbols: Set[str] = field(default_factory=set)
    imported_types: Dict[str, str] = field(default_factory=dict)  # alias -> qualified_name
    imported_modules: Set[str] = field(default_factory=set)
    namespace: Optional[str] = None

    def add_resolved_type(self, name: str, type_info: PBType):
        """Add a resolved type to the context."""
        self.resolved_types[name] = type_info
        self.unresolved_symbols.discard(name)

    def add_unresolved_symbol(self, name: str):
        """Add an unresolved symbol."""
        if name not in self.resolved_types:
            self.unresolved_symbols.add(name)

    def is_resolved(self, name: str) -> bool:
        """Check if a type is resolved."""
        return name in self.resolved_types

    def get_type(self, name: str) -> Optional[PBType]:
        """Get resolved type information."""
        return self.resolved_types.get(name)

    def add_import(self, module_name: str, alias: Optional[str] = None):
        """Add an imported module or type."""
        self.imported_modules.add(module_name)
        if alias:
            self.imported_types[alias] = module_name

    def resolve_imported_name(self, name: str) -> str:
        """Resolve an alias to its qualified name."""
        return self.imported_types.get(name, name)


class TypeResolver:
    """Resolves types in PowerBuilder code."""

    def __init__(self, library_manager: Optional[LibraryManager] = None):
        """Initialize the type resolver."""
        self.contexts: Dict[Path, ResolutionContext] = {}
        self.type_registry = PBTypeRegistry()
        self.library_manager = library_manager
        self._type_cache: Dict[str, PBType] = {}
        self._initialize_system_types()

    def _initialize_system_types(self):
        """Initialize PowerBuilder system types."""
        # Basic types are already initialized by PBTypeRegistry

        # Add common object types
        object_types = [
            ("window", "window"),
            ("datawindow", "datawindow"),
            ("datastore", "datawindow"),
            ("menu", "menu"),
            ("application", "application"),
            ("transaction", "transaction"),
            ("pipeline", "pipeline"),
            ("connection", "connection"),
            ("error", "error"),
            ("message", "message"),
            ("dynamicdescriptionarea", "dynamicdescriptionarea"),
            ("dynamicstagingarea", "dynamicstagingarea"),
            ("userobject", "userobject"),
            ("structure", "structure"),
            ("nonvisualobject", "nonvisualobject"),
            ("powerobject", "powerobject"),
        ]

        for type_name, base_class in object_types:
            custom_type = PBCustomType(
                name=type_name,
                base_class=base_class
            )
            # Set category to object explicitly
            custom_type.category = "object"
            self.type_registry.register(custom_type)

        # Add array type aliases
        self._register_common_array_types()

    def _register_common_array_types(self):
        """Register commonly used array types."""
        common_arrays = [
            ("integer", 1),
            ("string", 1),
            ("long", 1),
            ("decimal", 1),
            ("boolean", 1),
        ]

        for base_type_name, dimensions in common_arrays:
            base_type = self.type_registry.get(base_type_name)
            if base_type:
                self.type_registry.create_array_type(base_type, [dimensions])

    def create_context(self, file_path: Path, namespace: Optional[str] = None) -> ResolutionContext:
        """Create a resolution context for a file."""
        context = ResolutionContext(file_path, namespace=namespace)
        self.contexts[file_path] = context
        return context

    def resolve_type(self, type_name: str, context: ResolutionContext) -> Optional[PBType]:
        """Resolve a type name in the given context.

        Args:
            type_name: Name of the type to resolve
            context: Resolution context

        Returns:
            Type information if resolved, None otherwise
        """
        # Check cache first
        cache_key = f"{context.file_path}:{type_name}"
        if cache_key in self._type_cache:
            return self._type_cache[cache_key]

        # Try to resolve
        resolved_type = self._resolve_type_internal(type_name, context)

        if resolved_type:
            self._type_cache[cache_key] = resolved_type
            context.add_resolved_type(type_name, resolved_type)
        else:
            context.add_unresolved_symbol(type_name)

        return resolved_type

    def _resolve_type_internal(self, type_name: str, context: ResolutionContext) -> Optional[PBType]:
        """Internal type resolution logic."""
        # Clean the type name
        clean_name = type_name.strip().lower()

        # 1. Check if it's already resolved in context
        if context.is_resolved(type_name):
            return context.get_type(type_name)

        # 2. Check for array type syntax
        if "[" in type_name and "]" in type_name:
            return self.resolve_array_type(type_name, context)

        # 3. Check type registry (includes basic and system types)
        type_info = self.type_registry.get(clean_name)
        if type_info:
            return type_info

        # 4. Check imported types
        resolved_name = context.resolve_imported_name(type_name)
        if resolved_name != type_name:
            type_info = self.type_registry.get(resolved_name)
            if type_info:
                return type_info

        # 5. Try with namespace prefix
        if context.namespace and not "." in type_name:
            qualified_name = f"{context.namespace}.{type_name}"
            type_info = self.type_registry.get(qualified_name)
            if type_info:
                return type_info

        # 6. Check for custom types through library manager
        if self.library_manager:
            return self.resolve_custom_type(type_name, context)

        return None

    def resolve_custom_type(self, type_name: str, context: ResolutionContext) -> Optional[PBType]:
        """Resolve user-defined types (structures, objects).

        Args:
            type_name: Name of the custom type
            context: Resolution context

        Returns:
            Resolved custom type or None
        """
        if not self.library_manager:
            return None

        # Check in imported modules first
        for module in context.imported_modules:
            symbol_info = self.library_manager.get_symbol(f"{module}.{type_name}")
            if symbol_info:
                symbol = symbol_info.ast if hasattr(symbol_info, 'ast') else symbol_info
                if isinstance(symbol, dict):
                    return self._create_custom_type_from_symbol(symbol, module)

        # Check global symbols
        symbol_info = self.library_manager.get_symbol(type_name)
        if symbol_info:
            # Extract the actual symbol value from SymbolInfo
            symbol = symbol_info.ast if hasattr(symbol_info, 'ast') else symbol_info
            if isinstance(symbol, dict):
                return self._create_custom_type_from_symbol(symbol)

        # Check with namespace
        if context.namespace:
            qualified_name = f"{context.namespace}.{type_name}"
            symbol_info = self.library_manager.get_symbol(qualified_name)
            if symbol_info:
                symbol = symbol_info.ast if hasattr(symbol_info, 'ast') else symbol_info
                if isinstance(symbol, dict):
                    return self._create_custom_type_from_symbol(symbol, context.namespace)

        return None

    def _create_custom_type_from_symbol(self, symbol: Dict[str, Any], 
                                       namespace: Optional[str] = None) -> PBCustomType:
        """Create a custom type from a symbol definition."""
        type_name = symbol.get("name", "unknown")
        base_class = symbol.get("base_class", symbol.get("type", "object"))

        # Handle special cases
        if base_class == "datawindow":
            custom_type = PBDataWindowType(
                name=type_name,
                namespace=namespace
            )
        else:
            custom_type = PBCustomType(
                name=type_name,
                namespace=namespace,
                base_class=base_class,
                is_interface=symbol.get("is_interface", False)
            )

        # Add attributes if available
        attributes = symbol.get("attributes", {})
        for attr_name, attr_info in attributes.items():
            if isinstance(attr_info, dict):
                attr_type_name = attr_info.get("type", "any")
                attr_type = self.type_registry.get(attr_type_name) or PBBasicType(name=attr_type_name)
                custom_type.add_attribute(attr_name, attr_type)

        # Handle inheritance
        if "super_type" in symbol:
            super_type_name = symbol["super_type"]
            super_type = self.type_registry.get(super_type_name)
            if isinstance(super_type, PBCustomType):
                custom_type.super_type = super_type

        # Register the type
        self.type_registry.register(custom_type)

        return custom_type

    def resolve_array_type(self, type_name: str, context: ResolutionContext) -> Optional[PBArrayType]:
        """Resolve array types.

        Handles:
        - Single-dimensional arrays: integer[]
        - Multi-dimensional arrays: string[10,20]
        - Dynamic arrays: decimal[]
        - Nested arrays: integer[][]

        Args:
            type_name: Array type string
            context: Resolution context

        Returns:
            Resolved array type or None
        """
        # Parse array syntax
        base_name, dimensions = self._parse_array_syntax(type_name)
        if not base_name:
            return None

        # Resolve base type
        base_type = self.resolve_type(base_name, context)
        if not base_type:
            logger.warning(f"Cannot resolve base type '{base_name}' for array '{type_name}'")
            return None

        # Handle nested arrays
        if isinstance(base_type, PBArrayType):
            # Create a new array type with additional dimensions
            total_dims = len(base_type.dimensions) + len(dimensions)
            all_dims = list(base_type.dimensions) + dimensions
            return self.type_registry.create_array_type(base_type.element_type, all_dims)

        # Create array type
        return self.type_registry.create_array_type(base_type, dimensions)

    def _parse_array_syntax(self, type_name: str) -> Tuple[str, List[Optional[int]]]:
        """Parse array type syntax.

        Returns:
            Tuple of (base_type_name, dimensions)
        """
        import re

        # Match array syntax: type[dim1,dim2,...] or type[][]...
        match = re.match(r'^(\w+(?:\.\w+)*)\s*(\[.*\])$', type_name.strip())
        if not match:
            return "", []

        base_name = match.group(1)
        bracket_part = match.group(2)

        # Count dimensions
        dimensions = []

        # Handle explicit dimensions: [10,20]
        if "," in bracket_part:
            dim_match = re.match(r'\[([^\]]+)\]', bracket_part)
            if dim_match:
                dim_parts = dim_match.group(1).split(",")
                for part in dim_parts:
                    part = part.strip()
                    if part.isdigit():
                        dimensions.append(int(part))
                    else:
                        dimensions.append(None)  # Dynamic dimension
        else:
            # Count bracket pairs for [][] syntax
            bracket_count = bracket_part.count("[]")
            if bracket_count > 0:
                dimensions = [None] * bracket_count
            else:
                # Single dimension with size: [10]
                size_match = re.match(r'\[(\d+)\]', bracket_part)
                if size_match:
                    dimensions = [int(size_match.group(1))]
                else:
                    dimensions = [None]  # Dynamic array

        return base_name, dimensions

    def resolve_type_alias(self, alias: str, context: ResolutionContext) -> Optional[PBType]:
        """Resolve type aliases."""
        # Check if it's an imported alias
        resolved_name = context.resolve_imported_name(alias)
        if resolved_name != alias:
            return self.resolve_type(resolved_name, context)

        # Check for common aliases
        type_aliases = {
            "int": "integer",
            "bool": "boolean",
            "str": "string",
            "char": "character",
            "dw": "datawindow",
            "ds": "datastore",
            "nvo": "nonvisualobject",
            "uo": "userobject",
        }

        if alias.lower() in type_aliases:
            return self.resolve_type(type_aliases[alias.lower()], context)

        return None

    def is_compatible(self, source_type: PBType, target_type: PBType) -> bool:
        """Check if source type is compatible with target type."""
        # Same type
        if source_type == target_type:
            return True

        # Check using type's accept method
        if target_type.accepts(source_type):
            return True

        # Any type accepts everything
        if target_type.name.lower() == "any":
            return True

        # Numeric type compatibility
        numeric_types = {"byte", "integer", "long", "decimal", "real", "double", "uint", "ulong"}
        if (isinstance(source_type, PBBasicType) and isinstance(target_type, PBBasicType) and
            source_type.name.lower() in numeric_types and target_type.name.lower() in numeric_types):
            return self._check_numeric_compatibility(source_type.name, target_type.name)

        return False

    def _check_numeric_compatibility(self, source: str, target: str) -> bool:
        """Check numeric type compatibility based on PowerBuilder rules."""
        # Define numeric type hierarchy
        type_hierarchy = {
            "byte": 0,
            "integer": 1,
            "uint": 1,
            "long": 2,
            "ulong": 2,
            "real": 3,
            "double": 4,
            "decimal": 5,
        }

        source_level = type_hierarchy.get(source.lower(), -1)
        target_level = type_hierarchy.get(target.lower(), -1)

        # Can assign to same or higher precision type
        return source_level <= target_level

    def get_context(self, file_path: Path) -> Optional[ResolutionContext]:
        """Get the resolution context for a file."""
        return self.contexts.get(file_path)

    def clear_cache(self):
        """Clear the type resolution cache."""
        self._type_cache.clear()

    @lru_cache(maxsize=256)
    def get_type_category(self, type_name: str) -> str:
        """Get the category of a type (basic, object, array, etc.)."""
        type_obj = self.type_registry.get(type_name.lower())
        if type_obj:
            return type_obj.category

        # Check for array syntax
        if "[" in type_name and "]" in type_name:
            return "array"

        # Check for known object suffixes
        object_suffixes = ["window", "object", "control", "datawindow", "menu"]
        lower_name = type_name.lower()
        for suffix in object_suffixes:
            if lower_name.endswith(suffix):
                return "object"

        return "unknown"