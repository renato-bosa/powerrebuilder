"""Base extraction functionality for PowerBuilder files."""

import logging
from pathlib import Path
from typing import Any

from src.extract.pbd.structures import HeaderClass

logger = logging.getLogger(__name__)


def _get_resource_manager(header: HeaderClass, output_path: Path) -> Any | None:
    """Get or create resource manager if resource extraction is enabled."""
    if not hasattr(header, "extract_resources") or not header.extract_resources:
        return None

    # Import here to avoid circular imports
    from src.extract.pbd.res_manager import ResourceExtractionManager

    # Store resource manager as a module-level variable
    if not hasattr(_get_resource_manager, "_instance"):
        _get_resource_manager._instance = ResourceExtractionManager(output_path)

    return _get_resource_manager._instance
