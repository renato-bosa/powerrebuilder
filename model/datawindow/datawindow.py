"""DataWindow classes for PowerBuilder.

This module contains classes for representing PowerBuilder DataWindow objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..utils.base import PBNode


# ─── DataWindow Core ────────────────────────────────────────────────────
@dataclass
class DataWindow(PBNode):
    """PowerBuilder DataWindow object."""

    name: str
    type: str  # grid, freeform, etc.
    table: Table
    columns: list[Column]
    compute_expressions: list[ComputeExpression] = field(default_factory=list)
    display_objects: list[DisplayObject] = field(default_factory=list)


@dataclass
class Table(PBNode):
    """DataWindow table definition."""

    name: str
    select_statement: str
    update_table: str | None = None
    key_columns: list[str] = field(default_factory=list)


# ─── Column Elements ────────────────────────────────────────────────────
@dataclass
class Column(PBNode):
    """DataWindow column."""

    name: str
    type: str
    display_name: str | None = None
    edit_style: str | None = None
    validation: str | None = None


@dataclass
class ComputeExpression(PBNode):
    """DataWindow compute expression."""

    name: str
    expression: str
    type: str
    format: str | None = None


# ─── Display Objects ────────────────────────────────────────────────────
@dataclass
class DisplayObject(PBNode):
    """Base class for DataWindow display objects."""

    position: tuple[int, int]
    size: tuple[int, int]
    type: str
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class Text(DisplayObject):
    """Static text object."""

    text: str = field(default="")
    alignment: str = field(default="left")
    type: str = field(default="text", init=False)


@dataclass
class Line(DisplayObject):
    """Line object."""

    pen_width: int = field(default=1)
    pen_style: str = field(default="solid")
    type: str = field(default="line", init=False)


@dataclass
class Rectangle(DisplayObject):
    """Rectangle object."""

    fill_pattern: str | None = None
    border_style: str = field(default="solid")
    type: str = field(default="rectangle", init=False)
