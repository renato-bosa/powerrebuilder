"""Test configuration and fixtures for PowerBuilder model tests."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Add model directory to Python path
model_dir = project_root / "model"
sys.path.insert(0, str(model_dir))
