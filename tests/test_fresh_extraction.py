#!/usr/bin/env python3
"""Test fresh extraction with DataWindow fixes."""

import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_fresh_datawindow_extraction():






    """Test extracting a DataWindow with the fixed DAT* header handling."""
    logger.info("Testing fresh DataWindow extraction...")

    # Find a PBD file to extract from
    pbd_files = list(Path("input").glob("**/*.pbd"))

    if not pbd_files:
        logger.error("No PBD files found in input directory")
        return False

    # Use the first PBD file
    pbd_file = pbd_files[0]
    logger.info(f"Using PBD file: {pbd_file}")

    # Import extraction modules
    from src.extract.pbd.constants import BLOCK_SIZE as DEFAULT_BLOCK_SIZE
    from src.extract.pbd.io.file_operations import save_to_file
    from src.extract.pbd.structures.data_block import extract_data_from_entry
    from src.extract.pbd.structures.header import extract_pbl_header
    from src.extract.pbd.structures.node import extract_nods

    output_dir = Path("output/test_fresh_extraction")
    output_dir.mkdir(parents=True, exist_ok=True)

    success = False

    with open(pbd_file, "rb") as f:
        # Extract header
        header = extract_pbl_header(f, DEFAULT_BLOCK_SIZE, str(pbd_file))

        # Extract entries
        nodes = extract_nods(
            f, header.is_unicode, header.first_nod_offset, DEFAULT_BLOCK_SIZE,
        )

        # Find DataWindow entries
        dwo_count = 0
        sql_count = 0

        for node in nodes:
            if node and hasattr(node, "entry_defs"):
                for entry in node.entry_defs:
                    if entry and entry.objectname.lower().endswith(".dwo"):
                        dwo_count += 1
                        logger.info(f"  Found DataWindow: {entry.objectname}")

                        # Extract data
                        data_blocks, is_partial = extract_data_from_entry(
                            f,
                            entry,
                            header.is_unicode,
                            DEFAULT_BLOCK_SIZE,
                            pbd_file.stat().st_size,
                        )

                        if data_blocks and not is_partial:
                            # Save using the fixed save_to_file function
                            save_to_file(
                                entry, data_blocks, output_dir, header.is_unicode,
                            )

                            # Check if .sql file was created
                            sql_file = output_dir / f"{entry.objectname}.sql"
                            if sql_file.exists():
                                logger.info(f"    ✓ Created SQL file: {sql_file.name}")
                                sql_count += 1
                                success = True
                            else:
                                logger.warning("    ✗ No SQL file created")

                        # Only test first few DataWindows
                        if dwo_count >= 3:
                            break

        logger.info(
            f"\nExtracted {dwo_count} DataWindows, created {sql_count} SQL files",
        )

    return success


def main() -> None:








    """Run the test."""
    if test_fresh_datawindow_extraction():
        logger.info("\n✅ DataWindow extraction with DAT* headers is working!")
    else:
        logger.error("\n❌ DataWindow extraction still has issues")


if __name__ == "__main__":
    main()
