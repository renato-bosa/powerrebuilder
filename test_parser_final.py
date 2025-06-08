#!/usr/bin/env python3
"""Final test of the parser with our fixed grammar."""

from parse.parse_coordinator import PowerBuilderParser

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
    
    # Full window (simplified)
    ("""global type w_customer from window
    integer width = 2400
    integer height = 1600
    string title = "Customer Management"
end type""", "Window with properties"),
]

def test_parser():
    """Test the parser with various inputs."""
    print("PowerBuilder Parser Test")
    print("=" * 50)
    
    try:
        parser = PowerBuilderParser()
        print("✓ Parser created successfully\n")
    except Exception as e:
        print(f"✗ Failed to create parser: {e}")
        return
    
    for code, description in TEST_CASES:
        print(f"\n--- {description} ---")
        print(f"Code:\n{code}")
        print("-" * 30)
        
        try:
            # Try without preprocessing first
            result = parser.parse(code, preprocess=False)
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