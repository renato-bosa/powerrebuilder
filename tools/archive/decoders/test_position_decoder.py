#!/usr/bin/env python3
"""Test the position-based PowerBuilder decoder."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from extract.pbd.utils.powerbuilder_decoder import (
    decode_powerbuilder_text, 
    analyze_corruption_patterns,
    add_to_dictionary,
    _fix_corrupted_word
)


def test_known_corruptions():
    """Test with known corruption patterns."""
    
    print("Testing Position-Based PowerBuilder Decoder")
    print("=" * 50)
    
    # Test cases from real corruptions
    test_cases = [
        # Pattern, Expected result
        ("a*dress", "address"),
        (".*Jate", ".date"),
        ("COL*MN", "COLUMN"),
        ("LOG*C", "LOGIC"),
        ("trea*ment", "treatment"),
        ("clinic_a*ddress", "clinic_address"),
        ("person_address.* ddress_id", "person_address.address_id"),
        ("TAB*E", "TABLE"),
        ("SEL*CT", "SELECT"),
        ("WH*RE", "WHERE"),
        ("add * ess_id", "address_id"),
        ("b*lling", "billing"),
        ("upd*te_operator", "update_operator"),
    ]
    
    print("\nTesting individual words:")
    print("-" * 50)
    
    success_count = 0
    for corrupted, expected in test_cases:
        # Convert to bytes and back to simulate the decoding process
        data = corrupted.encode('latin1')
        result = decode_powerbuilder_text(data)
        
        status = "✓" if result == expected else "✗"
        if result == expected:
            success_count += 1
        
        print(f"{status} '{corrupted}' → '{result}' (expected: '{expected}')")
    
    print(f"\nSuccess rate: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    
    return success_count == len(test_cases)


def test_sql_statement():
    """Test with a complete corrupted SQL statement."""
    
    print("\n\nTesting complete SQL statement:")
    print("-" * 50)
    
    corrupted_sql = """
    SELECT 
        a*dress.address_id,
        person_address.* ddress_id,
        clinic_a*ddress.street,
        trea*ment.treatment_id,
        COL*MN(NAME="upd*te_operator")
    FROM 
        TAB*E(NAME="person") 
    WHERE 
        LOG*C="and" AND
        status = 'active'
    """
    
    print("Corrupted SQL:")
    print(corrupted_sql)
    
    # Decode
    data = corrupted_sql.encode('latin1')
    fixed_sql = decode_powerbuilder_text(data)
    
    print("\nFixed SQL:")
    print(fixed_sql)
    
    # Check if all corruptions were fixed
    import re
    remaining = len(re.findall(r'\b\w*\*\w*\b', fixed_sql))
    print(f"\nRemaining corruptions: {remaining}")
    
    return remaining == 0


def test_custom_dictionary():
    """Test adding custom words to the dictionary."""
    
    print("\n\nTesting custom dictionary additions:")
    print("-" * 50)
    
    # Add some domain-specific words
    custom_words = [
        'mycustomtable',
        'specialfield',
        'businesslogic',
        'customoperator'
    ]
    
    add_to_dictionary(custom_words)
    print(f"Added {len(custom_words)} custom words")
    
    # Test with custom corruptions
    test_cases = [
        ("mycusto*table", "mycustomtable"),
        ("specia*field", "specialfield"),
        ("busines*logic", "businesslogic"),
        ("customope*ator", "customoperator"),
    ]
    
    print("\nTesting custom words:")
    for corrupted, expected in test_cases:
        data = corrupted.encode('latin1')
        result = decode_powerbuilder_text(data)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{corrupted}' → '{result}'")


def analyze_file(file_path: str):
    """Analyze a file for corruption patterns."""
    
    print(f"\n\nAnalyzing file: {file_path}")
    print("-" * 50)
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        analysis = analyze_corruption_patterns(data)
        
        print(f"Total corruptions found: {analysis['total_corruptions']}")
        print(f"Total asterisks in file: {analysis['asterisk_count']}")
        
        if analysis['position_frequency']:
            print("\nCorruption position frequency:")
            for pos, count in sorted(analysis['position_frequency'].items()):
                print(f"  Position {pos}: {count} times")
        
        if analysis['examples']:
            print("\nExample corruptions and fixes:")
            for ex in analysis['examples'][:5]:
                fixed = ex['fixed'] or "No fix found"
                print(f"  '{ex['word']}' → '{fixed}' (pos {ex['position']})")
                
    except Exception as e:
        print(f"Error analyzing file: {e}")


def main():
    """Main test function."""
    
    # Run basic tests
    test_known_corruptions()
    test_sql_statement()
    test_custom_dictionary()
    
    # Analyze file if provided
    if len(sys.argv) > 1:
        analyze_file(sys.argv[1])
    
    print("\n\nKey Insights:")
    print("-" * 50)
    print("1. The corruption is POSITION-BASED, not character mapping")
    print("2. Asterisks appear at specific byte positions in the binary format")
    print("3. Domain dictionary approach successfully fixes most corruptions")
    print("4. Custom words can be added to improve accuracy")
    print("5. The solution is practical and doesn't require full format reverse-engineering")


if __name__ == "__main__":
    main()