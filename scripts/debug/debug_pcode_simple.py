#!/usr/bin/env python3
"""
Simple P-code analysis to debug repetitive return statements.
"""

import sys
from pathlib import Path


class SimplePCodeDebugger:
    """Simple P-code debugger without complex dependencies."""

    def __init__(self, file_path: str) -> None:


        self.file_path = Path(file_path)
        self.raw_data = None

    def load_and_analyze(self) -> None:




        """Load file and perform basic analysis."""
        print(f"=== Analyzing {self.file_path} ===")

        # Load file
        with open(self.file_path, "rb") as f:
            self.raw_data = f.read()

        print(f"File size: {len(self.raw_data)} bytes")

        # Show file header
        print(f"\nFile header (first 128 bytes):")
        self.hex_dump(self.raw_data[:128])

        # Look for P-code patterns
        self.find_pcode_patterns()

        # Analyze byte frequency
        self.analyze_byte_frequency()

        # Look for specific patterns that might cause repetitive returns
        self.find_repetitive_patterns()

        # Check for DataWindow patterns
        self.check_datawindow_patterns()

    def hex_dump(self, data, start_offset=0) -> None:


        """Create a hex dump of the data."""
        for i in range(0, len(data), 16):
            hex_part = " ".join(f"{b:02x}" for b in data[i:i+16])
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in data[i:i+16])
            print(f"{start_offset + i:08x}: {hex_part:<48} {ascii_part}")

    def find_pcode_patterns(self) -> None:




        """Look for common P-code patterns."""
        print(f"\n=== P-code Pattern Analysis ===")

        # Common P-code opcodes and their potential meanings
        common_opcodes = {
            0x03: "RETURN/EXIT",
            0x04: "CALL", 
            0x05: "LOAD",
            0x06: "STORE",
            0x0A: "BRANCH",
            0x0B: "COMPARE",
            0x0C: "ARITHMETIC",
            0x0D: "LOGICAL",
            0x0E: "STACK_OP",
            0x0F: "MEMORY_OP",
        }

        opcode_counts = {}
        opcode_positions = {}

        for i, byte in enumerate(self.raw_data):
            if byte in common_opcodes:
                opcode_counts[byte] = opcode_counts.get(byte, 0) + 1
                if byte not in opcode_positions:
                    opcode_positions[byte] = []
                opcode_positions[byte].append(i)

        print("Potential P-code opcodes found:")
        for opcode, count in opcode_counts.items():
            name = common_opcodes[opcode]
            print(f"  0x{opcode:02x} ({name}): {count} occurrences")

            # Show first few positions
            positions = opcode_positions[opcode][:10]
            print(f"    First positions: {positions}")

        # Special focus on 0x03 (potential RETURN)
        if 0x03 in opcode_counts:
            return_count = opcode_counts[0x03]
            total_bytes = len(self.raw_data)
            percentage = (return_count / total_bytes) * 100
            print(f"\nRETURN opcode (0x03) analysis:")
            print(f"  Count: {return_count}")
            print(f"  Percentage of file: {percentage:.2f}%")

            if percentage > 1.0:  # More than 1% of the file is return opcodes
                print(f"  WARNING: Unusually high return opcode frequency!")

                # Look at the context around return opcodes
                print(f"  Context analysis (first 5 returns):")
                for i, pos in enumerate(opcode_positions[0x03][:
                    5]):
                    start = max(0, pos - 8)
                    end = min(len(self.raw_data), pos + 8)
                    context = self.raw_data[start:end]
                    print(f"    Return {i+1} at {pos}: {context.hex()}")

    def analyze_byte_frequency(self) -> None:




        """Analyze byte frequency distribution."""
        print(f"\n=== Byte Frequency Analysis ===")

        byte_counts = {}
        for byte in self.raw_data:
            byte_counts[byte] = byte_counts.get(byte, 0) + 1

        # Sort by frequency
        sorted_bytes = sorted(byte_counts.items(), key=lambda x: x[1], reverse=True)

        print("Most frequent bytes:")
        for i, (byte, count) in enumerate(sorted_bytes[:20]):
            percentage = (count / len(self.raw_data)) * 100
            ascii_char = chr(byte) if 32 <= byte < 127 else "."
            print(f"  {i+1:2d}. 0x{byte:02x} ('{ascii_char}'): {count:6d} times ({percentage:5.2f}%)")

        # Check for suspicious patterns
        total_bytes = len(self.raw_data)
        for byte, count in sorted_bytes[:
            5]:
            if count > total_bytes * 0.05:  # More than 5% of the file
                print(f"WARNING: Byte 0x{byte:02x} appears {count} times ({count/total_bytes*100:.1f}%) - very frequent!")

    def find_repetitive_patterns(self) -> None:




        """Look for repetitive patterns that might cause issues."""
        print(f"\n=== Repetitive Pattern Analysis ===")

        # Look for repeated 2-byte, 4-byte, and 8-byte patterns
        pattern_lengths = [2, 4, 8]

        for length in pattern_lengths:
            print(f"\nRepeated {length}-byte patterns:")
            pattern_counts = {}

            for i in range(len(self.raw_data) - length + 1):
                pattern = self.raw_data[i:i+length]
                pattern_key = pattern.hex()
                pattern_counts[pattern_key] = pattern_counts.get(pattern_key, 0) + 1

            # Find most repeated patterns
            sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)

            for pattern_hex, count in sorted_patterns[:
                5]:
                if count > 10:  # Only show patterns that repeat more than 10 times
                    percentage = (count * length / len(self.raw_data)) * 100
                    print(f"  {pattern_hex}: {count} times ({percentage:.2f}% of file)")

                    # Show some positions where this pattern occurs
                    pattern_bytes = bytes.fromhex(pattern_hex)
                    positions = []
                    start_pos = 0
                    while len(positions) < 5:
                        pos = self.raw_data.find(pattern_bytes, start_pos)
                        if pos == -1:
                            break
                        positions.append(pos)
                        start_pos = pos + 1

                    print(f"    Positions: {positions}")

    def check_datawindow_patterns(self) -> None:




        """Check if this might be a DataWindow file."""
        print(f"\n=== DataWindow Pattern Check ===")

        # Look for DataWindow-specific patterns
        dw_patterns = [
            b"$PBExportHeader",
            b"$PBExportComments", 
            b"datawindow",
            b"column",
            b"table",
            b"retrieve",
            b"header",
            b"detail",
            b"summary",
        ]

        found_patterns = []
        for pattern in dw_patterns:
            pos = self.raw_data.find(pattern)
            if pos >= 0:
                found_patterns.append((pattern.decode("utf-8", errors="ignore"), pos))

        if found_patterns:
            print("DataWindow patterns found:")
            for pattern, pos in found_patterns:
                print(f"  '{pattern}' at position {pos}")

            if len(found_patterns) > 2:
                print("WARNING: This appears to be a DataWindow file, not a regular function!")
                print("DataWindow files have different structure and shouldn't be decoded as P-code.")
        else:
            print("No obvious DataWindow patterns found.")

    def analyze_potential_pcode_sections(self) -> None:




        """Try to identify potential P-code sections."""
        print(f"\n=== Potential P-code Section Analysis ===")

        # Look for binary sections (areas with high entropy)
        # P-code typically has lower entropy than random data but higher than text

        chunk_size = 256
        chunks = []

        for i in range(0, len(self.raw_data), chunk_size):
            chunk = self.raw_data[i:i+chunk_size]
            if len(chunk) < chunk_size:
                continue

            # Calculate entropy-like measure
            byte_counts = {}
            for byte in chunk:
                byte_counts[byte] = byte_counts.get(byte, 0) + 1

            # Simple diversity measure
            unique_bytes = len(byte_counts)
            diversity = unique_bytes / 256.0  # 0-1 scale

            chunks.append({
                "offset": i,
                "diversity": diversity,
                "unique_bytes": unique_bytes,
                "chunk": chunk,
            })

        # Sort by diversity to find interesting sections
        chunks.sort(key=lambda x: x["diversity"], reverse=True)

        print(f"Analyzed {len(chunks)} chunks of {chunk_size} bytes each")
        print("Most diverse chunks (potential P-code sections):")

        for i, chunk_info in enumerate(chunks[:
            5]):
            offset = chunk_info["offset"]
            diversity = chunk_info["diversity"]
            unique_bytes = chunk_info["unique_bytes"]

            print(f"  Chunk {i+1}: offset {offset}, diversity {diversity:.3f}, unique bytes {unique_bytes}")

            # Show hex dump of this chunk
            print(f"    First 32 bytes:")
            self.hex_dump(chunk_info["chunk"][:32], offset)

def main() -> None:





    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python debug_pcode_simple.py <path_to_fun_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    debugger = SimplePCodeDebugger(file_path)
    debugger.load_and_analyze()
    debugger.analyze_potential_pcode_sections()

if __name__ == "__main__":
    main()
