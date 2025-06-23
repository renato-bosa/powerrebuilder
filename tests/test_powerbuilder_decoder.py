#!/usr/bin/env python3
"""Test script for PowerBuilder decoder - consolidated version."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extract.pbd.utils.powerbuilder_decoder import (
    PowerBuilderDecoder, decode_powerbuilder_text
)


def test_decoder():
    """Test the fixed decoder functionality."""
    
    # Test cases with known corruptions
    test_cases = [
        # Position-based corruption (asterisk)
        (b"a*dress", "address"),  # This was failing in v2
        (b"COL*MN", "COLUMN"),
        (b"trea*ment", "treatment"),
        (b"NA *E=", "NAME="),
        
        # Missing character (no asterisk)
        (b"addess", "address"),
        (b"treament", "treatment"),
        
        # Mixed case
        (b"A*DRESS", "ADDRESS"),
        (b"col*mn", "column"),
        
        # Edge cases
        (b"*ate", "date"),  # Asterisk at start
        (b"patien*", "patient"),  # Asterisk at end
    ]
    
    decoder = PowerBuilderDecoder()
    passed = 0
    failed = 0
    
    print("Testing PowerBuilder Decoder (Consolidated)")
    print("=" * 50)
    
    for test_input, expected in test_cases:
        result = decoder.decode(test_input)
        if result == expected:
            print(f"✓ {test_input!r} -> {result!r}")
            passed += 1
        else:
            print(f"✗ {test_input!r} -> {result!r} (expected: {expected!r})")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Summary: {passed}/{passed+failed} tests passed")
    
    # Test context-aware fixing
    print("\nTesting context-aware fixing:")
    print("-" * 50)
    
    sql_context = b"SELECT patient.patient_id, a*dress.street FROM patient JOIN a*dress ON patient.id = a*dress.person_id"
    result = decoder.decode(sql_context)
    print(f"SQL Context:\n  Input:  {sql_context.decode('latin1', errors='replace')}")
    print(f"  Output: {result}")
    
    # Verify the fix
    if "address" in result and "a*dress" not in result:
        print("  ✓ SQL context correctly fixed!")
    else:
        print("  ✗ SQL context fix failed!")
        failed += 1
    
    # Test that it doesn't interfere with normal text
    print("\nTesting normal text (no corruption):")
    print("-" * 50)
    
    normal_text = b"This is normal text without any corruption"
    result = decoder.decode(normal_text)
    if result == normal_text.decode('latin1'):
        print("✓ Normal text unchanged")
    else:
        print("✗ Normal text was modified incorrectly")
        failed += 1
    
    return failed == 0


def test_real_sql_corruption():
    """Test on a realistic SQL statement with corruption."""
    print("\nTesting realistic SQL corruption:")
    print("-" * 50)
    
    # Simulate a corrupted SQL from a DataWindow
    corrupted_sql = b"""
SELECT 
    person.person_id,
    person.firstname,
    person.lastname,
    a*dress.street,
    a*dress.city,
    trea*ment.description,
    COL*MN billing.amount
FROM person
JOIN a*dress ON person.id = a*dress.person_id
JOIN trea*ment ON person.id = trea*ment.patient_id
JOIN billing ON trea*ment.id = billing.treatment_id
WHERE person.active = 1
"""
    
    result = decode_powerbuilder_text(corrupted_sql)
    
    print("Input SQL (with corruption):")
    print(corrupted_sql.decode('latin1'))
    print("\nOutput SQL (fixed):")
    print(result)
    
    # Check if all corruptions were fixed
    corruptions_fixed = [
        "address" in result and "a*dress" not in result,
        "treatment" in result and "trea*ment" not in result,
        "COLUMN" in result and "COL*MN" not in result,
    ]
    
    if all(corruptions_fixed):
        print("\n✓ All SQL corruptions fixed correctly!")
        return True
    else:
        print("\n✗ Some SQL corruptions were not fixed")
        return False


if __name__ == "__main__":
    success = test_decoder()
    sql_success = test_real_sql_corruption()
    
    if success and sql_success:
        print("\n🎉 All tests passed! The decoder fix is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output above.")
        sys.exit(1)