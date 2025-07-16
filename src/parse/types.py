"""Shared types for the parse layer.

This module contains types that are shared between parsers and transformers
to prevent circular dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.base import PBNode


@dataclass
class EnumeratedType(PBNode):
    """Represents an enumerated type."""
    name: str
    values: List[str] = field(default_factory=list)
    

@dataclass  
class StructureType(PBNode):
    """Represents a structure type."""
    name: str
    fields: Dict[str, Any] = field(default_factory=dict)
    parent: Optional[str] = None


__all__ = ['EnumeratedType', 'StructureType']