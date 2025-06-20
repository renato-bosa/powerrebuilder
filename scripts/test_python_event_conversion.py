#!/usr/bin/env python3
"""Test Python event and method body conversion."""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate.python_ui_generator import PythonUIGenerator, PythonTypeConverter, PythonExpressionConverter

def test_expression_converter():
    """Test the enhanced expression converter."""
    print("Testing Expression Converter")
    print("=" * 60)
    
    type_converter = PythonTypeConverter()
    expr_converter = PythonExpressionConverter(type_converter)
    
    test_cases = [
        # Basic expressions
        ("x = 10", "x == 10"),
        ("x <> 10", "x != 10"),
        ("x and y", "x and y"),
        ("x or y", "x or y"),
        ("not x", "not x"),
        ("x mod 5", "x % 5"),
        ("2 ^ 3", "2 ** 3"),
        
        # Null handling
        ("IsNull(myvar)", "(myvar is None)"),
        ("IsValid(obj)", "(obj is not None)"),
        ("SetNull(var)", "var = None"),
        
        # String functions
        ("Trim(text)", "text.strip()"),
        ("Upper(name)", "name.upper()"),
        ("Len(str)", "len(str)"),
        ("Mid(text, 5, 3)", "text[5-1:(5-1)+3]"),
        
        # Control structures
        ("IF x > 0 THEN", "if x > 0:"),
        ("ELSEIF x < 0 THEN", "elif x < 0:"),
        ("FOR i = 1 TO 10", "for i in range(1, 10 + 1):"),
        
        # Property access
        ("this.value", "self.value"),
        ("parent.width", "self.parent.width"),
    ]
    
    for pb_expr, expected in test_cases:
        result = expr_converter.convert_expression(pb_expr)
        status = "✓" if result == expected else "✗"
        print(f"{status} {pb_expr:<30} -> {result}")
        if result != expected:
            print(f"  Expected: {expected}")
    
    print()

def test_event_body_conversion():
    """Test event body conversion."""
    print("Testing Event Body Conversion")
    print("=" * 60)
    
    # Create a test generator
    generator = PythonUIGenerator(
        template_dir=str(Path(__file__).parent.parent / "generate" / "backend" / "templates"),
        output_dir="test_output",
        validate_templates=False
    )
    
    # Test event bodies
    test_bodies = [
        {
            "name": "Simple assignment",
            "body": [
                "sle_emp_id.text = f_get_next_emp_id()",
                "sle_name.SetFocus()"
            ],
            "expected": [
                "self.set_text('sle_emp_id', f_get_next_emp_id())",
                "self._controls['sle_name'].focus_set()"
            ]
        },
        {
            "name": "If statement with MessageBox",
            "body": [
                "IF Len(Trim(sle_name.text)) = 0 THEN",
                "   MessageBox('Error', 'Please enter employee name')",
                "   RETURN",
                "END IF"
            ],
            "expected": [
                "if len(sle_name.get().strip()) == 0:",
                "    messagebox.showinfo('Error', 'Please enter employee name')",
                "    return"
            ]
        },
        {
            "name": "Variable assignment and method call",
            "body": [
                "is_emp_id = sle_emp_id.text",
                "ib_modified = TRUE",
                "IF f_save_employee(sle_emp_id.text, sle_name.text, cbx_active.checked) THEN",
                "   MessageBox('Success', 'Employee saved')",
                "   Close(This)",
                "END IF"
            ],
            "expected": [
                "self.isEmpId = sle_emp_id.get()",
                "self.ibModified = TRUE",
                "if f_save_employee(sle_emp_id.get(), sle_name.get(), cbx_active.var.get()):",
                "    messagebox.showinfo('Success', 'Employee saved')",
                "    self.destroy()"
            ]
        }
    ]
    
    for test_case in test_bodies:
        print(f"\n{test_case['name']}:")
        print("-" * 40)
        result = generator._convert_event_body(test_case["body"])
        print("Result:")
        print(result)
        print()

