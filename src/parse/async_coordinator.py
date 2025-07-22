"""Async parsing coordinator for parallel processing."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import aiofiles

from src.core.cache import file_hash, get_ast_cache

logger = logging.getLogger(__name__)


class PipelineMetrics:
    """Placeholder for pipeline metrics."""



class AsyncParseCoordinator:
    """Async parsing coordinator for parallel processing."""

    def __init__(self) -> None:
        self.ast_cache = None
        self.metrics = PipelineMetrics()

    async def initialize(self) -> None:
        """Initialize async resources."""
        self.ast_cache = await get_ast_cache()

    async def parse_file_async(self, file_path: Path) -> dict[str, Any]:
        """Parse a single file asynchronously."""
        # Check cache first
        key = file_hash(file_path)
        cached_ast = await self.ast_cache.get(key)
        if cached_ast:
            return {"status": "success", "ast": cached_ast, "cached": True}

        try:
            # Read file content
            async with aiofiles.open(file_path, encoding="utf-8") as f:
                content = await f.read()

            # Parse in thread pool (parser is CPU-bound)
            from src.parse.parser.powerbuilder import PowerBuilderParser

            parser = PowerBuilderParser()

            loop = asyncio.get_event_loop()
            ast = await loop.run_in_executor(None, parser.parse, content)

            # Cache result
            await self.ast_cache.put(key, ast)

            return {"status": "success", "ast": ast, "cached": False}
        except OSError as e:
            logger.error("File I/O error parsing %s: %s", file_path, e)
            return {"status": "error", "error": f"I/O error: {e}"}
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in cached AST for %s: %s", file_path, e)
            return {"status": "error", "error": f"Invalid cached AST: {e}"}
        except Exception as e:
            logger.exception("Unexpected error parsing %s: %s", file_path, e)
            return {"status": "error", "error": str(e)}

    async def parse_directory_async(
        self, input_dir: Path, output_dir: Path, extensions: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Parse all source files in directory asynchronously."""
        if extensions is None:
            extensions = [".sru", ".srw", ".srf", ".sra", ".srm"]

        # Find all source files
        source_files = []
        for ext in extensions:
            source_files.extend(input_dir.rglob(f"*{ext}"))

        if not source_files:
            logger.warning("No source files found in %s", input_dir)
            return []

        # Parse files in parallel
        tasks = []
        for file_path in source_files:
            tasks.append(self.parse_file_async(file_path))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Save ASTs
        successful = []
        for file_path, result in zip(source_files, results, strict=False):
            if isinstance(result, Exception):
                logger.exception("Failed to parse %s: %s", file_path, result)
            elif isinstance(result, dict) and result.get("status") == "success":
                # Save AST
                output_path = output_dir / file_path.relative_to(input_dir).with_suffix(
                    ".ast.json"
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(output_path, "w") as f:
                    await f.write(json.dumps(result["ast"], indent=2))

                result["file"] = str(file_path)
                successful.append(result)

        return successful
