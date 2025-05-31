"""Library and behavioral classes for PowerBuilder.

This module contains classes for handling PowerBuilder libraries and behavioral elements.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..utils.base import PBNode


# ─── Library Core ──────────────────────────────────────────────────────
@dataclass
class Library(PBNode):
    """PowerBuilder library object."""

    name: str
    path: str
    is_system: bool = False
    exports: list[Export] = field(default_factory=list)
    imports: list[Import] = field(default_factory=list)


@dataclass
class Export(PBNode):
    """Library export definition."""

    object_name: str
    to_library: str | None = None


@dataclass
class Import(PBNode):
    """Library import definition."""

    from_library: str
    object_name: str


@dataclass
class LibraryObject(PBNode):
    """Library object definition."""

    name: str = ""
    object_type: str = ""  # window, menu, userobject, datawindow, etc.
    source_file: str | None = field(default=None)


# ─── Behavioral Elements ──────────────────────────────────────────────────
@dataclass
class BehavioralOption(PBNode):
    """Behavioral option (library or alias)."""

    type: str  # library, alias
    value: str


@dataclass
class Behavioral(PBNode):
    """Base class for behavioral elements."""

    name: str
    access_modifier: str = field(default="public")
    is_shared: bool = field(default=False)
    options: list[BehavioralOption] = field(default_factory=list)


@dataclass
class BehavioralLibrary(PBNode):
    """Library-based behavioral element."""

    name: str
    library_name: str
    entry_point: str
    access_modifier: str = field(default="public")
    is_shared: bool = field(default=False)
    options: list[BehavioralOption] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)


@dataclass
class BehavioralAlias(PBNode):
    """Alias-based behavioral element."""

    name: str
    alias_name: str
    target_name: str
    access_modifier: str = field(default="public")
    is_shared: bool = field(default=False)
    options: list[BehavioralOption] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)


# ─── Parameter Handling ──────────────────────────────────────────────────
@dataclass
class Parameter(PBNode):
    """Behavioral element parameter."""

    name: str
    type: str
    direction: str = field(default="in")  # in, out, ref
    default_value: str | None = field(default=None)
