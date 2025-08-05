"""Decompile coordinator with caching support."""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.cache import file_hash
from src.core.cache_config import get_cache_manager

from .extractors.datawindow import DataWindowExtractor
from .extractors.logic import BusinessLogicExtractor
from .extractors.schema import DatabaseSchemaExtractor
from .factory import create_decompile_coordinator
from .opcodes.opcodes import initialize_opcodes

logger = logging.getLogger(__name__)


class CachedDecompileCoordinator:
    """Decompile coordinator with caching support."""

    def __init__(
        self,
        input_dir: Path | str,
        output_dir: Path | str,
        enable_byte_recovery: bool = True,
        output_format: str = "pb",
        enable_filtering: bool = True,
        enable_cache: bool = True,
        cache_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the cached decompile coordinator.

        Args:
            input_dir: Directory containing P-code files from extract stage
            output_dir: Directory to write decompiled source files
            enable_byte_recovery: Whether to enable byte-level recovery
            output_format: Output format ("pb" or "text")
            enable_filtering: Whether to enable output filtering
            enable_cache: Whether to enable caching
            cache_config: Optional cache configuration
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.enable_byte_recovery = enable_byte_recovery
        self.output_format = output_format
        self.enable_filtering = enable_filtering
        self.enable_cache = enable_cache

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize opcodes
        initialize_opcodes()

        # Initialize decompiler
        self.decompiler = create_decompile_coordinator(
            enable_byte_recovery=enable_byte_recovery,
            enable_filtering=enable_filtering,
        )

        # Initialize extractors
        self.datawindow_extractor = DataWindowExtractor()
        self.logic_extractor = BusinessLogicExtractor()
        self.schema_extractor = DatabaseSchemaExtractor()

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
            "extracted": {
                "datawindow": 0,
                "business_logic": 0,
                "database_schema": 0,
            },
        }

    async def decompile_async(self, progress_callback=None) -> dict[str, Any]:
        """Decompile all P-code files with caching support.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary containing decompilation results and statistics
        """
        start_time = datetime.now()
        logger.info(
            "Starting decompile stage with caching %s",
            "enabled" if self.enable_cache else "disabled",
        )

        # Collect P-code files
        pcode_files = list(self._collect_pcode_files())
        self._stats["total_files"] = len(pcode_files)

        if progress_callback:
            progress_callback(0, len(pcode_files), "Starting decompile...")

        # Process files
        tasks = []
        for idx, pcode_file in enumerate(pcode_files):
            task = self._decompile_file_cached(pcode_file)
            tasks.append(task)

            if progress_callback and idx % 10 == 0:
                progress_callback(
                    idx, len(pcode_files), f"Decompiling {pcode_file.name}"
                )

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
            progress_callback(len(pcode_files), len(pcode_files), "Decompile complete")

        # Calculate statistics
        elapsed_time = (datetime.now() - start_time).total_seconds()

        # Add cache statistics
        if self.cache_manager:
            cache_stats = self.cache_manager.get_stats()
            self._stats["cache_stats"] = cache_stats.get("decompile", {})

        # Create summary
        summary = {
            "stage": "decompile",
            "status": "success" if self._stats["failed"] == 0 else "partial",
            "start_time": start_time.isoformat(),
            "elapsed_time": elapsed_time,
            "statistics": self._stats,
        }

        # Write summary
        summary_path = self.output_dir / "decompile_summary.json"
        with summary_path.open("w") as f:
            json.dump(summary, f, indent=2)

        logger.info(
            "Decompile complete: %d/%d successful (%.1f%% cache hit rate)",
            self._stats["successful"],
            self._stats["total_files"],
            self._get_cache_hit_rate(),
        )

        return summary

    def decompile(self, progress_callback=None) -> dict[str, Any]:
        """Synchronous wrapper for decompile_async."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.decompile_async(progress_callback))
        finally:
            loop.close()

    async def _decompile_file_cached(self, pcode_file: Path) -> None:
        """Decompile a single file with caching support."""
        try:
            if self.cache_manager:
                # Generate cache key based on file content
                cache_key = file_hash(pcode_file)

                # Check if output already exists and is up-to-date
                output_path = self._get_output_path(pcode_file)
                if output_path.exists():
                    # Check if cached result is still valid
                    output_mtime = output_path.stat().st_mtime
                    source_mtime = pcode_file.stat().st_mtime

                    if output_mtime > source_mtime:
                        # Output is newer than source, use cached result
                        self._stats["cache_hits"] += 1
                        logger.debug(
                            "Using cached decompiled output for %s", pcode_file
                        )
                        return

                # Try to get from cache
                cached_content = await self.cache_manager.get_cache("decompile").get(
                    cache_key
                )
                if cached_content:
                    self._stats["cache_hits"] += 1
                    logger.debug("Cache hit for %s", pcode_file)

                    # Write cached content to output
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with output_path.open("w", encoding="utf-8") as f:
                        f.write(cached_content)
                    return
                self._stats["cache_misses"] += 1

            # Decompile the file
            decompiled_content = await self._decompile_file(pcode_file)

            # Store in cache
            if self.cache_manager and decompiled_content:
                cache_key = file_hash(pcode_file)
                await self.cache_manager.get_cache("decompile").put(
                    cache_key, decompiled_content
                )

        except Exception as e:
            logger.error("Failed to decompile %s: %s", pcode_file, e)
            self._stats["errors"].append({"file": str(pcode_file), "error": str(e)})
            raise

    async def _decompile_file(self, pcode_file: Path) -> str:
        """Decompile a single P-code file."""
        logger.debug("Decompiling %s", pcode_file)

        # Decompile the P-code file
        decompiled_content = self.decompiler.decompile_file(pcode_file)
        
        # Create a simple result object for compatibility
        class DecompileResult:
            def __init__(self, content: str, filename: str, success: bool = True, error: str | None = None):
                self.decompiled = content
                self.filename = filename
                self.success = success
                self.error = error
                self.object_type = "unknown"
                
        result = DecompileResult(decompiled_content, str(pcode_file)) if decompiled_content else DecompileResult("", str(pcode_file), False, "Decompilation returned empty content")

        if not result.success:
            raise Exception(f"Decompilation failed: {result.error}")

        # Extract additional information
        dw_info = None
        if result.object_type == "datawindow":
            dw_info = self.datawindow_extractor.extract(result.decompiled)
            if dw_info:
                self._stats["extracted"]["datawindow"] += 1

        # Extract business logic
        logic_info = self.logic_extractor.extract(result.decompiled)
        if logic_info:
            self._stats["extracted"]["business_logic"] += 1

        # Extract database schema
        schema_info = self.schema_extractor.extract(result.decompiled)
        if schema_info:
            self._stats["extracted"]["database_schema"] += 1

        # Format output
        if self.output_format == "pb":
            output_content = result.decompiled
        else:
            # Text format with metadata
            output_content = self._format_text_output(
                result, dw_info, logic_info, schema_info
            )

        # Write output file
        output_path = self._get_output_path(pcode_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            f.write(output_content)

        logger.debug("Wrote decompiled output to %s", output_path)

        return output_content

    def _collect_pcode_files(self):
        """Collect all P-code files to decompile."""
        # P-code files have .fun extension from extract stage
        for pcode_file in self.input_dir.rglob("*.fun"):
            if pcode_file.is_file():
                yield pcode_file

    def _get_output_path(self, pcode_file: Path) -> Path:
        """Get output path for decompiled file."""
        try:
            relative_path = pcode_file.relative_to(self.input_dir)
        except ValueError:
            relative_path = Path(pcode_file.name)

        # Map P-code extension to PowerBuilder source extension
        ext_mapping = {
            ".fun": ".sru",  # function/user object
            ".win": ".srw",  # window
            ".men": ".srm",  # menu
            ".str": ".srs",  # structure
            ".dwo": ".srd",  # datawindow
            ".app": ".sra",  # application
        }

        new_ext = ext_mapping.get(pcode_file.suffix, ".sru")
        output_filename = relative_path.stem + new_ext

        return self.output_dir / relative_path.parent / output_filename

    def _format_text_output(self, result, dw_info, logic_info, schema_info) -> str:
        """Format decompiled output as text with metadata."""
        lines = [
            f"// Decompiled from: {result.filename}",
            f"// Object type: {result.object_type}",
            f"// Decompiled at: {datetime.now().isoformat()}",
            "",
        ]

        if dw_info:
            lines.extend(
                [
                    "// DataWindow Information:",
                    f"//   SQL: {dw_info.get('sql_statement', 'N/A')}",
                    f"//   Columns: {len(dw_info.get('columns', []))}",
                    "",
                ]
            )

        if logic_info:
            lines.extend(
                [
                    "// Business Logic:",
                    f"//   Functions: {len(logic_info.get('functions', []))}",
                    f"//   Events: {len(logic_info.get('events', []))}",
                    "",
                ]
            )

        if schema_info:
            lines.extend(
                [
                    "// Database Schema:",
                    f"//   Tables: {len(schema_info.get('tables', []))}",
                    f"//   Columns: {len(schema_info.get('columns', []))}",
                    "",
                ]
            )

        lines.append(result.decompiled)

        return "\n".join(lines)

    def _get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self._stats["cache_hits"] + self._stats["cache_misses"]
        if total == 0:
            return 0.0
        return (self._stats["cache_hits"] / total) * 100
