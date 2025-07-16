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
from typing import Any, Dict, Type

from lark import Token, Transformer, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF, UnexpectedInput

from src.parse.parser.base import PowerBuilderBaseParser
from src.parse.parser.specialized.sql_parser import SQLParser
from src.parse.parser.specialized.transaction_parser import TransactionParser
from src.parse.parser.specialized.type_parser import TypeParser
from src.parse.parser.specialized.pseudocode_parser import PowerBuilderPseudocodeParser

logger = logging.getLogger(__name__)


# ============================================================================
# Error Recovery Transformer (from enhanced_parser.py)
# ============================================================================

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

    def __init__(self, base_path: Path | None = None, enable_error_recovery: bool = True) -> None:
        """Initialize enhanced parser with error recovery."""
        super().__init__(base_path)
        self.enable_error_recovery = enable_error_recovery

        # Load enhanced grammar with error recovery rules
        grammar_text = self._load_enhanced_grammar()

        # Create parser with error recovery options
        parser_kwargs = {
            "parser": "earley",  # More robust than LALR for error recovery
            "propagate_positions": True,
            "maybe_placeholders": True,
            "keep_all_tokens": True,  # Keep all tokens for better error analysis
            "regex": False,  # Don't require regex module
            "debug": False,
        }

        # Get grammar directory for imports
        from pathlib import Path
        grammar_dir = Path(__file__).parent.parent / "grammar" / "definitions"

        # Always use GrammarManager for consistent behavior
        from src.parse.grammar.loader import GrammarManager
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
        """
        if not self.enable_error_recovery:
            # Use base parser without error recovery
            return super().parse(source)

        try:
            # Load source if path provided
            if isinstance(source, Path):
                with open(source, encoding="utf-8") as f:
                    source_text = f.read()
                file_path = source
            else:
                source_text = source
                file_path = None

            # Clear previous errors
            self.parse_errors = []
            self.transformer.errors = []

            # Attempt full parse
            try:
                tree = self.parser.parse(source_text)
                # Don't use transformer for now - it might be creating Tree objects
                # that aren't being serialized properly
                return tree
            except UnexpectedEOF as e:
                # Handle EOF errors by adding completion
                logger.info("Handling EOF error at line %s", e.line)
                return self._parse_with_eof_recovery(source_text, e)
            except UnexpectedCharacters as e:
                # Handle character errors with token recovery
                logger.info(
                    f"Handling unexpected character at line {e.line}, column {e.column}",
                )
                return self._parse_with_token_recovery(source_text, e)
            except UnexpectedInput as e:
                # General parse error - use partial parsing
                logger.info("Handling parse error at line %s", e.line)
                return self._parse_with_partial_recovery(source_text, e)

        except Exception as e:
            logger.error("Enhanced parser failed: %s", e)
            # Return minimal AST with error information
            return self._create_error_ast(str(e), source_text)

    def _parse_with_eof_recovery(self, source: str, error: UnexpectedEOF) -> Tree:
        """Recover from EOF errors by completing incomplete constructs."""
        lines = source.split("\n")

        # Analyze the last few lines to determine what's missing
        last_lines = lines[-5:] if len(lines) > 5 else lines

        # Common completions for PowerBuilder
        completions = []

        # Check for unclosed blocks
        for line in reversed(last_lines):
            line_stripped = line.strip().lower()
            if line_stripped.startswith("if ") and "then" in line_stripped:
                completions.append("end if")
            elif line_stripped.startswith("for "):
                completions.append("next")
            elif line_stripped.startswith("do "):
                completions.append("loop")
            elif line_stripped.startswith("choose case"):
                completions.append("end choose")
            elif line_stripped.startswith("try"):
                completions.append("catch\nend try")

        # Add completions and retry
        completed_source = source + "\n" + "\n".join(completions)

        try:
            tree = self.parser.parse(completed_source)
            # Mark the tree as having recoveries
            # Note: Can't modify tree.meta as it's read-only, so add custom attributes
            tree.had_eof_recovery = True
            tree.added_completions = completions
            return self.transformer.transform(tree)
        except Exception:
            # If completion didn't work, use partial parsing
            return self._parse_with_partial_recovery(source, error)

    def _parse_with_token_recovery(
        self, source: str, error: UnexpectedCharacters,
    ) -> Tree:
        """Recover from unexpected character errors."""
        lines = source.split("\n")
        error_line = error.line - 1
        error_column = error.column - 1

        if 0 <= error_line < len(lines):
            line = lines[error_line]

            # Try common fixes
            fixes = [
                # Replace common encoding issues
                (""", "'"),
                (""", "'"),
                ('"', '"'),
                ('"', '"'),
                ("–", "-"),
                ("—", "--"),
                # Handle special characters
                ("•", "*"),
                ("…", "..."),
                # Remove non-ASCII characters
                (lambda c: ord(c) > 127, ""),
            ]

            # Apply fixes to the problematic line
            fixed_line = line
            for old, new in fixes:
                if callable(old):
                    fixed_line = "".join(new if old(c) else c for c in fixed_line)
                else:
                    fixed_line = fixed_line.replace(old, new)

            lines[error_line] = fixed_line
            fixed_source = "\n".join(lines)

            try:
                tree = self.parser.parse(fixed_source)
                # Note: Can't modify tree.meta as it's read-only, so add custom attributes
                tree.had_token_recovery = True
                tree.fixed_characters = True
                return self.transformer.transform(tree)
            except Exception:
                # If fix didn't work, skip the problematic line
                return self._parse_with_line_skip(source, error_line)

        return self._parse_with_partial_recovery(source, error)

    def _parse_with_partial_recovery(self, source: str, error: UnexpectedInput) -> Tree:
        """Parse source in sections, recovering from errors."""
        lines = source.split("\n")
        sections = []
        current_section = []

        # Split into sections at major boundaries
        section_starts = [
            "forward",
            "global",
            "type",
            "end type",
            "public function",
            "private function",
            "protected function",
            "public subroutine",
            "private subroutine",
            "protected subroutine",
            "event",
            "on",
            "create",
            "destroy",
        ]

        for i, line in enumerate(lines):
            line_lower = line.strip().lower()

            # Check if this line starts a new section
            is_section_start = any(
                line_lower.startswith(start) for start in section_starts
            )

            if is_section_start and current_section:
                # Parse the current section
                section_tree = self._try_parse_section(current_section)
                if section_tree:
                    sections.append(section_tree)
                current_section = []

            current_section.append(line)

        # Parse the last section
        if current_section:
            section_tree = self._try_parse_section(current_section)
            if section_tree:
                sections.append(section_tree)

        # Combine sections into a single tree
        combined_tree = Tree("start", sections)
        # Note: Can't modify tree.meta as it's read-only, so add custom attributes
        combined_tree.had_partial_recovery = True
        combined_tree.num_sections = len(sections)

        return combined_tree

    def _parse_with_line_skip(self, source: str, skip_line: int) -> Tree:
        """Parse source skipping a problematic line."""
        lines = source.split("\n")

        # Comment out the problematic line
        if 0 <= skip_line < len(lines):
            original_line = lines[skip_line]
            lines[skip_line] = f"// PARSE_ERROR: {original_line}"

        modified_source = "\n".join(lines)

        try:
            tree = self.parser.parse(modified_source)
            # Note: Can't modify tree.meta as it's read-only, so add custom attributes
            tree.had_line_skip = True
            tree.skipped_lines = [skip_line]
            return self.transformer.transform(tree)
        except Exception as e:
            logger.debug("Exception caught: %s", e)
            # If still failing, create error AST
            return self._create_error_ast(str(e), source)

    def _try_parse_section(self, lines: list[str]) -> Tree | None:
        """Try to parse a section of code."""
        section_text = "\n".join(lines)

        try:
            # Try parsing as a complete unit
            tree = self.parser.parse(section_text)
            return self.transformer.transform(tree)
        except Exception as e:
            logger.debug("Exception caught: %s", e)
            # If parsing fails, create an error node with the content
            error_node = Tree(
                "error_section",
                [Token("ERROR_CONTENT", section_text), Token("ERROR_MESSAGE", str(e))],
            )
            self.parse_errors.append(
                {
                    "section": section_text[:100] + "..."
                    if len(section_text) > 100
                    else section_text,
                    "error": str(e),
                },
            )
            return error_node

    def _create_error_ast(self, error_msg: str, source: str) -> Tree:
        """Create a minimal AST representing a parse error."""
        error_tree = Tree(
            "start",
            [
                Tree(
                    "parse_error",
                    [
                        Token("ERROR_MESSAGE", error_msg),
                        Token(
                            "SOURCE_PREVIEW",
                            source[:500] + "..." if len(source) > 500 else source,
                        ),
                    ],
                ),
            ],
        )

        # Note: Can't modify tree.meta as it's read-only, so add custom attributes
        error_tree.is_error_ast = True
        error_tree.error_message = error_msg

        return error_tree

    def get_parse_errors(self) -> list[dict[str, Any]]:
        """Get all parse errors encountered during parsing."""
        return self.parse_errors + self.transformer.errors


# ============================================================================
# Unified PowerBuilder Parser (from parser.py)
# ============================================================================

class UnifiedPowerBuilderParser:
    """Unified parser for all PowerBuilder file types.

    This parser automatically selects the appropriate specialized parser
    based on file extension or content type.
    """

    # Map of file extensions to specialized parsers
    EXTENSION_PARSERS: Dict[str, Type[PowerBuilderBaseParser]] = {
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

    def __init__(self, base_path: Path | None = None, enable_error_recovery: bool = True):
        """Initialize unified parser.

        Args:
            base_path: Base path for resolving includes
            enable_error_recovery: Whether to enable error recovery
        """
        self.base_path = base_path or Path.cwd()
        self.enable_error_recovery = enable_error_recovery
        self._parser_cache: Dict[Type[PowerBuilderBaseParser], PowerBuilderBaseParser] = {}

    def parse(self, source: str | Path, parser_type: str | None = None) -> Tree | Dict[str, Any]:
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
            with open(source, 'r', encoding='utf-8') as f:
                source_text = f.read()
        else:
            source_path = None
            source_text = source

        # Determine which parser to use
        if parser_type:
            parser_class = self._get_parser_by_type(parser_type)
        elif source_path:
            parser_class = self._get_parser_by_extension(source_path.suffix.lstrip('.'))
        else:
            parser_class = self._get_parser_by_content(source_text)

        if not parser_class:
            raise ValueError("Could not determine appropriate parser for source")

        # Get or create parser instance
        parser = self._get_parser_instance(parser_class)

        # Parse the source
        try:
            return parser.parse(source)
        except UnexpectedInput as e:
            logger.error(f"Parse error: {e}")
            raise

    def _get_parser_by_type(self, parser_type: str) -> Type[PowerBuilderBaseParser] | None:
        """Get parser class by type name."""
        type_map = {
            'sql': SQLParser,
            'transaction': TransactionParser,
            'type': TypeParser,
            'enhanced': EnhancedPowerBuilderParser,
            'pseudocode': PowerBuilderPseudocodeParser,
        }
        return type_map.get(parser_type.lower())

    def _get_parser_by_extension(self, extension: str) -> Type[PowerBuilderBaseParser] | None:
        """Get parser class by file extension."""
        return self.EXTENSION_PARSERS.get(extension.lower())

    def _get_parser_by_content(self, content: str) -> Type[PowerBuilderBaseParser]:
        """Detect parser type by content analysis."""
        # Check for specific patterns
        content_upper = content.upper()
        for pattern, parser_class in self.CONTENT_PATTERNS.items():
            if pattern in content_upper:
                return parser_class

        # Default to enhanced parser
        return EnhancedPowerBuilderParser

    def _get_parser_instance(self, parser_class: Type[PowerBuilderBaseParser]) -> PowerBuilderBaseParser:
        """Get or create parser instance."""
        if parser_class not in self._parser_cache:
            # Create appropriate instance based on parser type
            if parser_class == SQLParser:
                self._parser_cache[parser_class] = SQLParser()
            elif parser_class == TransactionParser:
                self._parser_cache[parser_class] = TransactionParser(self.base_path)
            elif parser_class == TypeParser:
                self._parser_cache[parser_class] = TypeParser(self.base_path)
            elif parser_class == EnhancedPowerBuilderParser:
                self._parser_cache[parser_class] = EnhancedPowerBuilderParser(
                    self.base_path, 
                    self.enable_error_recovery
                )
            elif parser_class == PowerBuilderPseudocodeParser:
                self._parser_cache[parser_class] = PowerBuilderPseudocodeParser()
            else:
                self._parser_cache[parser_class] = parser_class(self.base_path)

        return self._parser_cache[parser_class]

    def parse_file(self, file_path: Path) -> Tree | Dict[str, Any]:
        """Parse a PowerBuilder file.

        Args:
            file_path: Path to the file to parse

        Returns:
            Parse tree or dictionary representation
        """
        return self.parse(file_path)

    def parse_string(self, source: str, parser_type: str | None = None) -> Tree | Dict[str, Any]:
        """Parse a PowerBuilder source string.

        Args:
            source: Source code string
            parser_type: Optional parser type override

        Returns:
            Parse tree or dictionary representation
        """
        return self.parse(source, parser_type)

    def get_parser_for_type(self, parser_type: str) -> PowerBuilderBaseParser | None:
        """Get a specific parser instance by type.

        Args:
            parser_type: Parser type name

        Returns:
            Parser instance or None if type not found
        """
        parser_class = self._get_parser_by_type(parser_type)
        if parser_class:
            return self._get_parser_instance(parser_class)
        return None

    def get_parser_for_file(self, file_path: Path) -> PowerBuilderBaseParser | None:
        """Get appropriate parser for a file.

        Args:
            file_path: File path to determine parser for

        Returns:
            Parser instance or None if no appropriate parser found
        """
        parser_class = self._get_parser_by_extension(file_path.suffix.lstrip('.'))
        if parser_class:
            return self._get_parser_instance(parser_class)
        return None


# ============================================================================
# Convenience Functions
# ============================================================================

def parse_powerbuilder(source: str | Path, **kwargs) -> Tree | Dict[str, Any]:
    """Parse PowerBuilder source using unified parser.

    Args:
        source: Source code or file path
        **kwargs: Additional arguments passed to UnifiedPowerBuilderParser

    Returns:
        Parse tree or dictionary representation
    """
    parser = UnifiedPowerBuilderParser(**kwargs)
    return parser.parse(source)


def create_parser(parser_type: str = "unified", **kwargs) -> PowerBuilderBaseParser | UnifiedPowerBuilderParser:
    """Create a PowerBuilder parser instance.

    Args:
        parser_type: Type of parser to create ('unified', 'enhanced', 'sql', 'transaction', 'type', 'pseudocode')
        **kwargs: Additional arguments for parser initialization

    Returns:
        Parser instance

    Raises:
        ValueError: If parser type is not recognized
    """
    if parser_type == "unified":
        return UnifiedPowerBuilderParser(**kwargs)

    parser_map = {
        'enhanced': EnhancedPowerBuilderParser,
        'sql': SQLParser,
        'transaction': TransactionParser,
        'type': TypeParser,
        'pseudocode': PowerBuilderPseudocodeParser,
    }

    parser_class = parser_map.get(parser_type)
    if not parser_class:
        raise ValueError(f"Unknown parser type: {parser_type}")

    # Create parser with appropriate arguments
    if parser_type == 'enhanced':
        return parser_class(kwargs.get('base_path'), kwargs.get('enable_error_recovery', True))
    elif parser_type in ('transaction', 'type'):
        return parser_class(kwargs.get('base_path'))
    else:
        return parser_class()


# Export main classes and functions
__all__ = [
    'UnifiedPowerBuilderParser',
    'EnhancedPowerBuilderParser',
    'ErrorRecoveryTransformer',
    'parse_powerbuilder',
    'create_parser',
]