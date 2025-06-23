#!/usr/bin/env python3
"""Test script to validate COMPUTE clause parsing."""

import sys
from pathlib import Path
from lark import Lark
from lark.exceptions import UnexpectedToken, UnexpectedCharacters

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_compute_parsing():
    """Test parsing of COMPUTE clauses in PBSELECT statements."""
    
    # Load the datawindow grammar
    grammar_path = Path(__file__).parent.parent / "parse" / "grammar" / "datawindow.lark"
    grammar_dir = grammar_path.parent
    
    with open(grammar_path, 'r') as f:
        grammar_content = f.read()
    
    # Create parser with import paths
    parser = Lark(grammar_content, 
                  start='datawindow_file', 
                  parser='lalr',
                  import_paths=[str(grammar_dir)])
    
    # Test case 1: Simple COMPUTE
    test_case1 = """// Test COMPUTE
PBSELECT(VERSION(400)
    TABLE(NAME="billing")
    COMPUTE(NAME="min(billing.bill_date)")
    WHERE(EXP1="billing.billing_type" OP="=" EXP2="'I'"))
"""
    
    # Test case 2: Multi-line COMPUTE (like the failing case)
    test_case2 = """// Test multi-line COMPUTE
PBSELECT(VERSION(400)
    TABLE(NAME="billing")
    COMPUTE(NAME="min(billing.bill_date)
        asfirstbill_date")
    WHERE(EXP1="billing.billing_type" OP="=" EXP2="'I'" LOGC="and")
    WHERE(EXP1="billing.bill_id_link" OP="is" EXP2="null" LOGIC=" And"))
"""
    
    # Test case 3: Complex COMPUTE expression
    test_case3 = """// Test complex COMPUTE
PBSELECT(VERSION(400)
    TABLE(NAME="orders")
    COMPUTE(NAME="sum(orders.quantity * orders.price) as total_value")
    WHERE(EXP1="orders.status" OP="=" EXP2="'ACTIVE'"))
"""
    
    test_cases = [
        ("Simple COMPUTE", test_case1),
        ("Multi-line COMPUTE", test_case2),
        ("Complex COMPUTE expression", test_case3)
    ]
    
    success_count = 0
    
    for name, test_code in test_cases:
        print(f"\nTesting: {name}")
        print("-" * 40)
        try:
            tree = parser.parse(test_code)
            print(f"✓ SUCCESS: Parsed successfully")
            success_count += 1
        except (UnexpectedToken, UnexpectedCharacters) as e:
            print(f"✗ FAILED: {type(e).__name__}")
            print(f"  Error: {str(e)[:200]}...")
        except Exception as e:
            print(f"✗ FAILED: Unexpected error - {type(e).__name__}")
            print(f"  Error: {str(e)[:200]}...")
    
    print(f"\n{'='*50}")
    print(f"Summary: {success_count}/{len(test_cases)} tests passed")
    print(f"Success rate: {success_count/len(test_cases)*100:.1f}%")
    
    # Test on the actual failing file
    print(f"\n{'='*50}")
    print("Testing on actual failing file (d_firstbilldate_sql.dwo.srd)...")
    
    failing_file = Path(__file__).parent.parent / "output" / "extracted" / "pbd_files" / "dcm_detailobjects.pbd" / "dcm_detailobjects.pbd" / "d_firstbilldate_sql.dwo.srd"
    
    if failing_file.exists():
        with open(failing_file, 'r') as f:
            content = f.read()
        
        try:
            tree = parser.parse(content)
            print(f"✓ SUCCESS: Actual file parsed successfully!")
        except Exception as e:
            print(f"✗ FAILED: {type(e).__name__}")
            print(f"  Error: {str(e)[:300]}...")
            
            # Show the problematic part
            lines = content.split('\n')
            if len(lines) > 6:
                print("\n  Problematic section:")
                for i in range(4, min(12, len(lines))):
                    print(f"    {i+1}: {lines[i]}")
    else:
        print("  File not found")
    
    return success_count == len(test_cases)


if __name__ == "__main__":
    success = test_compute_parsing()
    sys.exit(0 if success else 1)