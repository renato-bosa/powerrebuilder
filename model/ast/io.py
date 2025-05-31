"""File I/O related AST nodes for PowerBuilder and Pseudocode.

This module contains AST nodes for representing file operations, including:
- File opening/closing
- File reading/writing
- File mode handling
- Error handling
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..utils.base import PBNode


class FileMode(Enum):
    """File access modes."""

    READ = "r"
    WRITE = "w"
    APPEND = "a"
    READ_WRITE = "r+"
    WRITE_READ = "w+"
    APPEND_READ = "a+"
    BINARY_READ = "rb"
    BINARY_WRITE = "wb"
    BINARY_APPEND = "ab"


@dataclass
class FileOperation(PBNode):
    """Base class for file operations."""

    file_path: str
    mode: FileMode | None = None
    operation_type: str = "GENERIC"  # Internal use
    content: Any = None
    max_bytes: int | None = None

    def __init__(
        self,
        file_path: str,
        mode: FileMode | None = None,
        operation_type: str = "GENERIC",
        content: Any = None,
        max_bytes: int | None = None,
        **kwargs,
    ) -> None:
        """Initialize a file operation.

        Handles 'type' parameter by aliasing it to operation_type for compatibility with tests.

        Args:
            file_path: Path to the file
            mode: File mode (read, write, etc.)
            operation_type: Type of operation (OPEN, READ, WRITE, CLOSE)
            content: Content to write (for write operations)
            max_bytes: Maximum bytes to read (for read operations)
            **kwargs: Additional arguments for compatibility
        """
        self.file_path = file_path
        self.mode = mode
        # Allow 'type' as an alias for 'operation_type' for compatibility
        self.operation_type = kwargs.get("type", operation_type)
        self.content = content
        self.max_bytes = max_bytes

    @property
    def type(self) -> str:
        """Getter for 'type' to maintain compatibility with code generator.

        Returns:
            str: The operation_type of the file operation
        """
        return self.operation_type

    def validate(self) -> bool:
        """Validate file operation."""
        return self.file_path


@dataclass
class OpenFile(PBNode):
    """File open operation node."""

    file_path: str
    mode: FileMode | None = None

    def validate(self) -> bool:
        """Validate file open operation."""
        if not self.file_path:
            return False
        return self.mode


@dataclass
class CloseFile(PBNode):
    """File close operation node."""

    file_path: str
    mode: FileMode | None = None

    def validate(self) -> bool:
        """Validate file close operation."""
        return self.file_path


@dataclass
class ReadFile(PBNode):
    """File read operation node."""

    file_path: str
    max_bytes: int | None = None
    mode: FileMode | None = None
    encoding: str = "utf-8"

    def validate(self) -> bool:
        """Validate file read operation."""
        if not self.file_path:
            return False
        return not (self.max_bytes is not None and self.max_bytes <= 0)


@dataclass
class WriteFile(PBNode):
    """File write operation node."""

    file_path: str
    content: Any
    mode: FileMode | None = None
    append: bool = False
    encoding: str = "utf-8"

    def validate(self) -> bool:
        """Validate file write operation."""
        if not self.file_path:
            return False
        return self.content is not None


@dataclass
class FileManager(PBNode):
    """File manager for tracking open files."""

    open_files: dict[str, FileMode] = field(default_factory=dict)

    def is_file_open(self, file_path: str) -> bool:
        """Check if a file is open."""
        return file_path in self.open_files

    def get_file_mode(self, file_path: str) -> FileMode | None:
        """Get mode of an open file."""
        return self.open_files.get(file_path)

    def open_file(self, file_path: str, mode: FileMode) -> bool:
        """Track file opening."""
        if self.is_file_open(file_path):
            return False
        self.open_files[file_path] = mode
        return True

    def close_file(self, file_path: str) -> bool:
        """Track file closing."""
        if not self.is_file_open(file_path):
            return False
        del self.open_files[file_path]
        return True

    def validate_operation(self, operation: Any) -> bool:
        """Validate a file operation."""
        if isinstance(operation, OpenFile):
            return not self.is_file_open(operation.file_path)

        if not self.is_file_open(operation.file_path):
            return False

        if isinstance(operation, ReadFile):
            mode = self.get_file_mode(operation.file_path)
            return mode in {
                FileMode.READ,
                FileMode.READ_WRITE,
                FileMode.WRITE_READ,
                FileMode.APPEND_READ,
                FileMode.BINARY_READ,
            }

        if isinstance(operation, WriteFile):
            mode = self.get_file_mode(operation.file_path)
            return mode in {
                FileMode.WRITE,
                FileMode.APPEND,
                FileMode.READ_WRITE,
                FileMode.WRITE_READ,
                FileMode.APPEND_READ,
                FileMode.BINARY_WRITE,
                FileMode.BINARY_APPEND,
            }

        if isinstance(operation, CloseFile):
            return True

        if isinstance(operation, FileOperation):
            if operation.operation_type == "OPEN":
                return not self.is_file_open(operation.file_path)
            if operation.operation_type == "READ":
                mode = self.get_file_mode(operation.file_path)
                return mode in {
                    FileMode.READ,
                    FileMode.READ_WRITE,
                    FileMode.WRITE_READ,
                    FileMode.APPEND_READ,
                    FileMode.BINARY_READ,
                }
            if operation.operation_type == "WRITE":
                mode = self.get_file_mode(operation.file_path)
                return mode in {
                    FileMode.WRITE,
                    FileMode.APPEND,
                    FileMode.READ_WRITE,
                    FileMode.WRITE_READ,
                    FileMode.APPEND_READ,
                    FileMode.BINARY_WRITE,
                    FileMode.BINARY_APPEND,
                }
            if operation.operation_type == "CLOSE":
                return True

        return False
