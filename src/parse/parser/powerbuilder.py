"""Unified PowerBuilder parser module.

This module merges functionality from:
- parse/parsers/parser.py - Unified parser with specialized parser selection
- parse/parsers/enhanced_parser.py - Enhanced parser with error recovery

Provides a unified parser that can handle all PowerBuilder file types
by delegating to specialized parsers as needed, with robust error recovery.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from lark import Token, Transformer, Tree
from lark.exceptions import UnexpectedInput

from src.parse.grammar.loader import GrammarManager

from .base import PowerBuilderBaseParser
from .specialized.pseudocode import PowerBuilderPseudocodeParser
from .specialized.transactions import TransactionParser
from .specialized.types import TypeParser
from .sql import SQLParser

logger = logging.getLogger(__name__)


class ErrorRecoveryTransformer(Transformer):
    """Transformer that helps recover from parse errors."""

    def __init__(self) -> None:
        super().__init__()
        self.errors = []

    def __default__(self, data, children, meta):
        """Default handler for unrecognized rules."""
        # Log the error but continue
        self.errors.append({"type": "unrecognized_rule", "data": data, "meta": meta})
        # Return a placeholder node
        return Tree(data, children, meta)

    def error_recovery(self, items) -> None:
        """Handle error recovery rules."""
        logger.debug("Recovered from error: %s", items)
        return Tree("recovered_error", items)


# ============================================================================
# Enhanced PowerBuilder Parser (from enhanced_parser.py)
# ============================================================================


class EnhancedPowerBuilderParser(PowerBuilderBaseParser):
    """Enhanced parser with error recovery capabilities."""

    def __init__(
        self, base_path: Path | None = None, enable_error_recovery: bool = True
    ) -> None:
        """Initialize enhanced parser with error recovery."""
        super().__init__(base_path)
        self.enable_error_recovery = enable_error_recovery

        # Load enhanced grammar with error recovery rules
        self._load_enhanced_grammar()

        # Create parser with error recovery options

        # Get grammar directory for imports
        from pathlib import Path

        Path(__file__).parent.parent / "grammar" / "definitions"

        # Always use GrammarManager for consistent behavior

        manager = GrammarManager()

        if enable_error_recovery:
            # Use earley parser for better error recovery
            self.parser = manager.load_grammar("powerbuilder", parser="earley")
        else:
            # Use earley parser (LALR has conflicts with this grammar)
            self.parser = manager.load_grammar("powerbuilder", parser="earley")

        self.transformer = ErrorRecoveryTransformer()
        self.parse_errors = []

    def _load_enhanced_grammar(self) -> str:
        """Load and enhance the PowerBuilder grammar with error recovery rules."""
        # This method is not needed anymore since we use GrammarManager
        # Return empty string as placeholder
        return ""

    def parse(self, source: str | Path) -> Tree:
        """Parse PowerBuilder source with error recovery.

        Args:
            source: Source code string or file path

        Returns:
            Parsed AST with error nodes for unrecoverable sections

        Raises:
            ParseError: If parsing fails without recovery
        """
        # Read source if path provided
        if isinstance(source, Path):
            with source.open(encoding="utf-8") as f:
                source_text = f.read()
        else:
            source_text = str(source)

        # Clear previous errors
        self.parse_errors.clear()
        self.transformer.errors.clear()

        try:
            # Attempt normal parsing
            return self.parser.parse(source_text)

        except UnexpectedInput as e:
            if not self.enable_error_recovery:
                # Re-raise if error recovery is disabled
                raise

            # Try to recover from the error
            logger.warning("Parse error at line %s, col %s: %s", e.line, e.column, e)

            # Store the error
            self.parse_errors.append(
                {
                    "line": e.line,
                    "column": e.column,
                    "message": str(e),
                    "expected": getattr(e, "expected", None),
                }
            )

            # Attempt partial parsing with recovery
            return self._parse_with_recovery(source_text, e)

    def _parse_with_recovery(self, source: str, error: UnexpectedInput) -> Tree:
        """Parse with error recovery strategies.

        Args:
            source: Source code
            error: The parsing error encountered

        Returns:
            Partially parsed tree with error nodes
        """
        logger.info("Attempting error recovery parsing")

        # Strategy 1: Try to skip problematic lines
        lines = source.splitlines()
        error_line = error.line - 1  # Convert to 0-based

        if error_line < len(lines):
            # Comment out the problematic line
            lines[error_line] = f"// ERROR: {lines[error_line]}"
            modified_source = "\n".join(lines)

            try:
                tree = self.parser.parse(modified_source)
                logger.info("Successfully recovered by commenting problematic line")
                return tree
            except UnexpectedInput:
                pass

        # Strategy 2: Try to parse up to the error point
        try:
            partial_source = "\n".join(lines[:error_line])
            if partial_source.strip():
                tree = self.parser.parse(partial_source)
                logger.info("Successfully parsed up to line %s", error_line)
                return tree
        except UnexpectedInput:
            pass

        # Strategy 3: Create minimal tree with error node
        logger.warning("Could not recover, creating minimal error tree")
        return Tree("error", [Token("ERROR", source)])

    def get_parse_errors(self) -> list[dict[str, Any]]:
        """Get list of parse errors encountered.

        Returns:
            List of error dictionaries with line, column, message, and expected tokens
        """
        all_errors = self.parse_errors.copy()
        all_errors.extend(self.transformer.errors)
        return all_errors

    def has_errors(self) -> bool:
        """Check if any parse errors were encountered.

        Returns:
            True if errors exist, False otherwise
        """
        return bool(self.parse_errors or self.transformer.errors)

    def parse_with_fallback(self, source: str | Path) -> Tree:
        """Parse with multiple fallback strategies.

        Args:
            source: Source code or file path

        Returns:
            Parsed tree (possibly partial)

        Raises:
            ParseError: If all parsing strategies fail
        """
        # First try normal parsing
        try:
            return self.parse(source)
        except Exception as e:
            logger.warning("Normal parsing failed: %s", e)

        # Read source if needed
        if isinstance(source, Path):
            with source.open(encoding="utf-8") as f:
                source_text = f.read()
        else:
            source_text = str(source)

        # Try with preprocessed source
        try:
            from src.parse.preprocessor.preprocessor import PowerBuilderPreprocessor

            preprocessor = PowerBuilderPreprocessor()
            processed = preprocessor.preprocess(source_text)
            tree = self.parser.parse(processed)
            logger.info("Successfully parsed with preprocessing")
            return tree
        except Exception as e:
            logger.warning("Preprocessed parsing failed: %s", e)

        # Try with simplified grammar
        try:
            # Use basic parser without complex rules
            simplified_parser = self._create_simplified_parser()
            tree = simplified_parser.parse(source_text)
            logger.info("Successfully parsed with simplified grammar")
            return tree
        except Exception as e:
            logger.warning("Simplified parsing failed: %s", e)

        # Final fallback: create error tree
        logger.error("All parsing strategies failed")
        return Tree("parse_failed", [Token("SOURCE", source_text)])

    def _create_simplified_parser(self):
        """Create a simplified parser for fallback parsing.

        Returns:
            Simplified Lark parser instance
        """
        # This is a placeholder - in a real implementation,
        # this would load a simplified grammar

        manager = GrammarManager()
        # For now, just return the regular parser
        # In future, could have a 'powerbuilder_simple' grammar
        return manager.load_grammar("powerbuilder", parser="earley")


# ============================================================================
# Unified PowerBuilder Parser (from parser.py)
# ============================================================================


class UnifiedPowerBuilderParser:
    """Unified parser for all PowerBuilder file types.

    This parser automatically selects the appropriate specialized parser
    based on file extension or content type.
    """

    # Map of file extensions to specialized parsers
    EXTENSION_PARSERS: dict[str, type[PowerBuilderBaseParser]] = {
        # SQL files
        "sql": SQLParser,
        "srq": SQLParser,
        # Transaction files
        "trn": TransactionParser,
        # Type definition files
        "srd": TypeParser,
        "typ": TypeParser,
        # Standard PowerBuilder source files
        "sra": EnhancedPowerBuilderParser,
        "srw": EnhancedPowerBuilderParser,
        "sru": EnhancedPowerBuilderParser,
        "srf": EnhancedPowerBuilderParser,
        "srm": EnhancedPowerBuilderParser,
        "srs": EnhancedPowerBuilderParser,
    }

    # Content type detection patterns
    CONTENT_PATTERNS = {
        "SELECT": SQLParser,
        "INSERT": SQLParser,
        "UPDATE": SQLParser,
        "DELETE": SQLParser,
        "BEGIN TRANSACTION": TransactionParser,
        "COMMIT": TransactionParser,
        "ROLLBACK": TransactionParser,
        "type ": TypeParser,
        "global type": TypeParser,
    }

    def __init__(
        self, base_path: Path | None = None, enable_error_recovery: bool = True
    ) -> None:
        """Initialize unified parser.

        Args:
            base_path: Base path for resolving includes
            enable_error_recovery: Whether to enable error recovery
        """
        self.base_path = base_path or Path.cwd()
        self.enable_error_recovery = enable_error_recovery
        self._parser_cache: dict[
            type[PowerBuilderBaseParser], PowerBuilderBaseParser
        ] = {}

    def parse(
        self, source: str | Path, parser_type: str | None = None
    ) -> Tree | dict[str, Any]:
        """Parse PowerBuilder source code.

        Args:
            source: Source code string or file path
            parser_type: Optional parser type override ('sql', 'transaction', 'type', 'enhanced')

        Returns:
            Parse tree or dictionary representation

        Raises:
            ValueError: If appropriate parser cannot be determined
            UnexpectedInput: If parsing fails
        """
        # Determine source content and path
        if isinstance(source, Path):
            source_path = source
            with Path(source).open(encoding="utf-8") as f:
                source_text = f.read()
        else:
            source_path = None
            source_text = source

        # Determine which parser to use
        if parser_type:
            parser_class = self._get_parser_by_type(parser_type)
        elif source_path:
            parser_class = self._get_parser_by_extension(source_path.suffix.lstrip("."))
        else:
            parser_class = self._get_parser_by_content(source_text)

        if not parser_class:
            raise ValueError("Could not determine appropriate parser for source")

        # Get or create parser instance
        parser = self._get_parser_instance(parser_class)

        # Parse the source
        try:
            result = parser.parse(source_text)
            logger.info("Successfully parsed with %s", parser_class.__name__)
            return result
        except Exception as e:
            logger.error("Failed to parse with %s: %s", parser_class.__name__, e)
            if self.enable_error_recovery and hasattr(parser, "parse_with_fallback"):
                # Try fallback parsing for enhanced parser
                return parser.parse_with_fallback(source_text)
            raise

    def _get_parser_by_type(
        self, parser_type: str
    ) -> type[PowerBuilderBaseParser] | None:
        """Get parser class by explicit type.

        Args:
            parser_type: Parser type name

        Returns:
            Parser class or None
        """
        type_map = {
            "sql": SQLParser,
            "transaction": TransactionParser,
            "type": TypeParser,
            "pseudocode": PowerBuilderPseudocodeParser,
            "enhanced": EnhancedPowerBuilderParser,
        }
        return type_map.get(parser_type.lower())

    def _get_parser_by_extension(
        self, extension: str
    ) -> type[PowerBuilderBaseParser] | None:
        """Get parser class by file extension.

        Args:
            extension: File extension without dot

        Returns:
            Parser class or None
        """
        return self.EXTENSION_PARSERS.get(extension.lower())

    def _get_parser_by_content(
        self, content: str
    ) -> type[PowerBuilderBaseParser] | None:
        """Get parser class by analyzing content.

        Args:
            content: Source code content

        Returns:
            Parser class or None
        """
        # Check first few lines for patterns
        lines = content.strip().split("\n", 5)
        header = " ".join(lines[:5]).upper()

        for pattern, parser_class in self.CONTENT_PATTERNS.items():
            if pattern in header:
                return parser_class

        # Default to enhanced parser
        return EnhancedPowerBuilderParser

    def _get_parser_instance(
        self, parser_class: type[PowerBuilderBaseParser]
    ) -> PowerBuilderBaseParser:
        """Get or create parser instance.

        Args:
            parser_class: Parser class to instantiate

        Returns:
            Parser instance
        """
        if parser_class not in self._parser_cache:
            if parser_class == EnhancedPowerBuilderParser:
                instance = parser_class(
                    self.base_path, enable_error_recovery=self.enable_error_recovery
                )
            else:
                instance = parser_class(self.base_path)
            self._parser_cache[parser_class] = instance

        return self._parser_cache[parser_class]

    def clear_cache(self) -> None:
        """Clear parser instance cache."""
        self._parser_cache.clear()

    @property
    def supported_extensions(self) -> list[str]:
        """Get list of supported file extensions.

        Returns:
            List of file extensions
        """
        return list(self.EXTENSION_PARSERS.keys())

    def can_parse(self, source: str | Path) -> bool:
        """Check if the parser can handle the given source.

        Args:
            source: Source code or file path

        Returns:
            True if parser can handle it, False otherwise
        """
        if isinstance(source, Path):
            extension = source.suffix.lstrip(".")
            return extension.lower() in self.EXTENSION_PARSERS

        # For string source, check if we can detect content type
        return bool(self._get_parser_by_content(str(source)))


# For backward compatibility - prefer UnifiedPowerBuilderParser
PowerBuilderParser = UnifiedPowerBuilderParser
