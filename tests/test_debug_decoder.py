#!/usr/bin/env python3
"""Debug test for the P-code decoder to find where it gets stuck."""

import logging
import time
from pathlib import Path

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import only what we need
from decompile.analysis.object_parser import ObjectParser
from decompile.core.pcode_decoder import PCodeDecoderV2
from extract.pbd.utils.version_detector import PowerBuilderVersion


def test_decoder_with_timeout() -> None:








    """Test the decoder with debugging to find timeout issue."""
    # Find a test .fun file
    test_file = Path("output/test_fixed_extraction4/w_loginwizard.fun")

    if not test_file.exists():
        # Try to find any .fun file
        fun_files = list(Path("output").glob("**/*.fun"))
        if fun_files:
            test_file = fun_files[0]
        else:
            logger.error("No .fun files found!")
            return

    logger.info(f"Testing decoder on: {test_file}")

    # Read the file
    with open(test_file, "rb") as f:
        data = f.read()

    logger.info(f"File size: {len(data)} bytes")

    # Parse object structure
    parser = ObjectParser()
    pb_object = parser.parse_object(data, str(test_file))

    if not pb_object:
        logger.error("Failed to parse object structure")
        return

    if pb_object.pcode_offset < 0 or not pb_object.pcode_data:
        logger.error("No P-code found in object")
        return

    logger.info(
        f"P-code found at offset 0x{pb_object.pcode_offset:04x}, length {pb_object.pcode_length} bytes",
    )

    # Create decoder with debugging
    version = PowerBuilderVersion(10, 5, True)
    decoder = PCodeDecoderV2(version)

    # Patch the decoder to add debugging
    original_decode_next = decoder._decode_next_instruction
    instruction_count = 0
    last_offset = 0
    start_time = time.time()

    def debug_decode_next(pcode, base_offset):


        nonlocal instruction_count, last_offset

        # Check timeout every 100 instructions
        if instruction_count % 100 == 0:
            elapsed = time.time() - start_time
            if elapsed > 10:  # 10 second timeout
                logger.error(
                    f"Timeout after {instruction_count} instructions, {elapsed:.1f} seconds",
                )
                logger.error(
                    f"Last offset: 0x{last_offset:04x}, current offset: 0x{decoder.current_offset:04x}",
                )
                msg = "Decoder timeout"
                raise TimeoutError(msg)

            if instruction_count > 0:
                logger.debug(
                    f"Decoded {instruction_count} instructions, offset 0x{decoder.current_offset:04x}",
                )

        last_offset = decoder.current_offset
        result = original_decode_next(pcode, base_offset)

        if result:
            instruction_count += 1
            # Log every 10th instruction
            if instruction_count % 10 == 0:
                logger.debug(
                    f"Instruction {instruction_count}: {result.opcode_name} at 0x{result.address:04x}",
                )

        return result

    decoder._decode_next_instruction = debug_decode_next

    # Try to decode with timeout protection
    try:
        logger.info("Starting P-code decoding...")
        instructions = decoder.decode_pcode(
            pb_object.pcode_data, pb_object.pcode_offset,
        )
        logger.info(f"Successfully decoded {len(instructions)} instructions!")

        # Show first few instructions
        for _i, inst in enumerate(instructions[:
            10]):
            logger.info(f"  {inst.text_format}")

    except TimeoutError as e:
        logger.exception(f"Decoder timeout: {e}")
        # Show where we got stuck
        if hasattr(decoder, "current_offset"):
            stuck_offset = decoder.current_offset
            logger.exception(f"Stuck at offset 0x{stuck_offset:04x}")
            # Show bytes around that offset
            if stuck_offset < len(pb_object.pcode_data):
                window = 20
                start = max(0, stuck_offset - window)
                end = min(len(pb_object.pcode_data), stuck_offset + window)
                bytes_window = pb_object.pcode_data[start:end]
                logger.exception(f"Bytes around stuck offset: {bytes_window.hex()}")
    except Exception as e:
        logger.error(f"Decoder error: {e}", exc_info=True)


if __name__ == "__main__":
    test_decoder_with_timeout()
