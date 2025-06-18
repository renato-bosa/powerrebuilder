#!/usr/bin/env python3
"""Test script to verify pipeline architecture fixes."""

import sys
import json
from pathlib import Path

def test_imports():
    """Test that all coordinator classes can be imported."""
    print("Testing imports...")
    
    try:
        from generate.generate_coordinator import GenerateCoordinator
        print("✓ GenerateCoordinator imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import GenerateCoordinator: {e}")
        return False
    
    try:
        from common.pipeline_coordinator import PipelineCoordinator
        print("✓ PipelineCoordinator imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PipelineCoordinator: {e}")
        return False
    
    return True

def test_coordinator_instantiation():
    """Test that coordinators can be instantiated."""
    print("\nTesting coordinator instantiation...")
    
    try:
        from generate.generate_coordinator import GenerateCoordinator
        gen = GenerateCoordinator('test_input/', 'test_output/')
        print("✓ GenerateCoordinator instantiated successfully")
    except Exception as e:
        print(f"✗ Failed to instantiate GenerateCoordinator: {e}")
        return False
    
    try:
        from common.pipeline_coordinator import PipelineCoordinator
        pipeline = PipelineCoordinator('test_input/', 'test_output/')
        print("✓ PipelineCoordinator instantiated successfully")
    except Exception as e:
        print(f"✗ Failed to instantiate PipelineCoordinator: {e}")
        return False
    
    return True

def test_generate_from_object():
    """Test GenerateCoordinator.generate_from_object method."""
    print("\nTesting generate_from_object method...")
    
    try:
        from generate.generate_coordinator import GenerateCoordinator
        
        # Create test AST file
        test_dir = Path('test_generate')
        test_dir.mkdir(exist_ok=True)
        
        test_ast = test_dir / 'test_window.srw.ast.json'
        test_ast.write_text(json.dumps({
            'type': 'window',
            'name': 'test_window',
            'controls': []
        }))
        
        gen = GenerateCoordinator(str(test_dir), str(test_dir / 'output'))
        result = gen.generate_from_object(
            object_type='window',
            object_name='test_window',
            ast_file=str(test_ast)
        )
        
        if result and 'success' in result:
            print(f"✓ generate_from_object returned: {result}")
        else:
            print(f"✗ generate_from_object returned unexpected result: {result}")
            return False
            
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
    except Exception as e:
        print(f"✗ Failed to test generate_from_object: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Run all tests."""
    print("Pipeline Architecture Fix Verification")
    print("=" * 50)
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
    
    if not test_coordinator_instantiation():
        all_passed = False
    
    if not test_generate_from_object():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! Pipeline architecture fixes are working.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())