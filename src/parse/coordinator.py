"""PowerBuilder SOURCE FILE parser using modular grammar and preprocessing.

This module implements a comprehensive parser for PowerBuilder SOURCE code files,
converting raw text into structured Abstract Syntax Trees (ASTs). It processes
PowerBuilder source files (.sru) that are produced by the Decompile stage.

IMPORTANT: This module runs AFTER the Decompile module in the sequential pipeline:
- Decompile: Converts .fun (P-code) files → .sru (source) files
- Parse: Processes .sru files → produces AST JSON

Key features:
- Extension-based parser selection for different PowerBuilder source file types
- Modular grammar design with shared rules across file types
- Preprocessing support for handling macros, includes, and conditional compilation
- Source location tracking for error reporting
- Visitor pattern support for AST traversal and transformation
- Specialized parsers for different PowerBuilder constructs (DataWindow, SQL, etc.)

The parsers are implemented using the Lark parsing library with LALR parsing
and custom visitor classes for transforming parse trees into the model layer's
AST nodes. Error handling is enhanced with context-aware error messages.

Input: Source files (.sru) from the Decompile stage
Output: AST JSON files for the Model stage

Based on reference implementation from Moose PowerBuilder Parser:
reference/moose-pb-parser/PowerBuilder-Parser-Core/PWBAbstractGrammar.class.st
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from lark import Token, Tree
from lark.exceptions import UnexpectedInput

from .parser.base import PowerBuilderBaseParser
from .error_recovery.strategy import (
    EnhancedErrorRecovery,
    ErrorRecoveryParser,
)
from src.common.types.errors import ErrorCollector, ParseError
from .exceptions import GrammarParseError, SyntaxError
from .preprocessor.import_resolver import DependencyContext, ImplicitImportResolver
from .library import LibraryManager
from .preprocessor.pb_preprocessor import PowerBuilderPreprocessor
from .transformer.ast_builder import PowerBuilderTransformer
from .type_resolution import ResolutionContext, TypeResolver
from .grammar.loader import GrammarManager

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
        return ["sra", "srw", "sru", "srf", "srm", "srs", "srq", "srd", "dwo", "sql"]

    def __init__(self, base_path: Path | None = None, enable_error_recovery: bool = None) -> None:




        """Initialize parser with environment variable configuration support.

        Args:
            base_path: Optional base path for resolving includes
            enable_error_recovery: Whether to enable error recovery (default from env or True)

        Environment variables:
            PB_PARSER_ERROR_RECOVERY: Enable error recovery (true/false)
            PB_PARSER_TYPE: Parser type (earley/lalr)
            PB_PARSER_MAX_ERRORS: Maximum errors to collect
        """
        self.base_path = base_path or Path.cwd()
        self.preprocessor = PowerBuilderPreprocessor(self.base_path)

        # Configure from environment variables with defaults
        if enable_error_recovery is None:
            enable_error_recovery = os.getenv("PB_PARSER_ERROR_RECOVERY", "true").lower() == "true"
        self.enable_error_recovery = enable_error_recovery

        # Get parser type from environment
        self.parser_type = os.getenv("PB_PARSER_TYPE", "earley")

        # Configure error collector with environment settings
        if self.enable_error_recovery:
            max_errors = int(os.getenv("PB_PARSER_MAX_ERRORS", "500"))
            self.error_collector = ErrorCollector(max_errors=max_errors)
        else:
            self.error_collector = None

        # Use GrammarManager to load grammar instead of hardcoded paths
        grammar_manager = GrammarManager()

        # Load grammar with proper error handling
        try:
            # Try to load powerbuilder grammar with error recovery if enabled
            if enable_error_recovery:
                # First load the base grammar
                self.parser = grammar_manager.load_grammar(
                    "powerbuilder",
                    parser=self.parser_type,
                    propagate_positions=True,
                    maybe_placeholders=True,
                    keep_all_tokens=True,  # Keep all tokens for better error analysis
                )

                # Get the grammar text to add error recovery rules
                # Since we already have the parser, we'll use it as-is
                # The error recovery will be handled by the wrapper classes
            else:
                # Load without error recovery modifications
                self.parser = grammar_manager.load_grammar(
                    "powerbuilder",
                    parser=self.parser_type,
                    propagate_positions=True,
                    maybe_placeholders=True,
                    keep_all_tokens=True,
                )

        except Exception as e:
            logger.error("Failed to load grammar: %s", e)
            # Try fallback grammars
            fallback_grammars = ["powerbuilder_fixed_v2", "powerbuilder_core", "common_grammar"]

            for fallback in fallback_grammars:
                try:
                    logger.warning("Trying fallback grammar: %s", fallback)
                    self.parser = grammar_manager.load_grammar(
                        fallback,
                        parser=self.parser_type,
                        propagate_positions=True,
                        maybe_placeholders=True,
                        keep_all_tokens=True,
                    )
                    logger.info("Successfully loaded fallback grammar: %s", fallback)
                    break
                except Exception as fallback_error:
                    logger.debug("Fallback %s failed: %s", fallback, fallback_error)
                    continue
            else:
                # All fallbacks failed
                msg = f"Failed to load any grammar: {e}"
                raise GrammarParseError(msg)

        # Create error recovery parser wrapper if enabled
        if enable_error_recovery:
            self.recovery_parser = ErrorRecoveryParser(self.parser, self.error_collector)
            self.enhanced_recovery = EnhancedErrorRecovery(self.parser, self.error_collector)

    def parse(
        self, source: str | Path, preprocess: bool= True, file_path: Path | None = None, ) -> Tree:




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
                    # Log the error
                    logger.warning("Parse error at line %s, column %s: %s", e.line, e.column, e)
                    logger.info("Attempting enhanced error recovery")

                    # Use enhanced error recovery
                    try:
                        recovered_tree = self.enhanced_recovery.parse_with_recovery(source_text)

                        # Apply transformer to recovered tree
                        transformer = PowerBuilderTransformer()
                        recovered_ast = transformer.transform(recovered_tree)

                        # Add error information to AST if it's a dict
                        if self.error_collector.has_errors() and isinstance(recovered_ast, dict):
                            recovered_ast["parse_errors"] = [
                                {
                                    "line": err.line, "column": err.column, "message": err.message, "type": err.error_type, "context": err.context,
                                }
                                for err in self.error_collector.errors
                            ]

                        logger.info("Error recovery succeeded with %s errors recorded", self.error_collector.get_error_count())
                        return recovered_ast

                    except Exception as recovery_error:
                        logger.error("Enhanced error recovery failed: %s", recovery_error)

                        # Fall back to minimal AST
                        # Record the error
                        parse_error = ParseError(
                            line=e.line, column=e.column, message=str(e), error_type="syntax_error", context=e.get_context(source_text), file_path=file_path,
                        )
                        self.error_collector.add_error(parse_error)

                        # Return a minimal AST with error information
                        error_ast = {
                            "type": "file", "elements": [{
                            "type": "error", "line": e.line, "column": e.column, "message": str(e), "partial_content": source_text[:1000],  # First 1000 chars
                        },], "has_errors": True, "error_count": 1,
                    }

                    # Try to salvage what we can by parsing line by line
                    lines = source_text.split("\n")
                    valid_elements = []

                    for i, line in enumerate(lines):
                        if line.strip() and not line.strip().startswith("//"):
                            try:
                                # Try to parse individual lines - note: this is a fallback approach
                                # The grammar doesn't have a 'statement' start rule, so we'll
                                # just collect the line content for now
                                valid_elements.append({
                                    "type": "recovered_line", "line": i + 1, "content": line.strip(),
                                })
                            except Exception as e:
                                logger.debug("Exception caught: %s", e)
                                # Skip unparseable lines - continue with next line
                                continue

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

            logger.exception("%s\n%s", msg, context)

            raise SyntaxError(
                message=msg, file_path=file_path, line=e.line, column=e.column, source_context=context, ) from e

        except Exception as e:
            logger.debug("Exception caught: %s", e)
            # Log and re-raise with context
            logger.exception("Error parsing %s: %s", file_path, e)

            raise SyntaxError(
                message=f"Error parsing source: {e!s}", file_path=file_path, ) from e

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


# NOTE: DataWindow parsing is now handled by PowerBuilderParser since the main grammar supports it
# class PowerBuilderDataWindowParser(PowerBuilderBaseParser):
#     """Parser for PowerBuilder DataWindow files."""
# 
#     @classmethod
#     def supported_extensions(cls) -> list[str]:
# 
# 
#         """Get supported file extensions."""
#         return ["srd", "dwo"]

#     def __init__(self, base_path: Path | None = None) -> None:
# 
# 
# 
# 
#         """Initialize parser.
# 
#         Args:
#             base_path: Optional base path for resolving includes
#         """
#         self.base_path = base_path or Path.cwd()
# 
#         # Load DataWindow grammar
#         from .constants import DATAWINDOW_GRAMMAR, GRAMMAR_DIR
# 
#         # Use simplified grammar for now
#         simple_grammar = GRAMMAR_DIR / "datawindow_simple.lark"
#         if simple_grammar.exists():
#             with open(simple_grammar, encoding="utf-8") as f:
#                 grammar = f.read()
#         else:
#             with open(DATAWINDOW_GRAMMAR, encoding="utf-8") as f:
#                 grammar = f.read()
# 
#         self.parser = Lark(
#             grammar, parser="lalr", propagate_positions=True, maybe_placeholders=True, import_paths=[str(GRAMMAR_DIR)], )
# 
#     def parse(self, source: str | Path) -> Tree:
# 
# 
# 
# 
#         """Parse PowerBuilder DataWindow source code.
# 
#         Args:
#             source: Source code string or file path
# 
#         Returns:
#             Parsed AST
# 
#         Raises:
#             ValueError: On parsing errors
#         """
#         try:
#             # Load source if path provided
#             if isinstance(source, Path):
#                 with open(source, encoding="utf-8") as f:
#                     source_text = f.read()
#                 file_path = source
#             else:
#                 source_text = source
#                 file_path = None
# 
#             # Parse the source
#             return self.parser.parse(source_text)
# 
#         except UnexpectedInput as e:
#             # Enhance error reporting
#             context = f"in file {file_path}" if file_path else "in source"
# 
#             msg = (
#                 f"Syntax error {context} at line {e.line}, column {e.column}:\n"
#                 f"{e.get_context(source_text)}\n"
#                 f"{" " * e.column}^\n"
#                 f"{e!s}"
#             )
#             raise ValueError(
#                 msg, ) from e
# 
#         except Exception as e:
#             context = f" in file {file_path}" if file_path else ""
# 
#             msg = f"Error parsing source{context}: {e!s}"
#             raise ValueError(msg) from e


