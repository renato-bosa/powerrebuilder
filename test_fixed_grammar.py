#!/usr/bin/env python3
"""Test the fixed PowerBuilder grammar v2."""

from lark import Lark
from pathlib import Path

# Load the fixed grammar
grammar_path = Path("parse/grammar/experimental/powerbuilder_fixed_v2.lark")
with open(grammar_path) as f:
    grammar = f.read()

# Test different PowerBuilder constructs
TEST_CASES = [
    # Simple variable declaration
    ("integer x", "Variable declaration"),
    
    # Assignment
    ("x = 5", "Simple assignment"),
    
    # Window type declaration
    ("""global type w_test from window
end type""", "Window type declaration"),
    
    # Function
    ("""function integer of_test()
    return 1
end function""", "Function declaration"),
    
    # Full window with properties
    ("""global type w_customer from window
    integer width = 2400
    integer height = 1600
    string title = "Customer Management"
end type""", "Window with properties"),
    
    # If statement
    ("""if x > 5 then
    y = 10
else
    y = 20
end if""", "If statement"),
    
    # For loop
    ("""for i = 1 to 10
    total = total + i
next""", "For loop"),
]

def test_parser():
    """Test the parser with various inputs."""
    print("Fixed PowerBuilder Grammar v2 Test")
    print("=" * 50)
    
    try:
        parser = Lark(grammar, start='start', parser='lalr', debug=True)
        print("✓ Parser created successfully!")
        print("✓ No reduce/reduce conflicts!\n")
    except Exception as e:
        print(f"✗ Failed to create parser: {e}")
        return
    
    success_count = 0
    for code, description in TEST_CASES:
        print(f"\n--- {description} ---")
        print(f"Code:\n{code}")
        print("-" * 30)
        
        try:
            result = parser.parse(code)
            print(f"✓ Parsed successfully!")
            success_count += 1
            # Show parse tree structure
            print("Parse tree:")
            print(result.pretty()[:300] + "..." if len(result.pretty()) > 300 else result.pretty())
        except Exception as e:
            print(f"✗ Parse failed: {type(e).__name__}: {e}")
    
    print(f"\n\nSummary: {success_count}/{len(TEST_CASES)} tests passed")

def main():
    """Run the test."""
    test_parser()

if __name__ == "__main__":
    main()