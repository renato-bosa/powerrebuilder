"""Async decompilation coordinator for parallel processing."""

import asyncio
import json
import logging
import struct
from pathlib import Path
from typing import Any

import aiofiles

logger = logging.getLogger(__name__)


class PipelineMetrics:
    """Placeholder for pipeline metrics."""



class AsyncDecompileCoordinator:
    """Async decompilation coordinator for parallel processing."""

    def __init__(self) -> None:
        self.metrics = PipelineMetrics()

    async def decompile_pcode_async(self, pcode_path: Path) -> dict[str, Any]:
        """Decompile P-code file asynchronously."""
        try:
            # Read P-code data
            async with aiofiles.open(pcode_path, "rb") as f:
                pcode_data = await f.read()

            # Decompile in thread pool (CPU-bound)
            from src.decompile.pcode.decoder import PCodeDecoderV2 as PCodeDecoder

            decoder = PCodeDecoder()

            loop = asyncio.get_event_loop()
            instructions = await loop.run_in_executor(None, decoder.decode, pcode_data)

            return {"status": "success", "instructions": instructions}
        except FileNotFoundError:
            logger.error("P-code file not found: %s", pcode_path)
            return {"status": "error", "error": f"File not found: {pcode_path}"}
        except struct.error as e:
            logger.error("Invalid P-code format in %s: %s", pcode_path, e)
            return {"status": "error", "error": f"Invalid P-code format: {e}"}
        except Exception as e:
            logger.exception("Unexpected error decompiling %s: %s", pcode_path, e)
            return {"status": "error", "error": str(e)}

    async def decompile_directory_async(
        self, input_dir: Path, output_dir: Path
    ) -> list[dict[str, Any]]:
        """Decompile all P-code files in directory asynchronously."""
        pcode_files = list(input_dir.rglob("*.fun"))

        if not pcode_files:
            logger.warning("No P-code files found in %s", input_dir)
            return []

        # Decompile files in parallel
        tasks = []
        for pcode_file in pcode_files:
            tasks.append(self.decompile_pcode_async(pcode_file))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Save decompiled code
        successful = []
        for pcode_file, result in zip(pcode_files, results, strict=False):
            if isinstance(result, Exception):
                logger.exception("Failed to decompile %s: %s", pcode_file, result)
            elif isinstance(result, dict) and result.get("status") == "success":
                # Save decompiled instructions
                output_path = output_dir / pcode_file.relative_to(
                    input_dir
                ).with_suffix(".dec.json")
                output_path.parent.mkdir(parents=True, exist_ok=True)

                async with aiofiles.open(output_path, "w") as f:
                    await f.write(json.dumps(result["instructions"], indent=2))

                result["file"] = str(pcode_file)
                successful.append(result)

        return successful
