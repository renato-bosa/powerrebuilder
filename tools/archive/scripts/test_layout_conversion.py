#!/usr/bin/env python3
"""Test the layout conversion with absolute positioning."""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate.generate_coordinator import GenerateCoordinator
from generate.layout_converter import LayoutConverter, LayoutStrategy

def test_layout_strategies():




    """Test different layout conversion strategies."""
    print("Testing Layout Conversion Strategies")
    print("=" * 60)

    # Create a window with carefully positioned controls
    test_ast = {
        "node_type": "Window",
        "name": "w_layout_test",
        "title": "Layout Test Window",
        "controls": [
            # Row 1: Labels and inputs aligned horizontally
            {
                "type": "statictext",
                "name": "st_name",
                "properties": {"text": "Name:"},
                "position": {"x": 10, "y": 10},
                "size": {"width": 80, "height": 20}
            },
            {
                "type": "singlelineedit",
                "name": "sle_name",
                "properties": {"text": ""},
                "position": {"x": 100, "y": 10},
                "size": {"width": 200, "height": 25}
            },
            # Row 2: Another label/input pair
            {
                "type": "statictext",
                "name": "st_email",
                "properties": {"text": "Email:"},
                "position": {"x": 10, "y": 40},
                "size": {"width": 80, "height": 20}
            },
            {
                "type": "singlelineedit",
                "name": "sle_email",
                "properties": {"text": ""},
                "position": {"x": 100, "y": 40},
                "size": {"width": 200, "height": 25}
            },
            # Overlapping controls (to test Stack)
            {
                "type": "rectangle",
                "name": "rect_background",
                "properties": {"fillcolor": "lightblue"},
                "position": {"x": 320, "y": 10},
                "size": {"width": 150, "height": 100}
            },
            {
                "type": "statictext",
                "name": "st_overlay",
                "properties": {"text": "Overlaid Text"},
                "position": {"x": 340, "y": 50},
                "size": {"width": 100, "height": 20}
            },
            # Buttons at bottom
            {
                "type": "commandbutton",
                "name": "cb_ok",
                "properties": {"text": "OK"},
                "position": {"x": 100, "y": 120},
                "size": {"width": 80, "height": 30}
            },
            {
                "type": "commandbutton",
                "name": "cb_cancel",
                "properties": {"text": "Cancel"},
                "position": {"x": 190, "y": 120},
                "size": {"width": 80, "height": 30}
            }
        ]
    }

    # Save test AST to file
    test_file = Path("test_layout_window.ast.json")
    with open(test_file, "w") as f:
        json.dump(test_ast, f, indent=2)

    try:
        # Test 1: Absolute positioning (default)
        print("\n1. Testing ABSOLUTE positioning strategy...")
        coord = GenerateCoordinator(
            input_dir=".",
            output_dir="test_output_absolute",
            framework="flutter"
        )

        result = coord.generate_from_object(
            object_type="window",
            object_name="w_layout_test",
            ast_file=str(test_file)
        )

        if result.get("success"):
            print("✓ Absolute positioning generation succeeded")
            output_file = Path("test_output_absolute/flutter/screens/w_layout_test_screen.dart")
            if output_file.exists():
                with open(output_file) as f:
                    content = f.read()
                if "Stack(" in content and "Positioned(" in content:
                    print("✓ Stack and Positioned widgets found")
                else:
                    print("✗ Stack/Positioned widgets not found")

        # Test 2: Intelligent layout
        print("\n2. Testing INTELLIGENT layout strategy...")

        # Create a new coordinator with intelligent layout
        coord2 = GenerateCoordinator(
            input_dir=".",
            output_dir="test_output_intelligent",
            framework="flutter"
        )
        coord2.layout_converter = LayoutConverter(LayoutStrategy.INTELLIGENT)

        result2 = coord2.generate_from_object(
            object_type="window",
            object_name="w_layout_test",
            ast_file=str(test_file)
        )

        if result2.get("success"):
            print("✓ Intelligent layout generation succeeded")
            output_file2 = Path("test_output_intelligent/flutter/screens/w_layout_test_screen.dart")
            if output_file2.exists():
                with open(output_file2) as f:
                    content = f.read()
                if "Row(" in content:
                    print("✓ Row widgets found (intelligent grouping)")
                else:
                    print("✗ Row widgets not found")

        # Test 3: Responsive layout
        print("\n3. Testing RESPONSIVE layout strategy...")

        coord3 = GenerateCoordinator(
            input_dir=".",
            output_dir="test_output_responsive",
            framework="flutter"
        )
        coord3.layout_converter = LayoutConverter(LayoutStrategy.RESPONSIVE)

        result3 = coord3.generate_from_object(
            object_type="window",
            object_name="w_layout_test",
            ast_file=str(test_file)
        )

        if result3.get("success"):
            print("✓ Responsive layout generation succeeded")
            output_file3 = Path("test_output_responsive/flutter/screens/w_layout_test_screen.dart")
            if output_file3.exists():
                with open(output_file3) as f:
                    content = f.read()
                if "LayoutBuilder(" in content and "constraints" in content:
                    print("✓ LayoutBuilder found (responsive design)")
                else:
                    print("✗ LayoutBuilder not found")

        # Show sample of absolute positioning output
        print("\n4. Sample of generated code (Absolute positioning):")
        print("-" * 60)
        if output_file.exists():
            with open(output_file) as f:
                content = f.read()
                # Find the Stack widget
                stack_start = content.find("Stack(")
                if stack_start != -1:
                    # Print 30 lines from Stack
                    lines = content[stack_start:].split('\n')[:30]
                    print('\n'.join(lines))

    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()

        # Cleanup output directories
        for output_dir in ["test_output_absolute", "test_output_intelligent", "test_output_responsive"]:
            output_path = Path(output_dir)
            if output_path.exists():
                import shutil
                shutil.rmtree(output_path)

if __name__ == "__main__":
    test_layout_strategies()