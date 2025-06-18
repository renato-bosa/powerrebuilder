"""I/O operation AST nodes for PowerBuilder.

This module contains AST nodes for file and I/O operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from model.utils.base import PBNode
from .ast_nodes import Expression, Statement


@dataclass
class FileOperation(Statement):
    """Base class for file operations."""
    
    file_path: Optional[Expression] = None
    operation_type: str = "unknown"
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_file_operation(self)