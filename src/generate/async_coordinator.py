"""Async code generation coordinator for parallel processing."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)


class PipelineMetrics:
    """Placeholder for pipeline metrics."""



class AsyncGenerateCoordinator:
    """Async code generation coordinator for parallel processing."""

    def __init__(self, target: str = "flutter") -> None:
        self.target = target
        self.metrics = PipelineMetrics()

    async def generate_from_ast_async(self, ast_path: Path) -> dict[str, Any]:
        """Generate code from AST asynchronously."""
        try:
            # Read AST
            async with aiofiles.open(ast_path) as f:
                ast_data = json.loads(await f.read())

            # Generate code in thread pool
            from src.generate.base import BaseGenerator

            generator = BaseGenerator.create(self.target)

            loop = asyncio.get_event_loop()
            generated = await loop.run_in_executor(None, generator.generate, ast_data)

            return {"status": "success", "code": generated}
        except FileNotFoundError:
            logger.error("AST file not found: %s", ast_path)
            return {"status": "error", "error": f"File not found: {ast_path}"}
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in AST file %s: %s", ast_path, e)
            return {"status": "error", "error": f"Invalid AST format: {e}"}
        except Exception as e:
            logger.exception("Unexpected error generating from %s: %s", ast_path, e)
            return {"status": "error", "error": str(e)}

    async def generate_directory_async(
        self, input_dir: Path, output_dir: Path
    ) -> list[dict[str, Any]]:
        """Generate code for all AST files in directory asynchronously."""
        ast_files = list(input_dir.rglob("*.ast.json"))

        if not ast_files:
            logger.warning("No AST files found in %s", input_dir)
            return []

        # Generate code in parallel
        tasks = []
        for ast_file in ast_files:
            tasks.append(self.generate_from_ast_async(ast_file))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Save generated code
        successful = []
        for ast_file, result in zip(ast_files, results, strict=False):
            if isinstance(result, Exception):
                logger.exception("Failed to generate from %s: %s", ast_file, result)
            elif isinstance(result, dict) and result.get("status") == "success":
                # Determine output extension based on target
                ext_map = {"flutter": ".dart", "python": ".py", "typescript": ".ts"}
                ext = ext_map.get(self.target, ".txt")

                output_path = output_dir / ast_file.relative_to(input_dir).with_suffix(
                    ext
                )
                output_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(output_path, "w") as f:
                    await f.write(result["code"])

                result["file"] = str(ast_file)
                successful.append(result)

        return successful
