"""Test configuration and fixtures for PowerBuilder model tests."""

import sys
import logging
from pathlib import Path
import pytest

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add model directory to Python path
model_dir = project_root / "model"
sys.path.insert(0, str(model_dir))


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    # Save current state
    original_level = logging.root.level
    original_handlers = logging.root.handlers[:]
    
    yield
    
    # Restore state
    logging.root.handlers.clear()
    logging.root.handlers.extend(original_handlers)
    logging.root.setLevel(original_level)
    
    # Reset specific logger levels that may have been changed
    for logger_name in [
        "extract.pbd.structures.data_block",
        "extract.pbd.extraction",
        "extract.pbd.io",
        "decompile.analysis",
        "decompile.core.pcode_decoder",
        "decompile.core.expression_reconstructor",
        "extract.extract_coordinator",
        "decompile.decompile_coordinator",
        "parse.parse_coordinator",
        "model.model_coordinator",
        "generate.generate_coordinator",
    ]:
        logging.getLogger(logger_name).setLevel(logging.NOTSET)
