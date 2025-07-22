"""Consolidated AST node definitions.

This module combines the base AST node definitions from nodes.py and control.py,
eliminating duplicate definitions and providing a clear hierarchy.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from ..node_kind import NodeKind
from src.model.types.base import SourceAnchor
# from .types import Type  # TODO: Resolve this import

# Minimal base classes to satisfy imports
@dataclass
class Expression(ABC):
    """Base class for expressions."""
    pass

@dataclass
class Statement(ABC):
    """Base class for statements."""
    pass
