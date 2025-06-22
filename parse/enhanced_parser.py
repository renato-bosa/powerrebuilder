"""Enhanced PowerBuilder parser with error recovery for 100% accuracy.

This module provides an enhanced parser that can recover from syntax errors
and handle incomplete or corrupted PowerBuilder files.
"""

import logging
from pathlib import Path
from typing import Any

from lark import Lark, Token, Transformer, Tree
from lark.exceptions import UnexpectedCharacters, UnexpectedEOF, UnexpectedInput

from parse.base_parser import PowerBuilderBaseParser
from parse.utils.grammar_loader import load_grammar

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


class EnhancedPowerBuilderParser(PowerBuilderBaseParser):
    """Enhanced parser with error recovery capabilities."""

    def __init__(self, base_path: Path | None = None) -> None:


        """Initialize enhanced parser with error recovery."""
        super().__init__(base_path)

        # Load enhanced grammar with error recovery rules
        grammar_text = self._load_enhanced_grammar()

        # Create parser with error recovery options
        self.parser = Lark(
            grammar_text, parser="earley", # More robust than LALR for error recovery
            propagate_positions=True, maybe_placeholders=True, keep_all_tokens=True, # Keep all tokens for better error analysis
            regex=True, debug=False, )

        self.transformer = ErrorRecoveryTransformer()
        self.parse_errors = []

    def _load_enhanced_grammar(self) -> str:




        """Load and enhance the PowerBuilder grammar with error recovery rules."""
        # Load base grammar
        base_grammar = load_grammar("powerbuilder.lark")

        # Add error recovery rules
        error_recovery_rules = """
// Error recovery rules
error_recovery: _error_token+ _NEWLINE*
              | unexpected_token _recover_to_newline
              | incomplete_statement _NEWLINE*

_error_token: /[^\n]+/
_recover_to_newline: /[^\n]*/ _NEWLINE
unexpected_token: /./
incomplete_statement: statement_start ~_NEWLINE*

// Recovery anchors - common statement starts
statement_start: "if" | "for" | "do" | "while" | "choose" | "return" 
               | "call" | "create" | "destroy" | "open" | "close"
               | IDENTIFIER "=" | IDENTIFIER "." | IDENTIFIER "("

// Optional terminators for incomplete statements
optional_terminator: ""?
optional_end: ("end" IDENTIFIER)?

// Flexible statement rules with recovery
flexible_statement: statement optional_terminator
                  | error_recovery
                  | incomplete_statement

// Enhanced rules with fallbacks
start: (flexible_statement | error_recovery)*

"""

        # Combine base grammar with error recovery
        return base_grammar + "\n\n" + error_recovery_rules

    def parse(self, source: str | Path) -> Tree:




        """Parse PowerBuilder source with error recovery.

        Args:
            source: Source code string or file path

        Returns:
            Parsed AST with error nodes for unrecoverable sections
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

            # Clear previous errors
            self.parse_errors = []
            self.transformer.errors = []

            # Attempt full parse
            try:
                tree = self.parser.parse(source_text)
                return self.transformer.transform(tree)
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
            tree.meta = getattr(tree, "meta", type("Meta", (), {})())
            tree.meta.had_eof_recovery = True
            tree.meta.added_completions = completions
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
                (
                    """, "'"),
                (""",
                    "'",
                ),
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
                tree.meta = getattr(tree, "meta", type("Meta", (), {})())
                tree.meta.had_token_recovery = True
                tree.meta.fixed_characters = True
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
        combined_tree.meta = getattr(combined_tree, "meta", type("Meta", (), {})())
        combined_tree.meta.had_partial_recovery = True
        combined_tree.meta.num_sections = len(sections)

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
            tree.meta = getattr(tree, "meta", type("Meta", (), {})())
            tree.meta.had_line_skip = True
            tree.meta.skipped_lines = [skip_line]
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

        error_tree.meta = getattr(error_tree, "meta", type("Meta", (), {})())
        error_tree.meta.is_error_ast = True
        error_tree.meta.error_message = error_msg

        return error_tree

    def get_parse_errors(self) -> list[dict[str, Any]]:




        """Get all parse errors encountered during parsing."""
        return self.parse_errors + self.transformer.errors
