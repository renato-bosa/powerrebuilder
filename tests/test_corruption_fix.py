#!/usr/bin/env python3
"""Test the data corruption fix."""

from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from extract.pbd.structures.data_corruption_fix import DataCorruptionFixer, fix_extracted_datawindow


def test_corruption_fix():
    """Test the corruption fix on real examples."""
    
    # Real corrupted examples from the extraction
    test_cases = [
        # Example 1: address split
        ('COLUMN(NAME="address.add * ess_id")', 'COLUMN(NAME="address.address_id")'),
        
        # Example 2: COL *L MN
        ('COL *L MN(NAME="jobs.update_datetime")', 'COLUMN(NAME="jobs.update_datetime")'),
        
        # Example 3: date field  
        ('COLUMN(NAME="jobs.*Jate_required")', 'COLUMN(NAME="jobs.Jate_required")'),
        
        # Example 4: table name
        ('TAB * E(NAME="person_address")', 'TABLE(NAME="person_address")'),
        
        # Example 5: Full SQL with corruption
        (
            '''PBSELECT(VERSION(400)
    TAB * E(NAME="address")
    COLUMN(NAME="address.add * ess_id")
    COLUMN(NAME="address.* ddress_type")
    WHERE(EXP1 ="person_address.person_id" OP ="=" EXP2 ="*))''',
            '''PBSELECT(VERSION(400)
    TABLE(NAME="address")
    COLUMN(NAME="address.address_id")
    COLUMN(NAME="address.address_type")
    WHERE(EXP1 ="person_address.person_id" OP ="=" EXP2 ="*))'''
        )
    ]
    
    print("Testing Data Corruption Fix")
    print("=" * 60)
    
    fixer = DataCorruptionFixer()
    
    for i, (corrupted, expected) in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Input:    {corrupted[:50]}...")
        
        # Detect corruption
        has_corruption = fixer.detect_corruption(corrupted)
        print(f"Detected: {has_corruption}")
        
        # Fix corruption
        fixed, fix_count = fixer.fix_corrupted_content(corrupted)
        print(f"Fixed:    {fixed[:50]}...")
        print(f"Fixes:    {fix_count}")
        
        # Check if it matches expected
        success = fixed.strip() == expected.strip()
        print(f"Success:  {success}")
        
        if not success:
            print(f"Expected: {expected[:50]}...")
            print(f"Diff: Got '{fixed}' but expected '{expected}'")
    
    # Test the main function
    print("\n" + "=" * 60)
    print("Testing fix_extracted_datawindow function:")
    
    sample_dw = '''// DataWindow: d_test.dwo
PBSELECT(VERSION(400)
    TAB * E(NAME="test_table")
    COL *L MN(NAME="test_table.id")
    COLUMN(NAME="test_table.na * me")
    WHERE(EXP1 ="test_table.status" OP ="=" EXP2 ="A"))'''
    
    print("\nOriginal:")
    print(sample_dw)
    
    fixed = fix_extracted_datawindow(sample_dw, "d_test.dwo")
    
    print("\nFixed:")
    print(fixed)
    
    # Validate the fixed content
    issues = fixer.validate_sql_syntax(fixed)
    print(f"\nValidation issues: {issues if issues else 'None'}")


if __name__ == "__main__":
    test_corruption_fix()