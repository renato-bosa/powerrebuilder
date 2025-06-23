#!/usr/bin/env python3
"""Test script to run advanced decompilation on a single .fun file.

This script tests the full decompilation pipeline including:
- Object parsing to extract P-code
- P-code decoding
- Control flow analysis
- Expression reconstruction
- Output formatting
"""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from decompile.decompile_coordinator import ExtractedFileDecompiler


def test_single_fun_file(fun_file_path: str):






    """Test decompilation of a single .fun file.

    Args:
        fun_file_path: Path to the .fun file to decompile
    """
    # Set up detailed logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Create output directory for results
    output_dir = Path("output/test_advanced_decompile")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create decompiler instance
    decompiler = ExtractedFileDecompiler(output_dir)

    # Convert to Path object
    fun_path = Path(fun_file_path)

    if not fun_path.exists():
        return False

    try:
        # Run decompilation
        success = decompiler.decompile_extracted_file(fun_path)

        if success:
            # Try to read and display the output
            output_file = output_dir / f"{fun_path.stem}.sru"
            if output_file.exists():
                with open(output_file) as f:
                    content = f.read()
                    # Limit output to first 100 lines for readability
                    lines = content.split("\n")
                    if len(lines) > 100:
                        pass
                    else:
                        pass
        else:
            pass

        return success

    except Exception:
        logging.error("Exception details:", exc_info=True)
        return False


def main() -> None:








    """Main entry point."""
    # Test with a specific .fun file
    # Let's try a simple function first
    test_files = [
        # Try a simple function first
        "output/extracted/dcm_login.pbd/dcm_login.pbd/f_get_username.fun",
        # Then a more complex one
        "output/extracted/dcm_login.pbd/dcm_login.pbd/w_dcmframe.fun",
        # And a window function
        "output/extracted/dcm_login.pbd/dcm_login.pbd/w_login_maintenance.fun",
    ]

    # Find the first file that exists
    fun_file = None
    for test_file in test_files:
        test_path = project_root / test_file
        if test_path.exists():
            fun_file = str(test_path)
            break

    if not fun_file:
        # If none of the default files exist, try to find any .fun file
        for fun_path in project_root.rglob("*.fun"):
            fun_file = str(fun_path)
            break

    if fun_file:
        success = test_single_fun_file(fun_file)
        sys.exit(0 if success else 1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
