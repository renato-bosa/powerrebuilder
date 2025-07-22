"""Async extraction coordinator for parallel processing."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from src.extract.pbd.reader import AsyncStreamingPBDReader

logger = logging.getLogger(__name__)


class PipelineMetrics:
    """Placeholder for pipeline metrics."""



class AsyncExtractCoordinator:
    """Async extraction coordinator for parallel processing."""

    def __init__(self, silent_progress: bool = False) -> None:
        self.silent_progress = silent_progress
        self.metrics = PipelineMetrics()

    async def extract_pbd_async(
        self, pbd_path: Path, output_dir: Path
    ) -> dict[str, Any]:
        """Extract PBD file asynchronously."""
        try:
            entries = []
            async with AsyncStreamingPBDReader(pbd_path) as reader:
                async for entry in reader.iter_entries():
                    entries.append(
                        {
                            "name": entry.objectname,
                            "type": entry.objecttype,
                            "size": entry.objectsize,
                        }
                    )
                    await reader.extract_entry(entry, output_dir)

            return {"status": "success", "entries": entries, "count": len(entries)}
        except FileNotFoundError:
            logger.error("PBD file not found: %s", pbd_path)
            return {"status": "error", "error": f"File not found: {pbd_path}"}
        except OSError as e:
            logger.error("File I/O error extracting %s: %s", pbd_path, e)
            return {"status": "error", "error": f"I/O error: {e}"}
        except Exception as e:
            logger.exception("Unexpected error extracting %s: %s", pbd_path, e)
            return {"status": "error", "error": str(e)}

    async def extract_directory_async(
        self, input_dir: Path, output_dir: Path, pattern: str = "*.pbd"
    ) -> list[dict[str, Any]]:
        """Extract all PBD files in directory asynchronously."""
        pbd_files = list(input_dir.glob(pattern))

        if not pbd_files:
            logger.warning("No PBD files found in %s", input_dir)
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
        for pbd_file, result in zip(pbd_files, results, strict=False):
            if isinstance(result, Exception):
                logger.exception("Failed to extract %s: %s", pbd_file, result)
            elif isinstance(result, dict):
                result["file"] = str(pbd_file)
                successful.append(result)

        return successful
