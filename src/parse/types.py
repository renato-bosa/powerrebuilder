"""Shared types for the parse layer.

This module contains types that are shared between parsers and transformers
to prevent circular dependencies.
"""

from dataclasses import field
from typing import Any

from src.model.types.base import PBNode


class EnumeratedType(PBNode):
    """Represents an enumerated type."""

    name: str
    values: list[str] = field(default_factory=list)


class StructureType(PBNode):
    """Represents a structure type."""

    name: str
    fields: dict[str, Any] = field(default_factory=dict)
    parent: str | None = None


__all__ = ["EnumeratedType", "StructureType"]
