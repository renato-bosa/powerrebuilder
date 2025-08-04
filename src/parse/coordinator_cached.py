"""PowerBuilder SOURCE FILE parser with caching support.

This module extends the base parse coordinator with comprehensive caching
to avoid re-parsing unchanged files.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.cache import file_hash
from src.core.cache_config import get_cache_manager
from src.model.ast.serialization import serialize_ast
from src.model.types.errors import ParseErrorCollector

from .grammar.loader import GrammarManager
from .library import LibraryManager
from .parser.base import PowerBuilderBaseParser
from .preprocessor.preprocessor import PowerBuilderPreprocessor
from .recovery_strategy import EnhancedErrorRecovery
from .transformer.builder import PowerBuilderTransformer

logger = logging.getLogger(__name__)


class CachedParseCoordinator:
    """Parse coordinator with caching support."""

    def __init__(
        self,
        input_dir: Path | str,
        output_dir: Path | str,
        enable_recovery: bool = True,
        validate_ast: bool = True,
        enable_cache: bool = True,
        cache_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the cached parse coordinator.

        Args:
            input_dir: Directory containing decompiled source files
            output_dir: Directory to write AST JSON files
            enable_recovery: Whether to enable error recovery during parsing
            validate_ast: Whether to validate generated ASTs
            enable_cache: Whether to enable caching
            cache_config: Optional cache configuration
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.enable_recovery = enable_recovery
        self.validate_ast = validate_ast
        self.enable_cache = enable_cache

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.grammar_manager = GrammarManager()
        self.library_manager = LibraryManager()
        self.preprocessor = PowerBuilderPreprocessor()
        self.error_collector = ParseErrorCollector()

        # Initialize cache manager
        self.cache_manager = get_cache_manager(cache_config) if enable_cache else None

        # Statistics
        self._stats = {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
            "warnings": [],
            "cache_hits": 0,
            "cache_misses": 0,
        }

    async def parse_async(self, progress_callback=None) -> dict[str, Any]:
        """Parse all source files with caching support.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary containing parsing results and statistics
        """
        start_time = datetime.now()
        logger.info(
            "Starting parse stage with caching %s",
            "enabled" if self.enable_cache else "disabled",
        )

        # Collect source files
        source_files = list(self._collect_source_files())
        self._stats["total_files"] = len(source_files)

        if progress_callback:
            progress_callback(0, len(source_files), "Starting parse...")

        # Process files
        tasks = []
        for idx, source_file in enumerate(source_files):
            task = self._parse_file_cached(source_file)
            tasks.append(task)

            if progress_callback and idx % 10 == 0:
                progress_callback(idx, len(source_files), f"Parsing {source_file.name}")

        # Wait for all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                self._stats["failed"] += 1
                self._stats["errors"].append(str(result))
            else:
                self._stats["successful"] += 1

        # Final callback
        if progress_callback:
            progress_callback(len(source_files), len(source_files), "Parse complete")

        # Calculate statistics
        elapsed_time = (datetime.now() - start_time).total_seconds()

        # Add cache statistics
        if self.cache_manager:
            cache_stats = self.cache_manager.get_stats()
            self._stats["cache_stats"] = cache_stats.get("parse", {})

        # Create summary
        summary = {
            "stage": "parse",
            "status": "success" if self._stats["failed"] == 0 else "partial",
            "start_time": start_time.isoformat(),
            "elapsed_time": elapsed_time,
            "statistics": self._stats,
        }

        # Write summary
        summary_path = self.output_dir / "parse_summary.json"
        with summary_path.open("w") as f:
            json.dump(summary, f, indent=2)

        logger.info(
            "Parse complete: %d/%d successful (%.1f%% cache hit rate)",
            self._stats["successful"],
            self._stats["total_files"],
            self._get_cache_hit_rate(),
        )

        return summary

    def parse(self, progress_callback=None) -> dict[str, Any]:
        """Synchronous wrapper for parse_async."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.parse_async(progress_callback))
        finally:
            loop.close()

    async def _parse_file_cached(self, source_file: Path) -> None:
        """Parse a single file with caching support."""
        try:
            if self.cache_manager:
                # Generate cache key based on file content
                cache_key = file_hash(source_file)

                # Check if output already exists and is up-to-date
                output_path = self._get_output_path(source_file)
                if output_path.exists():
                    # Check if cached result is still valid
                    output_mtime = output_path.stat().st_mtime
                    source_mtime = source_file.stat().st_mtime

                    if output_mtime > source_mtime:
                        # Output is newer than source, use cached result
                        self._stats["cache_hits"] += 1
                        logger.debug("Using cached AST for %s", source_file)
                        return

                # Try to get from cache
                cached_ast = await self.cache_manager.get_cache("parse").get(cache_key)
                if cached_ast:
                    self._stats["cache_hits"] += 1
                    logger.debug("Cache hit for %s", source_file)

                    # Write cached AST to output
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with output_path.open("w", encoding="utf-8") as f:
                        json.dump(cached_ast, f, indent=2)
                    return
                self._stats["cache_misses"] += 1

            # Parse the file
            ast_json = await self._parse_file(source_file)

            # Store in cache
            if self.cache_manager and ast_json:
                cache_key = file_hash(source_file)
                await self.cache_manager.get_cache("parse").put(cache_key, ast_json)

        except Exception as e:
            logger.error("Failed to parse %s: %s", source_file, e)
            self._stats["errors"].append({"file": str(source_file), "error": str(e)})
            raise

    async def _parse_file(self, source_file: Path) -> dict[str, Any]:
        """Parse a single source file."""
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

        return ast_json

    def _collect_source_files(self):
        """Collect all source files to parse."""
        extensions = [".sru", ".srw", ".srm", ".srs", ".srd", ".sra"]

        for ext in extensions:
            for source_file in self.input_dir.rglob(f"*{ext}"):
                if source_file.is_file():
                    yield source_file

    def _get_parser_for_extension(self, extension: str) -> PowerBuilderBaseParser:
        """Get appropriate parser for file extension."""
        ext_to_type = {
            ".sru": "userobject",
            ".srw": "window",
            ".srm": "menu",
            ".srs": "structure",
            ".srd": "datawindow",
            ".sra": "application",
        }

        object_type = ext_to_type.get(extension, "generic")
        grammar = self.grammar_manager.get_grammar(object_type)
        return PowerBuilderBaseParser(grammar)

    def _get_object_type(self, extension: str) -> str:
        """Get object type from file extension."""
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
        """Get output path for AST JSON file."""
        try:
            relative_path = source_file.relative_to(self.input_dir)
        except ValueError:
            relative_path = Path(source_file.name)

        ast_filename = relative_path.stem + ".ast.json"
        return self.output_dir / relative_path.parent / ast_filename

    def _validate_ast(self, ast: Any) -> list[str]:
        """Validate AST structure."""
        errors = []

        if not ast:
            errors.append("AST is empty")
            return errors

        if hasattr(ast, "__dict__"):
            if not hasattr(ast, "type") or not ast.type:
                errors.append("AST node missing 'type' attribute")

            if not hasattr(ast, "line") or not hasattr(ast, "column"):
                errors.append("AST node missing source location info")

        return errors

    def _get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self._stats["cache_hits"] + self._stats["cache_misses"]
        if total == 0:
            return 0.0
        return (self._stats["cache_hits"] / total) * 100
