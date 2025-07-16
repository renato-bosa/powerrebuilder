"""SQL Parser for PowerBuilder embedded SQL.

This module provides SQL parsing functionality for PowerBuilder.
"""

from src.parse.parser.sql import SQLParser

# Create alias for backward compatibility
PowerBuilderSQLParser = SQLParser

__all__ = ['SQLParser', 'PowerBuilderSQLParser']