#!/usr/bin/env python3
"""
Deep analysis of the specific f_get_username.fun file to determine
if it actually contains executable P-code or is just data.
"""

import sys
import os
from pathlib import Path
import math

def analyze_file_deeply(file_path: str):
    """Perform deep analysis of the file."""
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"=== DEEP ANALYSIS OF {Path(file_path).name} ===")
    print(f"File size: {len(data)} bytes")
    
    # Find the P-code section
    first_newline = data.find(b'\n')
    second_newline = data.find(b'\n', first_newline + 1)
    pcode_start = second_newline + 1
    pcode_data = data[pcode_start:]
    
    print(f"P-code section: {len(pcode_data)} bytes starting at offset {pcode_start}")
    
    # Detailed analysis of P-code section
    analyze_pcode_section(pcode_data)
    
    # Check if this looks like a DataWindow
    check_datawindow_characteristics(data)

def analyze_pcode_section(pcode_data: bytes):
    """Analyze the supposed P-code section in detail."""
    
    print(f"\n=== P-CODE SECTION ANALYSIS ===")
    
    # Basic statistics
    null_count = pcode_data.count(0x00)
    null_percentage = (null_count / len(pcode_data)) * 100
    
    print(f"Null bytes: {null_count}/{len(pcode_data)} ({null_percentage:.1f}%)")
    
    # Entropy calculation
    byte_counts = {}
    for byte in pcode_data:
        byte_counts[byte] = byte_counts.get(byte, 0) + 1
    
    entropy = 0.0
    for count in byte_counts.values():
        probability = count / len(pcode_data)
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    print(f"Entropy: {entropy:.3f} bits/byte")
    
    # Most common bytes
    sorted_bytes = sorted(byte_counts.items(), key=lambda x: x[1], reverse=True)
    print(f"Most common bytes:")
    for i, (byte, count) in enumerate(sorted_bytes[:10]):
        percentage = (count / len(pcode_data)) * 100
        ascii_char = chr(byte) if 32 <= byte < 127 else '.'
        print(f"  {i+1:2d}. 0x{byte:02x} ('{ascii_char}'): {count:6d} times ({percentage:5.2f}%)")
    
    # Look for text patterns that suggest this is data, not code
    print(f"\n=== TEXT PATTERN ANALYSIS ===")
    
    # Look for Unicode text patterns (Windows uses UTF-16LE)
    unicode_patterns = 0
    for i in range(0, len(pcode_data) - 1, 2):
        if pcode_data[i] != 0 and pcode_data[i+1] == 0:
            unicode_patterns += 1
    
    unicode_percentage = (unicode_patterns * 2 / len(pcode_data)) * 100
    print(f"Potential Unicode text patterns: {unicode_patterns} ({unicode_percentage:.1f}%)")
    
    # Extract some potential text
    potential_text = []
    for i in range(0, min(1000, len(pcode_data) - 1), 2):
        if pcode_data[i] != 0 and pcode_data[i+1] == 0:
            char = chr(pcode_data[i])
            if 32 <= ord(char) < 127:  # Printable ASCII
                potential_text.append(char)
        else:
            if potential_text and len(potential_text) >= 3:
                text = ''.join(potential_text)
                if len(text) >= 3:
                    print(f"  Found text: '{text}'")
            potential_text = []
    
    # Show hex dump of interesting sections
    print(f"\n=== HEX DUMP SAMPLES ===")
    
    # Show beginning of P-code section
    print(f"Beginning of P-code section (first 64 bytes):")
    hex_dump(pcode_data[:64])
    
    # Find and show sections with higher diversity
    chunk_size = 256
    interesting_chunks = []
    
    for i in range(0, len(pcode_data), chunk_size):
        chunk = pcode_data[i:i+chunk_size]
        if len(chunk) < chunk_size // 2:
            continue
        
        unique_bytes = len(set(chunk))
        null_pct = (chunk.count(0x00) / len(chunk)) * 100
        
        if unique_bytes > 30 and null_pct < 50:
            interesting_chunks.append((i, unique_bytes, null_pct, chunk))
    
    print(f"\nMost interesting chunks (high diversity, low nulls):")
    interesting_chunks.sort(key=lambda x: (x[1], -x[2]), reverse=True)
    
    for i, (offset, unique, null_pct, chunk) in enumerate(interesting_chunks[:3]):
        print(f"Chunk {i+1} at offset {offset}: {unique} unique bytes, {null_pct:.1f}% nulls")
        hex_dump(chunk[:64], offset)

