#!/usr/bin/env python3
"""Utility runner for SIME Finch project.

This script provides a command-line interface to run various utility tools
for working with PowerBuilder binary files.
"""

import argparse
import importlib.util
import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("pb-utils")

# Directory containing this script
SCRIPT_DIR = Path(__file__).parent.absolute()

# Map of utility names to their module paths
UTILITIES = {
    "extract": "extract_binary_file.py",
    "text": "pb_to_text.py",
    "inspect": str(Path(SCRIPT_DIR).parent.parent / "pbd_core" / "utils" / "inspect_pbd.py"),
    "hexdump": str(Path(SCRIPT_DIR).parent.parent / "pbd_core" / "utils" / "hexdump_viewer.py"),
}


def ensure_dependencies() -> None:
    """Ensure all dependencies are installed."""
    try:
        # Use uv if available (modern package manager)
        if importlib.util.find_spec("uv"):
            subprocess.run(["uv", "pip", "install", "hexdump", "click"], check=True)
        else:
            # Fall back to pip
            subprocess.run([sys.executable, "-m", "pip", "install", "hexdump", "click"], check=True)
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        sys.exit(1)


def list_utilities() -> None:
    """List available utilities."""
    for _name, _path in UTILITIES.items():
        pass


def main() -> None:
    """Main entry point for the utility runner."""
    parser = argparse.ArgumentParser(
        description="PowerBuilder utility runner",
        usage="%(prog)s <utility> [options]",
    )
    parser.add_argument("utility", nargs="?", help="Utility to run")
    parser.add_argument("--list", action="store_true", help="List available utilities")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies")

    # Parse just the utility name first
    args, remaining = parser.parse_known_args()

    if args.install_deps:
        ensure_dependencies()
        return

    if args.list or not args.utility:
        list_utilities()
        return

    # Check if the utility exists
    if args.utility not in UTILITIES:
        logger.error(f"Unknown utility: {args.utility}")
        list_utilities()
        return

    # Get the path to the utility
    utility_path = Path(UTILITIES[args.utility])
    if not utility_path.is_absolute():
        utility_path = SCRIPT_DIR / utility_path

    if not utility_path.exists():
        logger.error(f"Utility not found: {utility_path}")
        return

    # Run the utility with the remaining arguments
    try:
        os.execv(sys.executable, [sys.executable, str(utility_path)] + remaining)
    except Exception as e:
        logger.error(f"Failed to run utility: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
