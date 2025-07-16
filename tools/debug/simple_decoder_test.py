#!/usr/bin/env python3
"""Simple test to check basic P-code decoding."""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.decompile.pcode.decoder import PCodeDecoderV2
from src.extract.utils.version import PowerBuilderVersion
from src.decompile.pcode.detector import EnhancedPCodeDetector

# Test with some sample P-code bytes
# This is a hypothetical P-code sequence
test_pcode = bytes([
    0x32, 0x00, 0x01,  # PUSH_CONST_INT 1
    0x32, 0x00, 0x02,  # PUSH_CONST_INT 2
    0x53,              # ADD_INT
    0x00,              # RETURN
    0x00, 0x00, 0x00,  # Padding
])

print("Testing P-code decoder with sample data")
print(f"Test P-code ({len(test_pcode)} bytes):")
for i in range(0, len(test_pcode), 16):
    hex_str = ' '.join(f'{b:02x}' for b in test_pcode[i:i+16])
    print(f"  {i:04x}: {hex_str}")

# Test detection
detector = EnhancedPCodeDetector()
sections = detector.find_all_pcode_sections(test_pcode, "function")
print(f"\nDetected {len(sections)} P-code sections")

# Create decoder
version = PowerBuilderVersion(10, 5, True)
decoder = PCodeDecoderV2(version)

# Decode
instructions = decoder.decode_pcode(test_pcode, 0, validate=False)
print(f"\nDecoded {len(instructions)} instructions:")
for i, inst in enumerate(instructions):
    print(f"  {i+1}. {inst.text_format}")

# Test with a real file if provided
if len(sys.argv) > 1:
    file_path = Path(sys.argv[1])
    if file_path.exists():
        print(f"\n\nTesting with real file: {file_path}")
        with open(file_path, 'rb') as f:
            data = f.read()
        
        print(f"File size: {len(data)} bytes")
        
        # Try to detect P-code
        detector = EnhancedPCodeDetector()
        pcode_info = detector.detect_pcode(data, file_path.name)
        
        if pcode_info.pcode_offset >= 0:
            print(f"P-code detected at offset 0x{pcode_info.pcode_offset:04x}, length {pcode_info.pcode_length}")
            print(f"Confidence: {pcode_info.confidence}")
            print(f"Sections: {len(pcode_info.sections)}")
            
            # Extract and show P-code
            pcode_data = data[pcode_info.pcode_offset:pcode_info.pcode_offset + pcode_info.pcode_length]
            print(f"\nFirst 64 bytes of P-code:")
            for i in range(0, min(64, len(pcode_data)), 16):
                hex_str = ' '.join(f'{b:02x}' for b in pcode_data[i:i+16])
                ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in pcode_data[i:i+16])
                print(f"  {i:04x}: {hex_str:<48}  {ascii_str}")
            
            # Decode it
            decoder = PCodeDecoderV2(version)
            decoded = decoder.decode_pcode_section(pcode_data, file_path.name, pcode_info)
            print(f"\nDecoded {len(decoded.instructions)} instructions")
            
            # Show first few
            if decoded.instructions:
                print("\nFirst 10 instructions:")
                for i, inst in enumerate(decoded.instructions[:10]):
                    print(f"  {i+1:2d}. {inst.text_format}")
        else:
            print("No P-code detected in file")