def hex_dump(data: bytes, start_offset: int = 0):
    """Create a hex dump of the data."""
    for i in range(0, len(data), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"  {start_offset + i:08x}: {hex_part:<48} {ascii_part}")

def check_datawindow_characteristics(data: bytes):
    """Check if this file has DataWindow characteristics."""
    
    print(f"\n=== DATAWINDOW CHARACTERISTICS CHECK ===")
    
    # Look for DataWindow-specific keywords
    dw_keywords = [
        b'column', b'table', b'retrieve', b'header', b'detail', b'summary',
        b'datawindow', b'processing', b'control', b'text', b'expression',
        b'edit', b'dropdown', b'validation', b'format'
    ]
    
    found_keywords = []
    for keyword in dw_keywords:
        # Look for both direct and Unicode versions
        if keyword in data:
            found_keywords.append(keyword.decode('utf-8'))
        
        # Check Unicode version (UTF-16LE)
        unicode_keyword = keyword.decode('utf-8').encode('utf-16le')
        if unicode_keyword in data:
            found_keywords.append(f"{keyword.decode('utf-8')} (Unicode)")
    
    if found_keywords:
        print(f"DataWindow keywords found: {found_keywords}")
        print("CONCLUSION: This appears to be a DataWindow definition file")
        print("DataWindow files contain layout/formatting data, not executable P-code")
    else:
        print("No obvious DataWindow keywords found")
    
    # Check for form/control definitions
    control_patterns = [
        b'id=', b'name=', b'x=', b'y=', b'width=', b'height=', 
        b'type=', b'color=', b'font='
    ]
    
    control_count = 0
    for pattern in control_patterns:
        if pattern in data:
            control_count += 1
    
    if control_count > 3:
        print(f"Found {control_count} control-related patterns")
        print("This suggests UI/form definition data rather than executable code")

def final_assessment(file_path: str):
    """Provide final assessment."""
    
    print(f"\n" + "="*60)
    print(f"FINAL ASSESSMENT")
    print(f"="*60)
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Get P-code section
    first_newline = data.find(b'\n')
    second_newline = data.find(b'\n', first_newline + 1)
    pcode_data = data[second_newline + 1:]
    
    null_percentage = (pcode_data.count(0x00) / len(pcode_data)) * 100
    
    # Count Unicode text patterns
    unicode_patterns = 0
    for i in range(0, len(pcode_data) - 1, 2):
        if pcode_data[i] != 0 and pcode_data[i+1] == 0:
            unicode_patterns += 1
    unicode_percentage = (unicode_patterns * 2 / len(pcode_data)) * 100
    
    print(f"File: {Path(file_path).name}")
    print(f"Null bytes: {null_percentage:.1f}%")
    print(f"Unicode text patterns: {unicode_percentage:.1f}%")
    
    if null_percentage > 60:
        print("❌ VERDICT: NOT EXECUTABLE P-CODE")
        print("   Reason: Too many null bytes (padding/structure data)")
    elif unicode_percentage > 30:
        print("❌ VERDICT: NOT EXECUTABLE P-CODE") 
        print("   Reason: Contains too much text data (likely DataWindow definition)")
    else:
        print("✅ VERDICT: POSSIBLY EXECUTABLE P-CODE")
        print("   Reason: Reasonable byte distribution for binary code")
    
    print(f"\nROOT CAUSE OF REPETITIVE RETURNS:")
    print(f"1. Current decoder treats ALL bytes as P-code instructions")
    print(f"2. Null bytes (0x00) are mapped to RETURN instructions")
    print(f"3. With {null_percentage:.1f}% null bytes, this creates massive repetition")
    print(f"4. The file appears to be data/structure definition, not executable code")

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python deep_pcode_analysis.py <path_to_fun_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    analyze_file_deeply(file_path)
    final_assessment(file_path)

if __name__ == "__main__":
    main()