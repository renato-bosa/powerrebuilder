"""Shared types for the parse layer.

This module contains types that are shared between parsers and transformers
to prevent circular dependencies.
"""

from dataclasses import field
from typing import Any

from src.model.types.base import PBNode


class EnumeratedType(PBNode):
    """Represents an enumerated type."""

    values: list[str]

    def __init__(self, name: str, values: list[str] | None = None):
        super().__init__()
        self.name = name  # Use inherited property
        self.values = values or []


class StructureType(PBNode):
    """Represents a structure type."""

    fields: dict[str, Any]
    parent: str | None = None

    def __init__(self, name: str, fields: dict[str, Any] | None = None, parent: str | None = None):
        super().__init__()
        self.name = name  # Use inherited property
        self.fields = fields or {}
        self.parent = parent


__all__ = ["EnumeratedType", "StructureType"]
