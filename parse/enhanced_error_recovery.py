"""Enhanced error recovery system for PowerBuilder parser.

This module provides robust error recovery capabilities that allow the parser
to continue processing after encountering syntax errors, producing a more 
complete AST with error nodes.
"""

import logging
import re
from dataclasses import dataclass, field

from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedInput, UnexpectedToken

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET

from .error_recovery import ErrorCollector, ParseError

logger = logging.getLogger(__name__)


@dataclass
class RecoveryPoint:
    """Represents a point where parsing can be resumed after an error."""

    position: int
    line: int
    column: int
    keyword: str | None = None
    context: str = ""
    confidence: float = 0.0  # 0.0 to 1.0

    def __lt__(self, other) -> bool:




        """Compare recovery points by position and confidence."""
        if self.position == other.position:
            return self.confidence < other.confidence
        return self.position < other.position


@dataclass 
class ParseFragment:
    """Represents a successfully parsed fragment of code."""

    start_pos: int
    end_pos: int
    tree: Tree
    errors: list[ParseError] = field(default_factory=list)


class EnhancedErrorRecovery:
    """Enhanced error recovery for PowerBuilder parsing."""

    # PowerBuilder statement keywords for recovery
    STATEMENT_KEYWORDS = {
        # Control flow
        "if", "else", "elseif", "end if", "for", "to", "step", "next", "end for", "while", "loop", "end while", "do", "until", "loop while", "loop until", "choose", "case", "end choose", "try", "catch", "finally", "end try", # Declarations
        "function", "subroutine", "event", "on", "public", "private", "protected", "global", "type", "end type", "forward", "end forward", # Variables
        "constant", "integer", "string", "boolean", "long", "decimal", "real", "double", "char", "blob", "date", "time", "datetime", # Other statements
        "return", "exit", "continue", "halt", "call", "execute", "dynamic", "create", "destroy", "open", "close", "select", "insert", "update", "delete", "commit", "rollback", # Class/object related
        "class", "inherits", "autoinstantiate", "this", "super", "parent", }

    # Block end markers
    BLOCK_END_MARKERS = {
        "end if", "end for", "end while", "end do", "end choose", "end try", "end function", "end subroutine", "end event", "end on", "end type", "end forward", "next", "loop", "wend",
    }

    # Tokens that often indicate statement boundaries
    BOUNDARY_TOKENS = {"", "\n", "then", "do", "loop"}

    def __init__(self, parser: Lark, error_collector: ErrorCollector | None = None) -> None:


        """Initialize enhanced error recovery.

        Args:
            parser: Lark parser instance
            error_collector: Optional error collector
        """
        self.parser = parser
        self.error_collector = error_collector or ErrorCollector()
        self._keyword_pattern = self._build_keyword_pattern()

    def _build_keyword_pattern(self) -> re.Pattern:




        """Build regex pattern for keyword detection."""
        # Escape keywords and sort by length (longest first)
        keywords = sorted(self.STATEMENT_KEYWORDS, key=len, reverse=True)
        escaped = [re.escape(kw) for kw in keywords]
        pattern = r"\b(" + "|".join(escaped) + r")\b"
        return re.compile(pattern, re.IGNORECASE)

    def parse_with_recovery(self, text: str, start_rule: str | None = None) -> Tree:




        """Parse text with enhanced error recovery.

        Args:
            text: Source text to parse
            start_rule: Optional start rule

        Returns:
            AST with error nodes for unparseable sections
        """
        # Try normal parsing first
        try:
            tree = self.parser.parse(text, start=start_rule)
            logger.info("Parsing succeeded without errors")
            return tree
        except UnexpectedInput as e:
            logger.info("Initial parse failed at line %s, attempting recovery", e.line)
            return self._recover_and_parse(text, e, start_rule)

    def _recover_and_parse(self, text: str, initial_error: UnexpectedInput,
                          start_rule: str | None = None) -> Tree:




        """Recover from parse error and continue parsing.

        Args:
            text: Source text
            initial_error: Initial parse error
            start_rule: Start rule for parsing

        Returns:
            AST with successfully parsed fragments and error nodes
        """
        # Split text into lines for analysis
        lines = text.split("\n")

        # Record initial error
        self._record_error(initial_error, lines)

        # Find recovery points
        recovery_points = self._find_recovery_points(text, initial_error.pos_in_stream)

        # Parse fragments between recovery points
        fragments = self._parse_fragments(text, recovery_points, start_rule)

        # Build final AST
        return self._build_recovered_ast(fragments, text)

    def _find_recovery_points(self, text: str, error_pos: int) -> list[RecoveryPoint]:




        """Find potential recovery points in the text.

        Args:
            text: Source text
            error_pos: Position where error occurred

        Returns:
            List of recovery points sorted by position
        """
        recovery_points = []

        # Find keyword-based recovery points
        for match in self._keyword_pattern.finditer(text[error_pos:]):
            keyword = match.group(0).lower()
            pos = error_pos + match.start()
            line_num = text[:pos].count("\n") + 1
            col_num = pos - text.rfind("\n", 0, pos)

            # Calculate confidence based on keyword type
            confidence = self._calculate_keyword_confidence(keyword, text, pos)

            recovery_point = RecoveryPoint(
                position=pos,
                line=line_num,
                column=col_num,
                keyword=keyword,
                context=self._get_context(text, pos),
                confidence=confidence,
            )
            recovery_points.append(recovery_point)

        # Find line-based recovery points (after error line)
        error_line = text[:error_pos].count("\n")
        lines = text.split("\n")

        for i in range(error_line + 1, len(lines)):
            line = lines[i].strip()
            if line and not line.startswith("//"):  # Non-empty, non-comment line
                line_start = sum(len(lines[j]) + 1 for j in range(i))

                recovery_point = RecoveryPoint(
                    position=line_start,
                    line=i + 1,
                    column=1,
                    context=line[:50],
                    confidence=0.5,  # Medium confidence for line boundaries
                )
                recovery_points.append(recovery_point)

        # Sort by position and filter out low confidence points
        recovery_points = [rp for rp in recovery_points if rp.confidence >= 0.3]
        recovery_points.sort()

        return recovery_points

    def _calculate_keyword_confidence(self, keyword: str, text: str, pos: int) -> float:




        """Calculate confidence score for a recovery point.

        Args:
            keyword: Keyword found
            text: Source text
            pos: Position of keyword

        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence

        # Higher confidence for block starters
        if keyword in {"function", "subroutine", "event", "if", "for", "while", "type"}:
            confidence = 0.8

        # Very high confidence for function/event declarations
        if keyword in {"function", "subroutine", "event"}:
            # Check if it looks like a declaration
            line_start = text.rfind("\n", 0, pos) + 1
            line_end = text.find("\n", pos)
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end]

            if re.match(r"^\s*(public|private|protected)?\s*(function|subroutine|event)", line, re.IGNORECASE):
                confidence = 0.95

        # Lower confidence if inside a string or comment
        if self._is_in_string_or_comment(text, pos):
            confidence *= 0.3

        # Higher confidence if at start of line
        if pos == 0 or text[pos-1] in "\n\r":
            confidence *= 1.2

        return min(confidence, 1.0)

    def _is_in_string_or_comment(self, text: str, pos: int) -> bool:




        """Check if position is inside a string or comment.

        Args:
            text: Source text
            pos: Position to check

        Returns:
            True if inside string or comment
        """
        # Simple heuristic - count quotes before position
        before = text[:pos]

        # Check for line comment
        line_start = before.rfind("\n") + 1
        line_before_pos = before[line_start:]
        if "//" in line_before_pos:
            return True

        # Check for string (simple quote counting)
        single_quotes = before.count("'") - before.count("\\'")
        double_quotes = before.count('"') - before.count('\\"')

        return (single_quotes % 2 == 1) or (double_quotes % 2 == 1)

    def _parse_fragments(self, text: str, recovery_points: list[RecoveryPoint],
                        start_rule: str | None = None) -> list[ParseFragment]:




        """Parse text fragments between recovery points.

        Args:
            text: Source text
            recovery_points: List of recovery points
            start_rule: Start rule for parsing

        Returns:
            List of successfully parsed fragments
        """
        fragments = []

        # Try to parse from each recovery point
        for i, recovery_point in enumerate(recovery_points):
            # Determine end position (next recovery point or end of text)
            end_pos = recovery_points[i + 1].position if i + 1 < len(recovery_points) else len(text)

            # Extract fragment text
            fragment_text = text[recovery_point.position:end_pos]

            # Skip very small fragments
            if len(fragment_text.strip()) < 5:
                continue

            # Try different parsing strategies
            parsed_fragment = self._try_parse_fragment(
                fragment_text, 
                recovery_point.position,
                recovery_point.keyword,
                start_rule,
            )

            if parsed_fragment:
                parsed_fragment.start_pos = recovery_point.position
                parsed_fragment.end_pos = end_pos
                fragments.append(parsed_fragment)
            else:
                # Record error for unparseable fragment
                error = ParseError(
                    line=recovery_point.line,
                    column=recovery_point.column,
                    message=f"Could not parse fragment starting with: {recovery_point.context[:30]}...",
                    error_type="fragment_error",
                    context=recovery_point.context,
                )
                self.error_collector.add_error(error)

        return fragments

    def _try_parse_fragment(self, fragment_text: str, start_pos: int,
                           keyword: str | None, start_rule: str | None) -> ParseFragment | None:




        """Try to parse a text fragment using various strategies.

        Args:
            fragment_text: Text to parse
            start_pos: Starting position in original text
            keyword: Optional keyword at start of fragment
            start_rule: Start rule for parsing

        Returns:
            ParseFragment if successful, None otherwise
        """
        strategies = [
            # Try as complete statement/declaration
            lambda: self._parse_as_statement(fragment_text, keyword),

            # Try with synthetic wrapper
            lambda: self._parse_with_wrapper(fragment_text, keyword),

            # Try as expression
            lambda: self._parse_as_expression(fragment_text),

            # Try line by line
            lambda: self._parse_line_by_line(fragment_text),
        ]

        for strategy in strategies:
            try:
                tree = strategy()
                if tree:
                    return ParseFragment(
                        start_pos=start_pos,
                        end_pos=start_pos + len(fragment_text),
                        tree=tree,
                    )
            except Exception as e:
                logger.debug("Strategy failed: %s", e)
                continue

        return None

    def _parse_as_statement(self, text: str, keyword: str | None) -> Tree | None:




        """Try to parse text as a statement or declaration.

        Args:
            text: Text to parse
            keyword: Optional keyword hint

        Returns:
            Parsed tree or None
        """
        # Determine appropriate start rule based on keyword
        if keyword:
            if keyword in {"function", "subroutine"}:
                start_rule = "function_declaration"
            elif keyword == "event":
                start_rule = "event_declaration"
            elif keyword == "type":
                start_rule = "type_declaration"
            elif keyword in {"if", "for", "while", "do", "choose"}:
                start_rule = "statement"
            else:
                start_rule = "statement"
        else:
            start_rule = "statement"

        try:
            # Try to parse with specific rule
            return self.parser.parse(text, start=start_rule)
        except Exception as e:
            logger.debug("Exception caught: %s", e)
            # Try with general statement rule
            try:
                return self.parser.parse(text, start="statement")
            except Exception as e:
                return None

    def _parse_with_wrapper(self, text: str, keyword: str | None) -> Tree | None:




        """Try to parse text by wrapping it in a synthetic context.

        Args:
            text: Text to parse
            keyword: Optional keyword hint

        Returns:
            Parsed tree or None
        """
        # Add synthetic wrapper based on context
        if keyword in {"else", "elseif", "catch", "finally"}:
            # Wrap in if statement
            wrapped = f"if true then\n{text}\nend if"
            try:
                tree = self.parser.parse(wrapped, start="statement")
                # Extract the relevant part
                return self._extract_from_wrapper(tree, keyword)
            except Exception as e:
                return None

        elif keyword in {"case"}:
            # Wrap in choose statement
            wrapped = f"choose case 1\n{text}\nend choose"
            try:
                tree = self.parser.parse(wrapped, start="statement")
                return self._extract_from_wrapper(tree, keyword)
            except Exception as e:
                return None

        return None

    def _parse_as_expression(self, text: str) -> Tree | None:




        """Try to parse text as an expression.

        Args:
            text: Text to parse

        Returns:
            Parsed tree or None
        """
        try:
            return self.parser.parse(text, start="expression")
        except Exception as e:
            return None

    def _parse_line_by_line(self, text: str) -> Tree | None:




        """Try to parse text line by line.

        Args:
            text: Text to parse

        Returns:
            Tree containing successfully parsed lines
        """
        lines = text.split("\n")
        parsed_lines = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("//"):
                continue

            # Try to parse as various constructs
            for start_rule in ["statement", "expression", "declaration"]:
                try:
                    tree = self.parser.parse(line, start=start_rule)
                    parsed_lines.append(tree)
                    break
                except Exception as e:
                    continue

        if parsed_lines:
            return Tree("statement_list", parsed_lines)

        return None

    def _extract_from_wrapper(self, tree: Tree, keyword: str) -> Tree | None:




        """Extract relevant subtree from wrapped parse result.

        Args:
            tree: Parsed tree with wrapper
            keyword: Keyword to find

        Returns:
            Extracted subtree or None
        """
        # Simple extraction - would need proper tree traversal
        # For now, return the tree as-is
        return tree

    def _build_recovered_ast(self, fragments: list[ParseFragment], original_text: str) -> Tree:




        """Build final AST from parsed fragments and error nodes.

        Args:
            fragments: List of parsed fragments
            original_text: Original source text

        Returns:
            Complete AST with error nodes
        """
        elements = []
        current_pos = 0

        for fragment in sorted(fragments, key=lambda f: f.start_pos):
            # Add error node for gap before fragment
            if current_pos < fragment.start_pos:
                gap_text = original_text[current_pos:fragment.start_pos]
                if gap_text.strip():
                    error_node = self._create_error_node(gap_text, current_pos)
                    elements.append(error_node)

            # Add parsed fragment
            elements.append(fragment.tree)
            current_pos = fragment.end_pos

        # Add error node for remaining text
        if current_pos < len(original_text):
            remaining_text = original_text[current_pos:]
            if remaining_text.strip():
                error_node = self._create_error_node(remaining_text, current_pos)
                elements.append(error_node)

        # Create file tree
        return Tree("file", elements)

    def _create_error_node(self, text: str, position: int) -> Tree:




        """Create an error node for unparseable text.

        Args:
            text: Unparseable text
            position: Position in original text

        Returns:
            Error tree node
        """
        # Calculate line and column
        lines_before = text[:position].count("\n")
        line = lines_before + 1
        col = position - text.rfind("\n", 0, position)

        # Create error token
        error_token = Token("ERROR", text.strip(), None, line, col)

        # Create error node
        return Tree("error_node", [error_token])

    def _record_error(self, error: UnexpectedInput, lines: list[str]) -> None:




        """Record a parse error.

        Args:
            error: Parse error
            lines: Source lines
        """
        parse_error = ParseError(
            line=error.line,
            column=error.column,
            message=str(error),
            error_type=error.__class__.__name__,
            context=lines[error.line - 1] if error.line <= len(lines) else None,
        )

        if isinstance(error, UnexpectedToken):
            parse_error.expected = error.expected
            parse_error.found = str(error.token)

        self.error_collector.add_error(parse_error)

    def _get_context(self, text: str, pos: int, context_size: int = 50) -> str:




        """Get text context around a position.

        Args:
            text: Source text
            pos: Position
            context_size: Size of context to extract

        Returns:
            Context string
        """
        start = max(0, pos)
        end = min(len(text), pos + context_size)
        context = text[start:end].replace("\n", " ").strip()
        return context
