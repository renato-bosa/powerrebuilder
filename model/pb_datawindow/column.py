"""PowerBuilder DataWindow Column implementation.

This module contains classes for representing PowerBuilder DataWindow columns
and related options that are used in the original PowerBuilder application.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..utils.base import PBNode


class ColumnType(Enum):
    """PowerBuilder column data types."""

    CHAR = "char"
    VARCHAR = "varchar"
    INTEGER = "integer"
    DECIMAL = "decimal"
    NUMBER = "number"
    NUMERIC = "numeric"
    FLOAT = "float"
    DOUBLE = "double"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    TIMESTAMP = "timestamp"
    BOOLEAN = "boolean"
    BLOB = "blob"
    TEXT = "text"
    LONG = "long"


@dataclass
class PBColumnOption(PBNode):
    """Base class for column options in PowerBuilder DataWindows.

    Attributes:
        name: Name of the option
        expression: Value of the option (usually a string or number)
    """

    name: str
    expression: str

    def __str__(self) -> str:
        """Return string representation of the column option.

        Returns:
            Option as a string in the format name=value
        """
        return f"{self.name}={self.expression}"


@dataclass
class PBColumnNameOption(PBNode):
    """Column name display option.

    This option specifies the display name for a column in the DataWindow.

    Attributes:
        name: For test compatibility only (ignored)
        expression: The display name, usually a quoted string
    """

    name: str | None = None  # For test compatibility
    expression: str = field(default="")

    def __str__(self) -> str:
        """Return string representation of the name option.

        Returns:
            Option as a string in the format name=value
        """
        return f"name={self.expression}"


@dataclass
class PBColumnTypeOption(PBNode):
    """Column type display option.

    This option specifies the display type/edit style for a column
    in the DataWindow.

    Attributes:
        name: For test compatibility only (ignored)
        expression: The display type, usually a quoted string
    """

    name: str | None = None  # For test compatibility
    expression: str = field(default="")

    def __str__(self) -> str:
        """Return string representation of the type option.

        Returns:
            Option as a string in the format type=value
        """
        return f"type={self.expression}"


@dataclass
class PBColumn(PBNode):
    """PowerBuilder DataWindow column definition.

    Attributes:
        name: Internal name for the column
        column_name: Actual database column name
        column_type: Data type of the column
        length: Length for character types
        precision: Precision for numeric types
        scale: Scale for numeric types
        is_nullable: Whether the column can be null
        default_value: Default value for the column
        name_option: Display name option
        type_option: Display type option
    """

    name: str
    column_name: str
    column_type: ColumnType
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    is_nullable: bool = True
    default_value: str | None = None
    name_option: PBColumnNameOption | None = None
    type_option: PBColumnTypeOption | None = None

    def __str__(self) -> str:
        """Return string representation of the column definition.

        Returns:
            Column definition as a string
        """
        parts = [self.column_name, self.column_type.value]

        # Add length/precision/scale as needed
        if self.column_type in {ColumnType.CHAR, ColumnType.VARCHAR} and self.length:
            parts[1] += f"({self.length})"
        elif (
            self.column_type in {ColumnType.DECIMAL, ColumnType.NUMERIC}
            and self.precision
        ):
            if self.scale:
                parts[1] += f"({self.precision},{self.scale})"
            else:
                parts[1] += f"({self.precision})"

        # Add nullability
        if not self.is_nullable:
            parts.append("not null")

        # Add default value if present
        if self.default_value:
            parts.append(f"default {self.default_value}")

        # Add options
        if self.name_option:
            parts.append(str(self.name_option))

        if self.type_option:
            parts.append(str(self.type_option))

        return " ".join(parts)
