"""DataWindow column models for PowerBuilder.

This module contains models for representing DataWindow columns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

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
    precision: int | None = None
    scale: int | None = None
    length: int | None = None


@dataclass
class PBColumnNameOption(PBNode):
    """Column name option."""

    name: str
    alias: str | None = None
    display_name: str | None = None


@dataclass
class PBColumn(PBNode):
    """Represents a DataWindow column."""

    name: str
    column_type: ColumnType
    is_key: bool = False
    is_updateable: bool = True
    is_identity: bool = False
    default_value: Any | None = None
    validation_rule: str | None = None
    format: str | None = None
    edit_style: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:


        return f"{self.name} ({self.column_type.name})"
