#!/usr/bin/env python3
"""Test script for unified PowerBuilder decoder v2."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extract.pbd.utils.powerbuilder_decoder_v2 import (
    PowerBuilderDecoderV2, decode_powerbuilder_text, analyze_file
)


def test_decoder():
    """Test the unified decoder functionality."""
    
    # Test cases with known corruptions
    test_cases = [
        # Position-based corruption (asterisk)
        (b"a*dress", "address"),
        (b"COL*MN", "COLUMN"),
        (b"trea*ment", "treatment"),
        (b"NA *E=", "NAME="),
        
        # Missing character (no asterisk)
        (b"addess", "address"),
        (b"treament", "treatment"),
        
        # Control byte sequences (if present)
        (b"test\x2a\x64data", "testddata"),  # \x2a\x64 -> 'd'
        
        # Mixed case
        (b"A*DRESS", "ADDRESS"),
        (b"col*mn", "column"),
    ]
    
    decoder = PowerBuilderDecoderV2()
    passed = 0
    failed = 0
    
    print("Testing PowerBuilder Decoder V2")
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
    
    # Test learning capability
    print("\nTesting learning capability:")
    print("-" * 50)
    
    # Add a custom term
    initial_dict_size = len(decoder.domain_dict)
    decoder.domain_dict.add('mycustomterm')
    
    # Test if it can fix corruption with the new term
    test_custom = b"mycusto*term"
    result = decoder.decode(test_custom)
    print(f"Custom term: {test_custom!r} -> {result!r}")
    
    # Test analysis
    print("\nTesting corruption analysis:")
    print("-" * 50)
    
    # Decode several corrupted strings to build statistics
    corrupted_samples = [
        b"a*dress field in the table",
        b"COL*MN name is important",
        b"trea*ment records updated",
        b"patient a*dress updated",
    ]
    
    for sample in corrupted_samples:
        decoder.decode(sample)
    
    analysis = decoder.analyze_corruption_patterns()
    print(f"Total fixes: {analysis['total_fixes']}")
    print(f"Common corruptions: {analysis['common_corruptions'][:3]}")
    print(f"Position frequency: {dict(list(analysis['position_frequency'].items())[:3])}")
    
    return passed == len(test_cases)


def test_real_file():
    """Test on a real PowerBuilder file if available."""
    test_file = Path(__file__).parent.parent / "output" / "extracted" / "pbd_files" / "dcm_detailobjects.pbd" / "dcm_detailobjects.pbd" / "d_get_person_cliniclink_sql.dwo.sql"
    
    if test_file.exists():
        print("\nTesting on real file:")
        print("-" * 50)
        print(f"File: {test_file.name}")
        
        # Read and decode
        with open(test_file, 'rb') as f:
            data = f.read()
        
        decoded = decode_powerbuilder_text(data)
        
        # Check for common corruptions
        corruptions_before = data.decode('latin1', errors='replace').count('*')
        corruptions_after = decoded.count('*')
        
        print(f"Asterisks before: {corruptions_before}")
        print(f"Asterisks after: {corruptions_after}")
        print(f"Reduction: {corruptions_before - corruptions_after}")
        
        # Show a sample
        if len(decoded) > 200:
            print(f"\nSample output:\n{decoded[:200]}...")
    else:
        print("\nReal file not found for testing")


if __name__ == "__main__":
    success = test_decoder()
    test_real_file()
    sys.exit(0 if success else 1)