#!/usr/bin/env python3
"""Final test of all corruption patterns including edge cases."""

import sys
sys.path.insert(0, '.')

from src.extract.utils.encoding import decode_powerbuilder_text

# Comprehensive test cases including all edge cases
test_cases = [
    # Original corruption patterns
    ('add*ess', 'address'),
    ('COL*MN', 'COLUMN'),
    ('trea*ment', 'treatment'),
    ('NA *E=', 'NAME='),
    
    # Edge case: parenthesis-asterisk
    ('WHERE(*EXP1', 'WHERE(EXP1'),
    ('TABLE(*NAME', 'TABLE(NAME'),
    
    # Edge case: missing letters without asterisk
    ('address.addess_id', 'address.address_id'),
    (' ddress.create_datetime', ' address.create_datetime'),
    ('"addess"', '"address"'),
    ('" ddress.field"', '"address.field"'),
    
    # Complex real-world patterns
    ('COLUMN(NA *E="person.medicare_number")', 'COLUMN(NAME="person.medicare_number")'),
    ('COLUMN(NAME="address.addess_id")', 'COLUMN(NAME="address.address_id")'),
    ('COLUMN(NAME=" ddress.create_datetime")', 'COLUMN(NAME="address.create_datetime")'),
    ('WHERE(*EXP1 ="tax_type.tax_type_id"', 'WHERE(EXP1 ="tax_type.tax_type_id"'),
    
    # Mixed patterns
    ('SELECT add*ess.addess_id FROM TAB*E', 'SELECT address.address_id FROM TABLE'),
    ('UPDATE cli*ic SET address = "123 ddress street"', 'UPDATE clinic SET address = "123 address street"'),
]

print("Final PowerBuilder Decoder Test - All Patterns")
print("=" * 50)

success_count = 0
for corrupted, expected in test_cases:
    data = corrupted.encode('latin1')
    result = decode_powerbuilder_text(data)
    
    status = "✓" if result == expected else "✗"
    if result == expected:
        success_count += 1
    else:
        print(f"\n{status} FAILED:")
        print(f"  Input:    {corrupted}")
        print(f"  Expected: {expected}")
        print(f"  Result:   {result}")

print(f"\nSuccess Rate: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")

if success_count == len(test_cases):
    print("\n🎉 ALL TESTS PASSED! 🎉")
    print("\nThe PowerBuilder decoder now handles:")
    print("  ✓ Position-based corruption (a*dress, COL*MN, etc.)")
    print("  ✓ Pattern-specific fixes (NA *E=, etc.)")
    print("  ✓ Parenthesis-asterisk patterns (WHERE(*EXP)")
    print("  ✓ Missing letters without asterisks (addess, ddress)")
    print("  ✓ Complex mixed patterns")
    print("\nAll known corruption patterns are now fixed!")