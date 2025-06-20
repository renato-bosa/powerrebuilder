"""I/O operation AST nodes for PowerBuilder.

This module contains AST nodes for file and I/O operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from model.utils.base import PBNode
from .ast_nodes import Expression, Statement


class FileMode(Enum):
    """File operation modes."""
    READ = "r"
    WRITE = "w"
    APPEND = "a"
    READ_WRITE = "r+"
    WRITE_READ = "w+"
    APPEND_READ = "a+"
    BINARY_READ = "rb"
    BINARY_WRITE = "wb"
    BINARY_APPEND = "ab"
    # Keep old names for compatibility
    READWRITE = "r+"


@dataclass
class FileOperation(Statement):
    """Base class for file operations."""
    
    file_path: Optional[Expression] = None
    operation_type: str = "unknown"
    type: Optional[str] = None  # Operation type (OPEN, READ, WRITE, etc.)
    mode: Optional[FileMode] = None  # File mode for OPEN operations
    max_bytes: Optional[int] = None  # Max bytes for READ operations
    content: Optional[Expression] = None  # Content for WRITE operations
    
    def accept(self, visitor):
        """Accept a visitor."""
        return visitor.visit_file_operation(self)


@dataclass
class OpenFile(FileOperation):
    """Open file operation."""
    
    file_handle: Optional[str] = None
    
    def __post_init__(self):
        self.type = "OPEN"


@dataclass
class CloseFile(FileOperation):
    """Close file operation."""
    
    file_handle: Optional[str] = None
    
    def __post_init__(self):
        self.type = "CLOSE"


@dataclass
class ReadFile(FileOperation):
    """Read file operation."""
    
    file_handle: Optional[str] = None
    variable: Optional[str] = None
    
    def __post_init__(self):
        self.type = "READ"


@dataclass
class WriteFile(FileOperation):
    """Write file operation."""
    
    file_handle: Optional[str] = None
    
    def __post_init__(self):
        self.type = "WRITE"


class FileManager:
    """Manages file handles and operations."""
    
    def __init__(self):
        self._handles: Dict[str, FileOperation] = {}
    
    def open_file(self, handle: str, operation: OpenFile) -> None:
        """Register an open file."""
        self._handles[handle] = operation
    
    def close_file(self, handle: str) -> None:
        """Close a file handle."""
        if handle in self._handles:
            del self._handles[handle]
    
    def is_open(self, handle: str) -> bool:
        """Check if a file handle is open."""
        return handle in self._handles