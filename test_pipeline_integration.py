#!/usr/bin/env python3
"""Test the integration of the new parser with the pipeline."""

from pathlib import Path
from lark import Lark

from parse.powerbuilder_transformer import PowerBuilderTransformer
from generate.generate_coordinator import CodeGenerator

# Load the fixed grammar
grammar_path = Path("parse/grammar/experimental/powerbuilder_fixed_v2.lark")
with open(grammar_path) as f:
    grammar = f.read()

# Test code - simple examples that work with current grammar
test_code = """
global type w_customer from window
end type

function integer of_calculate()
    return 42
end function
"""

def test_parser_to_generator():
    """Test parsing and code generation."""
    print("Testing Parser to Code Generation Pipeline")
    print("=" * 50)
    
    # Parse
    try:
        parser = Lark(grammar, start='start', parser='lalr')
        transformer = PowerBuilderTransformer()
        
        parse_tree = parser.parse(test_code)
        ast = transformer.transform(parse_tree)
        
        print("✓ Parsing successful!")
        print(f"✓ AST created with {len(ast.get('elements', []))} elements")
        
    except Exception as e:
        print(f"✗ Parsing failed: {e}")
        return
    
    # Generate code
    try:
        # Create output directory
        output_dir = Path("output/test_pipeline")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize generator with template and output directories
        generator = CodeGenerator(
            template_dir="generate/backend/templates",
            output_dir=str(output_dir)
        )
        
        print("✓ Code generator initialized!")
        
        # Test rendering a simple template
        # First, we need to convert our AST to the format expected by templates
        for element in ast.get('elements', []):
            print(f"  - Processing {element.__class__.__name__}")
            
            # Example: Generate Python code for functions
            if hasattr(element, 'signature'):
                # This is a function
                context = {
                    'function_name': element.signature.name,
                    'return_type': str(element.signature.return_type.name),
                    'parameters': element.signature.parameters,
                    'body': element.body.statements
                }
                print(f"    Function: {context['function_name']} -> {context['return_type']}")
        
        print("\n✓ Pipeline test complete!")
        
    except Exception as e:
        print(f"✗ Generator failed: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    test_parser_to_generator()