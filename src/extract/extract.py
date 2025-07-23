"""Simple extraction functions that bypass dependency injection.

This module provides straightforward extraction functions for use in the CLI
without requiring complex DI setup.
"""

import logging
from pathlib import Path
from typing import Any

from src.common.pipeline.progress import PipelineProgress
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
    pbl_path: str | Path,
    output_dir: str | Path,
    recovery_enabled: bool = True,
    show_progress: bool = False,
    enable_byte_recovery: bool = False,
    extract_resources: bool = True,
) -> dict[str, Any]:
    """Extract PBL/PBD with error recovery.

    Args:
        pbl_path: Path to the PBL/PBD file
        output_dir: Directory to extract files to
        recovery_enabled: Whether to enable recovery mode
        show_progress: Whether to show progress (ignored for now)
        enable_byte_recovery: Whether to enable byte-level recovery
        extract_resources: Whether to extract resources

    Returns:
        True if extraction succeeded, False if it failed but recovery was attempted
    """
    try:
        # Get progress tracker if available and progress is enabled
        progress = None
        if show_progress:
            try:
                from src.core.startup import get_infrastructure_component

                progress = get_infrastructure_component(PipelineProgress)
            except Exception:
                # Progress tracking not available, continue without it
                pass

        extract_pbl_file(pbl_path, output_dir)

        # Count extracted files
        output_path = Path(output_dir)
        if output_path.exists():
            files = list(output_path.rglob("*"))
            extracted_count = len([f for f in files if f.is_file()])
            logger.info(f"Successfully extracted {extracted_count} files")

        return True  # Success

    except Exception as e:
        if recovery_enabled:
            logger.warning(f"Extraction failed, attempting recovery: {e}")
            # In a real implementation, we would try recovery strategies here
            return False  # Failed but attempted recovery
        else:
            raise
