#!/usr/bin/env python3
"""Test script for PowerBuilder decoder to help refine the control sequence mappings."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from extract.pbd.utils.powerbuilder_decoder import (
    decode_powerbuilder_text, 
    analyze_control_sequences,
    PB_DECODE_MAP
)


def test_known_patterns():
    """Test the decoder with known patterns from the user's observations."""
    
    test_cases = [
        # Pattern: "a*dress" where * should be 'd'
        # If * is 0x2A followed by some byte that maps to 'd'
        (b"a\x2A\x4Adress", "address"),  # Assuming 0x4A -> 'd'
        
        # Pattern: ".*Jate" where *J should be 'd'
        (b".\x2A\x4Aate", ".date"),  # Assuming 0x4A -> 'd'
        
        # Pattern: "COL*LMN" where *L should be 'U'
        (b"COL\x2A\x4CMN", "COLUMN"),  # Assuming 0x4C -> 'u'
        
        # These patterns need the correct second byte to be determined:
        # Pattern: "trea*ment" where * should be 't'
        # Pattern: "LOG*C" where * should be 'I'
    ]
    
    print("Testing known patterns:")
    print("-" * 50)
    
    for input_bytes, expected in test_cases:
        decoded = decode_powerbuilder_text(input_bytes)
        status = "✓" if decoded == expected else "✗"
        print(f"{status} Input: {input_bytes.hex()} -> '{decoded}' (expected: '{expected}')")
    
    print()


def analyze_sample_file(file_path: str):
    """Analyze a sample file to find control sequences."""
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        print(f"Analyzing file: {file_path}")
        print(f"File size: {len(data)} bytes")
        print("-" * 50)
        
        # Analyze control sequences
        sequences = analyze_control_sequences(data)
        
        if sequences:
            print(f"Found {len(sequences)} unique control sequences:")
            # Sort by frequency
            for byte_val, count in sorted(sequences.items(), key=lambda x: x[1], reverse=True)[:20]:
                mapped_char = PB_DECODE_MAP.get(byte_val, '?')
                print(f"  0x{byte_val:02X} ({chr(byte_val) if 32 <= byte_val <= 126 else '?'}) -> '{mapped_char}' : {count} occurrences")
        else:
            print("No control sequences found.")
        
        print()
        
        # Try to find specific patterns
        print("Looking for specific patterns:")
        patterns_to_find = [
            (b"a\x2A", "a*"),
            (b"COL\x2A", "COL*"),
            (b"trea\x2A", "trea*"),
            (b"LOG\x2A", "LOG*"),
            (b"\x2AJ", "*J"),
            (b"\x2AL", "*L"),
        ]
        
        for pattern, display in patterns_to_find:
            count = data.count(pattern)
            if count > 0:
                print(f"  Found '{display}' pattern {count} times")
                # Show context
                pos = data.find(pattern)
                if pos >= 0:
                    start = max(0, pos - 10)
                    end = min(len(data), pos + len(pattern) + 10)
                    context = data[start:end]
                    print(f"    Context: {context.hex()}")
                    try:
                        context_decoded = decode_powerbuilder_text(context)
                        print(f"    Decoded: '{context_decoded}'")
                    except:
                        pass
        
    except Exception as e:
        print(f"Error analyzing file: {e}")


def interactive_test():
    """Interactive test mode to try different byte sequences."""
    
    print("\nInteractive decoder test mode")
    print("Enter hex bytes (e.g., '61 2A 4A 64 72 65 73 73') or 'quit' to exit")
    print("-" * 50)
    
    while True:
        hex_input = input("\nHex bytes: ").strip()
        
        if hex_input.lower() in ('quit', 'exit', 'q'):
            break
        
        try:
            # Convert hex string to bytes
            hex_bytes = hex_input.replace(' ', '')
            data = bytes.fromhex(hex_bytes)
            
            # Decode
            decoded = decode_powerbuilder_text(data)
            
            print(f"Input bytes: {data.hex(' ')}")
            print(f"Decoded text: '{decoded}'")
            
            # Show control sequences found
            sequences = analyze_control_sequences(data)
            if sequences:
                print("Control sequences found:")
                for byte_val, count in sequences.items():
                    mapped = PB_DECODE_MAP.get(byte_val, '?')
                    print(f"  0x2A 0x{byte_val:02X} -> '{mapped}'")
            
        except ValueError as e:
            print(f"Invalid hex input: {e}")


def main():
    """Main function."""
    
    print("PowerBuilder Decoder Test Tool")
    print("=" * 50)
    
    # Test known patterns
    test_known_patterns()
    
    # Check if file path provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        analyze_sample_file(file_path)
    
    # Interactive mode
    interactive_test()


if __name__ == "__main__":
    main()