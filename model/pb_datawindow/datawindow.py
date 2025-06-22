"""DataWindow models for PowerBuilder.

This module contains models for representing DataWindow objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from model.utils.base import PBNode
from .column import PBColumn


class DataWindowType(Enum):
    """Types of DataWindow objects."""
    
    GRID = auto()
    FREEFORM = auto()
    TABULAR = auto()
    GROUP = auto()
    CROSSTAB = auto()
    GRAPH = auto()
    COMPOSITE = auto()
    RICHTEXT = auto()
    OLE = auto()
    TREEVIEW = auto()
    NESTED = auto()


class PresentationStyle(Enum):
    """DataWindow presentation styles."""
    
    GRID = auto()
    FREEFORM = auto()
    TABULAR = auto()
    GROUP = auto()
    CROSSTAB = auto()
    GRAPH = auto()
    COMPOSITE = auto()
    RICHTEXT = auto()
    OLE = auto()
    TREEVIEW = auto()


@dataclass
class PBDataWindowBand(PBNode):
    """DataWindow band."""
    
    band_type: str  # header, detail, footer, etc.
    height: int = 0
    color: str | None = None
    visible: bool = True
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class PBDataWindowObject(PBNode):
    """DataWindow object (control within DataWindow)."""
    
    name: str
    object_type: str  # text, column, compute, etc.
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    band: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class PBDataWindow(PBNode):
    """Represents a PowerBuilder DataWindow."""
    
    name: str
    datawindow_type: DataWindowType = DataWindowType.GRID
    presentation_style: PresentationStyle = PresentationStyle.GRID
    sql_select: str | None = None
    table_name: str | None = None
    columns: list[PBColumn] = field(default_factory=list)
    bands: list[PBDataWindowBand] = field(default_factory=list)
    objects: list[PBDataWindowObject] = field(default_factory=list)
    retrieve_args: list[str] = field(default_factory=list)
    sort_order: str | None = None
    filter: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    
    def add_column(self, column: PBColumn) -> None:

    
        
    
        """Add a column to the DataWindow."""
        self.columns.append(column)
    
    def add_band(self, band: PBDataWindowBand) -> None:

    
        
    
        """Add a band to the DataWindow."""
        self.bands.append(band)
    
    def add_object(self, obj: PBDataWindowObject) -> None:

    
        
    
        """Add an object to the DataWindow."""
        self.objects.append(obj)
    
    def get_column(self, name: str) -> PBColumn | None:

    
        
    
        """Get a column by name."""
        for column in self.columns:
            if column.name == name:
                return column
        return None


@dataclass
class PBComputeExpression(PBNode):
    """Compute expression in a DataWindow."""
    
    name: str
    expression: str
    band: str | None = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    format: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class PBDisplayObject(PBNode):
    """Display object in a DataWindow."""
    
    name: str
    object_type: str
    band: str | None = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class PBGraphDataWindow(PBDataWindow):
    """Graph DataWindow."""
    
    graph_type: str = "column"
    series: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    values: list[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        
    
        self.datawindow_type = DataWindowType.GRAPH
        self.presentation_style = PresentationStyle.GRAPH


@dataclass
class PBCrosstabDataWindow(PBDataWindow):
    """Crosstab DataWindow."""
    
    rows: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    values: list[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        
    
        self.datawindow_type = DataWindowType.CROSSTAB
        self.presentation_style = PresentationStyle.CROSSTAB


@dataclass
class PBNestedDataWindow(PBDataWindow):
    """Nested DataWindow."""
    
    parent_datawindow: str | None = None
    link_columns: dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        
    
        self.datawindow_type = DataWindowType.NESTED