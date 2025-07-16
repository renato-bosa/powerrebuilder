#!/usr/bin/env python3
"""Analyze PowerBuilder encoding patterns to determine the correct mapping.

This script helps reverse-engineer the PowerBuilder 0x2A control byte encoding
by analyzing patterns in PBD files and comparing with known corruptions.
"""

import sys
import re
from pathlib import Path
from collections import Counter, defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.extract.pbd.utils.powerbuilder_decoder import PB_CONTROL_BYTE


def find_control_patterns(data: bytes, context_size: int = 20) -> list:
    """Find all occurrences of control byte patterns with context."""
    patterns = []
    i = 0
    
    while i < len(data) - 1:
        if data[i] == PB_CONTROL_BYTE:
            next_byte = data[i + 1]
            
            # Get surrounding context
            start = max(0, i - context_size)
            end = min(len(data), i + 2 + context_size)
            
            before = data[start:i].decode('latin1', errors='replace')
            after = data[i+2:end].decode('latin1', errors='replace')
            
            patterns.append({
                'position': i,
                'control_char': chr(next_byte) if 32 <= next_byte <= 126 else f'\\x{next_byte:02x}',
                'control_byte': next_byte,
                'before': before[-20:],  # Last 20 chars
                'after': after[:20],     # First 20 chars
                'full_context': before + f"*{chr(next_byte) if 32 <= next_byte <= 126 else '?'}" + after
            })
            
            i += 2
        else:
            i += 1
    
    return patterns


def analyze_word_patterns(patterns: list) -> dict:
    """Analyze patterns to find split words and deduce mappings."""
    mappings = defaultdict(list)
    
    # Known corruption patterns from data_corruption_fix.py
    known_fixes = {
        # From actual examples
        ('address', 'a*Jress'): ('J', 'd'),
        ('date', '.*Jate'): ('J', 'd'),
        ('COLUMN', 'COL*LMN'): ('L', 'U'),
        # Add more as we find them
    }
    
    # Look for patterns that match word splits
    word_pattern = re.compile(r'([a-zA-Z]+)\*([A-Z])([a-zA-Z]*)')
    
    for pattern in patterns:
        context = pattern['full_context']
        
        # Check if this matches a word split pattern
        match = word_pattern.search(context)
        if match:
            before_star = match.group(1)
            control_letter = match.group(2)
            after_star = match.group(3)
            
            # If this is the control character we found
            if pattern['control_char'] == control_letter:
                # This could be a split word
                suspected_word = before_star + '?' + after_star
                mappings[control_letter].append({
                    'context': context,
                    'suspected_word': suspected_word,
                    'position': pattern['position']
                })
    
    return mappings


