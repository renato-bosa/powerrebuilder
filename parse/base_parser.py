"""PowerBuilder base parser module.

This module provides the abstract base class for all PowerBuilder parsers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from lark import Lark, Tree
from lark.exceptions import UnexpectedInput

from .constants import FILE_EXTENSIONS, FileType


class PowerBuilderBaseParser(ABC):
    """Abstract base class for PowerBuilder parsers.

    This class defines the interface for all PowerBuilder parsers and provides
    common functionality such as file loading and error reporting.
    """

    # Map of file extensions to parser classes
    _parsers: ClassVar[dict[str, type[PowerBuilderBaseParser]]] = {}

    # Lark parser instance
    parser: Lark

    @classmethod
    def __init_subclass__(cls, **kwargs) -> None:
        """Register parser subclasses by their supported extensions."""
        super().__init_subclass__(**kwargs)
        for ext in cls.supported_extensions():
            cls._parsers[ext] = cls

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """Get supported file extensions.

        Returns:
            List of supported file extensions without the dot (e.g., 'srw', 'srd')
        """
        return []

    @classmethod
    def get_file_type(cls, extension: str) -> FileType:
        """Get the file type for an extension.

        Args:
            extension: File extension without the dot

        Returns:
            FileType enum value

        Raises:
            ValueError: If extension is not recognized
        """
        try:
            return FILE_EXTENSIONS[extension]
        except KeyError:
            return FileType.UNKNOWN

    @classmethod
    def get_parser_for_extension(cls, extension: str) -> type[PowerBuilderBaseParser]:
        """Get appropriate parser class for file extension.

        Args:
            extension: File extension without the dot

        Returns:
            Parser class

        Raises:
            ValueError: If no parser supports the extension
        """
        try:
            return cls._parsers[extension]
        except KeyError:
            raise ValueError(f"No parser available for extension: {extension}")

    @classmethod
    def parse_file(cls, file_path: str | Path) -> Tree:
        """Parse a PowerBuilder source file.

        Args:
            file_path: Path to source file

        Returns:
            Parsed AST

        Raises:
            ValueError: If parsing fails or no parser is available
        """
        path = Path(file_path)
        ext = path.suffix[1:].lower()  # Remove dot and normalize case
        parser_cls = cls.get_parser_for_extension(ext)
        parser = parser_cls(base_path=path.parent)

        # Parse the file and add metadata
        ast = parser.parse(path)
        if hasattr(ast, "meta"):
            ast.meta.file_name = path.name
            ast.meta.file_extension = ext
            ast.meta.file_type = cls.get_file_type(ext)

        return ast

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize parser.

        Args:
            base_path: Optional base path for resolving includes
        """
        self.base_path = base_path or Path.cwd()

    @abstractmethod
    def parse(self, source: str | Path) -> Tree:
        """Parse PowerBuilder source code.

        Args:
            source: Source code string or file path

        Returns:
            Parsed AST

        Raises:
            ValueError: If parsing fails
        """
        try:
            # Load source if path provided
            if isinstance(source, Path):
                with open(source, encoding="utf-8") as f:
                    source_text = f.read()
                file_path = source
            else:
                source_text = source
                file_path = None

            # Parse the source
            return self.parser.parse(source_text)

        except UnexpectedInput as e:
            # Enhance error reporting
            context = f"in file {file_path}" if file_path else "in source"

            raise ValueError(
                f"Syntax error {context} at line {e.line}, column {e.column}:\n"
                f"{e.get_context(source_text)}\n"
                f"{' ' * e.column}^\n"
                f"{str(e)}",
            ) from e

        except Exception as e:
            context = f" in file {file_path}" if file_path else ""

            raise ValueError(f"Error parsing source{context}: {str(e)}") from e
