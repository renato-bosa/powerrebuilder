"""PowerBuilder Pseudocode Parser.

This module provides a parser for PowerBuilder pseudocode syntax.
It extends the basic PowerBuilder parser functionality with specific handling
for pseudocode statements and expressions.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from lark import Lark, Tree
from lark.exceptions import UnexpectedInput

from .base_parser import PowerBuilderBaseParser
from .pseudocode_transformer import PseudocodeToPython
from .utils.grammar_loader import load_grammar

logger = logging.getLogger(__name__)


class PowerBuilderPseudocodeParser(PowerBuilderBaseParser):
    """Parser for PowerBuilder pseudocode syntax."""

    def __init__(self) -> None:
        """Initialize the pseudocode parser."""
        self.parser = load_grammar("pseudocode", start="start")
        self.transformer = PseudocodeToPython()

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """Get supported file extensions.

        Returns:
            List of supported file extensions
        """
        # Pseudocode typically doesn't have a specific extension
        # It's often embedded in documentation or test files
        return []

    def parse(self, code: str, start: str = "start") -> Tree:
        """Parse pseudocode into an AST.

        Args:
            code: Pseudocode string to parse
            start: Start rule for the parser (default: "start")

        Returns:
            Lark Tree representing the parsed pseudocode

        Raises:
            UnexpectedInput: If the code cannot be parsed
        """
        try:
            tree = self.parser.parse(code, start=start)
            return tree
        except UnexpectedInput as e:
            logger.error("Failed to parse pseudocode: %s", e)
            raise

    def parse_and_transform(self, code: str) -> str:
        """Parse pseudocode and transform to Python.

        Args:
            code: Pseudocode string to parse and transform

        Returns:
            Python code string

        Raises:
            UnexpectedInput: If the code cannot be parsed
        """
        tree = self.parse(code)
        python_code = self.transformer.transform(tree)
        return python_code

    def parse_file(self, file_path: Path) -> Tree:
        """Parse a file containing pseudocode.

        Args:
            file_path: Path to the file to parse

        Returns:
            Lark Tree representing the parsed pseudocode

        Raises:
            FileNotFoundError: If the file doesn't exist
            UnexpectedInput: If the code cannot be parsed
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        code = file_path.read_text(encoding="utf-8")
        return self.parse(code)

    def validate(self, code: str) -> bool:
        """Validate pseudocode syntax.

        Args:
            code: Pseudocode string to validate

        Returns:
            True if the code is valid, False otherwise
        """
        try:
            self.parse(code)
            return True
        except UnexpectedInput:
            return False

    def get_ast_summary(self, tree: Tree) -> dict[str, Any]:
        """Get a summary of the parsed AST.

        Args:
            tree: Parsed Lark Tree

        Returns:
            Dictionary containing AST summary information
        """
        summary = {
            "node_count": 0,
            "statement_types": {},
            "identifiers": set(),
            "literals": set(),
        }

        def visit_node(node: Tree) -> None:
            """Visit nodes recursively to build summary."""
            summary["node_count"] += 1
            
            if hasattr(node, "data"):
                # Track statement types
                if node.data.endswith("_stmt"):
                    stmt_type = node.data
                    summary["statement_types"][stmt_type] = (
                        summary["statement_types"].get(stmt_type, 0) + 1
                    )
                
                # Collect identifiers and literals
                for child in node.children:
                    if hasattr(child, "type"):
                        if child.type == "IDENTIFIER":
                            summary["identifiers"].add(str(child))
                        elif child.type in ["STRING", "NUMBER", "REAL_NUMBER"]:
                            summary["literals"].add(str(child))
                    elif hasattr(child, "data"):
                        visit_node(child)

        if hasattr(tree, "data"):
            visit_node(tree)

        # Convert sets to lists for JSON serialization
        summary["identifiers"] = list(summary["identifiers"])
        summary["literals"] = list(summary["literals"])

        return summary