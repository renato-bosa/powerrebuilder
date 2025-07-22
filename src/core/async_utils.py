"""Async pipeline utilities and main coordinator."""

from pathlib import Path
from typing import Any

from src.common.pipeline.progress import Progress
from src.decompile.async_coordinator import AsyncDecompileCoordinator
from src.extract.async_coordinator import AsyncExtractCoordinator
from src.generate.async_coordinator import AsyncGenerateCoordinator
from src.parse.async_coordinator import AsyncParseCoordinator


class PipelineMetrics:
    """Placeholder for pipeline metrics."""



class ParallelPipeline:
    """Placeholder for parallel pipeline."""

    def __init__(self, name: str) -> None:
        self.name = name


class AsyncPipelineCoordinator:
    """Main async pipeline coordinator that orchestrates all stages."""

    def __init__(self, target: str = "flutter") -> None:
        self.target = target
        self.extract = AsyncExtractCoordinator()
        self.parse = AsyncParseCoordinator()
        self.decompile = AsyncDecompileCoordinator()
        self.generate = AsyncGenerateCoordinator(target)

    async def run_pipeline_async(
        self,
        input_path: Path,
        output_path: Path,
        stages: list[str] | None = None,
        _progress: Progress | None = None,
    ) -> dict[str, Any]:
        """Run the full pipeline asynchronously with parallel stages."""
        if stages is None:
            stages = ["extract", "parse", "decompile", "generate"]

        # Initialize coordinators
        await self.parse.initialize()

        # Create parallel pipeline
        ParallelPipeline("powerrebuilder")

        # Set up working directories
        work_dir = output_path / ".work"
        work_dir.mkdir(parents=True, exist_ok=True)

        results = {"stages": {}, "metrics": {}}

        current_input = input_path

        # Add stages based on configuration
        if "extract" in stages:
            extract_output = work_dir / "extracted"
            extract_results = await self.extract.extract_directory_async(
                current_input, extract_output
            )
            results["stages"]["extract"] = extract_results
            current_input = extract_output

        # Parse and Decompile can run in parallel
        if "parse" in stages and "decompile" in stages:
            parse_output = work_dir / "parsed"
            decompile_output = work_dir / "decompiled"

            # Run both stages in parallel
            parse_task = self.parse.parse_directory_async(current_input, parse_output)
            decompile_task = self.decompile.decompile_directory_async(
                current_input, decompile_output
            )

            import asyncio

            parse_results, decompile_results = await asyncio.gather(
                parse_task, decompile_task
            )

            results["stages"]["parse"] = parse_results
            results["stages"]["decompile"] = decompile_results
            current_input = parse_output

        elif "parse" in stages:
            parse_output = work_dir / "parsed"
            parse_results = await self.parse.parse_directory_async(
                current_input, parse_output
            )
            results["stages"]["parse"] = parse_results
            current_input = parse_output

        elif "decompile" in stages:
            decompile_output = work_dir / "decompiled"
            decompile_results = await self.decompile.decompile_directory_async(
                current_input, decompile_output
            )
            results["stages"]["decompile"] = decompile_results

        if "generate" in stages:
            generate_output = output_path / "generated"
            generate_results = await self.generate.generate_directory_async(
                current_input, generate_output
            )
            results["stages"]["generate"] = generate_results

        # Collect metrics
        results["metrics"] = {
            "extract": self.extract.metrics.__dict__,
            "parse": self.parse.metrics.__dict__,
            "decompile": self.decompile.metrics.__dict__,
            "generate": self.generate.metrics.__dict__,
        }

        return results
