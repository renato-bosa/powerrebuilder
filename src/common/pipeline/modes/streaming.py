"""Streaming pipeline coordinator with in-memory communication.

This coordinator runs pipeline stages with direct memory streaming,
eliminating file I/O between stages.
"""

import asyncio
import json
import logging
import queue
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from src.common.pipeline.streaming import (
    AsyncMemoryStream,
    MemoryStream,
    StreamManager,
    get_stream_manager,
)

logger = logging.getLogger(__name__)


class StreamingPipelineCoordinator:
    """Coordinator for streaming pipeline execution."""

    def __init__(
        self,
        extract_coordinator,
        decompile_coordinator,
        parse_coordinator,
        model_coordinator,
        generate_coordinator,
        stream_manager=None,
        max_workers: int = 4,
    ) -> None:
        """Initialize streaming pipeline coordinator.

        Args:
            extract_coordinator: Extraction stage coordinator
            decompile_coordinator: Decompilation stage coordinator
            parse_coordinator: Parse stage coordinator
            model_coordinator: Model stage coordinator
            generate_coordinator: Generate stage coordinator
            stream_manager: Stream manager instance
            max_workers: Maximum worker threads
        """
        self.extract_coordinator = extract_coordinator
        self.decompile_coordinator = decompile_coordinator
        self.parse_coordinator = parse_coordinator
        self.model_coordinator = model_coordinator
        self.generate_coordinator = generate_coordinator

        self.stream_manager = stream_manager or get_stream_manager()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        self._running = False
        self._stats = {
            "stages_completed": 0,
            "items_processed": 0,
            "errors": [],
            "memory_saved_mb": 0,
        }

    def run_pipeline(
        self,
        input_path: Path,
        output_path: Path,
        target: str = "flutter",
        use_streaming: bool = True,
    ) -> dict[str, Any]:
        """Run the full pipeline with optional streaming.

        Args:
            input_path: Input file/directory path
            output_path: Output directory path
            target: Target framework for generation
            use_streaming: Use in-memory streaming vs file I/O

        Returns:
            Pipeline execution statistics
        """
        logger.info(
            "Starting pipeline: %s -> %s (streaming: %s)",
            input_path,
            output_path,
            use_streaming,
        )

        self._running = True

        try:
            if use_streaming:
                return self._run_streaming_pipeline(input_path, output_path, target)
            return self._run_file_based_pipeline(input_path, output_path, target)
        finally:
            self._running = False
            self.stream_manager.close_all()

    def _run_streaming_pipeline(
        self, input_path: Path, output_path: Path, target: str
    ) -> dict[str, Any]:
        """Run pipeline with in-memory streaming."""
        # Create streams between stages
        extract_to_decompile = self.stream_manager.create_stream(
            "extract_to_decompile", "extract", "decompile", "pcode_data", maxsize=100
        )

        decompile_to_parse = self.stream_manager.create_stream(
            "decompile_to_parse", "decompile", "parse", "source_code", maxsize=100
        )

        parse_to_model = self.stream_manager.create_stream(
            "parse_to_model", "parse", "model", "ast", maxsize=100
        )

        model_to_generate = self.stream_manager.create_stream(
            "model_to_generate", "model", "generate", "model", maxsize=100
        )

        # Create stage futures
        futures = []

        # Extract stage
        extract_future = self.executor.submit(
            self._run_extract_stage, input_path, extract_to_decompile
        )
        futures.append(("extract", extract_future))

        # Decompile stage
        decompile_future = self.executor.submit(
            self._run_decompile_stage, extract_to_decompile, decompile_to_parse
        )
        futures.append(("decompile", decompile_future))

        # Parse stage
        parse_future = self.executor.submit(
            self._run_parse_stage, decompile_to_parse, parse_to_model
        )
        futures.append(("parse", parse_future))

        # Model stage
        model_future = self.executor.submit(
            self._run_model_stage, parse_to_model, model_to_generate
        )
        futures.append(("model", model_future))

        # Generate stage
        generate_future = self.executor.submit(
            self._run_generate_stage, model_to_generate, output_path, target
        )
        futures.append(("generate", generate_future))

        # Wait for all stages to complete
        stage_results = {}
        for stage_name, future in futures:
            try:
                result = future.result(timeout=3600)  # 1 hour timeout
                stage_results[stage_name] = result
                self._stats["stages_completed"] += 1
                logger.info("Stage %s completed: %s", stage_name, result)
            except Exception as e:
                logger.error("Stage %s failed: %s", stage_name, e)
                self._stats["errors"].append(f"{stage_name}: {str(e)}")
                stage_results[stage_name] = {"error": str(e)}

        # Calculate memory savings
        stream_stats = self.stream_manager.get_stats()
        total_bytes = sum(s["bytes"] for s in stream_stats.values())
        self._stats["memory_saved_mb"] = total_bytes / (1024 * 1024)

        self._stats["stage_results"] = stage_results
        self._stats["stream_stats"] = stream_stats

        return self._stats

    def _run_extract_stage(
        self, input_path: Path, output_stream: MemoryStream
    ) -> dict[str, Any]:
        """Run extraction stage with streaming output."""
        logger.info("Starting extraction stage")
        stats = {"files_extracted": 0, "errors": 0}

        try:
            # For PBL/PBD files, we need to extract objects
            if input_path.suffix.lower() in [".pbl", ".pbd"]:
                # Use a temporary directory for extraction
                temp_dir = Path("/tmp/powerrebuilder_extract")
                temp_dir.mkdir(exist_ok=True)

                # Run extraction
                self.extract_coordinator.extract(input_path, temp_dir)

                # Stream extracted files
                pcode_extensions = ["*.fun", "*.udo", "*.win"]
                for pattern in pcode_extensions:
                    for pcode_file in temp_dir.rglob(pattern):
                        try:
                            with Path(pcode_file).open("rb") as f:
                                pcode_data = f.read()

                            # Write to stream
                            output_stream.write(
                                {
                                    "filename": pcode_file.name,
                                    "object_name": pcode_file.stem,
                                    "data": pcode_data,
                                    "size": len(pcode_data),
                                }
                            )

                            stats["files_extracted"] += 1

                            # Delete temporary file to save space
                            pcode_file.unlink()

                        except Exception as e:
                            logger.error("Failed to stream %s: %s", pcode_file, e)
                            stats["errors"] += 1

                # Clean up temp directory
                import shutil

                shutil.rmtree(temp_dir, ignore_errors=True)

            else:
                # For directories, stream existing P-code files (.fun, .udo, .win)
                pcode_extensions = ["*.fun", "*.udo", "*.win"]
                for pattern in pcode_extensions:
                    for pcode_file in Path(input_path).rglob(pattern):
                        try:
                            with Path(pcode_file).open("rb") as f:
                                pcode_data = f.read()

                            output_stream.write(
                                {
                                    "filename": pcode_file.name,
                                    "object_name": pcode_file.stem,
                                    "data": pcode_data,
                                    "size": len(pcode_data),
                                }
                            )

                            stats["files_extracted"] += 1

                        except Exception as e:
                            logger.error("Failed to stream %s: %s", pcode_file, e)
                            stats["errors"] += 1

        finally:
            output_stream.close()

        logger.info("Extraction stage complete: %s", stats)
        return stats

    def _run_decompile_stage(
        self, input_stream: MemoryStream, output_stream: MemoryStream
    ) -> dict[str, Any]:
        """Run decompilation stage with streaming."""
        logger.info("Starting decompilation stage")
        stats = {"files_decompiled": 0, "errors": 0}

        try:
            while not input_stream.is_closed or input_stream._queue.size > 0:
                try:
                    # Read pcode data from stream
                    pcode_item = input_stream.read()
                    if pcode_item is None:
                        break

                    # Decompile in memory
                    object_name = pcode_item["object_name"]
                    pcode_data = pcode_item["data"]

                    # Create minimal decompiler input
                    from io import BytesIO

                    BytesIO(pcode_data)

                    # Run decompilation
                    try:
                        # This would need adaptation in the decompiler
                        # For now, simulate decompilation
                        decompiled_source = self._decompile_pcode(
                            object_name, pcode_data
                        )

                        # Write to output stream
                        output_stream.write(
                            {
                                "filename": f"{object_name}.sru",
                                "object_name": object_name,
                                "source": decompiled_source,
                                "size": len(decompiled_source),
                            }
                        )

                        stats["files_decompiled"] += 1
                        self._stats["items_processed"] += 1

                    except Exception as e:
                        logger.error("Failed to decompile %s: %s", object_name, e)
                        stats["errors"] += 1

                except queue.Empty:
                    # No items available, wait a bit
                    import time

                    time.sleep(0.1)
                    continue

        finally:
            output_stream.close()

        logger.info("Decompilation stage complete: %s", stats)
        return stats

    def _run_parse_stage(
        self, input_stream: MemoryStream, output_stream: MemoryStream
    ) -> dict[str, Any]:
        """Run parse stage with streaming."""
        logger.info("Starting parse stage")
        stats = {"files_parsed": 0, "errors": 0}

        try:
            while not input_stream.is_closed or input_stream._queue.size > 0:
                try:
                    # Read source code from stream
                    source_item = input_stream.read()
                    if source_item is None:
                        break

                    object_name = source_item["object_name"]
                    source_code = source_item["source"]

                    # Parse source code
                    try:
                        # This would need the parser to accept string input
                        ast = self._parse_source(object_name, source_code)

                        # Write AST to output stream
                        output_stream.write(
                            {
                                "filename": f"{object_name}.ast",
                                "object_name": object_name,
                                "ast": ast,
                                "source_lines": len(source_code.splitlines()),
                            }
                        )

                        stats["files_parsed"] += 1
                        self._stats["items_processed"] += 1

                    except Exception as e:
                        logger.error("Failed to parse %s: %s", object_name, e)
                        stats["errors"] += 1

                except queue.Empty:
                    import time

                    time.sleep(0.1)
                    continue

        finally:
            output_stream.close()

        logger.info("Parse stage complete: %s", stats)
        return stats

    def _run_model_stage(
        self, input_stream: MemoryStream, output_stream: MemoryStream
    ) -> dict[str, Any]:
        """Run model stage with streaming."""
        logger.info("Starting model stage")
        stats = {"models_created": 0, "errors": 0}

        try:
            while not input_stream.is_closed or input_stream._queue.size > 0:
                try:
                    # Read AST from stream
                    ast_item = input_stream.read()
                    if ast_item is None:
                        break

                    object_name = ast_item["object_name"]
                    ast = ast_item["ast"]

                    # Build model
                    try:
                        model = self._build_model(object_name, ast)

                        # Write model to output stream
                        output_stream.write(
                            {
                                "filename": f"{object_name}.model",
                                "object_name": object_name,
                                "model": model,
                                "type": model.get("type", "unknown"),
                            }
                        )

                        stats["models_created"] += 1
                        self._stats["items_processed"] += 1

                    except Exception as e:
                        logger.error("Failed to build model %s: %s", object_name, e)
                        stats["errors"] += 1

                except queue.Empty:
                    import time

                    time.sleep(0.1)
                    continue

        finally:
            output_stream.close()

        logger.info("Model stage complete: %s", stats)
        return stats

    def _run_generate_stage(
        self, input_stream: MemoryStream, output_path: Path, target: str
    ) -> dict[str, Any]:
        """Run generate stage with streaming input."""
        logger.info("Starting generate stage")

        # Collect all models first (generator needs them all for relationships)
        models = {}

        try:
            while not input_stream.is_closed or input_stream._queue.size > 0:
                try:
                    model_item = input_stream.read()
                    if model_item is None:
                        break

                    object_name = model_item["object_name"]
                    model = model_item["model"]
                    models[object_name] = model

                except queue.Empty:
                    import time

                    time.sleep(0.1)
                    continue

        finally:
            input_stream.close()

        # Write models to temporary directory for generator
        # (Until generator supports in-memory models)
        temp_model_dir = Path("/tmp/powerrebuilder_models")
        temp_model_dir.mkdir(exist_ok=True)

        for name, model in models.items():
            model_path = temp_model_dir / f"{name}.json"
            with Path(model_path).open("w") as f:
                json.dump(model, f, indent=2)

        # Run generation
        result = self.generate_coordinator.generate(temp_model_dir, output_path, target)

        # Clean up
        import shutil

        shutil.rmtree(temp_model_dir, ignore_errors=True)

        logger.info("Generate stage complete: %s", result)
        return result

    def _run_file_based_pipeline(
        self, input_path: Path, output_path: Path, target: str
    ) -> dict[str, Any]:
        """Run traditional file-based pipeline."""
        # Stage directories
        extract_dir = output_path / "extracted"
        decompile_dir = output_path / "decompiled"
        parse_dir = output_path / "parsed"
        model_dir = output_path / "models"
        generate_dir = output_path / "generated"

        # Run stages sequentially
        stages = [
            ("extract", self.extract_coordinator.extract, input_path, extract_dir),
            (
                "decompile",
                self.decompile_coordinator.decompile,
                extract_dir,
                decompile_dir,
            ),
            ("parse", self.parse_coordinator.parse, decompile_dir, parse_dir),
            ("model", self.model_coordinator.build_models, parse_dir, model_dir),
            (
                "generate",
                self.generate_coordinator.generate,
                model_dir,
                generate_dir,
                target,
            ),
        ]

        stage_results = {}
        for stage_name, stage_func, *args in stages:
            try:
                logger.info("Running %s stage", stage_name)
                result = stage_func(*args)
                stage_results[stage_name] = result
                self._stats["stages_completed"] += 1
            except Exception as e:
                logger.error("Stage %s failed: %s", stage_name, e)
                self._stats["errors"].append(f"{stage_name}: {str(e)}")
                stage_results[stage_name] = {"error": str(e)}
                break

        self._stats["stage_results"] = stage_results
        return self._stats

    # Helper methods for in-memory processing

    def _decompile_pcode(self, object_name: str, pcode_data: bytes) -> str:
        """Decompile pcode data in memory."""
        # This is a simplified version - real implementation would use
        # the decompiler's internal methods
        from io import StringIO

        output = StringIO()

        # Write header
        output.write(f"// Object: {object_name}\n")
        output.write(f"// Size: {len(pcode_data)} bytes\n\n")

        # Simplified decompilation (would use real decompiler)
        output.write("forward\n")
        output.write(f"global type {object_name} from nonvisualobject\n")
        output.write("end type\n")
        output.write("end forward\n\n")

        return output.getvalue()

    def _parse_source(self, object_name: str, source_code: str) -> dict[str, Any]:
        """Parse source code in memory."""
        # Simplified parsing - real implementation would use parser
        return {
            "type": "parsed_object",
            "name": object_name,
            "source_lines": len(source_code.splitlines()),
            "body": [],  # Would contain actual AST
        }

    def _build_model(self, object_name: str, ast: dict[str, Any]) -> dict[str, Any]:
        """Build model from AST in memory."""
        # Simplified model building
        return {
            "type": "model",
            "name": object_name,
            "ast": ast,
            "properties": {},
            "methods": [],
        }


