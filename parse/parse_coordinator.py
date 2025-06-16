"""PowerBuilder parser using modular grammar and preprocessing.

This module implements a comprehensive parser for PowerBuilder source code,
converting raw text into structured Abstract Syntax Trees (ASTs).
It forms the second major stage in the reverse engineering pipeline after extraction.

Key features:
- Extension-based parser selection for different PowerBuilder file types (SRW, SRU, SRD, etc.)
- Modular grammar design with shared rules across file types
- Preprocessing support for handling macros, includes, and conditional compilation
- Source location tracking for error reporting
- Visitor pattern support for AST traversal and transformation
- Specialized parsers for different PowerBuilder constructs (DataWindow, SQL, etc.)

The parsers are implemented using the Lark parsing library with LALR parsing
and custom visitor classes for transforming parse trees into the model layer's
AST nodes. Error handling is enhanced with context-aware error messages.

Based on reference implementation from Moose PowerBuilder Parser:
reference/moose-pb-parser/PowerBuilder-Parser-Core/PWBAbstractGrammar.class.st
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from lark import Lark, Tree, Token
from lark.exceptions import UnexpectedInput

from .base_parser import PowerBuilderBaseParser
from .constants import GRAMMAR_DIR
from .exceptions import GrammarParseError, SyntaxError
from .pb_preprocessor import PowerBuilderPreprocessor
from .powerbuilder_transformer import PowerBuilderTransformer
from .library import LibraryManager, Library
from .error_recovery import (
    ErrorCollector, 
    ErrorRecoveryParser, 
    ErrorRecoveryTransformer,
    ParseError,
    add_error_recovery_to_grammar
)

# Set up module logger
logger = logging.getLogger(__name__)


class PowerBuilderParser(PowerBuilderBaseParser):
    """Parser for PowerBuilder source files.

    Features:
    - Modular grammar (common, window, datawindow, sql components)
    - Preprocessing support (includes, conditionals, macros)
    - Detailed error reporting
    """

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """Get supported file extensions."""
        return ["sra", "srw", "sru", "srf", "srm", "srs", "srq"]

    def __init__(self, base_path: Path | None = None, enable_error_recovery: bool = True) -> None:
        """Initialize parser.

        Args:
            base_path: Optional base path for resolving includes
            enable_error_recovery: Whether to enable error recovery (default: True)
        """
        self.base_path = base_path or Path.cwd()
        self.preprocessor = PowerBuilderPreprocessor(self.base_path)
        self.enable_error_recovery = enable_error_recovery
        self.error_collector = ErrorCollector() if enable_error_recovery else None

        # Load fixed grammar file
        grammar_file = GRAMMAR_DIR / "experimental" / "powerbuilder_fixed_v2.lark"
        try:
            with open(grammar_file, encoding="utf-8") as f:
                grammar = f.read()
        except FileNotFoundError:
            # Fallback to original grammar
            logger.warning(
                f"Fixed grammar not found: {grammar_file}, falling back to original"
            )
            grammar_file = GRAMMAR_DIR / "powerbuilder.lark"
            try:
                with open(grammar_file, encoding="utf-8") as f:
                    grammar = f.read()
            except FileNotFoundError:
                logger.exception(f"Grammar file not found: {grammar_file}")
                msg = f"Grammar file not found: {grammar_file}"
                raise GrammarParseError(msg)

        # Add error recovery rules if enabled
        if enable_error_recovery:
            grammar = add_error_recovery_to_grammar(grammar)

        # Create parser
        self.parser = Lark(
            grammar,
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=True,
            import_paths=[str(GRAMMAR_DIR)],
        )
        
        # Create error recovery parser wrapper if enabled
        if enable_error_recovery:
            self.recovery_parser = ErrorRecoveryParser(self.parser, self.error_collector)

    def parse(
        self,
        source: str | Path,
        preprocess: bool = True,
        file_path: Path | None = None,
    ) -> Tree:
        """Parse PowerBuilder source code.

        Args:
            source: Source code string or file path
            preprocess: Whether to run the preprocessor
            file_path: Optional file path for error reporting

        Returns:
            Parsed AST

        Raises:
            SyntaxError: On parsing or preprocessing errors
        """
        try:
            # Load source if path provided
            if isinstance(source, Path):
                with open(source, encoding="utf-8") as f:
                    source_text = f.read()
                file_path = source
            else:
                source_text = source
                file_path = file_path or Path("<string>")

            # Run preprocessor if enabled
            if preprocess:
                source_text = self.preprocessor.preprocess(source_text, file_path)

            # Parse the preprocessed source
            if self.enable_error_recovery:
                try:
                    # Try normal parsing first
                    parse_tree = self.parser.parse(source_text)
                    
                    # Apply transformer to get AST
                    transformer = PowerBuilderTransformer()
                    return transformer.transform(parse_tree)
                except UnexpectedInput as e:
                    # Record the error
                    parse_error = ParseError(
                        line=e.line,
                        column=e.column,
                        message=str(e),
                        error_type="syntax_error",
                        context=e.get_context(source_text),
                        file_path=file_path
                    )
                    self.error_collector.add_error(parse_error)
                    
                    # Log the error
                    logger.warning(f"Parse error at line {e.line}, column {e.column}: {e}")
                    
                    # Return a minimal AST with error information
                    error_ast = {
                        "type": "file",
                        "elements": [{
                            "type": "error",
                            "line": e.line,
                            "column": e.column,
                            "message": str(e),
                            "partial_content": source_text[:1000]  # First 1000 chars
                        }],
                        "has_errors": True,
                        "error_count": 1
                    }
                    
                    # Try to salvage what we can by parsing line by line
                    lines = source_text.split('\n')
                    valid_elements = []
                    
                    for i, line in enumerate(lines):
                        if line.strip() and not line.strip().startswith('//'):
                            try:
                                # Try to parse individual lines - note: this is a fallback approach
                                # The grammar doesn't have a 'statement' start rule, so we'll
                                # just collect the line content for now
                                valid_elements.append({
                                    "type": "recovered_line",
                                    "line": i + 1,
                                    "content": line.strip()
                                })
                            except:
                                # Skip unparseable lines
                                pass
                    
                    if valid_elements:
                        error_ast["elements"].extend(valid_elements)
                        error_ast["partial_parse"] = True
                    
                    return error_ast
            else:
                # Use normal parser without recovery
                parse_tree = self.parser.parse(source_text)
                
                # Apply transformer to get AST
                transformer = PowerBuilderTransformer()
                return transformer.transform(parse_tree)

            # Convert AST to model objects if needed
            # For now, return the AST

        except UnexpectedInput as e:
            # Convert to SyntaxError with position information
            msg = f"Syntax error at line {e.line}, column {e.column}"
            context = e.get_context(source_text)

            logger.exception(f"{msg}\n{context}")

            raise SyntaxError(
                message=msg,
                file_path=file_path,
                line=e.line,
                column=e.column,
                source_context=context,
            ) from e

        except Exception as e:
            # Log and re-raise with context
            logger.exception(f"Error parsing {file_path}: {e}")

            raise SyntaxError(
                message=f"Error parsing source: {e!s}",
                file_path=file_path,
            ) from e

    def add_define(self, symbol: str) -> None:
        """Add preprocessor symbol definition.

        Args:
            symbol: Symbol to define
        """
        self.preprocessor.add_define(symbol)

    def add_macro(self, name: str, value: str) -> None:
        """Add preprocessor macro definition.

        Args:
            name: Macro name
            value: Macro expansion value
        """
        self.preprocessor.add_macro(name, value)
    
    def get_parse_errors(self) -> list:
        """Get list of parse errors collected during parsing.
        
        Returns:
            List of ParseError objects, empty if no errors or error recovery disabled
        """
        if self.error_collector:
            return self.error_collector.errors
        return []
    
    def clear_errors(self) -> None:
        """Clear any collected parse errors."""
        if self.error_collector:
            self.error_collector.clear()


class PowerBuilderDataWindowParser(PowerBuilderBaseParser):
    """Parser for PowerBuilder DataWindow files."""

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """Get supported file extensions."""
        return ["srd"]

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize parser.

        Args:
            base_path: Optional base path for resolving includes
        """
        self.base_path = base_path or Path.cwd()

        # Load DataWindow grammar
        from .constants import DATAWINDOW_GRAMMAR, GRAMMAR_DIR

        with open(DATAWINDOW_GRAMMAR, encoding="utf-8") as f:
            grammar = f.read()

        self.parser = Lark(
            grammar,
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=True,
            import_paths=[str(GRAMMAR_DIR)],
        )

    def parse(self, source: str | Path) -> Tree:
        """Parse PowerBuilder DataWindow source code.

        Args:
            source: Source code string or file path

        Returns:
            Parsed AST

        Raises:
            ValueError: On parsing errors
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

            msg = (
                f"Syntax error {context} at line {e.line}, column {e.column}:\n"
                f"{e.get_context(source_text)}\n"
                f"{' ' * e.column}^\n"
                f"{e!s}"
            )
            raise ValueError(
                msg,
            ) from e

        except Exception as e:
            context = f" in file {file_path}" if file_path else ""

            msg = f"Error parsing source{context}: {e!s}"
            raise ValueError(msg) from e


class PowerBuilderQueryParser(PowerBuilderBaseParser):
    """Parser for PowerBuilder SQL query files."""

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """Get supported file extensions."""
        return ["srq"]

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize parser.

        Args:
            base_path: Optional base path for resolving includes
        """
        self.base_path = base_path or Path.cwd()

        # Load SQL grammar
        from .constants import GRAMMAR_DIR, SQL_GRAMMAR

        with open(SQL_GRAMMAR, encoding="utf-8") as f:
            grammar = f.read()

        self.parser = Lark(
            grammar,
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=True,
            import_paths=[str(GRAMMAR_DIR)],
        )

    def parse(self, source: str | Path) -> Tree:
        """Parse PowerBuilder SQL query source code.

        Args:
            source: Source code string or file path

        Returns:
            Parsed AST

        Raises:
            ValueError: On parsing errors
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

            msg = (
                f"Syntax error {context} at line {e.line}, column {e.column}:\n"
                f"{e.get_context(source_text)}\n"
                f"{' ' * e.column}^\n"
                f"{e!s}"
            )
            raise ValueError(
                msg,
            ) from e

        except Exception as e:
            context = f" in file {file_path}" if file_path else ""

            msg = f"Error parsing source{context}: {e!s}"
            raise ValueError(msg) from e


def parse_file(file_path: str | Path) -> Tree:
    """Parse a PowerBuilder file.

    Args:
        file_path: Path to the file to parse

    Returns:
        Parsed AST

    Raises:
        ValueError: If parsing fails
    """
    path = Path(file_path)
    parser_cls = PowerBuilderBaseParser.get_parser_for_extension(path.suffix[1:])
    parser = parser_cls(base_path=path.parent)
    return parser.parse(path)


def parse_string(source: str, extension: str = "sru") -> Tree:
    """Parse PowerBuilder source code.

    Args:
        source: Source code string
        extension: File extension to determine parser type (default: sru)

    Returns:
        Parsed AST

    Raises:
        ValueError: If parsing fails
    """
    parser_cls = PowerBuilderBaseParser.get_parser_for_extension(extension)
    parser = parser_cls()
    return parser.parse(source)


class ParseCoordinator:
    """Coordinates parsing with library resolution and symbol management."""
    
    def __init__(self, library_paths: list[Path] | None = None):
        """Initialize parse coordinator.
        
        Args:
            library_paths: List of paths to search for libraries
        """
        self.library_manager = LibraryManager(library_paths)
        self.parsed_files: dict[Path, Tree] = {}
        self.transformers: dict[Path, PowerBuilderTransformer] = {}
        
    def parse_with_imports(self, file_path: Path) -> Tree:
        """Parse a file with import resolution.
        
        Args:
            file_path: Path to file to parse
            
        Returns:
            Parsed AST with resolved imports
        """
        # Check cache
        if file_path in self.parsed_files:
            return self.parsed_files[file_path]
            
        # Parse the file
        tree = parse_file(file_path)
        
        # Extract imports from the parsed tree
        imports = self._extract_imports(tree)
        
        # Resolve imports
        resolved_symbols = {}
        for import_name in imports:
            library = self.library_manager.resolve_import(import_name)
            if library:
                # Add exported symbols to resolved symbols
                for symbol, value in library.exports.items():
                    resolved_symbols[symbol] = {
                        "library": library.name,
                        "value": value
                    }
                    
        # Create transformer with resolved symbols
        transformer = PowerBuilderTransformer()
        transformer.resolved_symbols = resolved_symbols
        
        # Transform the tree
        ast = transformer.transform(tree)
        
        # Cache results
        self.parsed_files[file_path] = ast
        self.transformers[file_path] = transformer
        
        return ast
        
    def _extract_imports(self, tree: Tree) -> list[str]:
        """Extract import statements from parsed tree.
        
        Args:
            tree: Parsed tree
            
        Returns:
            List of import names
        """
        imports = []
        
        def visit_imports(node):
            if isinstance(node, Tree):
                if node.data == "import_statement":
                    # Extract library name from import
                    for child in node.children:
                        if isinstance(child, Token) and child.type == "STRING":
                            # Remove quotes
                            import_name = child.value.strip('"')
                            imports.append(import_name)
                        elif isinstance(child, Tree) and child.data == "library_name":
                            import_name = str(child.children[0])
                            imports.append(import_name)
                            
                # Recurse
                for child in node.children:
                    visit_imports(child)
                    
        visit_imports(tree)
        return imports
        
    def add_library_path(self, path: Path) -> None:
        """Add a library search path.
        
        Args:
            path: Directory to add to search paths
        """
        self.library_manager.add_library_path(path)
        
    def get_symbol(self, symbol_name: str) -> Any | None:
        """Get a symbol from resolved libraries.
        
        Args:
            symbol_name: Name of symbol to find
            
        Returns:
            Symbol value or None if not found
        """
        return self.library_manager.get_symbol(symbol_name)


def parse_powerbuilder_directory(input_dir: Path, output_dir: Path) -> dict:
    """Parse all PowerBuilder files in a directory and save results.

    Args:
        input_dir: Directory containing PowerBuilder source files
        output_dir: Directory to save parsed results

    Returns:
        Dictionary containing parsing summary
    """
    import json
    from datetime import datetime

    # Find all PowerBuilder source files
    pb_extensions = [".sra", ".srw", ".sru", ".srf", ".srm", ".srs", ".srq", ".srd"]
    source_files = []
    for ext in pb_extensions:
        source_files.extend(input_dir.rglob(f"*{ext}"))

    logger.info(f"Found {len(source_files)} PowerBuilder source files")

    # Parse results
    parsed_files = []
    failed_files = []

    # Parse each file
    for source_file in source_files:
        try:
            logger.debug(f"Parsing {source_file}")

            # Parse the file
            tree = parse_file(source_file)

            # Create output path preserving directory structure
            relative_path = source_file.relative_to(input_dir)
            output_file = output_dir / relative_path.with_suffix(".ast.json")
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert tree to serializable format
            ast_data = {
                "file": str(relative_path),
                "parsed_at": datetime.now().isoformat(),
                "ast": tree.pretty() if hasattr(tree, "pretty") else str(tree),
                "metadata": {
                    "extension": source_file.suffix,
                    "size": source_file.stat().st_size,
                },
            }

            # Save parsed AST
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(ast_data, f, indent=2)

            parsed_files.append(
                {
                    "file": str(relative_path),
                    "output": str(output_file.relative_to(output_dir)),
                    "size": source_file.stat().st_size,
                }
            )

        except Exception as e:
            logger.exception(f"Failed to parse {source_file}: {e}")
            failed_files.append(
                {
                    "file": str(source_file.relative_to(input_dir)),
                    "error": str(e),
                }
            )

    # Create summary
    return {
        "parsed_at": datetime.now().isoformat(),
        "input_directory": str(input_dir),
        "output_directory": str(output_dir),
        "total_files": len(source_files),
        "parsed_files": len(parsed_files),
        "failed_files": len(failed_files),
        "files": parsed_files,
        "failures": failed_files,
    }
