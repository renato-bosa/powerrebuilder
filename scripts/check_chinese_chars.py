#!/usr/bin/env python3
"""Check for Chinese/garbled characters in output files."""

import os
import sys
from pathlib import Path
import json
import re

# Common Chinese/garbled character patterns found in the past
CHINESE_CHARS_REGEX = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u2000-\u2fff]')
COMMON_GARBLED = ['䅄⩔', '䑣呁', '舀', 'Ƕ']

def check_file_for_chinese(filepath: Path) -> list[tuple[int, str]]:
    """Check a file for Chinese/garbled characters and return line numbers with matches."""
    matches = []
    
    # Skip binary files
    if filepath.suffix in ['.fun', '.dwo', '.ico', '.bmp', '.jpg', '.png', '.gif']:
        return matches
    
    # Skip metadata JSON files (they're auto-generated)
    if filepath.name.endswith('.meta.json'):
        return matches
        
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                # Check for Chinese characters
                if CHINESE_CHARS_REGEX.search(line):
                    matches.append((line_num, line.strip()))
                # Check for known garbled patterns
                elif any(garbled in line for garbled in COMMON_GARBLED):
                    matches.append((line_num, line.strip()))
    except Exception as e:
        # If we can't read it as text, it's probably binary
        pass
        
    return matches

def main():
    output_dir = Path('output')
    if not output_dir.exists():
        print("No output directory found!")
        return 1
        
    total_files = 0
    files_with_issues = 0
    
    print("Checking for Chinese/garbled characters in output files...")
    print("=" * 80)
    
    for root, dirs, files in os.walk(output_dir):
        for filename in files:
            filepath = Path(root) / filename
            total_files += 1
            
            matches = check_file_for_chinese(filepath)
            if matches:
                files_with_issues += 1
                print(f"\n❌ Found issues in: {filepath.relative_to(output_dir)}")
                for line_num, line in matches[:5]:  # Show first 5 matches
                    print(f"   Line {line_num}: {line[:100]}{'...' if len(line) > 100 else ''}")
                if len(matches) > 5:
                    print(f"   ... and {len(matches) - 5} more matches")
    
    print("\n" + "=" * 80)
    print(f"Summary: Checked {total_files} files")
    if files_with_issues == 0:
        print("✅ No Chinese/garbled characters found!")
        return 0
    else:
        print(f"❌ Found issues in {files_with_issues} files")
        return 1

if __name__ == "__main__":
    sys.exit(main())