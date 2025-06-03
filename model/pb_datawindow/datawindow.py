"""PowerBuilder DataWindow implementation.

This module contains classes for representing PowerBuilder DataWindow objects
that are used in the original PowerBuilder application, including advanced
features like nested reports, crosstabs, and graph objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..utils.base import PBNode
from .column import PBColumn
from .table import PBTable


class DataWindowType(Enum):
    """Types of DataWindows in PowerBuilder."""

    GRID = "grid"
    FREEFORM = "freeform"
    TABULAR = "tabular"
    CROSSTAB = "crosstab"
    GRAPH = "graph"
    COMPOSITE = "composite"
    NESTED = "nested"
    LABEL = "label"
    GROUP = "group"
    OLEDB = "oledb"
    XML = "xml"


@dataclass
class PBComputeExpression(PBNode):
    """PowerBuilder compute expression in a DataWindow.

    Attributes:
        name: Name of the compute expression
        expression: SQL or PowerBuilder expression
        return_type: Return type of the expression
        format: Optional display format
        visible: Whether the computed column is visible
    """

    name: str
    expression: str
    return_type: str
    format: str | None = None
    visible: bool = True


@dataclass
class PBDisplayObject(PBNode):
    """Base class for DataWindow display objects.

    Attributes:
        name: Name of the display object
        x: X position
        y: Y position
        width: Width
        height: Height
        visible: Whether the object is visible
        properties: Additional object properties
    """

    name: str
    x: int
    y: int
    width: int
    height: int
    visible: bool = True
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class PBDataWindow(PBNode):
    """PowerBuilder DataWindow base class.

    Attributes:
        name: Name of the DataWindow
        dw_type: Type of DataWindow
        title: Title of the DataWindow
        table: Table associated with the DataWindow
        columns: List of columns
        compute_expressions: List of compute expressions
        display_objects: List of display objects
        retrieve_sql: SQL statement for retrieving data
        update_sql: SQL statement for updating data
        insert_sql: SQL statement for inserting data
        delete_sql: SQL statement for deleting data
    """

    name: str
    dw_type: DataWindowType = field(default=DataWindowType.GRID)
    title: str | None = None
    table: PBTable | None = None
    columns: list[PBColumn] = field(default_factory=list)
    compute_expressions: list[PBComputeExpression] = field(default_factory=list)
    display_objects: list[PBDisplayObject] = field(default_factory=list)
    retrieve_sql: str | None = None
    update_sql: str | None = None
    insert_sql: str | None = None
    delete_sql: str | None = None

    def set_table(self, table: PBTable) -> None:
        """Set the table for this DataWindow.

        Args:
            table: The table to associate with this DataWindow
        """
        self.table = table

    def get_table(self) -> PBTable | None:
        """Get the table associated with this DataWindow.

        Returns:
            The associated table or None if not set
        """
        return self.table

    def add_column(self, column: PBColumn) -> None:
        """Add a column to this DataWindow.

        Args:
            column: The column to add
        """
        self.columns.append(column)

    def add_compute_expression(self, expr: PBComputeExpression) -> None:
        """Add a compute expression to this DataWindow.

        Args:
            expr: The compute expression to add
        """
        self.compute_expressions.append(expr)

    def add_display_object(self, obj: PBDisplayObject) -> None:
        """Add a display object to this DataWindow.

        Args:
            obj: The display object to add
        """
        self.display_objects.append(obj)

    def __str__(self) -> str:
        """Return string representation of the DataWindow.

        Returns:
            DataWindow definition as string
        """
        result = [f"datawindow {self.name}"]

        # Add table if present
        if self.table:
            result.append(str(self.table))

        # Add SQL statements
        if self.retrieve_sql:
            result.append(f"retrieve: {self.retrieve_sql}")
        if self.update_sql:
            result.append(f"update: {self.update_sql}")
        if self.insert_sql:
            result.append(f"insert: {self.insert_sql}")
        if self.delete_sql:
            result.append(f"delete: {self.delete_sql}")

        return "\n".join(result)


@dataclass
class PBNestedDataWindow(PBDataWindow):
    """PowerBuilder Nested DataWindow.

    A nested DataWindow is a DataWindow that contains another DataWindow,
    enabling master-detail relationships.

    Attributes:
        parent_columns: Columns in the parent DataWindow
        child_datawindow: The child DataWindow
        linkage_columns: Column mappings between parent and child
    """

    parent_columns: list[str] = field(default_factory=list)
    child_datawindow: PBDataWindow | None = None
    linkage_columns: dict[str, str] = field(
        default_factory=dict,
    )  # parent_col -> child_col

    def __post_init__(self):
        """Set the DataWindow type to nested after initialization."""
        self.dw_type = DataWindowType.NESTED


@dataclass
class PBCrosstabDataWindow(PBDataWindow):
    """PowerBuilder Crosstab DataWindow.

    A crosstab DataWindow displays data in a cross-tabulation format,
    with rows representing one dimension and columns another.

    Attributes:
        row_dimension: Column used for row dimension
        column_dimension: Column used for column dimension
        value_column: Column containing the values to aggregate
        aggregate_function: Aggregation function (SUM, AVG, COUNT, etc.)
        ranges: Optional ranges for column dimension values
    """

    row_dimension: str | None = None
    column_dimension: str | None = None
    value_column: str | None = None
    aggregate_function: str = "SUM"
    ranges: dict[str, tuple[Any, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """Set the DataWindow type to crosstab after initialization."""
        self.dw_type = DataWindowType.CROSSTAB


@dataclass
class PBGraphDataWindow(PBDataWindow):
    """PowerBuilder Graph DataWindow.

    A graph DataWindow displays data in various chart types.

    Attributes:
        graph_type: Type of graph (bar, line, pie, etc.)
        category_column: Column used for categories
        series_columns: Columns used for data series
        title: Graph title
        axis_labels: Labels for X and Y axes
        colors: Colors for series
    """

    graph_type: str = "bar"
    category_column: str | None = None
    series_columns: list[str] = field(default_factory=list)
    axis_labels: dict[str, str] = field(default_factory=dict)
    colors: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Set the DataWindow type to graph after initialization."""
        self.dw_type = DataWindowType.GRAPH
