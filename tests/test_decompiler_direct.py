#!/usr/bin/env python3
"""Direct test of the decompiler without complex imports."""

import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import only what we need
from decompile.decompile_coordinator import ExtractedFileDecompiler


def test_decompiler() -> None:



    
    


    """Test the decompiler on extracted .fun files."""
    # Find some .fun files
    output_dir = Path("output")
    fun_files = list(output_dir.glob("**/*.fun"))[:3]

    if not fun_files:
        logger.error("No .fun files found!")
        return

    # Create decompiler
    decompiler = ExtractedFileDecompiler(Path("output/test_decompiler"))

    for fun_file in fun_files:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Testing decompiler on: {fun_file.name}")
        logger.info("=" * 60)

        try:
            result = decompiler.decompile_extracted_file(fun_file)
            if result:
                logger.info("✓ Decompilation successful!")
            else:
                logger.info("✗ Decompilation failed (stub generated)")
        except Exception as e:
            logger.exception(f"✗ Exception during decompilation: {e}")


if __name__ == "__main__":
    test_decompiler()
