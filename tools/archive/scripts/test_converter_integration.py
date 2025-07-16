#!/usr/bin/env python3
"""Test the converter integration in the generation pipeline."""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generate.generate_coordinator import GenerateCoordinator

def test_converter_integration():




    """Test if converters are properly integrated."""
    print("Testing Converter Integration")
    print("=" * 60)

    # Create a sample AST for testing
    test_ast = {
        "node_type": "Window",
        "name": "w_test_window",
        "title": "Test Window",
        "controls": [
            {
                "type": "statictext",
                "name": "st_label",
                "properties": {
                    "text": "Hello PowerBuilder",
                    "x": 10,
                    "y": 10,
                    "width": 200,
                    "height": 20
                }
            },
            {
                "type": "singlelineedit",
                "name": "sle_input",
                "properties": {
                    "text": "",
                    "x": 10,
                    "y": 40,
                    "width": 200,
                    "height": 25
                }
            },
            {
                "type": "commandbutton",
                "name": "cb_ok",
                "properties": {
                    "text": "OK",
                    "x": 10,
                    "y": 80,
                    "width": 80,
                    "height": 30
                }
            }
        ],
        "events": [
            {
                "name": "open",
                "body": ["// Window open event"]
            },
            {
                "name": "cb_ok.clicked",
                "body": ["MessageBox('Info', sle_input.text)"]
            }
        ],
        "variables": [
            {
                "name": "is_message",
                "type": "string",
                "visibility": "public"
            },
            {
                "name": "il_count",
                "type": "long",
                "visibility": "private",
                "initial_value": "0"
            }
        ]
    }

    # Save test AST to file
    test_file = Path("test_window.ast.json")
    with open(test_file, "w") as f:
        json.dump(test_ast, f, indent=2)

    try:
        # Initialize coordinator
        coord = GenerateCoordinator(
            input_dir=".",
            output_dir="test_output",
            framework="flutter"
        )

        print("\nRunning generation with converters...")

        # Test the generation
        result = coord.generate_from_object(
            object_type="window",
            object_name="w_test_window",
            ast_file=str(test_file)
        )

        print(f"\nGeneration result: {result}")

        if result.get("success"):
            print("\n✓ Generation succeeded!")
            print(f"  Generated files: {result.get('files', [])}")

            # Check if the generated file exists
            output_file = Path("test_output/flutter/screens/w_test_window_screen.dart")
            if output_file.exists():
                print(f"\n✓ Output file exists: {output_file}")
                print("\nGenerated content preview:")
                print("-" * 40)
                with open(output_file) as f:
                    content = f.read()
                    print(content[:500] + "..." if len(content) > 500 else content)
            else:
                print(f"\n✗ Output file not found: {output_file}")
        else:
            print(f"\n✗ Generation failed: {result.get('error')}")

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()

        # Print more detailed error information
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"\nCaused by: {e.__cause__}")
            print("Cause traceback:")
            traceback.print_exception(type(e.__cause__), e.__cause__, e.__cause__.__traceback__)
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()

        # Cleanup output directory
        output_dir = Path("test_output")
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    test_converter_integration()