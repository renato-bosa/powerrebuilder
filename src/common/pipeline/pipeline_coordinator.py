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
import psutil
from collections.abc import Callable
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.contracts.types import PipelineStatsDict, StageStatsDict, PipelineErrorSummaryDict, CachePerformanceDict, ExtractionStatsDict

from src.common.pipeline.progress import PipelineProgress
from src.core.cache_config import get_cache_manager
from src.decompile.coordinator import DecompileCoordinator
from src.decompile.coordinator_cached import CachedDecompileCoordinator
from src.extract.coordinator import ExtractCoordinator
from src.generate.coordinator import GenerateCoordinator
from src.model.model_coordinator import ModelingCoordinator
from src.parse.coordinator import ParseCoordinator
from src.parse.coordinator_cached import CachedParseCoordinator

logger = logging.getLogger(__name__)


class PipelineCoordinator:
    """Main coordinator for the complete PowerBuilder pipeline."""

    # Coordinator attributes with Union types to support both regular and cached coordinators
    decompile_coordinator: Union[DecompileCoordinator, CachedDecompileCoordinator]
    parse_coordinator: Union[ParseCoordinator, CachedParseCoordinator]
    
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
        
        # Create all stage directories upfront
        for stage_dir in [self.extracted_dir, self.decompiled_dir, self.parsed_dir, self.model_dir, self.generated_dir]:
            stage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize stage coordinators
        self._init_coordinators()

        # Statistics
        error_summary: PipelineErrorSummaryDict = {
            "errors": {},
            "warnings": {},
        }
        
        self._stats: PipelineStatsDict = {
            "start_time": None,
            "end_time": None,
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "stages": {},
            "error_summary": error_summary,
        }
        
        # Enhanced stage tracking
        self._stage_timings: Dict[str, Dict[str, float]] = {}
        self._stage_memory: Dict[str, Dict[str, float]] = {}
        self._stage_details: Dict[str, Dict[str, Any]] = {}

        # Progress tracker
        self.progress: PipelineProgress | None = None

    def _init_coordinators(self) -> None:
        """Initialize all stage coordinators."""
        # Check if caching is enabled
        enable_cache = self.config.get("cache", {}).get("enabled", True)

        # Initialize cache manager if enabled
        self.cache_manager: Optional[Any] = get_cache_manager(self.config) if enable_cache else None

        # Extract coordinator
        self.config.get("extract", {})
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
                enable_byte_recovery=decompile_config.get(
                    "enable_byte_recovery", False
                ),
                output_format=decompile_config.get("output_format", "pb"),
                enable_filtering=decompile_config.get("enable_filtering", True),
                enable_cache=True,
                cache_config=self.config,
            )
        else:
            self.decompile_coordinator = DecompileCoordinator(
                input_dir=self.extracted_dir,
                output_dir=self.decompiled_dir,
                enable_byte_recovery=decompile_config.get(
                    "enable_byte_recovery", False
                ),
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
        pbl_files: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> PipelineStatsDict:
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
                    logger.info(
                        "Processing file %s/%s: %s", idx + 1, len(pbl_files), pbl_file
                    )
                    self._process_single_file(Path(pbl_file), progress)
                    self._stats["successful"] += 1
                # File processing: catch all exceptions during PBL file processing
                except Exception as e:
                    logger.error("Failed to process {pbl_file}: %s", e)
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
        self._run_extract(pbl_file, progress)
        progress.complete_step(1)

        # Stage 2: Decompile
        progress.start_step("Decompiling P-code", 2)
        self._run_decompile(progress)
        progress.complete_step(2)

        # Stage 3: Parse
        progress.start_step("Parsing source code", 3)
        self._run_parse(progress)
        progress.complete_step(3)

        # Stage 4: Model
        progress.start_step("Building models", 4)
        self._run_model(progress)
        progress.complete_step(4)

        # Stage 5: Generate
        progress.start_step("Generating output", 5)
        self._run_generate(progress)
        progress.complete_step(5)

    def _run_extract(
        self, pbl_file: Path, progress: PipelineProgress
    ) -> ExtractionStatsDict:
        """Run extraction stage with progress tracking.

        Args:
            pbl_file: PBL/PBD file to extract
            progress: Progress tracker

        Returns:
            Extraction results
        """
        stage_start_time = time.time()
        stage_start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
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

            with progress.file_extraction_context(total_files):
                result = self.extract_coordinator.extract(
                    progress_callback=extract_progress
                )

            # Track timing and memory
            stage_end_time = time.time()
            stage_end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            self._record_stage_metrics(
                "extract", 
                stage_start_time, 
                stage_end_time, 
                stage_start_memory, 
                stage_end_memory,
                result
            )

            # Update statistics
            self._update_stage_stats("extract", result)
            return result

        except Exception as e:
            logger.error("Extraction failed: %s", e)
            self._record_error("extract", str(e))
            raise

    def _run_decompile(self, progress: PipelineProgress) -> dict[str, Any]:
        """Run decompilation stage with progress tracking.

        Args:
            progress: Progress tracker

        Returns:
            Decompilation results
        """
        stage_start_time = time.time()
        stage_start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Update coordinator input directory to current extracted files
            self.decompile_coordinator.input_dir = self.extracted_dir
            self.decompile_coordinator.output_dir = self.decompiled_dir
            
            # Count P-code files to decompile - use same extensions as decompile coordinator
            pcode_extensions = [".fun", ".men", ".mef", ".apf", ".udo", ".win"]
            pcode_files: list[Path] = []
            for ext in pcode_extensions:
                pcode_files.extend(self.extracted_dir.rglob(f"*{ext}"))
            total_files = len(pcode_files)

            logger.info(f"Found {total_files} P-code files to decompile in {self.extracted_dir}")

            def decompile_progress(current: int, total: int, message: str) -> None:
                progress.update_operation(current, message)

            with progress.operation_context("Decompiling functions", total_files):
                result = self.decompile_coordinator.decompile(
                    progress_callback=decompile_progress
                )

            # Track timing and memory
            stage_end_time = time.time()
            stage_end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Count lines of code generated
            lines_of_code = self._count_generated_lines(self.decompiled_dir)
            result_with_metrics = dict(result)
            result_with_metrics["lines_of_code_generated"] = lines_of_code
            
            self._record_stage_metrics(
                "decompile", 
                stage_start_time, 
                stage_end_time, 
                stage_start_memory, 
                stage_end_memory,
                result_with_metrics
            )

            # Update statistics
            self._update_stage_stats("decompile", result)
            return result

        except Exception as e:
            logger.error("Decompilation failed: %s", e)
            self._record_error("decompile", str(e))
            raise

    def _run_parse(self, progress: PipelineProgress) -> dict[str, Any]:
        """Run parsing stage with progress tracking.

        Args:
            progress: Progress tracker

        Returns:
            Parsing results
        """
        stage_start_time = time.time()
        stage_start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Update coordinator input directory to current decompiled files
            self.parse_coordinator.input_dir = self.decompiled_dir
            self.parse_coordinator.output_dir = self.parsed_dir
            
            # Count source files to parse
            source_files: list[Path] = []
            for ext in [".sru", ".srw", ".srm", ".srs", ".srd", ".sra"]:
                source_files.extend(self.decompiled_dir.rglob(f"*{ext}"))
            total_files = len(source_files)

            logger.info(f"Found {total_files} source files to parse in {self.decompiled_dir}")

            def parse_progress(current: int, total: int, message: str) -> None:
                progress.update_operation(current, message)

            with progress.operation_context("Parsing source files", total_files):
                result = self.parse_coordinator.parse(progress_callback=parse_progress)

            # Track timing and memory
            stage_end_time = time.time()
            stage_end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Count AST nodes created
            ast_nodes = self._count_ast_nodes(self.parsed_dir)
            result_with_metrics = dict(result)
            result_with_metrics["ast_nodes_created"] = ast_nodes
            
            self._record_stage_metrics(
                "parse", 
                stage_start_time, 
                stage_end_time, 
                stage_start_memory, 
                stage_end_memory,
                result_with_metrics
            )

            # Update statistics
            self._update_stage_stats("parse", result)
            return dict(result)  # Cast ParseStatsDict to dict[str, Any]

        except Exception as e:
            logger.error("Parsing failed: %s", e)
            self._record_error("parse", str(e))
            raise

    def _run_model(self, progress: PipelineProgress) -> dict[str, Any]:
        """Run modeling stage with progress tracking.

        Args:
            progress: Progress tracker

        Returns:
            Modeling results
        """
        stage_start_time = time.time()
        stage_start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Update coordinator input directory to current parsed files
            self.model_coordinator.input_dir = self.parsed_dir
            self.model_coordinator.output_dir = self.model_dir
            
            # Count AST files to process
            ast_files = list(self.parsed_dir.rglob("*.ast.json"))
            total_files = len(ast_files)

            logger.info(f"Found {total_files} AST files to model in {self.parsed_dir}")

            def model_progress(current: int, total: int, message: str) -> None:
                progress.update_operation(current, message)

            with progress.operation_context("Building models", total_files):
                result = self.model_coordinator.process_all(
                    progress_callback=model_progress
                )

            # Track timing and memory
            stage_end_time = time.time()
            stage_end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Count types detected
            types_detected = self._count_types_detected(self.model_dir)
            result_with_metrics = dict(result)
            result_with_metrics["types_detected"] = types_detected
            
            self._record_stage_metrics(
                "model", 
                stage_start_time, 
                stage_end_time, 
                stage_start_memory, 
                stage_end_memory,
                result_with_metrics
            )

            # Update statistics
            self._update_stage_stats("model", result)
            return result

        except Exception as e:
            logger.error("Modeling failed: %s", e)
            self._record_error("model", str(e))
            raise

    def _run_generate(self, progress: PipelineProgress) -> dict[str, Any]:
        """Run generation stage with progress tracking.

        Args:
            progress: Progress tracker

        Returns:
            Generation results
        """
        stage_start_time = time.time()
        stage_start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Update coordinator input directory to current model files
            self.generate_coordinator.input_dir = self.model_dir
            self.generate_coordinator.output_dir = self.generated_dir
            
            # Count model files to process
            model_files = list(self.model_dir.rglob("*.model.json"))
            total_files = len(model_files)

            logger.info(f"Found {total_files} model files to generate from in {self.model_dir}")

            def generate_progress(current: int, total: int, message: str) -> None:
                progress.update_operation(current, message)

            with progress.operation_context("Generating code", total_files):
                result = self.generate_coordinator.generate(
                    progress_callback=generate_progress
                )

            # Track timing and memory
            stage_end_time = time.time()
            stage_end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # Count target language files generated
            target_files = self._count_target_files(self.generated_dir)
            result_with_metrics = dict(result)
            result_with_metrics["target_files_generated"] = target_files
            
            self._record_stage_metrics(
                "generate", 
                stage_start_time, 
                stage_end_time, 
                stage_start_memory, 
                stage_end_memory,
                result_with_metrics
            )

            # Update statistics
            self._update_stage_stats("generate", result)
            return result

        except Exception as e:
            logger.error("Generation failed: %s", e)
            self._record_error("generate", str(e))
            raise

    def _update_stage_stats(self, stage: str, result: Union[Dict[str, Any], Any]) -> None:
        """Update statistics for a stage.

        Args:
            stage: Stage name
            result: Stage results
        """
        if stage not in self._stats["stages"]:
            stage_stats: StageStatsDict = {
                "processed": 0,
                "successful": 0,
                "failed": 0,
            }
            self._stats["stages"][stage] = stage_stats

        stats = self._stats["stages"][stage]
        logger.debug(f"Updating stats for {stage}: {result}")

        # Different stages return results differently - handle each stage specifically
        if isinstance(result, dict):
            if stage == "extract":
                # Extract stage - check for extraction statistics structure
                if "files" in result and isinstance(result["files"], dict):
                    files_stats = result["files"]
                    stats["processed"] += files_stats.get("total", 0)
                    stats["successful"] += files_stats.get("successful", 0)
                    stats["failed"] += files_stats.get("failed", 0)
                elif "entries" in result and isinstance(result["entries"], dict):
                    # Alternative: use entries count if files count not available
                    entries_stats = result["entries"]
                    stats["processed"] += entries_stats.get("total", 0)
                    stats["successful"] += entries_stats.get("successful", 0)
                    stats["failed"] += entries_stats.get("failed", 0)
                elif "extracted_count" in result:
                    # Legacy format support
                    stats["processed"] += result["extracted_count"]
                    stats["successful"] += result["extracted_count"]
                    stats["failed"] += result.get("error_count", 0)
                else:
                    logger.warning(f"Unknown extract result format: {list(result.keys())}")
                    
            elif stage == "decompile":
                # Decompile stage - multiple possible formats
                if "total_files" in result:
                    stats["processed"] += result["total_files"]
                    stats["successful"] += result.get("decompiled", result.get("successful", 0))
                    stats["failed"] += result.get("failed", 0)
                elif "decompiled" in result:
                    # Basic decompile format
                    total = result.get("decompiled", 0) + result.get("failed", 0)
                    stats["processed"] += total
                    stats["successful"] += result["decompiled"]
                    stats["failed"] += result.get("failed", 0)
                elif "status" in result and result["status"] == "completed":
                    # Enhanced decompile format
                    stats["processed"] += result.get("total_files", 0)
                    stats["successful"] += result.get("decompiled", 0)
                    stats["failed"] += result.get("failed", 0)
                else:
                    logger.warning(f"Unknown decompile result format: {list(result.keys())}")
                    
            elif stage == "parse":
                # Parse stage - typically has total_files, successful, failed
                if "total_files" in result:
                    stats["processed"] += result["total_files"]
                    stats["successful"] += result.get("successful", 0)
                    stats["failed"] += result.get("failed", 0)
                elif "statistics" in result and isinstance(result["statistics"], dict):
                    # Nested statistics format
                    parse_stats = result["statistics"]
                    stats["processed"] += parse_stats.get("total_files", 0)
                    stats["successful"] += parse_stats.get("successful", 0)
                    stats["failed"] += parse_stats.get("failed", 0)
                else:
                    logger.warning(f"Unknown parse result format: {list(result.keys())}")
                    
            elif stage == "model":
                # Model stage - typically has total_files, successful, failed
                if "total_files" in result:
                    stats["processed"] += result["total_files"]
                    stats["successful"] += result.get("successful", 0)
                    stats["failed"] += result.get("failed", 0)
                elif "models_created" in result:
                    # Alternative model format
                    total = result.get("models_created", 0) + result.get("failed", 0)
                    stats["processed"] += total
                    stats["successful"] += result.get("models_created", 0)
                    stats["failed"] += result.get("failed", 0)
                else:
                    logger.warning(f"Unknown model result format: {list(result.keys())}")
                    
            elif stage == "generate":
                # Generate stage - has total_models, successful_models, failed_models
                if "total_models" in result:
                    stats["processed"] += result["total_models"]
                    stats["successful"] += result.get("successful_models", 0)
                    stats["failed"] += result.get("failed_models", 0)
                elif "models_processed" in result:
                    # Alternative format
                    stats["processed"] += result.get("models_processed", 0)
                    stats["successful"] += result.get("successful_models", 0)
                    stats["failed"] += result.get("failed_models", 0)
                else:
                    logger.warning(f"Unknown generate result format: {list(result.keys())}")
                    
            else:
                # Generic fallback for unknown stages
                if "total_files" in result:
                    stats["processed"] += result["total_files"]
                    stats["successful"] += result.get("successful", 0)
                    stats["failed"] += result.get("failed", 0)
                else:
                    logger.warning(f"Unknown stage '{stage}' result format: {list(result.keys())}")
        else:
            logger.warning(f"Non-dict result for stage {stage}: {type(result)}")
            
        logger.info(f"Stage {stage} stats: processed={stats['processed']}, successful={stats['successful']}, failed={stats['failed']}")

    def _record_error(self, stage: str, error: str) -> None:
        """Record an error for a stage.

        Args:
            stage: Stage name
            error: Error message
        """
        if stage not in self._stats["error_summary"]["errors"]:
            self._stats["error_summary"]["errors"][stage] = 0
        self._stats["error_summary"]["errors"][stage] += 1

    def _record_stage_metrics(
        self, 
        stage: str, 
        start_time: float, 
        end_time: float, 
        start_memory: float, 
        end_memory: float,
        stage_result: Dict[str, Any]
    ) -> None:
        """Record timing and memory metrics for a stage.

        Args:
            stage: Stage name
            start_time: Stage start timestamp
            end_time: Stage end timestamp
            start_memory: Memory usage at start (MB)
            end_memory: Memory usage at end (MB)
            stage_result: Stage processing results
        """
        duration = end_time - start_time
        memory_used = end_memory - start_memory
        peak_memory = max(start_memory, end_memory)
        
        self._stage_timings[stage] = {
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration,
        }
        
        self._stage_memory[stage] = {
            "start_memory_mb": start_memory,
            "end_memory_mb": end_memory,
            "memory_used_mb": memory_used,
            "peak_memory_mb": peak_memory,
        }
        
        self._stage_details[stage] = stage_result
        
        logger.info(
            f"Stage {stage} completed in {duration:.2f}s, "
            f"memory: {memory_used:+.1f}MB (peak: {peak_memory:.1f}MB)"
        )

    def _count_generated_lines(self, directory: Path) -> int:
        """Count lines of code generated in decompiled files.

        Args:
            directory: Directory containing generated files

        Returns:
            Total number of lines
        """
        total_lines = 0
        try:
            for file_path in directory.rglob("*.sru"):
                try:
                    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                        total_lines += sum(1 for line in f)
                except Exception as e:
                    logger.debug(f"Failed to count lines in {file_path}: {e}")
            
            for file_path in directory.rglob("*.srw"):
                try:
                    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                        total_lines += sum(1 for line in f)
                except Exception as e:
                    logger.debug(f"Failed to count lines in {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Failed to count generated lines: {e}")
        
        return total_lines

    def _count_ast_nodes(self, directory: Path) -> int:
        """Count AST nodes created in parsed files.

        Args:
            directory: Directory containing AST files

        Returns:
            Total number of AST nodes
        """
        total_nodes = 0
        try:
            for ast_file in directory.rglob("*.ast.json"):
                try:
                    with ast_file.open("r", encoding="utf-8") as f:
                        ast_data = json.load(f)
                        # Count nodes recursively in the AST
                        total_nodes += self._count_nodes_recursive(ast_data.get("ast", {}))
                except Exception as e:
                    logger.debug(f"Failed to count nodes in {ast_file}: {e}")
        except Exception as e:
            logger.warning(f"Failed to count AST nodes: {e}")
        
        return total_nodes

    def _count_nodes_recursive(self, node: Any) -> int:
        """Recursively count nodes in an AST structure.

        Args:
            node: AST node (dict, list, or primitive)

        Returns:
            Number of nodes
        """
        if isinstance(node, dict):
            count = 1  # Count this node
            for value in node.values():
                count += self._count_nodes_recursive(value)
            return count
        elif isinstance(node, list):
            count = 0
            for item in node:
                count += self._count_nodes_recursive(item)
            return count
        else:
            return 1  # Primitive value counts as 1 node

    def _count_types_detected(self, directory: Path) -> Dict[str, int]:
        """Count types detected in model files.

        Args:
            directory: Directory containing model files

        Returns:
            Dictionary of type counts
        """
        type_counts = {
            "windows": 0,
            "datawindows": 0,
            "userobjects": 0,
            "functions": 0,
            "structures": 0,
            "menus": 0,
            "applications": 0,
        }
        
        try:
            for model_file in directory.rglob("*.model.json"):
                try:
                    with model_file.open("r", encoding="utf-8") as f:
                        model_data = json.load(f)
                        models = model_data.get("models", [])
                        
                        for model in models:
                            model_type = model.get("type", "").lower()
                            if model_type == "window":
                                type_counts["windows"] += 1
                            elif model_type == "datawindow":
                                type_counts["datawindows"] += 1
                            elif model_type == "userobject":
                                type_counts["userobjects"] += 1
                            elif model_type == "function":
                                type_counts["functions"] += 1
                            elif model_type == "structure":
                                type_counts["structures"] += 1
                            elif model_type == "menu":
                                type_counts["menus"] += 1
                            elif model_type == "application":
                                type_counts["applications"] += 1
                        
                except Exception as e:
                    logger.debug(f"Failed to count types in {model_file}: {e}")
        except Exception as e:
            logger.warning(f"Failed to count types: {e}")
        
        return type_counts

    def _count_target_files(self, directory: Path) -> Dict[str, int]:
        """Count target language files generated.

        Args:
            directory: Directory containing generated files

        Returns:
            Dictionary of file counts by language/type
        """
        file_counts = {
            "dart_files": 0,
            "python_files": 0,
            "sql_files": 0,
            "json_files": 0,
            "other_files": 0,
        }
        
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    suffix = file_path.suffix.lower()
                    if suffix == ".dart":
                        file_counts["dart_files"] += 1
                    elif suffix == ".py":
                        file_counts["python_files"] += 1
                    elif suffix == ".sql":
                        file_counts["sql_files"] += 1
                    elif suffix == ".json":
                        file_counts["json_files"] += 1
                    else:
                        file_counts["other_files"] += 1
        except Exception as e:
            logger.warning(f"Failed to count target files: {e}")
        
        return file_counts

    def _generate_summary(self) -> PipelineStatsDict:
        """Generate final pipeline summary.

        Returns:
            Summary dictionary
        """
        # Add duration
        if self._stats["start_time"] and self._stats["end_time"]:
            duration = self._stats["end_time"] - self._stats["start_time"]
            self._stats["duration_seconds"] = duration

        # Add enhanced stage metrics
        if self._stage_timings:
            self._stats["stage_timings"] = self._stage_timings
        if self._stage_memory:
            self._stats["stage_memory"] = self._stage_memory
        if self._stage_details:
            self._stats["stage_details"] = self._stage_details

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
                cache_perf: CachePerformanceDict = {
                    "total_hits": total_hits,
                    "total_misses": total_misses,
                    "overall_hit_rate": overall_hit_rate,
                }
                self._stats["cache_performance"] = cache_perf

        # Create comprehensive summary with enhanced metrics
        enhanced_summary = self._create_enhanced_summary()
        
        # Save detailed summary to file
        summary_path = self.output_dir / "pipeline_summary.json"
        with open(summary_path, "w") as f:
            json.dump(self._stats, f, indent=2)

        # Save user-friendly summary
        readable_summary_path = self.output_dir / "pipeline_summary_readable.txt"
        with open(readable_summary_path, "w") as f:
            f.write(enhanced_summary)

        logger.info("Pipeline summary saved to %s", summary_path)
        logger.info("Readable summary saved to %s", readable_summary_path)

        return self._stats

    def _create_enhanced_summary(self) -> str:
        """Create a comprehensive, user-friendly summary report.
        
        Returns:
            Formatted summary string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("POWERBUILDER PIPELINE SUMMARY REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Overall statistics
        total_files = self._stats.get("total_files", 0)
        successful = self._stats.get("successful", 0)
        failed = self._stats.get("failed", 0)
        duration = self._stats.get("duration_seconds", 0)
        
        lines.append("OVERALL PIPELINE RESULTS")
        lines.append("-" * 40)
        lines.append(f"Total Files Processed: {total_files}")
        lines.append(f"Successful: {successful}")
        lines.append(f"Failed: {failed}")
        if total_files > 0:
            success_rate = (successful / total_files) * 100
            lines.append(f"Success Rate: {success_rate:.1f}%")
        lines.append(f"Total Duration: {duration:.2f} seconds")
        lines.append("")
        
        # Stage-by-stage breakdown
        lines.append("STAGE-BY-STAGE BREAKDOWN")
        lines.append("-" * 40)
        
        for stage_name in ["extract", "decompile", "parse", "model", "generate"]:
            if stage_name in self._stats.get("stages", {}):
                stage_stats = self._stats["stages"][stage_name]
                stage_timing = self._stage_timings.get(stage_name, {})
                stage_memory = self._stage_memory.get(stage_name, {})
                stage_details = self._stage_details.get(stage_name, {})
                
                lines.append(f"\n{stage_name.upper()} STAGE:")
                lines.append(f"  Files Processed: {stage_stats.get('processed', 0)}")
                lines.append(f"  Successful: {stage_stats.get('successful', 0)}")
                lines.append(f"  Failed: {stage_stats.get('failed', 0)}")
                
                if stage_timing:
                    duration = stage_timing.get("duration_seconds", 0)
                    lines.append(f"  Duration: {duration:.2f} seconds")
                
                if stage_memory:
                    memory_used = stage_memory.get("memory_used_mb", 0)
                    peak_memory = stage_memory.get("peak_memory_mb", 0)
                    lines.append(f"  Memory Used: {memory_used:+.1f}MB (Peak: {peak_memory:.1f}MB)")
                
                # Stage-specific metrics
                if stage_name == "extract" and stage_details:
                    if "entries" in stage_details:
                        entries = stage_details["entries"]
                        lines.append(f"  Entries Extracted: {entries.get('successful', 0)}")
                
                elif stage_name == "decompile" and stage_details:
                    if "lines_of_code_generated" in stage_details:
                        lines.append(f"  Lines of Code Generated: {stage_details['lines_of_code_generated']}")
                
                elif stage_name == "parse" and stage_details:
                    if "ast_nodes_created" in stage_details:
                        lines.append(f"  AST Nodes Created: {stage_details['ast_nodes_created']}")
                    if "errors" in stage_details:
                        lines.append(f"  Parse Errors: {len(stage_details['errors'])}")
                
                elif stage_name == "model" and stage_details:
                    if "types_detected" in stage_details:
                        types = stage_details["types_detected"]
                        lines.append(f"  Types Detected:")
                        for type_name, count in types.items():
                            if count > 0:
                                lines.append(f"    {type_name.title()}: {count}")
                
                elif stage_name == "generate" and stage_details:
                    if "target_files_generated" in stage_details:
                        files = stage_details["target_files_generated"]
                        lines.append(f"  Target Files Generated:")
                        for file_type, count in files.items():
                            if count > 0:
                                lines.append(f"    {file_type.replace('_', ' ').title()}: {count}")
        
        # Error summary
        if self._stats.get("error_summary", {}).get("errors"):
            lines.append("\nERROR SUMMARY")
            lines.append("-" * 40)
            for stage, error_count in self._stats["error_summary"]["errors"].items():
                lines.append(f"{stage.title()}: {error_count} errors")
        
        # Cache performance
        if "cache_performance" in self._stats:
            cache_perf = self._stats["cache_performance"]
            lines.append("\nCACHE PERFORMANCE")
            lines.append("-" * 40)
            lines.append(f"Total Hits: {cache_perf['total_hits']}")
            lines.append(f"Total Misses: {cache_perf['total_misses']}")
            lines.append(f"Hit Rate: {cache_perf['overall_hit_rate']:.1f}%")
        
        lines.append("")
        lines.append("=" * 80)
        
        return "\n".join(lines)
