#!/usr/bin/env python3
"""Test Python UI generation from PowerBuilder windows."""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate.generate_coordinator import GenerateCoordinator

def test_python_ui_generation():
    """Test generating Python Tkinter code from PowerBuilder window."""
    print("Testing Python UI Generation")
    print("=" * 60)
    
    # Create a test window AST
    test_ast = {
        "node_type": "Window",
        "name": "w_employee_form",
        "title": "Employee Information",
        "controls": [
            # Labels
            {
                "type": "statictext",
                "name": "st_emp_id",
                "properties": {
                    "text": "Employee ID:",
                    "x": 20,
                    "y": 20,
                    "width": 100,
                    "height": 20
                },
                "position": {"x": 20, "y": 20},
                "size": {"width": 100, "height": 20}
            },
            {
                "type": "statictext",
                "name": "st_name",
                "properties": {
                    "text": "Name:",
                    "x": 20,
                    "y": 50,
                    "width": 100,
                    "height": 20
                },
                "position": {"x": 20, "y": 50},
                "size": {"width": 100, "height": 20}
            },
            # Input fields
            {
                "type": "singlelineedit",
                "name": "sle_emp_id",
                "properties": {
                    "text": "",
                    "x": 130,
                    "y": 20,
                    "width": 150,
                    "height": 25,
                    "enabled": False
                },
                "position": {"x": 130, "y": 20},
                "size": {"width": 150, "height": 25}
            },
            {
                "type": "singlelineedit",
                "name": "sle_name",
                "properties": {
                    "text": "",
                    "x": 130,
                    "y": 50,
                    "width": 250,
                    "height": 25
                },
                "position": {"x": 130, "y": 50},
                "size": {"width": 250, "height": 25}
            },
            # Checkbox
            {
                "type": "checkbox",
                "name": "cbx_active",
                "properties": {
                    "text": "Active Employee",
                    "x": 130,
                    "y": 85,
                    "width": 150,
                    "height": 20,
                    "checked": True
                },
                "position": {"x": 130, "y": 85},
                "size": {"width": 150, "height": 20}
            },
            # Dropdown
            {
                "type": "dropdownlistbox",
                "name": "ddlb_department",
                "properties": {
                    "x": 130,
                    "y": 115,
                    "width": 200,
                    "height": 25,
                    "items": ["Sales", "Engineering", "HR", "Finance"]
                },
                "position": {"x": 130, "y": 115},
                "size": {"width": 200, "height": 25}
            },
            # Buttons
            {
                "type": "commandbutton",
                "name": "cb_save",
                "properties": {
                    "text": "Save",
                    "x": 130,
                    "y": 160,
                    "width": 80,
                    "height": 30
                },
                "position": {"x": 130, "y": 160},
                "size": {"width": 80, "height": 30}
            },
            {
                "type": "commandbutton",
                "name": "cb_cancel",
                "properties": {
                    "text": "Cancel",
                    "x": 220,
                    "y": 160,
                    "width": 80,
                    "height": 30
                },
                "position": {"x": 220, "y": 160},
                "size": {"width": 80, "height": 30}
            }
        ],
        "events": [
            {
                "name": "open",
                "body": [
                    "// Initialize window",
                    "sle_emp_id.text = f_get_next_emp_id()",
                    "sle_name.SetFocus()"
                ]
            },
            {
                "name": "cb_save.clicked",
                "body": [
                    "IF Len(Trim(sle_name.text)) = 0 THEN",
                    "   MessageBox('Error', 'Please enter employee name')",
                    "   RETURN",
                    "END IF",
                    "",
                    "// Save employee data",
                    "IF f_save_employee(sle_emp_id.text, sle_name.text, cbx_active.checked) THEN",
                    "   MessageBox('Success', 'Employee saved')",
                    "   Close(This)",
                    "END IF"
                ]
            },
            {
                "name": "cb_cancel.clicked",
                "body": ["Close(This)"]
            }
        ],
        "variables": [
            {
                "name": "is_emp_id",
                "type": "string",
                "visibility": "public"
            },
            {
                "name": "ib_modified",
                "type": "boolean",
                "visibility": "private",
                "initial_value": "false"
            }
        ],
        "methods": [
            {
                "name": "of_validate",
                "visibility": "public",
                "return_type": "boolean",
                "parameters": [],
                "body": [
                    "IF Len(Trim(sle_name.text)) = 0 THEN",
                    "   MessageBox('Validation', 'Name is required')",
                    "   RETURN FALSE",
                    "END IF",
                    "RETURN TRUE"
                ]
            }
        ]
    }
    
    # Save test AST to file
    test_file = Path("test_employee_window.ast.json")
    with open(test_file, "w") as f:
        json.dump(test_ast, f, indent=2)
    
    try:
        # Test both Flutter and Python generation
        for framework in ["flutter", "python"]:
            print(f"\n{framework.upper()} Generation:")
            print("-" * 40)
            
            # Initialize coordinator
            coord = GenerateCoordinator(
                input_dir=".",
                output_dir=f"test_output_{framework}",
                framework=framework
            )
            
            # Generate code
            result = coord.generate_from_object(
                object_type="window",
                object_name="w_employee_form",
                ast_file=str(test_file)
            )
            
            print(f"Generation result: {result}")
            
            if result.get("success"):
                print(f"✓ {framework} generation succeeded!")
                
                # Check output file
                if framework == "flutter":
                    output_file = Path(f"test_output_{framework}/flutter/screens/w_employee_form_screen.dart")
                else:
                    output_file = Path(f"test_output_{framework}/python/windows/w_employee_form.py")
                
                if output_file.exists():
                    print(f"✓ Output file exists: {output_file}")
                    
                    # Show sample of generated code
                    with open(output_file) as f:
                        content = f.read()
                    
                    # Check for key elements
                    if framework == "python":
                        checks = {
                            "Tkinter import": "import tkinter as tk" in content,
                            "Window class": "class EmployeeForm(tk.Tk):" in content or "class WEmployeeForm(tk.Tk):" in content,
                            "Controls created": "_create_widgets" in content,
                            "Event handlers": "_on_cb_save_clicked" in content,
                            "Title set": "Employee Information" in content
                        }
                        
                        print("\nPython code validation:")
                        for check_name, passed in checks.items():
                            status = "✓" if passed else "✗"
                            print(f"  {status} {check_name}")
                    
                    print(f"\n{framework} code preview:")
                    print("-" * 40)
                    lines = content.split('\n')
                    print('\n'.join(lines[:30]) + "\n...")
                else:
                    print(f"✗ Output file not found: {output_file}")
            else:
                print(f"✗ {framework} generation failed: {result.get('error')}")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        
        # Cleanup output directories
        for framework in ["flutter", "python"]:
            output_dir = Path(f"test_output_{framework}")
            if output_dir.exists():
                import shutil
                shutil.rmtree(output_dir)


if __name__ == "__main__":
    test_python_ui_generation()