class AsyncStreamingPipeline:
    """Async version of streaming pipeline for better concurrency."""

    def __init__(self, coordinators: dict[str, Any]) -> None:
        """Initialize async streaming pipeline.

        Args:
            coordinators: Dictionary of stage coordinators
        """
        self.coordinators = coordinators
        self.stream_manager = StreamManager()

    async def run_pipeline(
        self, input_path: Path, output_path: Path, target: str = "flutter"
    ) -> dict[str, Any]:
        """Run async pipeline with streaming."""
        # Create async streams
        streams = {
            "extract_to_decompile": AsyncMemoryStream(
                "extract", "decompile", "pcode", 100
            ),
            "decompile_to_parse": AsyncMemoryStream(
                "decompile", "parse", "source", 100
            ),
            "parse_to_model": AsyncMemoryStream("parse", "model", "ast", 100),
            "model_to_generate": AsyncMemoryStream("model", "generate", "model", 100),
        }

        # Create stage tasks
        tasks = [
            self._run_extract_async(input_path, streams["extract_to_decompile"]),
            self._run_decompile_async(
                streams["extract_to_decompile"], streams["decompile_to_parse"]
            ),
            self._run_parse_async(
                streams["decompile_to_parse"], streams["parse_to_model"]
            ),
            self._run_model_async(
                streams["parse_to_model"], streams["model_to_generate"]
            ),
            self._run_generate_async(streams["model_to_generate"], output_path, target),
        ]

        # Run all stages concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        stats = {
            "stages": ["extract", "decompile", "parse", "model", "generate"],
            "results": {},
        }

        for stage, result in zip(stats["stages"], results, strict=False):
            if isinstance(result, Exception):
                stats["results"][stage] = {"error": str(result)}
            else:
                stats["results"][stage] = result

        return stats

    async def _run_extract_async(
        self, _input_path: Path, output_stream: AsyncMemoryStream
    ) -> dict[str, Any]:
        """Async extraction stage."""
        # Implementation would stream extraction results
        stats = {"extracted": 0}

        # Close stream when done
        await output_stream.close()

        return stats

    async def _run_decompile_async(
        self, input_stream: AsyncMemoryStream, output_stream: AsyncMemoryStream
    ) -> dict[str, Any]:
        """Async decompilation stage."""
        stats = {"decompiled": 0}

        async for item in input_stream:
            # Process item
            decompiled = await self._async_decompile(item)
            await output_stream.write(decompiled)
            stats["decompiled"] += 1

        await output_stream.close()
        return stats

    async def _run_parse_async(
        self, input_stream: AsyncMemoryStream, output_stream: AsyncMemoryStream
    ) -> dict[str, Any]:
        """Async parse stage."""
        stats = {"parsed": 0}

        async for item in input_stream:
            # Process item
            parsed = await self._async_parse(item)
            await output_stream.write(parsed)
            stats["parsed"] += 1

        await output_stream.close()
        return stats

    async def _run_model_async(
        self, input_stream: AsyncMemoryStream, output_stream: AsyncMemoryStream
    ) -> dict[str, Any]:
        """Async model stage."""
        stats = {"models": 0}

        async for item in input_stream:
            # Process item
            model = await self._async_build_model(item)
            await output_stream.write(model)
            stats["models"] += 1

        await output_stream.close()
        return stats

    async def _run_generate_async(
        self, input_stream: AsyncMemoryStream, _output_path: Path, _target: str
    ) -> dict[str, Any]:
        """Async generate stage."""
        # Collect all models
        models = []
        async for model in input_stream:
            models.append(model)

        # Generate output
        # This would need async generator support
        return {"generated": len(models)}

    # Async processing helpers
    async def _async_decompile(self, _pcode_item: dict[str, Any]) -> dict[str, Any]:
        """Async decompile helper."""
        await asyncio.sleep(0.01)  # Simulate work
        return {"source": "decompiled source"}

    async def _async_parse(self, _source_item: dict[str, Any]) -> dict[str, Any]:
        """Async parse helper."""
        await asyncio.sleep(0.01)  # Simulate work
        return {"ast": {}}

    async def _async_build_model(self, _ast_item: dict[str, Any]) -> dict[str, Any]:
        """Async model building helper."""
        await asyncio.sleep(0.01)  # Simulate work
        return {"model": {}}
