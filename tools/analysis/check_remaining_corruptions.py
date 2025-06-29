#!/usr/bin/env python3
"""Check what corruption patterns remain after all improvements."""

import re
from pathlib import Path

# Files that had corruptions according to the earlier analysis
files_to_check = [
    'data/output/current/extracted/pbd_files/dcm_detailobjects.pbd/dcm_detailobjects.pbd/d_get_person_details_sql.dwo.srd',
    'data/output/current/extracted/pbd_files/dcm_detailobjects.pbd/dcm_detailobjects.pbd/d_gst_rate_ds.dwo.srd',
    'data/output/current/extracted/pbd_files/dcm_detailobjects.pbd/dcm_detailobjects.pbd/d_get_patientaddress_sql.dwo.srd'
]

print("Checking Remaining Corruption Patterns")
print("=" * 50)

# Import the improved decoder
import sys
sys.path.insert(0, '.')
from extract.pbd.utils.powerbuilder_decoder import decode_powerbuilder_text

for file_path in files_to_check:
    if Path(file_path).exists():
        print(f"\nFile: {Path(file_path).name}")
        print("-" * 40)
        
        # Read the file
        with open(file_path, 'r', encoding='latin1') as f:
            original_content = f.read()
        
        # Re-decode with improved decoder
        data = original_content.encode('latin1')
        decoded_content = decode_powerbuilder_text(data)
        
        # Look for remaining corruption patterns
        patterns_to_check = [
            (r'NA\s*\*\s*E=', 'NA *E='),
            (r'\*[A-Z]', '*[Letter]'),
            (r'\s\*\s', ' * '),
            (r'\w+\*\w+', 'word*word'),
            (r'addess', 'addess (missing r)'),
            (r'\s+ddress', ' ddress (missing a)'),
        ]
        
        remaining_issues = []
        for pattern, description in patterns_to_check:
            matches = re.findall(pattern, decoded_content)
            if matches:
                remaining_issues.append((description, matches))
        
        if remaining_issues:
            print("Remaining issues:")
            for desc, matches in remaining_issues:
                print(f"  - {desc}: {len(matches)} instances")
                print(f"    Examples: {matches[:3]}")
                
            # Show context for each match
            print("\nContext for remaining issues:")
            for desc, matches in remaining_issues:
                for match in matches[:2]:  # First 2 examples
                    # Find the match in context
                    idx = decoded_content.find(match)
                    if idx >= 0:
                        start = max(0, idx - 30)
                        end = min(len(decoded_content), idx + len(match) + 30)
                        context = decoded_content[start:end]
                        print(f"\n  '{match}' in context:")
                        print(f"    ...{context}...")
        else:
            print("✓ No corruption patterns found!")
    else:
        print(f"\nFile not found: {file_path}")

# Also check if the specific patterns mentioned in the test were fixed
print("\n\nChecking specific test patterns:")
print("-" * 40)

test_patterns = [
    ('COLUMN(NA *E="person.medicare_number")', 'COLUMN(NAME="person.medicare_number")'),
    ('COLUMN(NAME="address.addess_id")', 'COLUMN(NAME="address.address_id")'),
    ('COLUMN(NAME=" ddress.create_datetime")', 'COLUMN(NAME="address.create_datetime")'),
]

for corrupted, expected in test_patterns:
    data = corrupted.encode('latin1')
    result = decode_powerbuilder_text(data)
    status = "✓" if result == expected else "✗"
    print(f"{status} '{corrupted}' → '{result}'")