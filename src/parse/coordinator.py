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

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..model.ast.serialization import serialize_ast
from ..model.types.errors import ParseErrorCollector
from .recovery_strategy import EnhancedErrorRecovery
from .grammar.loader import GrammarManager
from .library import LibraryManager
from .parser.base import PowerBuilderBaseParser
from .preprocessor.preprocessor import PowerBuilderPreprocessor
from .transformer.builder import PowerBuilderTransformer

logger = logging.getLogger(__name__)


class ParseCoordinator:
    """Coordinator for PowerBuilder source file parsing.

    This coordinator handles the parsing of PowerBuilder source files (.sru, .srw, etc.)
    into Abstract Syntax Trees (ASTs) for further processing by the Model stage.
    """

    def __init__(
        self,
        input_dir: Path | str,
        output_dir: Path | str,
        enable_recovery: bool = True,
        validate_ast: bool = True,
    ) -> None:
        """Initialize the parse coordinator.

        Args:
            input_dir: Directory containing decompiled source files
            output_dir: Directory to write AST JSON files
            enable_recovery: Whether to enable error recovery during parsing
            validate_ast: Whether to validate generated ASTs
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.enable_recovery = enable_recovery
        self.validate_ast = validate_ast

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.grammar_manager = GrammarManager()
        self.library_manager = LibraryManager()
        self.preprocessor = PowerBuilderPreprocessor()
        self.error_collector = ParseErrorCollector()

        # Statistics
        self._stats = {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
            "warnings": [],
        }

    def parse(self, progress_callback=None) -> dict[str, Any]:
        """Parse all source files in the input directory.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with parsing results
        """
        logger.info("Starting parsing of decompiled files")
        logger.info("Input: %s", self.input_dir)
        logger.info("Output: %s", self.output_dir)

        # Collect source files
        source_extensions = [".sru", ".srw", ".srm", ".srs", ".srd", ".sra"]
        source_files = []
        for ext in source_extensions:
            source_files.extend(self.input_dir.rglob(f"*{ext}"))

        self._stats["total_files"] = len(source_files)
        logger.info("Found %d source files to parse", len(source_files))

        if progress_callback:
            progress_callback("Starting parsing", 0)

        # Process each file
        for idx, source_file in enumerate(source_files):
            if progress_callback:
                progress = int((idx / len(source_files)) * 100)
                progress_callback(f"Parsing {source_file.name}", progress)

            try:
                self._parse_file(source_file)
                self._stats["successful"] += 1
            except Exception as e:
                logger.error("Failed to parse %s: %s", source_file, e)
                self._stats["failed"] += 1
                self._stats["errors"].append(
                    {"file": str(source_file), "error": str(e)}
                )

        # Write summary
        self._write_summary()

        if progress_callback:
            progress_callback("Parsing complete", 100)

        logger.info(
            "Parsing complete. Success: %d, Failed: %d",
            self._stats["successful"],
            self._stats["failed"],
        )

        return self._stats

    def _parse_file(self, source_file: Path) -> None:
        """Parse a single source file.

        Args:
            source_file: Path to the source file
        """
        logger.debug("Parsing %s", source_file)

        # Read source content
        with source_file.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Preprocess the content
        preprocessed_content = self.preprocessor.preprocess(content, str(source_file))

        # Determine parser based on file extension
        file_ext = source_file.suffix.lower()
        parser = self._get_parser_for_extension(file_ext)

        # Parse with error recovery
        if self.enable_recovery:
            error_recovery = EnhancedErrorRecovery(self.error_collector)
            ast = parser.parse_with_recovery(preprocessed_content, error_recovery)
        else:
            ast = parser.parse(preprocessed_content)

        # Transform to AST nodes
        transformer = PowerBuilderTransformer()
        transformed_ast = transformer.transform(ast)

        # Validate AST if enabled
        if self.validate_ast:
            validation_errors = self._validate_ast(transformed_ast)
            if validation_errors:
                for error in validation_errors:
                    self._stats["warnings"].append(
                        {"file": str(source_file), "warning": error}
                    )

        # Serialize AST to JSON
        ast_data = serialize_ast(transformed_ast)

        # Add metadata
        ast_json = {
            "file": str(source_file.name),
            "type": self._get_object_type(file_ext),
            "parsed_at": datetime.now().isoformat(),
            "ast": ast_data,
            "errors": self.error_collector.get_errors_for_file(str(source_file)),
        }

        # Write AST JSON file
        output_path = self._get_output_path(source_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(ast_json, f, indent=2)

        logger.debug("Wrote AST to %s", output_path)

    def _get_parser_for_extension(self, extension: str) -> PowerBuilderBaseParser:
        """Get appropriate parser for file extension.

        Args:
            extension: File extension (e.g., ".sru")

        Returns:
            Parser instance
        """
        # Map extensions to object types
        ext_to_type = {
            ".sru": "userobject",
            ".srw": "window",
            ".srm": "menu",
            ".srs": "structure",
            ".srd": "datawindow",
            ".sra": "application",
        }

        object_type = ext_to_type.get(extension, "generic")

        # Get appropriate grammar
        grammar = self.grammar_manager.get_grammar(object_type)

        # Create parser with grammar
        return PowerBuilderBaseParser(grammar)

    def _get_object_type(self, extension: str) -> str:
        """Get object type from file extension.

        Args:
            extension: File extension

        Returns:
            Object type string
        """
        ext_to_type = {
            ".sru": "userobject",
            ".srw": "window",
            ".srm": "menu",
            ".srs": "structure",
            ".srd": "datawindow",
            ".sra": "application",
        }
        return ext_to_type.get(extension, "unknown")

    def _get_output_path(self, source_file: Path) -> Path:
        """Get output path for AST JSON file.

        Args:
            source_file: Source file path

        Returns:
            Output file path
        """
        # Preserve directory structure
        try:
            relative_path = source_file.relative_to(self.input_dir)
        except ValueError:
            relative_path = Path(source_file.name)

        # Change extension to .ast.json
        ast_filename = relative_path.stem + ".ast.json"
        return self.output_dir / relative_path.parent / ast_filename

    def _validate_ast(self, ast: Any) -> list[str]:
        """Validate AST structure.

        Args:
            ast: AST to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Basic validation checks
        if not ast:
            errors.append("AST is empty")
            return errors

        # Check for required attributes
        if hasattr(ast, "__dict__"):
            if not hasattr(ast, "type") or not ast.type:
                errors.append("AST node missing 'type' attribute")

            # Check for source location info
            if not hasattr(ast, "line") or not hasattr(ast, "column"):
                errors.append("AST node missing source location info")

        return errors

    def _write_summary(self) -> None:
        """Write parsing summary to output directory."""
        summary = {
            "parsed_at": datetime.now().isoformat(),
            "input_dir": str(self.input_dir),
            "output_dir": str(self.output_dir),
            "statistics": self._stats,
        }

        summary_path = self.output_dir / "parsed_summary.json"
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info("Wrote parsing summary to %s", summary_path)


# Utility function for compatibility
def parse_file(
    file_path: Path | str, output_dir: Path | str | None = None
) -> dict[str, Any]:
    """Parse a single PowerBuilder source file.

    Args:
        file_path: Path to the source file
        output_dir: Optional output directory for AST

    Returns:
        Dictionary containing the parsed AST
    """
    file_path = Path(file_path)

    # Use temporary directory if no output specified
    if not output_dir:
        import tempfile

        output_dir = Path(tempfile.mkdtemp())
    else:
        output_dir = Path(output_dir)

    # Create coordinator and parse single file
    coordinator = ParseCoordinator(file_path.parent, output_dir)
    coordinator._parse_file(file_path)

    # Read and return the generated AST
    output_path = coordinator._get_output_path(file_path)
    if output_path.exists():
        with output_path.open("r") as f:
            return json.load(f)

    raise RuntimeError(f"Failed to parse {file_path}")
