#!/usr/bin/env python3
"""Test the parser with simplified grammar."""

from lark import Lark
from pathlib import Path

# Load the simplified grammar
grammar_path = Path("parse/grammar/experimental/powerbuilder_simple.lark")
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
]

def test_parser():
    """Test the parser with various inputs."""
    print("Simplified PowerBuilder Parser Test")
    print("=" * 50)
    
    try:
        parser = Lark(grammar, start='start', parser='lalr')
        print("✓ Parser created successfully\n")
    except Exception as e:
        print(f"✗ Failed to create parser: {e}")
        return
    
    for code, description in TEST_CASES:
        print(f"\n--- {description} ---")
        print(f"Code:\n{code}")
        print("-" * 30)
        
        try:
            result = parser.parse(code)
            print(f"✓ Parsed successfully!")
            if hasattr(result, 'pretty'):
                print(f"Tree preview:\n{result.pretty()[:200]}...")
        except Exception as e:
            print(f"✗ Parse failed: {type(e).__name__}: {e}")

def main():
    """Run the test."""
    test_parser()

if __name__ == "__main__":
    main()