def deduce_mapping_table(data: bytes) -> dict:
    """Try to deduce the complete mapping table from patterns."""
    patterns = find_control_patterns(data)
    
    # Count frequency of each control byte
    control_freq = Counter(p['control_byte'] for p in patterns)
    
    # Analyze word patterns
    word_mappings = analyze_word_patterns(patterns)
    
    # Known mappings from observation
    known_mappings = {
        0x4A: 'd',  # *J → d
        0x4C: 'u',  # *L → u (but might be 'U' based on COLUMN example?)
    }
    
    # Try to deduce pattern
    print("Control Byte Frequency Analysis:")
    print("-" * 50)
    for byte_val, count in control_freq.most_common(20):
        char = chr(byte_val) if 32 <= byte_val <= 126 else f'0x{byte_val:02X}'
        known = known_mappings.get(byte_val, '?')
        print(f"*{char} (0x{byte_val:02X}) → '{known}' : {count} occurrences")
    
    print("\n\nWord Split Analysis:")
    print("-" * 50)
    for control_char, examples in word_mappings.items():
        print(f"\n*{control_char} appears in:")
        for ex in examples[:5]:  # Show first 5 examples
            print(f"  '{ex['context'].strip()}'")
            print(f"  Suspected word: {ex['suspected_word']}")
    
    # Look for specific patterns that might reveal the mapping
    print("\n\nSearching for specific patterns:")
    print("-" * 50)
    
    # Common words that might be split
    test_words = [
        'address', 'date', 'column', 'table', 'select', 'where', 'from',
        'update', 'insert', 'delete', 'treatment', 'logic', 'name'
    ]
    
    for word in test_words:
        # Check each possible split position
        for i in range(1, len(word)):
            prefix = word[:i]
            suffix = word[i:]
            
            # Search for this pattern in the data
            search_pattern = prefix.encode() + b'\x2A' + b'.' + suffix.encode()
            
            import re
            matches = list(re.finditer(search_pattern.replace(b'.', b'[\\x00-\\xFF]'), data))
            
            if matches:
                for match in matches[:3]:  # Show first 3 matches
                    control_byte = data[match.start() + len(prefix) + 1]
                    control_char = chr(control_byte) if 32 <= control_byte <= 126 else f'0x{control_byte:02X}'
                    missing_char = word[i]
                    
                    print(f"Found '{word}' split as '{prefix}*{control_char}{suffix}'")
                    print(f"  This suggests: *{control_char} (0x{control_byte:02X}) → '{missing_char}'")
    
    return known_mappings


def analyze_file(file_path: str):
    """Analyze a PBD file to understand the encoding."""
    print(f"\nAnalyzing: {file_path}")
    print("=" * 70)
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        print(f"File size: {len(data)} bytes")
        
        # Find how many control sequences exist
        control_count = data.count(b'\x2A')
        print(f"Total asterisk (*) characters: {control_count}")
        
        # Deduce the mapping
        mappings = deduce_mapping_table(data)
        
        # Show some example contexts
        patterns = find_control_patterns(data)
        print(f"\n\nExample contexts (first 10):")
        print("-" * 50)
        for i, pattern in enumerate(patterns[:10]):
            print(f"{i+1}. ...{pattern['before'][-10:]}*{pattern['control_char']}{pattern['after'][:10]}...")
        
    except Exception as e:
        print(f"Error analyzing file: {e}")


def create_mapping_hypothesis():
    """Create a hypothesis for the complete mapping based on analysis."""
    print("\n\nMapping Hypothesis:")
    print("=" * 50)
    
    # Based on the pattern that *J→d and *L→u, let's analyze:
    # J (ASCII 74) → d (ASCII 100)
    # L (ASCII 76) → u (ASCII 117)
    
    # Check if it's a simple rotation cipher
    j_rot = (ord('d') - ord('j')) % 26  # -6
    l_rot = (ord('u') - ord('l')) % 26  # +9
    
    print(f"ROT analysis: J→d is ROT{j_rot}, L→u is ROT{l_rot}")
    print("Not a simple rotation cipher.")
    
    # Check if it's based on alphabet position
    j_pos = ord('J') - ord('A') + 1  # 10
    d_pos = ord('d') - ord('a') + 1  # 4
    l_pos = ord('L') - ord('A') + 1  # 12
    u_pos = ord('u') - ord('a') + 1  # 21
    
    print(f"\nAlphabet position: J({j_pos})→d({d_pos}), L({l_pos})→u({u_pos})")
    
    # It might be a custom lookup table
    print("\nThis appears to be a custom lookup table, not a mathematical transformation.")
    print("We need more examples to complete the mapping.")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_pb_encoding.py <pbd_file> [pbd_file2 ...]")
        print("\nThis script analyzes PowerBuilder PBD files to reverse-engineer")
        print("the 0x2A control byte encoding scheme.")
        sys.exit(1)
    
    for file_path in sys.argv[1:]:
        if Path(file_path).exists():
            analyze_file(file_path)
        else:
            print(f"File not found: {file_path}")
    
    create_mapping_hypothesis()


if __name__ == "__main__":
    main()