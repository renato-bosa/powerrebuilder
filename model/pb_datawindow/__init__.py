"""PowerBuilder DataWindow implementation.

This module contains classes for representing PowerBuilder DataWindow objects
that are used in the original PowerBuilder application.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..utils.base import PBNode
from .column import ColumnType, PBColumn, PBColumnNameOption, PBColumnTypeOption
from .datawindow import (
    DataWindowType,
    PBComputeExpression,
    PBCrosstabDataWindow,
    PBDataWindow,
    PBDisplayObject,
    PBGraphDataWindow,
    PBNestedDataWindow,
)
from .table import PBTable


# Node classes for AST
@dataclass
class PBColumnDefinitionNode(PBNode):
    """Column definition node."""

    options: Any = None


@dataclass
class PBColumnNode(PBNode):
    """Column node."""

    column_definition: Any = None


@dataclass
class PBColumnNameOptionNode(PBNode):
    """Column name option node."""

    expression: Any = None


@dataclass
class PBColumnTypeOptionNode(PBNode):
    """Column type option node."""

    expression: Any = None


@dataclass
class PBDataWindowFileNode(PBNode):
    """DataWindow file node."""

    file_statements: list[Any] = None


@dataclass
class PBDataWindowNode(PBNode):
    """DataWindow node."""

    parameters: Any = None


__all__ = [
    "ColumnType",
    "PBColumn",
    "PBColumnNameOption",
    "PBColumnTypeOption",
    "PBTable",
    "DataWindowType",
    "PBComputeExpression",
    "PBDisplayObject",
    "PBDataWindow",
    "PBNestedDataWindow",
    "PBCrosstabDataWindow",
    "PBGraphDataWindow",
    # Node classes
    "PBColumnDefinitionNode",
    "PBColumnNode",
    "PBColumnNameOptionNode",
    "PBColumnTypeOptionNode",
    "PBDataWindowFileNode",
    "PBDataWindowNode",
]
