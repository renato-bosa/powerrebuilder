#!/usr/bin/env python3
"""Test the fixed pipeline components."""

import logging
import sys
from pathlib import Path
from typing import Never

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[
        logging.StreamHandler(sys.stdout), logging.FileHandler("test_fixes.log"), ], )
logger = logging.getLogger(__name__)


def test_extraction():






    """Test DataWindow extraction with fixed DAT* header handling."""
    logger.info("Testing DataWindow extraction...")

    # Find a .dwo file
    dwo_files = list(Path("data/output/current/extracted").glob("**/*.dwo"))[:3]

    if not dwo_files:
        logger.error("No .dwo files found to test")
        return False

    from src.decompile.extractors.datawindow_extractor import extract_datawindow_from_pbd

    success_count = 0
    for dwo_file in dwo_files:
        logger.info(f"Testing: {dwo_file.name}")

        # Read the file
        with open(dwo_file, "rb") as f:
            raw_data = f.read()

        # Check if it has DAT* header
        if raw_data.startswith((b"DAT*", b"D\x00A\x00T\x00")):
            logger.info("  ✓ File already has DAT* header")

            # Try extraction
            syntax = extract_datawindow_from_pbd(raw_data, dwo_file.name)
            if syntax:
                logger.info(f"  ✓ Extracted {len(syntax)} characters of SQL")
                success_count += 1
            else:
                logger.warning("  ✗ Failed to extract SQL")
        else:
            logger.info("  ⚠ File missing DAT* header (old extraction)")

    logger.info(f"DataWindow extraction: {success_count}/{len(dwo_files)} successful")
    return success_count > 0


def test_decompilation():






    """Test P-code decompilation with enhanced detector."""
    logger.info("\nTesting P-code decompilation...")

    # Find a .fun file
    fun_files = list(Path("data/output/current/extracted").glob("**/*.fun"))[:3]

    if not fun_files:
        logger.error("No .fun files found to test")
        return False

    from decompile.analyzers.object_parser import ObjectParser
    from src.decompile.pcode.decoder import PCodeDecoderV2
    from src.extract.utils.version import PowerBuilderVersion

    success_count = 0
    for fun_file in fun_files:
        logger.info(f"Testing: {fun_file.name}")

        # Read and parse
        with open(fun_file, "rb") as f:
            data = f.read()

        parser = ObjectParser()
        pb_object = parser.parse_object(data, fun_file.name)

        if pb_object and pb_object.pcode_data:
            logger.info(
                f"  ✓ Found P-code at 0x{pb_object.pcode_offset:04x}, {pb_object.pcode_length} bytes",
            )

            # Try decoding with timeout protection
            import signal

            def timeout_handler(signum, frame) -> Never:


                msg = "Decoder timeout"
                raise TimeoutError(msg)

            # Set 5 second timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)

            try:
                decoder = PCodeDecoderV2(PowerBuilderVersion(10, 5, True))
                instructions = decoder.decode_pcode(
                    pb_object.pcode_data, pb_object.pcode_offset,
                )
                signal.alarm(0)  # Cancel timeout

                if instructions:
                    logger.info(f"  ✓ Decoded {len(instructions)} instructions")
                    success_count += 1
                else:
                    logger.warning("  ✗ No instructions decoded")
            except TimeoutError:
                signal.alarm(0)  # Cancel timeout
                logger.exception("  ✗ Decoder timeout!")
            except Exception as e:
                signal.alarm(0)  # Cancel timeout
                logger.exception(f"  ✗ Decoder error: {e}")
        else:
            logger.warning("  ✗ No P-code found")

    logger.info(f"P-code decompilation: {success_count}/{len(fun_files)} successful")
    return success_count > 0


def main() -> None:








    """Run all tests."""
    logger.info("Testing pipeline fixes...\n")

    extraction_ok = test_extraction()
    decompilation_ok = test_decompilation()

    logger.info("\n" + "=" * 60)
    if extraction_ok and decompilation_ok:
        logger.info("✅ All tests passed! Pipeline fixes appear to be working.")
    else:
        logger.error("❌ Some tests failed. Check the logs above.")


if __name__ == "__main__":
    main()
