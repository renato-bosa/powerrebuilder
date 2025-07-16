"""Node kind enumeration for PowerBuilder AST nodes.

This module re-exports NodeKind from the base module to prevent circular dependencies.
"""

from src.base import NodeKind

__all__ = ['NodeKind']