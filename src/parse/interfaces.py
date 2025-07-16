"""Parser interfaces to prevent circular dependencies.

This module defines protocols that can be used by transformers without
creating direct dependencies on parser implementations.
"""

from typing import Protocol, Dict, List, Optional, Any
from lark import Tree


class ITypeParser(Protocol):
    """Interface for type parsers."""
    
    def parse_type_declaration(self, tree: Tree) -> Any:
        """Parse a type declaration."""
        ...
    
    def get_type(self, name: str) -> Optional[Any]:
        """Get a parsed type by name."""
        ...


class IEnumeratedType(Protocol):
    """Interface for enumerated types."""
    
    @property
    def name(self) -> str:
        """Type name."""
        ...
    
    @property  
    def values(self) -> Dict[str, int]:
        """Enum values."""
        ...
    
    def get_value(self, name: str) -> Optional[int]:
        """Get numeric value for enum name."""
        ...


class IStructureType(Protocol):
    """Interface for structure types."""
    
    @property
    def name(self) -> str:
        """Type name."""
        ...
    
    @property
    def fields(self) -> List[Any]:
        """Structure fields."""
        ...
    
    def get_field(self, name: str) -> Optional[Any]:
        """Get field by name."""
        ...


__all__ = ['ITypeParser', 'IEnumeratedType', 'IStructureType']