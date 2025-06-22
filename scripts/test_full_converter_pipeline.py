#!/usr/bin/env python3
"""Test the full converter pipeline with a more complex example."""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate.generate_coordinator import GenerateCoordinator

def test_full_converter_pipeline():


    

    """Test the converter pipeline with a complex window."""
    print("Testing Full Converter Pipeline")
    print("=" * 60)
    
    # Create a more complex AST for testing
    test_ast = {
        "node_type": "Window",
        "name": "w_customer_entry",
        "title": "Customer Entry Form",
        "controls": [
            # Labels
            {
                "type": "statictext",
                "name": "st_customer_id",
                "properties": {
                    "text": "Customer ID:",
                    "x": 10,
                    "y": 10,
                    "width": 100,
                    "height": 20,
                    "alignment": "right"
                }
            },
            {
                "type": "statictext",
                "name": "st_name",
                "properties": {
                    "text": "Name:",
                    "x": 10,
                    "y": 40,
                    "width": 100,
                    "height": 20,
                    "alignment": "right"
                }
            },
            {
                "type": "statictext",
                "name": "st_email",
                "properties": {
                    "text": "Email:",
                    "x": 10,
                    "y": 70,
                    "width": 100,
                    "height": 20,
                    "alignment": "right"
                }
            },
            # Input fields
            {
                "type": "singlelineedit",
                "name": "sle_customer_id",
                "properties": {
                    "text": "",
                    "x": 120,
                    "y": 10,
                    "width": 200,
                    "height": 25,
                    "enabled": False
                }
            },
            {
                "type": "singlelineedit",
                "name": "sle_name",
                "properties": {
                    "text": "",
                    "x": 120,
                    "y": 40,
                    "width": 300,
                    "height": 25,
                    "maxlength": 100
                }
            },
            {
                "type": "singlelineedit",
                "name": "sle_email",
                "properties": {
                    "text": "",
                    "x": 120,
                    "y": 70,
                    "width": 300,
                    "height": 25
                }
            },
            # Checkbox
            {
                "type": "checkbox",
                "name": "cbx_active",
                "properties": {
                    "text": "Active",
                    "x": 120,
                    "y": 100,
                    "width": 100,
                    "height": 20,
                    "checked": True
                }
            },
            # Dropdown
            {
                "type": "dropdownlistbox",
                "name": "ddlb_type",
                "properties": {
                    "x": 120,
                    "y": 130,
                    "width": 200,
                    "height": 25,
                    "items": ["Regular", "Premium", "VIP"]
                }
            },
            # Buttons
            {
                "type": "commandbutton",
                "name": "cb_save",
                "properties": {
                    "text": "Save",
                    "x": 120,
                    "y": 170,
                    "width": 80,
                    "height": 30,
                    "default": True
                }
            },
            {
                "type": "commandbutton",
                "name": "cb_cancel",
                "properties": {
                    "text": "Cancel",
                    "x": 210,
                    "y": 170,
                    "width": 80,
                    "height": 30
                }
            },
            {
                "type": "commandbutton",
                "name": "cb_delete",
                "properties": {
                    "text": "Delete",
                    "x": 300,
                    "y": 170,
                    "width": 80,
                    "height": 30,
                    "enabled": False
                }
            }
        ],
        "events": [
            {
                "name": "open",
                "body": [
                    "// Initialize window",
                    "This.Title = 'Customer Entry - New'",
                    "sle_customer_id.text = String(f_get_next_customer_id())"
                ]
            },
            {
                "name": "cb_save.clicked",
                "body": [
                    "// Save customer",
                    "IF Len(Trim(sle_name.text)) = 0 THEN",
                    "   MessageBox('Error', 'Please enter customer name')",
                    "   RETURN",
                    "END IF",
                    "",
                    "// Save to database",
                    "IF f_save_customer(sle_customer_id.text, sle_name.text, sle_email.text) THEN",
                    "   MessageBox('Success', 'Customer saved successfully')",
                    "   Close(This)",
                    "ELSE",
                    "   MessageBox('Error', 'Failed to save customer')",
                    "END IF"
                ]
            },
            {
                "name": "cb_cancel.clicked",
                "body": ["Close(This)"]
            },
            {
                "name": "cb_delete.clicked",
                "body": [
                    "IF MessageBox('Confirm', 'Delete this customer?', Question!, YesNo!) = 1 THEN",
                    "   IF f_delete_customer(sle_customer_id.text) THEN",
                    "      Close(This)",
                    "   END IF",
                    "END IF"
                ]
            }
        ],
        "variables": [
            {
                "name": "is_customer_id",
                "type": "string",
                "visibility": "public",
                "description": "Customer ID to edit"
            },
            {
                "name": "ib_edit_mode",
                "type": "boolean",
                "visibility": "private",
                "initial_value": "false"
            },
            {
                "name": "il_original_checksum",
                "type": "long",
                "visibility": "private"
            }
        ],
        "methods": [
            {
                "name": "of_load_customer",
                "visibility": "public",
                "return_type": "boolean",
                "parameters": [
                    {"name": "as_customer_id", "type": "string"}
                ],
                "body": [
                    "// Load customer data",
                    "RETURN true"
                ]
            },
            {
                "name": "of_validate_email",
                "visibility": "private",
                "return_type": "boolean",
                "parameters": [
                    {"name": "as_email", "type": "string"}
                ],
                "body": [
                    "// Validate email format",
                    "RETURN Match(as_email, '^[^@]+@[^@]+\\.[^@]+$')"
                ]
            }
        ]
    }
    
    # Save test AST to file
    test_file = Path("test_customer_window.ast.json")
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
            object_name="w_customer_entry",
            ast_file=str(test_file)
        )
        
        print(f"\nGeneration result: {result}")
        
        if result.get("success"):
            print("\n✓ Generation succeeded!")
            print(f"  Generated files: {result.get('files', [])}")
            
            # Check if the generated file exists
            output_file = Path("test_output/flutter/screens/w_customer_entry_screen.dart")
            if output_file.exists():
                print(f"\n✓ Output file exists: {output_file}")
                
                # Read and analyze the generated content
                with open(output_file) as f:
                    content = f.read()
                
                # Check for key elements
                checks = {
                    "StatefulWidget class": "class w_customer_entryScreen extends StatefulWidget" in content,
                    "Controllers generated": "Controller" in content,
                    "Build method": "Widget build(BuildContext context)" in content,
                    "Controls converted": "TextField" in content or "Text(" in content,
                    "Title set": "Customer Entry Form" in content
                }
                
                print("\nContent validation:")
                for check_name, passed in checks.items():
                    status = "✓" if passed else "✗"
                    print(f"  {status} {check_name}")
                
                # Print a sample of the generated code
                print("\nGenerated code sample:")
                print("-" * 40)
                lines = content.split('\n')
                # Find the build method
                build_start = None
                for i, line in enumerate(lines):
                    if "Widget build" in line:
                        build_start = i
                        break
                
                if build_start:
                    # Print 20 lines from the build method
                    sample = '\n'.join(lines[build_start:build_start+20])
                    print(sample)
                else:
                    # Just print first 20 lines
                    print('\n'.join(lines[:20]))
                
            else:
                print(f"\n✗ Output file not found: {output_file}")
        else:
            print(f"\n✗ Generation failed: {result.get('error')}")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
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
    test_full_converter_pipeline()