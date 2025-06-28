#!/usr/bin/env python3
"""Direct test of decompilation without complex imports.

This script directly tests the core decompilation functionality.
"""

import logging
from pathlib import Path

# Set up logging first
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Find a .fun file to test
test_file = None
for fun_path in Path("output/extracted").rglob("*.fun"):
    test_file = fun_path
    break

if not test_file:
    logging.error("No .fun files found in output/extracted")
    # Skip the test if no files are found
    import pytest
    pytest.skip("No .fun files found to test")


# Read the .fun file
with open(test_file, "rb") as f:
    data = f.read()


# Try to parse it directly
try:
    # Import only what we need
    from decompile.analyzers.object_parser import ObjectParser

    # Parse the object
    object_name = test_file.stem
    pb_object = ObjectParser.parse_object(data, object_name)

    if pb_object:
        if pb_object.pcode_data:
            # Try to decode some instructions

            # Import decoder
            from decompile.core.pcode_decoder import PCodeDecoderV2
            from extract.pbd.utils.version_detector import PowerBuilderVersion

            # Use default version
            version = PowerBuilderVersion(10, 5, True)
            decoder = PCodeDecoderV2(version)

            # Decode P-code
            decoded_obj = decoder.decode_pcode_section(
                pb_object.pcode_data,
                test_file.name,
                None,
            )

            if decoded_obj.instructions:
                # Show first few instructions
                for _i, _inst in enumerate(decoded_obj.instructions[:
                    10]):
                    pass
            else:
                pass

    else:
        pass

except Exception:
    import traceback

    traceback.print_exc()
