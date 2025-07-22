#!/usr/bin/env python3
"""Simple test to check basic P-code decoding."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.extract.pbd.version_detection import PowerBuilderVersion
from src.decompile.pcode.decoder import PCodeDecoderV2
from src.decompile.pcode.detector import EnhancedPCodeDetector

# Test with some sample P-code bytes
# This is a hypothetical P-code sequence
test_pcode = bytes(
    [
        0x32,
        0x00,
        0x01,  # PUSH_CONST_INT 1
        0x32,
        0x00,
        0x02,  # PUSH_CONST_INT 2
        0x53,  # ADD_INT
        0x00,  # RETURN
        0x00,
        0x00,
        0x00,  # Padding
    ]
)

for i in range(0, len(test_pcode), 16):
    hex_str = " ".join(f"{b:02x}" for b in test_pcode[i : i + 16])

# Test detection
detector = EnhancedPCodeDetector()
sections = detector.find_all_pcode_sections(test_pcode, "function")

# Create decoder
version = PowerBuilderVersion(10, 5, True)
decoder = PCodeDecoderV2(version)

# Decode
instructions = decoder.decode_pcode(test_pcode, 0, validate=False)
for i, _inst in enumerate(instructions):
    pass

# Test with a real file if provided
if len(sys.argv) > 1:
    file_path = Path(sys.argv[1])
    if file_path.exists():
        with open(file_path, "rb") as f:
            data = f.read()


        # Try to detect P-code
        detector = EnhancedPCodeDetector()
        pcode_info = detector.detect_pcode(data, file_path.name)

        if pcode_info.pcode_offset >= 0:

            # Extract and show P-code
            pcode_data = data[
                pcode_info.pcode_offset : pcode_info.pcode_offset
                + pcode_info.pcode_length
            ]
            for i in range(0, min(64, len(pcode_data)), 16):
                hex_str = " ".join(f"{b:02x}" for b in pcode_data[i : i + 16])
                ascii_str = "".join(
                    chr(b) if 32 <= b <= 126 else "." for b in pcode_data[i : i + 16]
                )

            # Decode it
            decoder = PCodeDecoderV2(version)
            decoded = decoder.decode_pcode_section(
                pcode_data, file_path.name, pcode_info
            )

            # Show first few
            if decoded.instructions:
                for i, _inst in enumerate(decoded.instructions[:10]):
                    pass
        else:
            pass
