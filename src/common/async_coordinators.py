"""Async versions of coordinators for parallel pipeline execution."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiofiles
import json

from .parallel_pipeline import ParallelPipeline, PipelineMetrics
from .cache import get_ast_cache, file_hash
from .pipeline.progress import Progress

logger = logging.getLogger(__name__)


class AsyncExtractCoordinator:
    """Async extraction coordinator for parallel processing."""

    def __init__(self, silent_progress: bool = False):
        self.silent_progress = silent_progress
        self.metrics = PipelineMetrics()

    async def extract_pbd_async(self, pbd_path: Path, output_dir: Path) -> Dict[str, Any]:
        """Extract PBD file asynchronously."""
        from src.extract.pbd.reader import AsyncStreamingPBDReader

        try:
            entries = []
            async with AsyncStreamingPBDReader(pbd_path) as reader:
                async for entry in reader.iter_entries():
                    entries.append({
                        "name": entry.objectname,
                        "type": entry.objecttype,
                        "size": entry.objectsize
                    })
                    await reader.extract_entry(entry, output_dir)

            return {
                "status": "success",
                "entries": entries,
                "count": len(entries)
            }
        except Exception as e:
            logger.error(f"Failed to extract {pbd_path}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def extract_directory_async(
        self, 
        input_dir: Path, 
        output_dir: Path,
        pattern: str = "*.pbd"
    ) -> List[Dict[str, Any]]:
        """Extract all PBD files in directory asynchronously."""
        pbd_files = list(input_dir.glob(pattern))

        if not pbd_files:
            logger.warning(f"No PBD files found in {input_dir}")
            return []

        # Create async tasks for each file
        tasks = []
        for pbd_file in pbd_files:
            file_output = output_dir / pbd_file.stem
            file_output.mkdir(parents=True, exist_ok=True)
            tasks.append(self.extract_pbd_async(pbd_file, file_output))

        # Execute all extractions in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful = []
        for pbd_file, result in zip(pbd_files, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to extract {pbd_file}: {result}")
            elif isinstance(result, dict):
                result["file"] = str(pbd_file)
                successful.append(result)

        return successful


class AsyncParseCoordinator:
    """Async parsing coordinator for parallel processing."""

    def __init__(self):
        self.ast_cache = None
        self.metrics = PipelineMetrics()

    async def initialize(self):
        """Initialize async resources."""
        self.ast_cache = await get_ast_cache()

    async def parse_file_async(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single file asynchronously."""
        # Check cache first
        key = file_hash(file_path)
        cached_ast = await self.ast_cache.get(key)
        if cached_ast:
            return {
                "status": "success",
                "ast": cached_ast,
                "cached": True
            }

        try:
            # Read file content
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()

            # Parse in thread pool (parser is CPU-bound)
            from src.parse.parser.powerbuilder import PowerBuilderParser
            parser = PowerBuilderParser()

            loop = asyncio.get_event_loop()
            ast = await loop.run_in_executor(None, parser.parse, content)

            # Cache result
            await self.ast_cache.put(key, ast)

            return {
                "status": "success",
                "ast": ast,
                "cached": False
            }
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def parse_directory_async(
        self,
        input_dir: Path,
        output_dir: Path,
        extensions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Parse all source files in directory asynchronously."""
        if extensions is None:
            extensions = ['.sru', '.srw', '.srf', '.sra', '.srm']

        # Find all source files
        source_files = []
        for ext in extensions:
            source_files.extend(input_dir.rglob(f"*{ext}"))

        if not source_files:
            logger.warning(f"No source files found in {input_dir}")
            return []

        # Parse files in parallel
        tasks = []
        for file_path in source_files:
            tasks.append(self.parse_file_async(file_path))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Save ASTs
        successful = []
        for file_path, result in zip(source_files, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to parse {file_path}: {result}")
            elif isinstance(result, dict) and result.get("status") == "success":
                # Save AST
                output_path = output_dir / file_path.relative_to(input_dir).with_suffix('.ast.json')
                output_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(output_path, 'w') as f:
                    await f.write(json.dumps(result["ast"], indent=2))

                result["file"] = str(file_path)
                successful.append(result)

        return successful


class AsyncDecompileCoordinator:
    """Async decompilation coordinator for parallel processing."""

    def __init__(self):
        self.metrics = PipelineMetrics()

    async def decompile_pcode_async(self, pcode_path: Path) -> Dict[str, Any]:
        """Decompile P-code file asynchronously."""
        try:
            # Read P-code data
            async with aiofiles.open(pcode_path, 'rb') as f:
                pcode_data = await f.read()

            # Decompile in thread pool (CPU-bound)
            from src.decompile.pcode.decoder import PCodeDecoderV2 as PCodeDecoder
            decoder = PCodeDecoder()

            loop = asyncio.get_event_loop()
            instructions = await loop.run_in_executor(None, decoder.decode, pcode_data)

            return {
                "status": "success",
                "instructions": instructions
            }
        except Exception as e:
            logger.error(f"Failed to decompile {pcode_path}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def decompile_directory_async(
        self,
        input_dir: Path,
        output_dir: Path
    ) -> List[Dict[str, Any]]:
        """Decompile all P-code files in directory asynchronously."""
        pcode_files = list(input_dir.rglob("*.fun"))

        if not pcode_files:
            logger.warning(f"No P-code files found in {input_dir}")
            return []

        # Decompile files in parallel
        tasks = []
        for pcode_file in pcode_files:
            tasks.append(self.decompile_pcode_async(pcode_file))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Save decompiled code
        successful = []
        for pcode_file, result in zip(pcode_files, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to decompile {pcode_file}: {result}")
            elif isinstance(result, dict) and result.get("status") == "success":
                # Save decompiled instructions
                output_path = output_dir / pcode_file.relative_to(input_dir).with_suffix('.dec.json')
                output_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(output_path, 'w') as f:
                    await f.write(json.dumps(result["instructions"], indent=2))

                result["file"] = str(pcode_file)
                successful.append(result)

        return successful


class AsyncGenerateCoordinator:
    """Async code generation coordinator for parallel processing."""

    def __init__(self, target: str = "flutter"):
        self.target = target
        self.metrics = PipelineMetrics()

    async def generate_from_ast_async(self, ast_path: Path) -> Dict[str, Any]:
        """Generate code from AST asynchronously."""
        try:
            # Read AST
            async with aiofiles.open(ast_path, 'r') as f:
                ast_data = json.loads(await f.read())

            # Generate code in thread pool
            from src.generate.base_generator import BaseGenerator
            generator = BaseGenerator.create(self.target)

            loop = asyncio.get_event_loop()
            generated = await loop.run_in_executor(None, generator.generate, ast_data)

            return {
                "status": "success",
                "code": generated
            }
        except Exception as e:
            logger.error(f"Failed to generate from {ast_path}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def generate_directory_async(
        self,
        input_dir: Path,
        output_dir: Path
    ) -> List[Dict[str, Any]]:
        """Generate code for all AST files in directory asynchronously."""
        ast_files = list(input_dir.rglob("*.ast.json"))

        if not ast_files:
            logger.warning(f"No AST files found in {input_dir}")
            return []

        # Generate code in parallel
        tasks = []
        for ast_file in ast_files:
            tasks.append(self.generate_from_ast_async(ast_file))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Save generated code
        successful = []
        for ast_file, result in zip(ast_files, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to generate from {ast_file}: {result}")
            elif isinstance(result, dict) and result.get("status") == "success":
                # Determine output extension based on target
                ext_map = {
                    "flutter": ".dart",
                    "python": ".py",
                    "typescript": ".ts"
                }
                ext = ext_map.get(self.target, ".txt")

                output_path = output_dir / ast_file.relative_to(input_dir).with_suffix(ext)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(output_path, 'w') as f:
                    await f.write(result["code"])

                result["file"] = str(ast_file)
                successful.append(result)

        return successful


class AsyncPipelineCoordinator:
    """Main async pipeline coordinator that orchestrates all stages."""

    def __init__(self, target: str = "flutter"):
        self.target = target
        self.extract = AsyncExtractCoordinator()
        self.parse = AsyncParseCoordinator()
        self.decompile = AsyncDecompileCoordinator()
        self.generate = AsyncGenerateCoordinator(target)

    async def run_pipeline_async(
        self,
        input_path: Path,
        output_path: Path,
        stages: Optional[List[str]] = None,
        progress: Optional[Progress] = None
    ) -> Dict[str, Any]:
        """Run the full pipeline asynchronously with parallel stages."""
        if stages is None:
            stages = ["extract", "parse", "decompile", "generate"]

        # Initialize coordinators
        await self.parse.initialize()

        # Create parallel pipeline
        pipeline = ParallelPipeline("powerrebuilder")

        # Set up working directories
        work_dir = output_path / ".work"
        work_dir.mkdir(parents=True, exist_ok=True)

        results = {
            "stages": {},
            "metrics": {}
        }

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
            parse_task = self.parse.parse_directory_async(
                current_input, parse_output
            )
            decompile_task = self.decompile.decompile_directory_async(
                current_input, decompile_output
            )

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
            "generate": self.generate.metrics.__dict__
        }

        return results