"""SQL Parser for PowerBuilder embedded SQL.

This module provides SQL parsing functionality for PowerBuilder.
"""

from pathlib import Path
from typing import Any

from src.parse.parser.sql import SQLParser

# Create alias for backward compatibility
PowerBuilderSQLParser = SQLParser


def parse_sql(source: str | Path, optimize: bool = False) -> Any:
    """Parse SQL statements using the default SQL parser.

    Args:
        source: SQL source code or file path
        optimize: Whether to apply SQL optimization

    Returns:
        Parsed and transformed AST

    Raises:
        ParseError: If parsing fails
    """
    parser = SQLParser()
    return parser.parse(source, optimize=optimize)


__all__ = ["PowerBuilderSQLParser", "SQLParser", "parse_sql"]
