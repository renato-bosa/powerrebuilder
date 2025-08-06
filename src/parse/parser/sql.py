"""PowerBuilder SQL Parser.

This module provides a parser for SQL queries embedded in PowerBuilder code.
It extends the basic PowerBuilder parser functionality with specific handling
for SQL statements, including advanced features like joins, subqueries, and CTEs.
"""

import logging
import re
from pathlib import Path
from typing import Any, ClassVar

from lark import Lark, Tree
from lark.exceptions import UnexpectedInput

from src.core.exceptions import ParseError
from src.model.optimization.sql_optimizer import SQLOptimizer
from src.parse.grammar.loader import GrammarManager
from src.parse.transformer.sql_transformer import SQLTransformer

from .base import PowerBuilderBaseParser

logger = logging.getLogger(__name__)


class SQLParser(PowerBuilderBaseParser):
    """Parser for SQL statements in PowerBuilder code.

    Handles parsing of SQL queries embedded in PowerBuilder scripts,
    including SELECT, INSERT, UPDATE, DELETE, and DDL statements.
    """

    # Parser configuration
    PARSER_TYPE: ClassVar[str] = "sql"
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {"sql", "srq"}

    # SQL statement patterns for detection
    SQL_PATTERNS = [
        r"^\s*SELECT\s+",
        r"^\s*INSERT\s+",
        r"^\s*UPDATE\s+",
        r"^\s*DELETE\s+",
        r"^\s*CREATE\s+",
        r"^\s*DROP\s+",
        r"^\s*ALTER\s+",
        r"^\s*WITH\s+",  # CTEs
    ]

    def __init__(self, base_path: Path | None = None, **parser_options: Any) -> None:
        """Initialize SQL parser.

        Args:
            base_path: Base path for resolving includes
            **parser_options: Additional parser options
        """
        # SQL parser uses basic lexer for better performance
        parser_options.setdefault("lexer", "basic")
        parser_options.setdefault("parser", "lalr")  # LALR is faster for SQL

        super().__init__(base_path, **parser_options)

        self._transformer: SQLTransformer | None = None
        self._optimizer: SQLOptimizer | None = None
        self._grammar_manager = GrammarManager()

    def _create_parser(self) -> Lark:
        """Create the SQL parser instance.

        Returns:
            Configured Lark parser for SQL

        Raises:
            ParseError: If parser creation fails
        """
        try:
            return self._grammar_manager.load_grammar(
                "sql", start="sql_statements", **self.parser_options
            )
        except (ImportError, AttributeError, ValueError) as e:
            raise ParseError(
                f"Failed to create SQL parser: {e}", error_code="PARSE_001"
            )

    def parse(
        self, source: str | Path, optimize: bool = False
    ) -> Tree | dict[str, Any] | list[Any]:
        """Parse SQL statements.

        Args:
            source: SQL source code or file path
            optimize: Whether to apply SQL optimization

        Returns:
            Parse tree or transformed AST

        Raises:
            ParseError: If parsing fails
        """
        # Validate and normalize source
        source_text, file_path = self._validate_source(source)
        self._current_file = file_path

        # Check if this looks like SQL
        if not self._is_sql(source_text):
            raise ParseError(
                "Source does not appear to contain SQL statements",
                filename=str(file_path) if file_path else None,
            )

        # Parse with error recovery
        tree = self.parse_with_error_recovery(
            source_text, str(file_path) if file_path else None
        )

        # Always transform to AST nodes (tests expect this)
        ast = self.transform_tree(tree, self.transformer)

        # Optionally optimize
        if optimize and self._optimizer:
            ast = self._optimizer.optimize(ast)

        return ast

    def _is_sql(self, source: str) -> bool:
        """Check if source contains SQL statements.

        Args:
            source: Source code to check

        Returns:
            True if source appears to be SQL
        """
        # Remove comments and normalize
        cleaned = self._remove_comments(source).strip()

        # Check for SQL patterns
        for pattern in self.SQL_PATTERNS:
            if re.match(pattern, cleaned, re.IGNORECASE | re.MULTILINE):
                return True

        return False

    def _remove_comments(self, source: str) -> str:
        """Remove SQL comments from source.

        Args:
            source: SQL source code

        Returns:
            Source with comments removed
        """
        # Remove single-line comments
        source = re.sub(r"--[^\n]*", "", source)

        # Remove multi-line comments
        return re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)

    def parse_query(self, query: str) -> Tree:
        """Parse a single SQL query.

        Args:
            query: SQL query string

        Returns:
            Parse tree for the query

        Raises:
            ParseError: If query parsing fails
        """
        # Use sql_statement as start rule for single queries
        parser = self._grammar_manager.load_grammar(
            "sql", start="sql_statement", **self.parser_options
        )

        try:
            return parser.parse(query)
        except UnexpectedInput as e:
            raise ParseError(
                f"Invalid SQL query: {e}",
                line=e.line,
                column=e.column,
                error_code="PARSE_002",
            )

    def extract_tables(self, tree: Tree) -> set[str]:
        """Extract table names from parsed SQL.

        Args:
            tree: Parsed SQL tree

        Returns:
            Set of table names referenced
        """
        tables = set()

        def visit(node) -> None:
            if isinstance(node, Tree):
                if node.data == "table_reference":
                    # Extract table name
                    for child in node.children:
                        if child.type == "IDENTIFIER":
                            tables.add(str(child))

                for child in node.children:
                    visit(child)

        visit(tree)
        return tables

    def extract_columns(self, tree: Tree) -> set[str]:
        """Extract column names from parsed SQL.

        Args:
            tree: Parsed SQL tree

        Returns:
            Set of column names referenced
        """
        columns = set()

        def visit(node) -> None:
            if isinstance(node, Tree):
                if node.data == "column_reference":
                    # Extract column name
                    for child in node.children:
                        if child.type == "IDENTIFIER":
                            columns.add(str(child))

                for child in node.children:
                    visit(child)

        visit(tree)
        return columns

    @property
    def transformer(self) -> SQLTransformer:
        """Get or create the SQL transformer.

        Returns:
            SQL transformer instance
        """
        if self._transformer is None:
            self._transformer = SQLTransformer()
        return self._transformer

    @transformer.setter
    def transformer(self, transformer: SQLTransformer) -> None:
        """Set a custom SQL transformer.

        Args:
            transformer: SQL transformer to use
        """
        self._transformer = transformer

    @property
    def optimizer(self) -> SQLOptimizer:
        """Get or create the SQL optimizer.

        Returns:
            SQL optimizer instance
        """
        if self._optimizer is None:
            self._optimizer = SQLOptimizer()
        return self._optimizer

    @optimizer.setter
    def optimizer(self, optimizer: SQLOptimizer) -> None:
        """Set a custom SQL optimizer.

        Args:
            optimizer: SQL optimizer to use
        """
        self._optimizer = optimizer