# NOTE: SQL query parsing is now handled by PowerBuilderParser since the main grammar supports it
# class PowerBuilderQueryParser(PowerBuilderBaseParser):
#     """Parser for PowerBuilder SQL query files."""
# 
#     @classmethod
#     def supported_extensions(cls) -> list[str]:
# 
# 
#         """Get supported file extensions."""
#         return ["srq"]

#    def __init__(self, base_path: Path | None = None) -> None:
#
#
#
#
#        """Initialize parser.
#
#        Args:
#            base_path: Optional base path for resolving includes
#        """
#        self.base_path = base_path or Path.cwd()
#
#        # Load SQL grammar
#        from .constants import GRAMMAR_DIR, SQL_GRAMMAR
#
#        with open(SQL_GRAMMAR, encoding="utf-8") as f:
#            grammar = f.read()
#
#        self.parser = Lark(
#            grammar, parser="lalr", propagate_positions=True, maybe_placeholders=True, import_paths=[str(GRAMMAR_DIR)], )
#
#    def parse(self, source: str | Path) -> Tree:
#
#
#
#
#        """Parse PowerBuilder SQL query source code.
#
#        Args:
#            source: Source code string or file path
#
#        Returns:
#            Parsed AST
#
#        Raises:
#            ValueError: On parsing errors
#        """
#        try:
#            # Load source if path provided
#            if isinstance(source, Path):
#                with open(source, encoding="utf-8") as f:
#                    source_text = f.read()
#                file_path = source
#            else:
#                source_text = source
#                file_path = None
#
#            # Parse the source
#            return self.parser.parse(source_text)
#
#        except UnexpectedInput as e:
#            # Enhance error reporting
#            context = f"in file {file_path}" if file_path else "in source"
#
#            msg = (
#                f"Syntax error {context} at line {e.line}, column {e.column}:\n"
#                f"{e.get_context(source_text)}\n"
#                f"{" " * e.column}^\n"
#                f"{e!s}"
#            )
#            raise ValueError(
#                msg, ) from e
#
#        except Exception as e:
#            context = f" in file {file_path}" if file_path else ""
#
#            msg = f"Error parsing source{context}: {e!s}"
#            raise ValueError(msg) from e


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
    """Coordinates parsing with library resolution, symbol management, and type resolution."""

    def __init__(self, library_paths: list[Path] | None = None) -> None:


        """Initialize parse coordinator.

        Args:
            library_paths: List of paths to search for libraries
        """
        self.library_manager = LibraryManager(library_paths)
        self.parsed_files: dict[Path, Tree] = {}
        self.transformers: dict[Path, PowerBuilderTransformer] = {}
        self.type_resolver = TypeResolver()
        self.type_contexts: dict[Path, ResolutionContext] = {}
        self.implicit_resolver = ImplicitImportResolver()
        self.dependency_contexts: dict[Path, DependencyContext] = {}

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
        parser_cls = PowerBuilderBaseParser.get_parser_for_extension(file_path.suffix[1:])
        parser = parser_cls(base_path=file_path.parent)

        # Parse to get AST (not just tree)
        ast = parser.parse(file_path)

        # Extract imports from the parsed AST
        imports = self._extract_imports(ast)

        # Resolve imports
        resolved_symbols = {}
        for library_name, object_name in imports:
            # Try to resolve the library
            library = self.library_manager.resolve_import(library_name)
            if library:
                # Add the specific object or all exports
                if object_name in library.exports:
                    resolved_symbols[object_name] = {
                        "library": library.name, "value": library.exports[object_name],
                    }
                else:
                    # If object not found, add all exports (PowerBuilder behavior)
                    for symbol, value in library.exports.items():
                        resolved_symbols[symbol] = {
                            "library": library.name, "value": value,
                        }

        # Store transformer with resolved symbols for later use
        if hasattr(ast, "__class__"):
            # If ast is already transformed, we just need to store the symbols
            transformer = PowerBuilderTransformer()
            transformer.resolved_symbols = resolved_symbols
            self.transformers[file_path] = transformer
        else:
            # If ast is a raw tree, transform it with resolved symbols
            transformer = PowerBuilderTransformer()
            transformer.resolved_symbols = resolved_symbols
            ast = transformer.transform(ast)
            self.transformers[file_path] = transformer

        # Perform type resolution
        type_context = self._resolve_types(ast, file_path)

        # Extract implicit dependencies
        dep_context = self._extract_implicit_dependencies(ast, file_path)

        # Resolve implicit dependencies against available symbols
        self._resolve_implicit_imports(dep_context, resolved_symbols)

        # Cache results
        self.parsed_files[file_path] = ast
        self.type_contexts[file_path] = type_context
        self.dependency_contexts[file_path] = dep_context

        return ast

    def _extract_imports(self, tree: Tree) -> list[tuple[str, str]]:




        """Extract import statements from parsed tree.

        Args:
            tree: Parsed tree

        Returns:
            List of (library, object) tuples
        """
        imports = []

        # Handle both Tree and transformed dict
        if isinstance(tree, dict):
            # Tree has been transformed
            if "elements" in tree:
                for elem in tree["elements"]:
                    if hasattr(elem, "__class__") and elem.__class__.__name__ == "Import":
                        imports.append((elem.from_library, elem.object_name))
        else:
            # Raw tree
            def visit_imports(node) -> None:

                if isinstance(node, Tree):
                    if node.data == "import_statement":
                        # Extract library name from import
                        for child in node.children:
                            if isinstance(child, Token) and child.type == "STRING":
                                # Remove quotes
                                import_name = child.value.strip('"')
                                imports.append((import_name, import_name))
                            elif isinstance(child, Tree) and child.data == "library_name":
                                import_name = str(child.children[0])
                                imports.append((import_name, import_name))

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

    def _resolve_types(self, ast: Tree, file_path: Path) -> ResolutionContext:




        """Resolve custom types and enums in the AST.

        Args:
            ast: Parsed AST
            file_path: Path to the source file

        Returns:
            Resolution context with type registry and errors
        """
        logger.debug("Resolving types for %s", file_path)

        # Perform type resolution
        context = self.type_resolver.resolve_types(ast)

        # Log any errors
        if context.errors:
            logger.warning("Type resolution errors for %s:", file_path)
            for error in context.errors:
                logger.warning("  - %s", error)

        # Log unresolved references
        if context.unresolved_references:
            logger.warning("Unresolved type references in %s:", file_path)
            for ref in context.unresolved_references:
                logger.warning("  - %s", ref)

        return context

    def get_type_context(self, file_path: Path) -> ResolutionContext | None:




        """Get type resolution context for a file.

        Args:
            file_path: Path to the file

        Returns:
            Type resolution context or None if not parsed
        """
        return self.type_contexts.get(file_path)

    def get_custom_type(self, type_name: str, file_path: Path | None = None) -> Any | None:




        """Get a custom type definition.

        Args:
            type_name: Name of the type
            file_path: Optional file path to search in first

        Returns:
            Custom type definition or None if not found
        """
        # Check specific file context first
        if file_path and file_path in self.type_contexts:
            context = self.type_contexts[file_path]
            custom_type = context.get_type(type_name)
            if custom_type:
                return custom_type

        # Search all contexts
        for context in self.type_contexts.values():
            custom_type = context.get_type(type_name)
            if custom_type:
                return custom_type

        return None

    def _extract_implicit_dependencies(self, ast: Tree, file_path: Path) -> DependencyContext:




        """Extract implicit dependencies from the AST.

        Args:
            ast: Parsed AST
            file_path: Path to the source file

        Returns:
            Dependency context with found dependencies
        """
        logger.debug("Extracting implicit dependencies for %s", file_path)

        # Extract dependencies
        dep_context = self.implicit_resolver.extract_dependencies(ast, file_path)

        # Log found dependencies
        if dep_context.implicit_deps:
            logger.info("Found %s implicit dependencies in %s", len(dep_context.implicit_deps), file_path)
            for dep in dep_context.implicit_deps[:5]:  # Log first 5
                logger.debug("  - %s (%s)", dep.symbol_name, dep.dependency_type)

        return dep_context

    def _resolve_implicit_imports(self, dep_context: DependencyContext, resolved_symbols: dict[str, Any]) -> None:




        """Resolve implicit imports against available symbols.

        Args:
            dep_context: Dependency context with unresolved symbols
            resolved_symbols: Already resolved symbols from libraries
        """
        logger.debug("Resolving implicit imports")

        # Build complete symbol registry
        symbol_registry = resolved_symbols.copy()

        # Add symbols from all parsed files
        for path, type_context in self.type_contexts.items():
            for type_name, custom_type in type_context.type_registry.items():
                symbol_registry[type_name] = {
                    "type": "custom_type", "source": str(path),
                }

        # Search for symbols in libraries
        for symbol in dep_context.unresolved_symbols:
            if symbol not in symbol_registry:
                # Try to find in library manager
                lib_symbol = self.library_manager.get_symbol(symbol)
                if lib_symbol:
                    symbol_registry[symbol] = lib_symbol

        # Resolve dependencies
        self.implicit_resolver.resolve_dependencies(dep_context, symbol_registry)

        # Log resolution results
        if dep_context.unresolved_symbols:
            logger.warning(
                f"Unresolved dependencies in {dep_context.current_file}: "
                f"{len(dep_context.unresolved_symbols)} symbols",
            )

    def get_dependencies(self, file_path: Path) -> DependencyContext | None:




        """Get dependency context for a file.

        Args:
            file_path: Path to the file

        Returns:
            Dependency context or None if not parsed
        """
        return self.dependency_contexts.get(file_path)

    def build_library_index(self, library_dirs: list[Path]) -> None:




        """Build an index of all libraries in the given directories.

        Args:
            library_dirs: List of directories containing PBL/PBD files
        """
        logger.info("Building library index from %s directories", len(library_dirs))

        for lib_dir in library_dirs:
            if not lib_dir.exists():
                logger.warning("Library directory not found: %s", lib_dir)
                continue

            # Find all library files
            for lib_file in lib_dir.glob("*.pb[ld]"):
                try:
                    library = self.library_manager.load_library(lib_file)
                    logger.info("Loaded library: %s with %s exports", lib_file.name, len(library.exports))
                except Exception as e:
                    logger.error("Failed to load library %s: %s", lib_file, e)


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
    pb_extensions = [".sra", ".srw", ".sru", ".srf", ".srm", ".srs", ".srq", ".srd", ".dwo", ".sql"]
    source_files = []
    for ext in pb_extensions:
        source_files.extend(input_dir.rglob(f"*{ext}"))

    logger.info("Found %s PowerBuilder source files", len(source_files))

    # Parse results
    parsed_files = []
    failed_files = []

    # Parse each file
    for source_file in source_files:
        try:
            logger.debug("Parsing %s", source_file)

            # Parse the file
            tree = parse_file(source_file)

            # Create output path preserving directory structure
            relative_path = source_file.relative_to(input_dir)
            output_file = output_dir / relative_path.with_suffix(".ast.json")
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert tree to serializable format
            # Import serialization utilities
            from src.model.ast.serialization import serialize_ast

            # Serialize the AST properly
            try:
                serialized_ast = serialize_ast(tree)
                ast_format = "structured"
            except Exception as e:
                logger.warning(f"Failed to serialize AST for {source_file}: {e}")
                # Fallback to pretty string
                serialized_ast = tree.pretty() if hasattr(tree, "pretty") else str(tree)
                ast_format = "pretty_string"

            ast_data = {
                "file": str(relative_path), "parsed_at": datetime.now().isoformat(), "ast": serialized_ast, "ast_format": ast_format, "metadata": {
                    "extension": source_file.suffix, "size": source_file.stat().st_size, }, }

            # Save parsed AST
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(ast_data, f, indent=2)
            except TypeError as e:
                # Debug what's causing the serialization error
                logger.error(f"JSON serialization failed for {source_file}")
                logger.error(f"ast_data keys: {list(ast_data.keys())}")
                logger.error(f"ast type: {type(ast_data.get('ast'))}")
                if isinstance(ast_data.get('ast'), dict):
                    logger.error(f"ast dict keys: {list(ast_data['ast'].keys())}")
                raise

            parsed_files.append(
                {
                    "file": str(relative_path), "output": str(output_file.relative_to(output_dir)), "size": source_file.stat().st_size, },
            )

        except Exception as e:
            logger.exception("Failed to parse %s: %s", source_file, e)
            failed_files.append(
                {
                    "file": str(source_file.relative_to(input_dir)), "error": str(e), },
            )

    # Create summary
    return {
        "parsed_at": datetime.now().isoformat(), "input_directory": str(input_dir), "output_directory": str(output_dir), "total_files": len(source_files), "parsed_files": len(parsed_files), "failed_files": len(failed_files), "files": parsed_files, "failures": failed_files, }
