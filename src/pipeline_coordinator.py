"""Main pipeline coordinator that orchestrates all conversion stages.

This module provides the main entry point for the PowerBuilder to Flutter
conversion pipeline, coordinating all stages from extraction to code generation.

Pipeline Architecture (Sequential Execution):
1. Extract: Produces .fun files from PBL/PBD archives
2. Decompile: Converts .fun files to .sru source files
3. Parse: Processes .sru files into Abstract Syntax Trees (ASTs)
4. Model: Converts ASTs into structured model objects
5. Generate: Produces Python/Dart code from model objects

IMPORTANT: All stages run SEQUENTIALLY, with each stage feeding into the next.
"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from src.common.pipeline.progress import PipelineProgress
from src.decompile.coordinator import DecompileCoordinator
from src.extract.coordinator import ExtractCoordinator
from src.generate.coordinator import GenerateCoordinator
from src.model.coordinator import ModelCoordinator
from src.parse.coordinator import ParseCoordinator

logger = logging.getLogger(__name__)


class PipelineCoordinator:
    """Main coordinator that orchestrates all pipeline stages.

    This coordinator manages the sequential execution of all stages in the
    PowerBuilder to Flutter conversion pipeline.
    """

    def __init__(
        self,
        input_path: Path | str,
        output_dir: Path | str,
        enable_recovery: bool = True,
        validate_output: bool = True,
        framework: str = "flutter",
    ) -> None:
        """Initialize the pipeline coordinator.

        Args:
            input_path: Path to input PBL/PBD file or directory
            output_dir: Base output directory for all stages
            enable_recovery: Whether to enable error recovery
            validate_output: Whether to validate outputs at each stage
            framework: Target framework for generation (flutter/python)
        """
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.enable_recovery = enable_recovery
        self.validate_output = validate_output
        self.framework = framework

        # Create stage output directories
        self.stage_dirs = {
            "extracted": self.output_dir / "1_extracted",
            "decompiled": self.output_dir / "2_decompiled",
            "parsed": self.output_dir / "3_parsed",
            "model": self.output_dir / "4_model",
            "generated": self.output_dir / "5_generated",
        }

        # Ensure all directories exist
        for stage_dir in self.stage_dirs.values():
            stage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize progress tracker
        self.progress = PipelineProgress()

        # Statistics for each stage
        self.stage_stats = {}

    def run(self, progress_callback=None) -> dict[str, Any]:
        """Run the complete pipeline.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with pipeline results
        """
        logger.info("Starting PowerBuilder to Flutter pipeline")
        logger.info("Input: %s", self.input_path)
        logger.info("Output: %s", self.output_dir)
        logger.info("Framework: %s", self.framework)

        start_time = datetime.now()
        results = {
            "success": True,
            "stages": {},
            "errors": [],
            "warnings": [],
        }

        try:
            # Stage 1: Extract
            if progress_callback:
                progress_callback("Stage 1/5: Extracting files", 0)

            extract_result = self._run_extract_stage(progress_callback)
            results["stages"]["extract"] = extract_result
            self.stage_stats["extract"] = extract_result

            if not extract_result.get("success", False):
                results["success"] = False
                results["errors"].append("Extract stage failed")
                return results

            # Stage 2: Decompile
            if progress_callback:
                progress_callback("Stage 2/5: Decompiling P-code", 20)

            decompile_result = self._run_decompile_stage(progress_callback)
            results["stages"]["decompile"] = decompile_result
            self.stage_stats["decompile"] = decompile_result

            if not decompile_result.get("success", False):
                results["success"] = False
                results["errors"].append("Decompile stage failed")
                return results

            # Stage 3: Parse
            if progress_callback:
                progress_callback("Stage 3/5: Parsing source files", 40)

            parse_result = self._run_parse_stage(progress_callback)
            results["stages"]["parse"] = parse_result
            self.stage_stats["parse"] = parse_result

            if not parse_result.get("success", False):
                results["success"] = False
                results["errors"].append("Parse stage failed")
                return results

            # Stage 4: Model
            if progress_callback:
                progress_callback("Stage 4/5: Building object models", 60)

            model_result = self._run_model_stage(progress_callback)
            results["stages"]["model"] = model_result
            self.stage_stats["model"] = model_result

            if not model_result.get("success", False):
                results["success"] = False
                results["errors"].append("Model stage failed")
                return results

            # Stage 5: Generate
            if progress_callback:
                progress_callback("Stage 5/5: Generating code", 80)

            generate_result = self._run_generate_stage(progress_callback)
            results["stages"]["generate"] = generate_result
            self.stage_stats["generate"] = generate_result

            if not generate_result.get("success", False):
                results["success"] = False
                results["errors"].append("Generate stage failed")

            # Write pipeline summary
            self._write_pipeline_summary(results)

            if progress_callback:
                progress_callback("Pipeline complete", 100)

        except Exception as e:
            logger.error("Pipeline failed with error: %s", e)
            logger.error(traceback.format_exc())
            results["success"] = False
            results["errors"].append(str(e))

        # Calculate total time
        end_time = datetime.now()
        results["duration"] = str(end_time - start_time)
        results["completed_at"] = end_time.isoformat()

        # Log summary
        logger.info("=" * 60)
        logger.info("Pipeline Summary:")
        logger.info("  Success: %s", results["success"])
        logger.info("  Duration: %s", results["duration"])

        for stage_name, stage_result in results["stages"].items():
            logger.info(
                "  %s: %s",
                stage_name.capitalize(),
                "✓" if stage_result.get("success", False) else "✗",
            )

        logger.info("=" * 60)

        return results

    def _run_extract_stage(self, progress_callback=None) -> dict[str, Any]:
        """Run the extract stage.

        Args:
            progress_callback: Optional progress callback

        Returns:
            Stage results
        """
        try:
            coordinator = ExtractCoordinator(
                input_path=self.input_path, output_dir=self.stage_dirs["extracted"]
            )

            # Create sub-progress callback
            def extract_progress(msg, pct):
                if progress_callback:
                    # Map 0-100% to 0-20% of overall pipeline
                    overall_pct = int(pct * 0.2)
                    progress_callback(f"Extract: {msg}", overall_pct)

            result = coordinator.extract(extract_progress)

            # Add success flag
            result["success"] = result.get("extracted_count", 0) > 0

            return result

        except Exception as e:
            logger.error("Extract stage failed: %s", e)
            return {
                "success": False,
                "error": str(e),
                "extracted_count": 0,
            }

    def _run_decompile_stage(self, progress_callback=None) -> dict[str, Any]:
        """Run the decompile stage.

        Args:
            progress_callback: Optional progress callback

        Returns:
            Stage results
        """
        try:
            coordinator = DecompileCoordinator(
                input_dir=self.stage_dirs["extracted"],
                output_dir=self.stage_dirs["decompiled"],
                enable_filtering=True,
            )

            # Create sub-progress callback
            def decompile_progress(msg, pct):
                if progress_callback:
                    # Map 0-100% to 20-40% of overall pipeline
                    overall_pct = 20 + int(pct * 0.2)
                    progress_callback(f"Decompile: {msg}", overall_pct)

            result = coordinator.decompile()

            # Add success flag
            result["success"] = result.get("status") == "completed"

            return result

        except Exception as e:
            logger.error("Decompile stage failed: %s", e)
            return {
                "success": False,
                "error": str(e),
                "status": "failed",
            }

    def _run_parse_stage(self, progress_callback=None) -> dict[str, Any]:
        """Run the parse stage.

        Args:
            progress_callback: Optional progress callback

        Returns:
            Stage results
        """
        try:
            coordinator = ParseCoordinator(
                input_dir=self.stage_dirs["decompiled"],
                output_dir=self.stage_dirs["parsed"],
                enable_recovery=self.enable_recovery,
                validate_ast=self.validate_output,
            )

            # Create sub-progress callback
            def parse_progress(msg, pct):
                if progress_callback:
                    # Map 0-100% to 40-60% of overall pipeline
                    overall_pct = 40 + int(pct * 0.2)
                    progress_callback(f"Parse: {msg}", overall_pct)

            result = coordinator.parse(parse_progress)

            # Add success flag
            result["success"] = result.get("successful", 0) > 0

            return result

        except Exception as e:
            logger.error("Parse stage failed: %s", e)
            return {
                "success": False,
                "error": str(e),
                "successful": 0,
                "failed": 0,
            }

    def _run_model_stage(self, progress_callback=None) -> dict[str, Any]:
        """Run the model stage.

        Args:
            progress_callback: Optional progress callback

        Returns:
            Stage results
        """
        try:
            # Import services for model coordinator
            from src.model.services.ast_processor import ASTProcessor
            from src.model.services.entity_factory import EntityFactory
            from src.model.services.entity_validator import EntityValidator
            from src.model.services.model_extractor import ModelExtractor
            from src.model.services.model_persistence import ModelPersistence
            from src.model.services.relationship_manager import RelationshipManager

            # Create services
            entity_factory = EntityFactory()
            entity_validator = EntityValidator()
            relationship_manager = RelationshipManager()
            ast_processor = ASTProcessor()
            model_extractor = ModelExtractor()
            model_persistence = ModelPersistence()

            coordinator = ModelCoordinator(
                entity_factory=entity_factory,
                entity_validator=entity_validator,
                relationship_manager=relationship_manager,
                ast_processor=ast_processor,
                model_extractor=model_extractor,
                model_persistence=model_persistence,
                input_dir=self.stage_dirs["parsed"],
                output_dir=self.stage_dirs["model"],
            )

            # Create sub-progress callback
            def model_progress(msg, pct):
                if progress_callback:
                    # Map 0-100% to 60-80% of overall pipeline
                    overall_pct = 60 + int(pct * 0.2)
                    progress_callback(f"Model: {msg}", overall_pct)

            result = coordinator.convert_directory()

            # Add success flag
            result["success"] = result.get("processed", 0) > 0

            return result

        except Exception as e:
            logger.error("Model stage failed: %s", e)
            return {
                "success": False,
                "error": str(e),
                "processed": 0,
                "failed": 0,
            }

    def _run_generate_stage(self, progress_callback=None) -> dict[str, Any]:
        """Run the generate stage.

        Args:
            progress_callback: Optional progress callback

        Returns:
            Stage results
        """
        try:
            coordinator = GenerateCoordinator(
                input_dir=self.stage_dirs["model"],
                output_dir=self.stage_dirs["generated"],
                framework=self.framework,
                null_safety=True,
                generate_tests=False,
            )

            # Create sub-progress callback
            def generate_progress(msg, pct):
                if progress_callback:
                    # Map 0-100% to 80-100% of overall pipeline
                    overall_pct = 80 + int(pct * 0.2)
                    progress_callback(f"Generate: {msg}", overall_pct)

            result = coordinator.generate(generate_progress)

            # Add success flag if not present
            if "success" not in result:
                result["success"] = result.get("successful_models", 0) > 0

            return result

        except Exception as e:
            logger.error("Generate stage failed: %s", e)
            return {
                "success": False,
                "error": str(e),
                "successful_models": 0,
                "failed_models": 0,
            }

    def _write_pipeline_summary(self, results: dict[str, Any]) -> None:
        """Write pipeline summary to output directory.

        Args:
            results: Pipeline results
        """
        summary = {
            "pipeline_version": "2.0",
            "executed_at": datetime.now().isoformat(),
            "input_path": str(self.input_path),
            "output_dir": str(self.output_dir),
            "framework": self.framework,
            "stages": self.stage_stats,
            "overall_success": results["success"],
            "errors": results["errors"],
            "warnings": results["warnings"],
        }

        summary_path = self.output_dir / "pipeline_summary.json"
        with summary_path.open("w") as f:
            json.dump(summary, f, indent=2)

        logger.info("Pipeline summary written to %s", summary_path)
