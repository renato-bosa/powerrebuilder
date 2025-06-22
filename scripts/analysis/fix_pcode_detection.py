#!/usr/bin/env python3
"""
Fix for the P-code detection issue that causes repetitive return statements.

This script creates an improved P-code detector that:
1. Filters out null-heavy regions before decoding
2. Validates P-code sections based on entropy and patterns
3. Implements proper DataWindow file handling
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from pathlib import Path
from typing import Any

def calculate_entropy(data: bytes) -> float:


    
    

    """Calculate the entropy of a byte sequence."""
    if not data:
        return 0.0
    
    # Count byte frequencies
    byte_counts = {}
    for byte in data:
        byte_counts[byte] = byte_counts.get(byte, 0) + 1
    
    # Calculate entropy
    length = len(data)
    entropy = 0.0
    
    import math
    for count in byte_counts.values():
        probability = count / length
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    return entropy

def is_valid_pcode_section(data: bytes, offset: int = 0, min_length: int = 32) -> bool:


    
    

    """Determine if a data section is likely to contain valid P-code."""
    if len(data) < min_length:
        return False
    
    # Check 1: Null byte percentage should be reasonable
    null_count = data.count(0x00)
    null_percentage = (null_count / len(data)) * 100
    
    if null_percentage > 70:  # More than 70% null bytes
        return False
    
    # Check 2: Entropy should be reasonable (not too low, not too high)
    entropy = calculate_entropy(data)
    if entropy < 1.0 or entropy > 7.0:  # Very low or very high entropy
        return False
    
    # Check 3: Should have reasonable diversity of bytes
    unique_bytes = len(set(data))
    if unique_bytes < 8:  # Too few unique bytes
        return False
    
    # Check 4: Look for P-code instruction patterns
    valid_opcodes = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F
    }
    
    # Count how many bytes look like valid opcodes
    opcode_like_count = 0
    for byte in data:
        if byte in valid_opcodes:
            opcode_like_count += 1
    
    opcode_percentage = (opcode_like_count / len(data)) * 100
    
    # Should have some opcodes, but not be dominated by them
    if opcode_percentage < 5 or opcode_percentage > 90:
        return False
    
    return True

def improved_pcode_detection(file_data: bytes, file_name: str) -> list[dict[str, Any]]:


    
    

    """Improved P-code detection that avoids null-heavy regions."""
    
    print(f"=== IMPROVED P-CODE DETECTION ===")
    print(f"File: {file_name}")
    print(f"Size: {len(file_data)} bytes")
    
    # Check if this is a DataWindow file first
    if b'$PBExportHeader' in file_data and b'datawindow' in file_data:
        print("DETECTED: DataWindow file - skipping P-code detection")
        return []
    
    # For PowerBuilder export format files
    if file_data.startswith(b'HA$PBExportHeader$'):
        # Find the end of headers
        first_newline = file_data.find(b'\n')
        if first_newline > 0:
            second_newline = file_data.find(b'\n', first_newline + 1)
            if second_newline > 0:
                # P-code starts after headers
                pcode_start = second_newline + 1
                pcode_data = file_data[pcode_start:]
                
                print(f"PowerBuilder export format detected")
                print(f"P-code section starts at offset {pcode_start}")
                print(f"P-code section size: {len(pcode_data)} bytes")
                
                # Validate this P-code section
                if is_valid_pcode_section(pcode_data):
                    print("P-code section validation: PASSED")
                    return [{
                        'offset': pcode_start, 'size': len(pcode_data), 'type': 'pcode', 'confidence': 0.9
                    }]
                else:
                    print("P-code section validation: FAILED")
                    print("This appears to be a DataWindow or non-executable object")
                    return []
    
    # For other file formats, scan for P-code sections
    sections = []
    chunk_size = 512
    
    print(f"Scanning for P-code sections in {len(file_data) // chunk_size} chunks...")
    
    for offset in range(0, len(file_data), chunk_size):
        chunk = file_data[offset:offset + chunk_size]
        
        if is_valid_pcode_section(chunk, offset):
            # Extend the section to find its boundaries
            section_start = offset
            section_end = offset + len(chunk)
            
            # Try to extend backwards
            while section_start > 0:
                extended_chunk = file_data[section_start - chunk_size:section_end]
                if is_valid_pcode_section(extended_chunk):
                    section_start -= chunk_size
                else:
                    break
            
            # Try to extend forwards
            while section_end < len(file_data):
                extended_chunk = file_data[section_start:section_end + chunk_size]
                if is_valid_pcode_section(extended_chunk):
                    section_end += chunk_size
                else:
                    break
            
            section_data = file_data[section_start:section_end]
            entropy = calculate_entropy(section_data)
            null_pct = (section_data.count(0x00) / len(section_data)) * 100
            
            print(f"Found P-code section: offset {section_start}, size {section_end - section_start}")
            print(f"  Entropy: {entropy:.2f}, Null%: {null_pct:.1f}%")
            
            sections.append({
                'offset': section_start, 'size': section_end - section_start, 'type': 'pcode', 'confidence': min(entropy / 4.0, 1.0), 'entropy': entropy, 'null_percentage': null_pct
            })
    
    # Remove overlapping sections
    sections = remove_overlapping_sections(sections)
    
    print(f"Final result: {len(sections)} P-code sections detected")
    return sections

def remove_overlapping_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:


    
    

    """Remove overlapping sections, keeping the ones with higher confidence."""
    if not sections:
        return sections
    
    # Sort by offset
    sections.sort(key=lambda x: x['offset'])
    
    result = []
    for section in sections:
        # Check if this section overlaps with any existing result
        overlaps = False
        for existing in result:
            if (section['offset'] < existing['offset'] + existing['size'] and
                section['offset'] + section['size'] > existing['offset']):
                # Overlapping - keep the one with higher confidence
                if section['confidence'] > existing['confidence']:
                    result.remove(existing)
                    result.append(section)
                overlaps = True
                break
        
        if not overlaps:
            result.append(section)
    
    return result

def test_improved_detection(file_path: str) -> None:


    

    """Test the improved detection on a file."""
    path = Path(file_path)
    
    with open(path, 'rb') as f:
        data = f.read()
    
    # Test current (broken) approach
    print("=== CURRENT (BROKEN) APPROACH ===")
    null_count = data.count(0x00)
    total_bytes = len(data)
    print(f"File is {null_count/total_bytes*100:.1f}% null bytes")
    print("Current approach: decode entire file as P-code")
    print("Result: hundreds of RETURN statements from null bytes")
    
    print("\n" + "="*50 + "\n")
    
    # Test improved approach
    sections = improved_pcode_detection(data, path.name)
    
    if not sections:
        print("IMPROVED RESULT: No valid P-code sections found")
        print("This file should not be decoded as P-code")
    else:
        print("IMPROVED RESULT: Found valid P-code sections")
        for i, section in enumerate(sections):
            print(f"  Section {i+1}: {section}")

def create_fixed_detector_class() -> None:


    

    """Create the fixed P-code detector class code."""
    
    fixed_code = '''
"""
Fixed P-code detector that properly handles null-heavy regions and DataWindow files.
"""

import logging
from typing import List, Any

logger = logging.getLogger(__name__)

class FixedPCodeDetector:
    """P-code detector that avoids null-heavy regions and handles DataWindow files."""
    
    @staticmethod
    def calculate_entropy(data: bytes) -> float:

        
        """Calculate the entropy of a byte sequence."""
        if not data:
            return 0.0
        
        byte_counts = {}
        for byte in data:
            byte_counts[byte] = byte_counts.get(byte, 0) + 1
        
        length = len(data)
        entropy = 0.0
        
        for count in byte_counts.values():
            probability = count / length
            if probability > 0:
                import math
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    @staticmethod
    def is_valid_pcode_section(data: bytes, min_length: int = 32) -> bool:

        
        """Determine if a data section is likely to contain valid P-code."""
        if len(data) < min_length:
            return False
        
        # Filter out null-heavy regions
        null_percentage = (data.count(0x00) / len(data)) * 100
        if null_percentage > 70:
            return False
        
        # Check entropy
        entropy = FixedPCodeDetector.calculate_entropy(data)
        if entropy < 1.0 or entropy > 7.0:
            return False
        
        # Check diversity
        unique_bytes = len(set(data))
        if unique_bytes < 8:
            return False
        
        return True
    
    def detect_pcode_sections(self, data: bytes) -> list[dict[str, Any]]:

    
        
    
        """Detect P-code sections using improved algorithms."""
        
        # Check for DataWindow files
        if b'$PBExportHeader' in data and b'datawindow' in data:
            logger.info("DataWindow file detected - no P-code sections")
            return []
        
        # Handle PowerBuilder export format
        if data.startswith(b'HA$PBExportHeader$'):
            first_newline = data.find(b'\\n')
            if first_newline > 0:
                second_newline = data.find(b'\\n', first_newline + 1)
                if second_newline > 0:
                    pcode_start = second_newline + 1
                    pcode_data = data[pcode_start:]
                    
                    if self.is_valid_pcode_section(pcode_data):
                        return [{
                            'offset': pcode_start, 'size': len(pcode_data), 'type': 'pcode', 'confidence': 0.9
                        }]
        
        logger.info("No valid P-code sections found")
        return []
'''
    
    return fixed_code

def main() -> None:


    

    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python fix_pcode_detection.py <path_to_fun_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    test_improved_detection(file_path)
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print("The repetitive RETURN statements are caused by:")
    print("1. P-code detector treating null-heavy regions as valid P-code")
    print("2. P-code decoder mapping 0x00 bytes to RETURN instructions")
    print("3. DataWindow files being processed as executable code")
    print("\nSOLUTION:")
    print("Implement entropy and null-byte filtering in P-code detection")
    print("Add proper DataWindow file detection and handling")
    
    # Show the fixed detector class
    print("\n" + "="*60)
    print("FIXED DETECTOR CLASS:")
    print(create_fixed_detector_class())

if __name__ == "__main__":
    main()