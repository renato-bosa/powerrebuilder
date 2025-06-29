#!/usr/bin/env python3
"""Analyze extraction results to see how well the PowerBuilder decoder worked."""

import re
import glob
from pathlib import Path

def analyze_corruption_patterns(file_path):
    """Analyze a file for remaining corruption patterns."""
    try:
        with open(file_path, 'r', encoding='latin-1') as f:
            content = f.read()
        
        # Common corruption patterns
        patterns = {
            'asterisk_upper': re.findall(r'\*[A-Z]', content),
            'space_asterisk': re.findall(r'\s\*\s', content),
            'asterisk_space': re.findall(r'\*\s[a-z]', content),
            'broken_words': re.findall(r'\b\w+\*\w+\b', content),
            'missing_quotes': re.findall(r'"\w+\s\*\)', content),
            'NA_*E': re.findall(r'NA\s*\*\s*E=', content),
            'COL_*MN': re.findall(r'COL\s*\*\s*MN', content),
            'address_variants': re.findall(r'a\*dress|ad\*ress|add\*ess|addr\*ss|addre\*s|addres\*', content, re.IGNORECASE),
        }
        
        # Count total corruptions
        total = sum(len(matches) for matches in patterns.values())
        
        return {
            'file': file_path,
            'total_corruptions': total,
            'patterns': {k: len(v) for k, v in patterns.items() if v},
            'examples': {k: v[:3] for k, v in patterns.items() if v}  # First 3 examples
        }
    except Exception as e:
        return {'file': file_path, 'error': str(e)}

def main():
    """Analyze all extracted files."""
    print("PowerBuilder Extraction Analysis")
    print("=" * 50)
    
    # Find all .srd files
    srd_files = glob.glob('data/output/current/extracted/**/*.srd', recursive=True)
    print(f"Found {len(srd_files)} .srd files")
    
    # Analyze corruption patterns
    corrupted_files = []
    total_corruptions = 0
    
    for file_path in srd_files:
        result = analyze_corruption_patterns(file_path)
        if result.get('total_corruptions', 0) > 0:
            corrupted_files.append(result)
            total_corruptions += result['total_corruptions']
    
    print(f"\nFiles with corruption: {len(corrupted_files)}/{len(srd_files)}")
    print(f"Total corruption instances: {total_corruptions}")
    
    # Show worst files
    if corrupted_files:
        print("\nMost corrupted files:")
        sorted_files = sorted(corrupted_files, key=lambda x: x['total_corruptions'], reverse=True)
        for file_info in sorted_files[:10]:
            print(f"\n{Path(file_info['file']).name}: {file_info['total_corruptions']} corruptions")
            for pattern, count in file_info['patterns'].items():
                print(f"  - {pattern}: {count}")
                if pattern in file_info['examples']:
                    print(f"    Examples: {file_info['examples'][pattern]}")
    
    # Check for successfully decoded patterns
    print("\n\nSuccessfully Decoded Patterns:")
    print("-" * 30)
    
    # Look for correctly decoded words
    success_patterns = ['address', 'COLUMN', 'treatment', 'update', 'operator', 'billing', 'clinic']
    
    for file_path in srd_files[:10]:  # Check first 10 files
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            
            found = []
            for pattern in success_patterns:
                if pattern in content:
                    found.append(pattern)
            
            if found:
                print(f"{Path(file_path).name}: Found {', '.join(found)}")
        except:
            pass

if __name__ == "__main__":
    main()