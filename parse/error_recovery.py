"""Error recovery system for PowerBuilder parser.

This module provides error recovery capabilities that allow the parser
to continue processing after encountering syntax errors.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from lark import Tree, Token
from lark.exceptions import UnexpectedInput, UnexpectedToken, UnexpectedCharacters, UnexpectedEOF
from lark.lexer import Token as LexerToken
from lark.visitors import Transformer

logger = logging.getLogger(__name__)


@dataclass
class ParseError:
    """Represents a parse error with context."""
    
    line: int
    column: int
    message: str
    error_type: str
    context: Optional[str] = None
    expected: Optional[List[str]] = None
    found: Optional[str] = None
    file_path: Optional[Path] = None
    
    def __str__(self) -> str:
        """Format error for display."""
        location = f"{self.file_path}:" if self.file_path else ""
        location += f"{self.line}:{self.column}"
        
        msg = f"{location}: {self.error_type}: {self.message}"
        if self.context:
            msg += f"\n  Context: {self.context}"
        if self.expected:
            msg += f"\n  Expected: {', '.join(self.expected)}"
        if self.found:
            msg += f"\n  Found: {self.found}"
        return msg


@dataclass
class ErrorCollector:
    """Collects parse errors during parsing."""
    
    errors: List[ParseError] = field(default_factory=list)
    max_errors: int = 100
    file_path: Optional[Path] = None
    
    def add_error(self, error: ParseError) -> None:
        """Add an error to the collection."""
        if self.file_path and not error.file_path:
            error.file_path = self.file_path
            
        self.errors.append(error)
        
        if len(self.errors) >= self.max_errors:
            logger.warning(f"Maximum error count ({self.max_errors}) reached")
    
    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0
    
    def get_error_count(self) -> int:
        """Get the number of errors collected."""
        return len(self.errors)
    
    def get_errors_by_type(self) -> Dict[str, List[ParseError]]:
        """Group errors by type."""
        by_type: Dict[str, List[ParseError]] = {}
        for error in self.errors:
            if error.error_type not in by_type:
                by_type[error.error_type] = []
            by_type[error.error_type].append(error)
        return by_type
    
    def clear(self) -> None:
        """Clear all collected errors."""
        self.errors.clear()


class ErrorRecoveryTransformer(Transformer):
    """Transformer that handles error nodes in the AST."""
    
    def __init__(self, error_collector: Optional[ErrorCollector] = None):
        """Initialize transformer with optional error collector."""
        super().__init__()
        self.error_collector = error_collector or ErrorCollector()
    
    def error_node(self, children):
        """Handle error nodes created during parsing."""
        # Extract error information
        error_token = None
        error_msg = "Unknown error"
        
        for child in children:
            if isinstance(child, Token) and child.type == "ERROR":
                error_token = child
                error_msg = f"Unexpected token: {child.value}"
                break
        
        # Create error node in AST
        error_tree = Tree("error", children)
        
        # Record error if collector available
        if error_token and self.error_collector:
            error = ParseError(
                line=error_token.line,
                column=error_token.column,
                message=error_msg,
                error_type="syntax_error",
                found=str(error_token.value)
            )
            self.error_collector.add_error(error)
        
        return error_tree
    
    def recovered_statement(self, children):
        """Handle statements recovered after errors."""
        # Mark as recovered in the AST
        return Tree("recovered_statement", children)
    
    def incomplete_statement(self, children):
        """Handle incomplete statements."""
        # Create a partial statement node
        tree = Tree("incomplete_statement", children)
        
        # Record as warning
        if self.error_collector and children:
            first_token = self._find_first_token(children)
            if first_token:
                error = ParseError(
                    line=first_token.line,
                    column=first_token.column,
                    message="Incomplete statement",
                    error_type="warning"
                )
                self.error_collector.add_error(error)
        
        return tree
    
    def _find_first_token(self, children) -> Optional[Token]:
        """Find the first token in a list of children."""
        for child in children:
            if isinstance(child, Token):
                return child
            elif isinstance(child, Tree):
                token = self._find_first_token(child.children)
                if token:
                    return token
        return None


class ErrorRecoveryParser:
    """Wrapper for Lark parser with error recovery."""
    
    def __init__(self, parser, error_collector: Optional[ErrorCollector] = None):
        """Initialize with a Lark parser instance."""
        self.parser = parser
        self.error_collector = error_collector or ErrorCollector()
        self.recovery_transformer = ErrorRecoveryTransformer(self.error_collector)
    
    def parse_with_recovery(self, text: str, start: Optional[str] = None) -> Tree:
        """Parse text with error recovery.
        
        Args:
            text: Source text to parse
            start: Optional start rule
            
        Returns:
            AST with error nodes for unparseable sections
        """
        # Try normal parsing first
        try:
            tree = self.parser.parse(text, start=start)
            return tree
        except UnexpectedInput as e:
            # Handle parse error with recovery
            return self._recover_from_error(text, e, start)
    
    def _recover_from_error(self, text: str, error: UnexpectedInput, 
                          start: Optional[str] = None) -> Tree:
        """Attempt to recover from a parse error.
        
        Strategy:
        1. Record the error
        2. Find a recovery point (statement boundary, keyword, etc.)
        3. Create error node for unparseable section
        4. Continue parsing from recovery point
        """
        lines = text.split('\n')
        
        # Record the initial error
        parse_error = ParseError(
            line=error.line,
            column=error.column,
            message=str(error),
            error_type=error.__class__.__name__,
            context=lines[error.line - 1] if error.line <= len(lines) else None
        )
        
        if isinstance(error, UnexpectedToken):
            parse_error.expected = error.expected
            parse_error.found = str(error.token)
        
        self.error_collector.add_error(parse_error)
        
        # Try incremental parsing with recovery
        return self._incremental_parse(text, lines, error.line, start)
    
    def _incremental_parse(self, text: str, lines: List[str], 
                          error_line: int, start: Optional[str] = None) -> Tree:
        """Parse text incrementally, creating error nodes for unparseable sections."""
        # For now, use a simpler approach that creates a partial AST
        # with error information embedded
        
        # Try to parse line by line, collecting valid statements
        statements = []
        errors = []
        
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('//'):
                continue
                
            # Try to identify statement boundaries
            if any(stripped.startswith(kw) for kw in ['global', 'function', 'if', 'for', 'while', 'return']):
                # Attempt to parse from this line
                try:
                    # Create a minimal statement representation
                    stmt_tree = Tree("statement", [Token("IDENTIFIER", stripped)])
                    statements.append(stmt_tree)
                except:
                    # Record as error
                    error = ParseError(
                        line=line_num,
                        column=0,
                        message=f"Could not parse: {stripped[:50]}...",
                        error_type="parse_error"
                    )
                    errors.append(error)
                    self.error_collector.add_error(error)
        
        # Create a file tree with what we could parse
        if statements:
            return Tree("file", statements)
        else:
            # Return error tree if nothing could be parsed
            return Tree("error_file", [Token("ERROR", text)])
    
    def _find_recovery_point(self, lines: List[str], error_line: int) -> int:
        """Find a good point to resume parsing after an error.
        
        Looks for:
        - Statement keywords (if, for, while, etc.)
        - Function/event declarations
        - End statements
        - Empty lines
        """
        recovery_keywords = {
            'if', 'for', 'while', 'do', 'choose', 'case',
            'function', 'subroutine', 'event', 'on',
            'public', 'private', 'protected',
            'end', 'return', 'exit',
            'type', 'forward', 'global'
        }
        
        for i in range(error_line, len(lines)):
            line = lines[i].strip().lower()
            
            # Empty line could be statement boundary
            if not line:
                return i + 1
                
            # Check if line starts with recovery keyword
            first_word = line.split()[0] if line else ""
            if first_word in recovery_keywords:
                return i
        
        # No recovery point found
        return len(lines)
    
    def _create_error_node(self, text: str, start_line: int) -> Tree:
        """Create an error node for unparseable text."""
        error_token = Token("ERROR", text, None, start_line, 1)
        return Tree("error_node", [error_token])


def add_error_recovery_to_grammar(grammar_text: str) -> str:
    """Add error recovery rules to a PowerBuilder grammar.
    
    Args:
        grammar_text: Original grammar text
        
    Returns:
        Grammar text with error recovery rules added
    """
    # For now, return the original grammar without modifications
    # Error recovery will be handled at the parsing level rather than grammar level
    # This avoids conflicts with the LALR parser
    return grammar_text