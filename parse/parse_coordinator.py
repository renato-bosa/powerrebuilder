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

from pathlib import Path
from typing import Any

from lark import Lark, Tree
from lark.exceptions import UnexpectedInput

import logging

from .base_parser import PowerBuilderBaseParser
from .constants import GRAMMAR_DIR
from .exceptions import GrammarParseError, SyntaxError
from .pb_preprocessor import PowerBuilderPreprocessor
from .powerbuilder_transformer import PowerBuilderTransformer
from .ast_to_model import ASTToModelConverter

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

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize parser.

        Args:
            base_path: Optional base path for resolving includes
        """
        self.base_path = base_path or Path.cwd()
        self.preprocessor = PowerBuilderPreprocessor(self.base_path)

        # Load fixed grammar file
        grammar_file = GRAMMAR_DIR / "experimental" / "powerbuilder_fixed_v2.lark"
        try:
            with open(grammar_file, encoding="utf-8") as f:
                grammar = f.read()
        except FileNotFoundError:
            # Fallback to original grammar
            logger.warning(f"Fixed grammar not found: {grammar_file}, falling back to original")
            grammar_file = GRAMMAR_DIR / "powerbuilder.lark"
            try:
                with open(grammar_file, encoding="utf-8") as f:
                    grammar = f.read()
            except FileNotFoundError:
                logger.error(f"Grammar file not found: {grammar_file}")
                raise GrammarParseError(f"Grammar file not found: {grammar_file}")

        # Create parser
        self.parser = Lark(
            grammar,
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=True,
            import_paths=[str(GRAMMAR_DIR)],
        )

    def parse(
        self, source: str | Path, preprocess: bool = True, file_path: Path | None = None
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
            parse_tree = self.parser.parse(source_text)

            # Apply transformer to get AST
            transformer = PowerBuilderTransformer()
            ast = transformer.transform(parse_tree)
            
            # Convert AST to model objects if needed
            # For now, return the AST
            return ast

        except UnexpectedInput as e:
            # Convert to SyntaxError with position information
            msg = f"Syntax error at line {e.line}, column {e.column}"
            context = e.get_context(source_text)

            logger.error(f"{msg}\n{context}")

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
                message=f"Error parsing source: {str(e)}",
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
        with open(self.base_path / "parse/datawindow.lark", encoding="utf-8") as f:
            grammar = f.read()

        self.parser = Lark(
            grammar,
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=True,
            import_paths=[str(self.base_path / "parse")],
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

            raise ValueError(
                f"Syntax error {context} at line {e.line}, column {e.column}:\n"
                f"{e.get_context(source_text)}\n"
                f"{' ' * e.column}^\n"
                f"{str(e)}",
            ) from e

        except Exception as e:
            context = f" in file {file_path}" if file_path else ""

            raise ValueError(f"Error parsing source{context}: {str(e)}") from e


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
        with open(self.base_path / "parse/sql.lark", encoding="utf-8") as f:
            grammar = f.read()

        self.parser = Lark(
            grammar,
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=True,
            import_paths=[str(self.base_path / "parse")],
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

            raise ValueError(
                f"Syntax error {context} at line {e.line}, column {e.column}:\n"
                f"{e.get_context(source_text)}\n"
                f"{' ' * e.column}^\n"
                f"{str(e)}",
            ) from e

        except Exception as e:
            context = f" in file {file_path}" if file_path else ""

            raise ValueError(f"Error parsing source{context}: {str(e)}") from e


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
    pb_extensions = ['.sra', '.srw', '.sru', '.srf', '.srm', '.srs', '.srq', '.srd']
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
            output_file = output_dir / relative_path.with_suffix('.ast.json')
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert tree to serializable format
            ast_data = {
                "file": str(relative_path),
                "parsed_at": datetime.now().isoformat(),
                "ast": tree.pretty() if hasattr(tree, 'pretty') else str(tree),
                "metadata": {
                    "extension": source_file.suffix,
                    "size": source_file.stat().st_size,
                }
            }
            
            # Save parsed AST
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(ast_data, f, indent=2)
            
            parsed_files.append({
                "file": str(relative_path),
                "output": str(output_file.relative_to(output_dir)),
                "size": source_file.stat().st_size,
            })
            
        except Exception as e:
            logger.error(f"Failed to parse {source_file}: {e}")
            failed_files.append({
                "file": str(source_file.relative_to(input_dir)),
                "error": str(e),
            })
    
    # Create summary
    summary = {
        "parsed_at": datetime.now().isoformat(),
        "input_directory": str(input_dir),
        "output_directory": str(output_dir),
        "total_files": len(source_files),
        "parsed_files": len(parsed_files),
        "failed_files": len(failed_files),
        "files": parsed_files,
        "failures": failed_files,
    }
    
    return summary