def test_full_window_generation():
    """Test full window generation with event handlers."""
    print("Testing Full Window Generation")
    print("=" * 60)
    
    # Create a test window model
    window_model = {
        "name": "w_test",
        "title": "Test Window",
        "controls": [
            {
                "type": "singlelineedit",
                "name": "sle_input",
                "flutter_widget": {
                    "flutter_properties": {
                        "text": "",
                        "enabled": True
                    }
                },
                "position": {"x": 10, "y": 10},
                "size": {"width": 200, "height": 25}
            },
            {
                "type": "commandbutton",
                "name": "cb_process",
                "flutter_widget": {
                    "flutter_properties": {
                        "text": "Process",
                        "enabled": True
                    }
                },
                "position": {"x": 10, "y": 50},
                "size": {"width": 80, "height": 30}
            }
        ],
        "events": [
            {
                "name": "open",
                "body": [
                    "// Initialize",
                    "sle_input.text = 'Enter value'",
                    "cb_process.enabled = FALSE"
                ]
            },
            {
                "name": "sle_input.modified",
                "body": [
                    "IF Len(Trim(sle_input.text)) > 0 THEN",
                    "   cb_process.enabled = TRUE",
                    "ELSE",
                    "   cb_process.enabled = FALSE",
                    "END IF"
                ]
            },
            {
                "name": "cb_process.clicked",
                "body": [
                    "STRING ls_value",
                    "ls_value = sle_input.text",
                    "",
                    "IF IsNull(ls_value) OR Trim(ls_value) = '' THEN",
                    "   MessageBox('Error', 'Please enter a value')",
                    "   RETURN",
                    "END IF",
                    "",
                    "// Process the value",
                    "MessageBox('Success', 'Value: ' + ls_value)",
                    "sle_input.text = ''",
                    "cb_process.enabled = FALSE"
                ]
            }
        ],
        "variables": [
            {"name": "is_status", "type": "string"},
            {"name": "ib_processing", "type": "boolean", "initial_value": "false"}
        ],
        "methods": [
            {
                "name": "of_validate",
                "parameters": [{"name": "as_value", "type": "string"}],
                "body": [
                    "IF IsNull(as_value) OR Trim(as_value) = '' THEN",
                    "   RETURN FALSE",
                    "END IF",
                    "",
                    "IF Len(as_value) < 3 THEN",
                    "   MessageBox('Validation', 'Value must be at least 3 characters')",
                    "   RETURN FALSE",
                    "END IF",
                    "",
                    "RETURN TRUE"
                ]
            }
        ]
    }
    
    # Initialize generator
    generator = PythonUIGenerator(
        template_dir=str(Path(__file__).parent.parent / "generate" / "backend" / "templates"),
        output_dir="test_output_detailed",
        validate_templates=False
    )
    
    # Generate the window
    generator.generate_window(window_model)
    
    # Read and display key parts of the generated file
    output_file = Path("test_output_detailed/windows/w_test.py")
    if output_file.exists():
        print("\n✓ Generated file exists")
        
        with open(output_file) as f:
            content = f.read()
        
        # Extract and display event handlers
        import re
        
        # Find _on_open method
        open_match = re.search(r'def _on_open\(self\):(.*?)(?=\n    def|\n\n|\Z)', content, re.DOTALL)
        if open_match:
            print("\n_on_open method:")
            print("-" * 40)
            print(open_match.group(0))
        
        # Find modified event handler
        modified_match = re.search(r'def .*modified.*\(self.*?\):(.*?)(?=\n    def|\n\n|\Z)', content, re.DOTALL)
        if modified_match:
            print("\n_modified handler:")
            print("-" * 40)
            print(modified_match.group(0))
        
        # Find clicked event handler
        clicked_match = re.search(r'def _on_cb_process_clicked\(self\):(.*?)(?=\n    def|\n\n|\Z)', content, re.DOTALL)
        if clicked_match:
            print("\n_on_cb_process_clicked method:")
            print("-" * 40)
            print(clicked_match.group(0))
        
        # Find of_validate method
        validate_match = re.search(r'def of_validate\(self.*?\):(.*?)(?=\n    def|\n\n|\Z)', content, re.DOTALL)
        if validate_match:
            print("\nof_validate method:")
            print("-" * 40)
            print(validate_match.group(0))
    else:
        print("\n✗ Generated file not found")
    
    # Cleanup
    import shutil
    if Path("test_output_detailed").exists():
        shutil.rmtree("test_output_detailed")

def main():
    """Run all tests."""
    test_expression_converter()
    test_event_body_conversion()
    test_full_window_generation()

if __name__ == "__main__":
    main()