"""Main pipeline coordinator that orchestrates all stages sequentially with progress tracking.

This coordinator manages the complete PowerBuilder reverse engineering pipeline:
1. Extract: Extracts P-code files from PBL/PBD archives
2. Decompile: Converts P-code to PowerBuilder source
3. Parse: Processes source into ASTs
4. Model: Builds semantic models
5. Generate: Produces modern code

The coordinator provides:
- Progress tracking for each stage and overall pipeline
- Error recovery and checkpoint support
- Configurable stage behavior
- Detailed statistics and reporting
- Comprehensive caching support
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from src.common.pipeline.progress import PipelineProgress
from src.core.cache_config import get_cache_manager
from src.decompile.coordinator import DecompileCoordinator
from src.decompile.coordinator_cached import CachedDecompileCoordinator
from src.extract.coordinator import ExtractCoordinator
from src.generate.coordinator import GenerateCoordinator
from src.model.modeling_coordinator import ModelingCoordinator
from src.parse.coordinator import ParseCoordinator
from src.parse.coordinator_cached import CachedParseCoordinator

logger = logging.getLogger(__name__)


class PipelineCoordinator:
    """Main coordinator for the complete PowerBuilder pipeline."""

    def __init__(
        self,
        input_dir: str | Path,
        output_dir: str | Path,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the pipeline coordinator.

        Args:
            input_dir: Directory containing PBL/PBD files
            output_dir: Base output directory for all stages
            config: Optional configuration for stages
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.config = config or {}

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Stage output directories
        self.extracted_dir = self.output_dir / "extracted"
        self.decompiled_dir = self.output_dir / "decompiled"
        self.parsed_dir = self.output_dir / "parsed"
        self.model_dir = self.output_dir / "models"
        self.generated_dir = self.output_dir / "generated"

        # Initialize stage coordinators
        self._init_coordinators()

        # Statistics
        self._stats = {
            "start_time": None,
            "end_time": None,
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "stages": {},
            "error_summary": {"errors": {}, "warnings": {}},
        }

        # Progress tracker
        self.progress: PipelineProgress | None = None

    def _init_coordinators(self) -> None:
        """Initialize all stage coordinators."""
        # Check if caching is enabled
        enable_cache = self.config.get("cache", {}).get("enabled", True)
        
        # Initialize cache manager if enabled
        self.cache_manager = get_cache_manager(self.config) if enable_cache else None
        
        # Extract coordinator
        extract_config = self.config.get("extract", {})
        self.extract_coordinator = ExtractCoordinator(
            input_path=None,  # Will be set per file
            output_dir=self.extracted_dir,
        )

        # Decompile coordinator - use cached version if caching enabled
        decompile_config = self.config.get("decompile", {})
        if enable_cache:
            self.decompile_coordinator = CachedDecompileCoordinator(
                input_dir=self.extracted_dir,
                output_dir=self.decompiled_dir,
                enable_byte_recovery=decompile_config.get("enable_byte_recovery", False),
                output_format=decompile_config.get("output_format", "pb"),
                enable_filtering=decompile_config.get("enable_filtering", True),
                enable_cache=True,
                cache_config=self.config,
            )
        else:
            self.decompile_coordinator = DecompileCoordinator(
                input_dir=self.extracted_dir,
                output_dir=self.decompiled_dir,
                enable_byte_recovery=decompile_config.get("enable_byte_recovery", False),
                output_format=decompile_config.get("output_format", "pb"),
                enable_filtering=decompile_config.get("enable_filtering", True),
            )

        # Parse coordinator - use cached version if caching enabled
        parse_config = self.config.get("parse", {})
        if enable_cache:
            self.parse_coordinator = CachedParseCoordinator(
                input_dir=self.decompiled_dir,
                output_dir=self.parsed_dir,
                enable_recovery=parse_config.get("enable_recovery", True),
                validate_ast=parse_config.get("validate_ast", True),
                enable_cache=True,
                cache_config=self.config,
            )
        else:
            self.parse_coordinator = ParseCoordinator(
                input_dir=self.decompiled_dir,
                output_dir=self.parsed_dir,
                enable_recovery=parse_config.get("enable_recovery", True),
                validate_ast=parse_config.get("validate_ast", True),
            )

        # Model coordinator
        self.model_coordinator = ModelingCoordinator(
            input_dir=self.parsed_dir,
            output_dir=self.model_dir,
        )

        # Generate coordinator
        generate_config = self.config.get("generate", {})
        self.generate_coordinator = GenerateCoordinator(
            input_dir=self.model_dir,
            output_dir=self.generated_dir,
            framework=generate_config.get("target_framework", "flutter"),
            null_safety=generate_config.get("null_safety", True),
            generate_tests=generate_config.get("generate_tests", False),
        )

    def process_files(
        self,
        pbl_files: list[str],
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> dict[str, Any]:
        """Process multiple PBL/PBD files through the complete pipeline.

        Args:
            pbl_files: List of PBL/PBD file paths
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with processing results
        """
        self._stats["start_time"] = time.time()
        self._stats["total_files"] = len(pbl_files)

        # Create progress tracker
        self.progress = PipelineProgress()

        with self.progress.pipeline_context(total_steps=5) as progress:
            # Process each PBL/PBD file
            for idx, pbl_file in enumerate(pbl_files):
                try:
                    logger.info(f"Processing file {idx + 1}/{len(pbl_files)}: {pbl_file}")
                    self._process_single_file(Path(pbl_file), progress)
                    self._stats["successful"] += 1
                except Exception as e:
                    logger.error(f"Failed to process {pbl_file}: {e}")
                    self._stats["failed"] += 1
                    self._record_error("pipeline", str(e))

        self._stats["end_time"] = time.time()
        return self._generate_summary()

    def _process_single_file(self, pbl_file: Path, progress: PipelineProgress) -> None:
        """Process a single PBL/PBD file through all stages.

        Args:
            pbl_file: Path to PBL/PBD file
            progress: Progress tracker instance
        """
        # Stage 1: Extract
        progress.start_step("Extracting PowerBuilder files", 1)
        extract_result = self._run_extract(pbl_file, progress)
        progress.complete_step(1)

        # Stage 2: Decompile
        progress.start_step("Decompiling P-code", 2)
        decompile_result = self._run_decompile(progress)
        progress.complete_step(2)

        # Stage 3: Parse
        progress.start_step("Parsing source code", 3)
        parse_result = self._run_parse(progress)
        progress.complete_step(3)

        # Stage 4: Model
        progress.start_step("Building models", 4)
        model_result = self._run_model(progress)
        progress.complete_step(4)

        # Stage 5: Generate
        progress.start_step("Generating output", 5)
        generate_result = self._run_generate(progress)
        progress.complete_step(5)

    def _run_extract(self, pbl_file: Path, progress: PipelineProgress) -> dict[str, Any]:
        """Run extraction stage with progress tracking.

        Args:
            pbl_file: PBL/PBD file to extract
            progress: Progress tracker

        Returns:
            Extraction results
        """
        try:
            # Create per-file output directory
            file_output_dir = self.extracted_dir / pbl_file.stem

            # Set up progress callback
            def extract_progress(current: int, total: int, message: str) -> None:
                progress.update_file_progress(current, message)

            # Configure coordinator for this file
            self.extract_coordinator.input_path = pbl_file
            self.extract_coordinator.output_dir = file_output_dir

            # Get the total number of files to extract (if available)
            # This would normally come from examining the PBL/PBD header
            total_files = 50  # Placeholder - actual count would come from PBL

            with progress.file_extraction_context(total_files) as task_id:
                result = self.extract_coordinator.extract(progress_callback=extract_progress)

            # Update statistics
            self._update_stage_stats("extract", result)
            return result

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            self._record_error("extract", str(e))
            raise

    def _run_decompile(self, progress: PipelineProgress) -> dict[str, Any]:
        """Run decompilation stage with progress tracking.

        Args:
            progress: Progress tracker

        Returns:
            Decompilation results
        """
        try:
            # Count P-code files to decompile
            pcode_files = list(self.extracted_dir.rglob("*.fun"))
            total_files = len(pcode_files)

            def decompile_progress(current: int, total: int, message: str) -> None:
                progress.update_operation(current, message)

            with progress.operation_context("Decompiling functions", total_files) as task_id:
                result = self.decompile_coordinator.decompile(
                    progress_callback=decompile_progress
                )

            # Update statistics
            self._update_stage_stats("decompile", result)
            return result

        except Exception as e:
            logger.error(f"Decompilation failed: {e}")
            self._record_error("decompile", str(e))
            raise

    def _run_parse(self, progress: PipelineProgress) -> dict[str, Any]:
        """Run parsing stage with progress tracking.

        Args:
            progress: Progress tracker

        Returns:
            Parsing results
        """
        try:
            # Count source files to parse
            source_files = []
            for ext in [".sru", ".srw", ".srm", ".srs", ".srd", ".sra"]:
                source_files.extend(self.decompiled_dir.rglob(f"*{ext}"))
            total_files = len(source_files)

            def parse_progress(message: str, percent: int) -> None:
                completed = int(total_files * percent / 100)
                progress.update_operation(completed, message)

            with progress.operation_context("Parsing source files", total_files) as task_id:
                result = self.parse_coordinator.parse(progress_callback=parse_progress)

            # Update statistics
            self._update_stage_stats("parse", result)
            return result

        except Exception as e:
            logger.error(f"Parsing failed: {e}")
            self._record_error("parse", str(e))
            raise

    def _run_model(self, progress: PipelineProgress) -> dict[str, Any]:
        """Run modeling stage with progress tracking.

        Args:
            progress: Progress tracker

        Returns:
            Modeling results
        """
        try:
            # Count AST files to process
            ast_files = list(self.parsed_dir.rglob("*.ast.json"))
            total_files = len(ast_files)

            def model_progress(current: int, total: int, message: str) -> None:
                progress.update_operation(current, message)

            with progress.operation_context("Building models", total_files) as task_id:
                result = self.model_coordinator.process_all(
                    progress_callback=model_progress
                )

            # Update statistics
            self._update_stage_stats("model", result)
            return result

        except Exception as e:
            logger.error(f"Modeling failed: {e}")
            self._record_error("model", str(e))
            raise

    def _run_generate(self, progress: PipelineProgress) -> dict[str, Any]:
        """Run generation stage with progress tracking.

        Args:
            progress: Progress tracker

        Returns:
            Generation results
        """
        try:
            # Count model files to process
            model_files = list(self.model_dir.rglob("*.model.json"))
            total_files = len(model_files)

            def generate_progress(message: str, percent: int) -> None:
                completed = int(total_files * percent / 100)
                progress.update_operation(completed, message)

            with progress.operation_context("Generating code", total_files) as task_id:
                result = self.generate_coordinator.generate(
                    progress_callback=generate_progress
                )

            # Update statistics
            self._update_stage_stats("generate", result)
            return result

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            self._record_error("generate", str(e))
            raise

    def _update_stage_stats(self, stage: str, result: dict[str, Any]) -> None:
        """Update statistics for a stage.

        Args:
            stage: Stage name
            result: Stage results
        """
        if stage not in self._stats["stages"]:
            self._stats["stages"][stage] = {
                "processed": 0,
                "successful": 0,
                "failed": 0,
            }

        stats = self._stats["stages"][stage]
        
        # Different stages return results differently
        if isinstance(result, dict):
            if "total_files" in result:
                stats["processed"] += result["total_files"]
                stats["successful"] += result.get("successful", 0)
                stats["failed"] += result.get("failed", 0)
            elif "extracted_count" in result:  # Extract stage
                stats["processed"] += result["extracted_count"]
                stats["successful"] += result["extracted_count"]
                stats["failed"] += result.get("error_count", 0)
            elif "decompiled" in result:  # Decompile stage
                stats["processed"] += result.get("total_files", 0)
                stats["successful"] += result["decompiled"]
                stats["failed"] += result.get("failed", 0)
            elif "successful_models" in result:  # Generate stage
                stats["processed"] += result.get("total_models", 0)
                stats["successful"] += result["successful_models"]
                stats["failed"] += result.get("failed_models", 0)

    def _record_error(self, stage: str, error: str) -> None:
        """Record an error for a stage.

        Args:
            stage: Stage name
            error: Error message
        """
        if stage not in self._stats["error_summary"]["errors"]:
            self._stats["error_summary"]["errors"][stage] = 0
        self._stats["error_summary"]["errors"][stage] += 1

    def _generate_summary(self) -> dict[str, Any]:
        """Generate final pipeline summary.

        Returns:
            Summary dictionary
        """
        # Add duration
        if self._stats["start_time"] and self._stats["end_time"]:
            duration = self._stats["end_time"] - self._stats["start_time"]
            self._stats["duration_seconds"] = duration

        # Add cache statistics if available
        if self.cache_manager:
            cache_stats = self.cache_manager.get_stats()
            self._stats["cache_statistics"] = cache_stats
            
            # Calculate overall cache performance
            total_hits = 0
            total_misses = 0
            for stage_stats in cache_stats.values():
                if isinstance(stage_stats, dict):
                    total_hits += stage_stats.get("hits", 0)
                    total_misses += stage_stats.get("misses", 0)
            
            total_requests = total_hits + total_misses
            if total_requests > 0:
                overall_hit_rate = (total_hits / total_requests) * 100
                self._stats["cache_performance"] = {
                    "total_hits": total_hits,
                    "total_misses": total_misses,
                    "overall_hit_rate": overall_hit_rate,
                }

        # Save summary to file
        summary_path = self.output_dir / "pipeline_summary.json"
        with open(summary_path, "w") as f:
            json.dump(self._stats, f, indent=2)

        logger.info(f"Pipeline summary saved to {summary_path}")

        return self._stats