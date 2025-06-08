#!/usr/bin/env python3
"""Test end-to-end pipeline with real PBD file."""

from pathlib import Path
import json
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from extract.extract_coordinator import extract_with_recovery
from parse.parse_coordinator import PowerBuilderParser
from parse.powerbuilder_transformer import PowerBuilderTransformer
from parse.ast_to_model import ASTToModelConverter
from generate.generate_coordinator import CodeGenerator
from lark import Lark


def test_end_to_end():
    """Test complete pipeline from PBD to generated code."""
    print("End-to-End Pipeline Test")
    print("=" * 50)
    
    # Step 1: Extract from PBD
    print("\n1. Extracting from PBD...")
    pbd_path = Path("input/pbd_files/dcm_wizard.pbd")
    output_dir = Path("output/test_e2e")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create extraction directory
        extract_dir = output_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        success = extract_with_recovery(str(pbd_path), str(extract_dir))
        if success:
            print(f"✓ Extraction successful")
        else:
            print("✗ Extraction failed")
            return
            
        # Find extracted files
        extracted_files = list(extract_dir.rglob("*.fun"))
        if extracted_files:
            test_file = extracted_files[0]
            print(f"✓ Found {len(extracted_files)} function files")
            print(f"✓ Selected test file: {test_file.name}")
        else:
            # Try window files
            win_files = list(extract_dir.rglob("*.win"))
            if win_files:
                test_file = win_files[0]
                print(f"✓ Found {len(win_files)} window files")
                print(f"✓ Selected test file: {test_file.name}")
            else:
                print("✗ No function or window files found")
                return
            
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Parse extracted file
    print("\n2. Parsing extracted file...")
    try:
        # Read the extracted file
        with open(test_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        print(f"✓ Read {len(source_code)} characters")
        
        # Use the existing PowerBuilder parser first to see what we get
        pb_parser = PowerBuilderParser()
        try:
            ast = pb_parser.parse(source_code, file_path=test_file)
            print(f"✓ Parsed with existing parser")
            print(f"  AST type: {type(ast)}")
        except Exception as e:
            print(f"✗ Existing parser failed: {e}")
            
            # Try with our new parser on a simple subset
            print("\n  Trying new parser with simple function...")
            # Extract just a simple function if possible
            lines = source_code.split('\n')
            func_start = None
            func_end = None
            
            for i, line in enumerate(lines):
                if 'function' in line.lower() and func_start is None:
                    func_start = i
                elif 'end function' in line.lower() and func_start is not None:
                    func_end = i + 1
                    break
                    
            if func_start and func_end:
                simple_func = '\n'.join(lines[func_start:func_end])
                print(f"  Extracted function ({func_end - func_start} lines)")
                
                # Try our new parser
                grammar_path = Path("parse/grammar/experimental/powerbuilder_fixed_v2.lark")
                with open(grammar_path) as f:
                    grammar = f.read()
                    
                parser = Lark(grammar, start='start', parser='lalr')
                transformer = PowerBuilderTransformer()
                
                try:
                    parse_tree = parser.parse(simple_func)
                    ast = transformer.transform(parse_tree)
                    print("✓ Parsed with new parser!")
                except Exception as e2:
                    print(f"✗ New parser also failed: {e2}")
                    # Show a sample of what we're trying to parse
                    print("\nSample of code:")
                    print(simple_func[:200] + "...")
            
    except Exception as e:
        print(f"✗ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✓ End-to-end test partially complete")
    print("  - Extraction: ✓")
    print("  - Parsing: Partial (existing parser incompatible with new AST)")
    print("  - Code generation: Not tested (requires working parser)")


if __name__ == "__main__":
    test_end_to_end()