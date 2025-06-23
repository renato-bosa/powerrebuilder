#!/usr/bin/env python3
"""Test the improved PowerBuilder decoder on the remaining corrupted files."""

import sys
sys.path.insert(0, '.')

from extract.pbd.utils.powerbuilder_decoder import decode_powerbuilder_text

# Test cases from the corrupted files
test_cases = [
    # From d_get_person_details_sql.dwo.srd
    ('COLUMN(NA *E="person.medicare_number")', 'COLUMN(NAME="person.medicare_number")'),
    
    # From d_gst_rate_ds.dwo.srd (similar pattern)
    ('COLUMN(NA *E="gst_rate.rate")', 'COLUMN(NAME="gst_rate.rate")'),
    
    # From d_get_patientaddress_sql.dwo.srd
    ('COLUMN(NAME="address.addess_id")', 'COLUMN(NAME="address.address_id")'),
    ('COLUMN(NAME=" ddress.create_datetime")', 'COLUMN(NAME="address.create_datetime")'),
    
    # Other patterns that might still exist
    ('COL*MN(NAME="test")', 'COLUMN(NAME="test")'),
    ('TABLE(NA *E="person")', 'TABLE(NAME="person")'),
    ('WHERE(LOG*C="and")', 'WHERE(LOGIC="and")'),
    
    # Unclosed quote patterns
    ('COLUMN(NAME="person.doctor_name *)', 'COLUMN(NAME="person.doctor_name")'),
    ('COLUMN(NAME="person.person_status"* COLUMN(NAME="person.discount_id")', 
     'COLUMN(NAME="person.person_status") COLUMN(NAME="person.discount_id")'),
]

print("Testing Improved PowerBuilder Decoder")
print("=" * 50)

success_count = 0
for corrupted, expected in test_cases:
    # Encode and decode to simulate real usage
    data = corrupted.encode('latin1')
    result = decode_powerbuilder_text(data)
    
    status = "✓" if result == expected else "✗"
    if result == expected:
        success_count += 1
    
    print(f"\n{status} Test {success_count}/{len(test_cases)}:")
    print(f"  Input:    {corrupted}")
    print(f"  Expected: {expected}")
    print(f"  Result:   {result}")

print(f"\nOverall Success Rate: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")

# Now test on actual file content
print("\n\nTesting on Actual File Content:")
print("-" * 50)

# Read one of the corrupted files
try:
    with open('output/extracted/pbd_files/dcm_detailobjects.pbd/dcm_detailobjects.pbd/d_get_person_details_sql.dwo.srd', 'r', encoding='latin1') as f:
        content = f.read()
    
    # Re-decode with improved decoder
    data = content.encode('latin1')
    fixed_content = decode_powerbuilder_text(data)
    
    # Check if NA *E= pattern is fixed
    import re
    na_e_count = len(re.findall(r'NA\s*\*\s*E=', fixed_content))
    print(f"NA *E= patterns remaining: {na_e_count}")
    
    # Check for other patterns
    asterisk_patterns = re.findall(r'\*[A-Z]', fixed_content)
    print(f"*[A-Z] patterns remaining: {len(asterisk_patterns)}")
    if asterisk_patterns:
        print(f"Examples: {asterisk_patterns[:5]}")
    
    # Show a sample of the fixed content
    lines = fixed_content.split('\n')
    print("\nSample of fixed content:")
    for i, line in enumerate(lines[5:25]):
        if 'NAME=' in line or '*' in line:
            print(f"  Line {i+6}: {line.strip()}")
            
except Exception as e:
    print(f"Error reading file: {e}")

print("\n\nConclusion:")
print("The improved decoder should now handle:")
print("  1. NA *E= patterns → NAME=")
print("  2. Common word patterns with specific fixes")
print("  3. Missing characters in 'address' variations")
print("  4. Unclosed quotes and parentheses")
print("  5. Expanded domain dictionary with learned words")