"""Simple extraction functions that bypass dependency injection.

This module provides straightforward extraction functions for use in the CLI
without requiring complex DI setup.
"""

import logging
from pathlib import Path
from typing import Any

from src.extract.pbd.manager import ResourceExtractionManager
from src.extract.pbd.reader import StreamingPBDReader

logger = logging.getLogger(__name__)


def extract_pbl_file(pbl_path: str | Path, output_dir: str | Path) -> None:
    """Extract all entries from a PBL/PBD file.

    Args:
        pbl_path: Path to the PBL/PBD file
        output_dir: Directory to extract files to
    """
    pbl_path = Path(pbl_path)
    output_dir = Path(output_dir)

    if not pbl_path.exists():
        raise FileNotFoundError(f"PBL/PBD file not found: {pbl_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Use the streaming reader to extract files
        reader = StreamingPBDReader(str(pbl_path))
        manager = ResourceExtractionManager(reader)

        # Extract all entries
        results = manager.extract_all(str(output_dir))

        logger.info(f"Extracted {len(results)} entries from {pbl_path}")

    except Exception as e:
        logger.error(f"Failed to extract {pbl_path}: {e}")
        raise


def extract_with_recovery(
    pbl_path: str | Path, output_dir: str | Path, recovery_enabled: bool = True
) -> dict[str, Any]:
    """Extract PBL/PBD with error recovery.

    Args:
        pbl_path: Path to the PBL/PBD file
        output_dir: Directory to extract files to
        recovery_enabled: Whether to enable recovery mode

    Returns:
        Dictionary with extraction results and any errors
    """
    results = {"extracted": 0, "failed": 0, "errors": [], "files": []}

    try:
        extract_pbl_file(pbl_path, output_dir)
        # Count extracted files
        output_path = Path(output_dir)
        if output_path.exists():
            files = list(output_path.rglob("*"))
            results["extracted"] = len([f for f in files if f.is_file()])
            results["files"] = [
                str(f.relative_to(output_path)) for f in files if f.is_file()
            ]
    except Exception as e:
        if recovery_enabled:
            logger.warning(f"Extraction failed, attempting recovery: {e}")
            results["errors"].append(str(e))
            results["failed"] = 1
            # In a real implementation, we would try recovery strategies here
        else:
            raise

    return results
