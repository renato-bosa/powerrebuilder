"""Source code representation for PowerBuilder.

This module contains classes for handling PowerBuilder source files and code.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..utils.base import PBNode


# ─── Source Core ──────────────────────────────────────────────────────
@dataclass
class SourceFile(PBNode):
    """PowerBuilder source file."""

    path: str
    type: str  # window, datawindow, function, etc.
    content: str
    encoding: str = "utf-8"


@dataclass
class SourcePosition(PBNode):
    """Source code position."""

    line: int
    column: int
    offset: int


@dataclass
class SourceRange(PBNode):
    """Source code range."""

    start: SourcePosition
    end: SourcePosition
    file: SourceFile | None = None


# ─── Source Elements ────────────────────────────────────────────────────
@dataclass
class SourceComment(PBNode):
    """Source code comment."""

    text: str
    range: SourceRange
    is_multiline: bool = False


@dataclass
class SourceDirective(PBNode):
    """Source code directive."""

    type: str  # include, ifdef, etc.
    value: str
    range: SourceRange


@dataclass
class SourceSection(PBNode):
    """Source code section."""

    type: str  # forward, variables, etc.
    content: list[PBNode]
    range: SourceRange


# ─── File Organization ──────────────────────────────────────────────────
@dataclass
class FileHeader(PBNode):
    """PowerBuilder file header."""

    version: str
    export_info: dict[str, str]
    range: SourceRange


@dataclass
class FileFooter(PBNode):
    """PowerBuilder file footer."""

    checksum: str | None = None
    range: SourceRange | None = None
