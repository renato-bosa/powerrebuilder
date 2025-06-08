#!/usr/bin/env python3
"""Test the PowerBuilder parser to AST transformation."""

from lark import Lark
from pathlib import Path
import json

from parse.powerbuilder_transformer import PowerBuilderTransformer

# Load the fixed grammar
grammar_path = Path("parse/grammar/experimental/powerbuilder_fixed_v2.lark")
with open(grammar_path) as f:
    grammar = f.read()

# Test cases that work with current grammar
TEST_CASES = [
    # Window type declaration
    ("""global type w_test from window
end type""", "Window type declaration"),
    
    # Function
    ("""function integer of_test()
    return 1
end function""", "Function declaration"),
    
    # Function with parameters
    ("""public function string get_name(string first_name, ref integer id)
    return first_name
end function""", "Function with parameters"),
]

def ast_to_dict(node):
    """Convert AST node to dictionary for display."""
    if hasattr(node, '__dict__'):
        result = {
            'type': node.__class__.__name__,
        }
        for key, value in node.__dict__.items():
            if key.startswith('_'):
                continue
            if isinstance(value, list):
                result[key] = [ast_to_dict(item) for item in value]
            elif hasattr(value, '__dict__'):
                result[key] = ast_to_dict(value)
            else:
                result[key] = str(value) if value is not None else None
        return result
    elif isinstance(node, dict):
        return {k: ast_to_dict(v) if hasattr(v, '__dict__') else v for k, v in node.items()}
    elif isinstance(node, list):
        return [ast_to_dict(item) for item in node]
    else:
        return str(node) if node is not None else None

def test_parser_to_ast():
    """Test the parser to AST transformation."""
    print("PowerBuilder Parser to AST Test")
    print("=" * 50)
    
    # Create parser
    try:
        parser = Lark(grammar, start='start', parser='lalr')
        transformer = PowerBuilderTransformer()
        print("✓ Parser and transformer created successfully!\n")
    except Exception as e:
        print(f"✗ Failed to create parser: {e}")
        return
    
    for code, description in TEST_CASES:
        print(f"\n--- {description} ---")
        print(f"Code:\n{code}")
        print("-" * 30)
        
        try:
            # Parse code
            parse_tree = parser.parse(code)
            print("✓ Parsed successfully!")
            
            # Transform to AST
            ast = transformer.transform(parse_tree)
            print("✓ Transformed to AST!")
            
            # Display AST structure
            print("\nAST Structure:")
            print(f"AST object: {ast}")
            print(f"AST type: {type(ast)}")
            if isinstance(ast, dict):
                print("File elements:")
                for elem in ast.get('elements', []):
                    if hasattr(elem, '__class__'):
                        print(f"  - {elem.__class__.__name__}")
                        if hasattr(elem, '__dict__'):
                            for key, value in elem.__dict__.items():
                                if not key.startswith('_'):
                                    print(f"    {key}: {value}")
            elif hasattr(ast, '__dict__'):
                print(f"Type: {ast.__class__.__name__}")
                for key, value in ast.__dict__.items():
                    if not key.startswith('_'):
                        print(f"  {key}: {value}")
            
        except Exception as e:
            print(f"✗ Failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Run the test."""
    test_parser_to_ast()

if __name__ == "__main__":
    main()