"""DataWindow column models for PowerBuilder.

This module contains models for representing DataWindow columns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Optional

from model.utils.base import PBNode


class ColumnType(Enum):
    """Types of DataWindow columns."""
    
    STRING = auto()
    NUMBER = auto()
    DATE = auto()
    TIME = auto()
    DATETIME = auto()
    DECIMAL = auto()
    BOOLEAN = auto()
    BLOB = auto()


@dataclass
class PBColumnTypeOption(PBNode):
    """Column type option."""
    
    column_type: ColumnType
    precision: Optional[int] = None
    scale: Optional[int] = None
    length: Optional[int] = None


@dataclass
class PBColumnNameOption(PBNode):
    """Column name option."""
    
    name: str
    alias: Optional[str] = None
    display_name: Optional[str] = None


@dataclass
class PBColumn(PBNode):
    """Represents a DataWindow column."""
    
    name: str
    column_type: ColumnType
    is_key: bool = False
    is_updateable: bool = True
    is_identity: bool = False
    default_value: Optional[Any] = None
    validation_rule: Optional[str] = None
    format: Optional[str] = None
    edit_style: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"{self.name} ({self.column_type.name})"