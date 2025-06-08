#!/usr/bin/env python3
"""Debug the transformer to see what's being parsed."""

from lark import Lark
from pathlib import Path

# Load the fixed grammar
grammar_path = Path("parse/grammar/experimental/powerbuilder_fixed_v2.lark")
with open(grammar_path) as f:
    grammar = f.read()

# Simple function to test
code = """function integer of_test()
    return 1
end function"""

def test_parse_tree():
    """Test parsing and show the tree structure."""
    print("PowerBuilder Parse Tree Debug")
    print("=" * 50)
    
    try:
        parser = Lark(grammar, start='start', parser='lalr')
        print("✓ Parser created successfully!\n")
    except Exception as e:
        print(f"✗ Failed to create parser: {e}")
        return
    
    print(f"Code:\n{code}")
    print("-" * 30)
    
    try:
        # Parse code
        parse_tree = parser.parse(code)
        print("✓ Parsed successfully!")
        
        # Show parse tree
        print("\nParse Tree:")
        print(parse_tree.pretty())
        
    except Exception as e:
        print(f"✗ Parse failed: {type(e).__name__}: {e}")

def main():
    """Run the test."""
    test_parse_tree()

if __name__ == "__main__":
    main()