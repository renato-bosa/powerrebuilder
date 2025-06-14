#!/usr/bin/env python3
"""Simple test script to run advanced decompilation on a single .fun file.

This script tests the decompilation pipeline with minimal imports.
"""

import os
import sys
from pathlib import Path

# Change to project directory
os.chdir(Path(__file__).parent)

# Run decompile_directory function directly
if __name__ == "__main__":
    import logging

    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Import after setting up path
    try:
        from decompile.decompile_coordinator import decompile_directory

        # Test with a small set of files
        input_dir = "output/extracted/dcm_login.pbd/dcm_login.pbd"
        output_dir = "output/test_advanced_decompile"

        if not Path(input_dir).exists():
            base_dir = Path("output/extracted")
            if base_dir.exists():
                for pbd_dir in base_dir.iterdir():
                    if pbd_dir.is_dir():
                        inner_dirs = list(pbd_dir.iterdir())
                        if inner_dirs:
                            input_dir = str(inner_dirs[0])
                            break

        # Run decompilation
        decompile_directory(input_dir, output_dir)

    except ImportError:
        # Try running as a module
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "decompile.decompile_coordinator",
                "-o",
                "output/test_advanced_decompile",
                "output/extracted/dcm_login.pbd/dcm_login.pbd",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stderr:
            pass

        sys.exit(result.returncode)
