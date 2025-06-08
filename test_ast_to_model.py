#!/usr/bin/env python3
"""Test AST to model conversion."""

from pathlib import Path
from lark import Lark

from parse.powerbuilder_transformer import PowerBuilderTransformer
from parse.ast_to_model import ASTToModelConverter

# Load the fixed grammar
grammar_path = Path("parse/grammar/experimental/powerbuilder_fixed_v2.lark")
with open(grammar_path) as f:
    grammar = f.read()

# Test code
test_code = """
global type w_customer from window
end type

function integer of_calculate()
    return 42
end function

public function string get_greeting(string name)
    return name
end function
"""

def test_ast_to_model():
    """Test AST to model conversion."""
    print("Testing AST to Model Conversion")
    print("=" * 50)
    
    # Parse
    try:
        parser = Lark(grammar, start='start', parser='lalr')
        transformer = PowerBuilderTransformer()
        
        parse_tree = parser.parse(test_code)
        ast = transformer.transform(parse_tree)
        
        print("✓ Parsing successful!")
        print(f"✓ AST created with {len(ast.get('elements', []))} elements\n")
        
    except Exception as e:
        print(f"✗ Parsing failed: {e}")
        return
    
    # Convert to model
    try:
        converter = ASTToModelConverter()
        model_objects = converter.convert_file(ast)
        
        print(f"✓ Converted to {len(model_objects)} model objects\n")
        
        for obj in model_objects:
            print(f"Model Object: {obj.__class__.__name__}")
            if hasattr(obj, 'name'):
                print(f"  Name: {obj.name}")
            if hasattr(obj, 'return_type'):
                print(f"  Return Type: {obj.return_type}")
            if hasattr(obj, 'parameters'):
                print(f"  Parameters: {obj.parameters}")
            if hasattr(obj, 'source') and obj.source:
                if isinstance(obj.source, str):
                    print(f"  Source:\n    {obj.source}")
                else:
                    print(f"  Source:\n    {obj.source.text}")
            print()
        
    except Exception as e:
        print(f"✗ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    test_ast_to_model()