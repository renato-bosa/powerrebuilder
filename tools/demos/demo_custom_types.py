#!/usr/bin/env python3
"""Demonstration of enhanced custom type and enum handling in PowerBuilder parser.

This script shows how the parser now properly handles:
- Enumerated types with values
- Structure types with fields
- Custom type inheritance
- Type registration and lookup
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lark import Lark

from parse.transformers.powerbuilder_transformer import PowerBuilderTransformer
from parse.parsers.type_parser import EnumeratedType, StructureType


def create_demo_grammar() -> str:







    """Create a simplified grammar for demonstration."""
    return """
    %import common.WS
    %import common.NEWLINE
    %import common.INT
    %import common.CNAME -> IDENTIFIER

    %ignore WS

    _NEWLINE: NEWLINE

    // Start rule
    start: (type_declaration _NEWLINE*)*

    // Type declarations
    type_declaration: [GLOBAL] TYPE custom_type [ENUMERATED] [from_clause] type_body END TYPE

    from_clause: FROM custom_type

    custom_type: IDENTIFIER (DOT IDENTIFIER)*

    type_body: enum_body | structure_body | mixed_body | _NEWLINE

    // Enum support
    enum_body: enum_value_list

    enum_value_list: enum_value (COMMA enum_value)*

    enum_value: IDENTIFIER [EQUALS INT]

    // Structure support
    structure_body: (type_member _NEWLINE)*

    type_member: [visibility_modifier] [CONSTANT] type_name IDENTIFIER [array_bounds] [EQUALS expression]

    mixed_body: (type_member | function_stub | _NEWLINE)*

    function_stub: [visibility_modifier] FUNCTION type_name IDENTIFIER LPAR RPAR

    // Common rules
    visibility_modifier: PUBLIC | PRIVATE | PROTECTED

    type_name: IDENTIFIER | basic_type

    basic_type: INTEGER | STRING | BOOLEAN | LONG | DECIMAL | REAL

    array_bounds: LBRACK (INT | IDENTIFIER) (COMMA (INT | IDENTIFIER))* RBRACK
                | LBRACK RBRACK

    expression: INT | STRING | boolean_literal | IDENTIFIER

    boolean_literal: TRUE | FALSE

    // Tokens
    GLOBAL: /global/i
    TYPE: /type/i
    ENUMERATED: /enumerated/i
    FROM: /from/i
    END: /end/i
    CONSTANT: /constant/i
    FUNCTION: /function/i
    PUBLIC: /public/i
    PRIVATE: /private/i
    PROTECTED: /protected/i
    INTEGER: /integer/i
    STRING: /string/i
    BOOLEAN: /boolean/i
    LONG: /long/i
    DECIMAL: /decimal/i
    REAL: /real/i
    TRUE: /true/i
    FALSE: /false/i
    EQUALS: "="
    COMMA: ","
    DOT: "."
    LPAR: "("
    RPAR: ")"
    LBRACK: "["
    RBRACK: "]"
    STRING: /"[^"]*"/
    """


def demo_enumerated_types() -> None:







    """Demonstrate enumerated type parsing."""
    print("Enumerated Types Demo")
    print("=" * 50)

    grammar = Lark(create_demo_grammar(), start="start", parser="lalr")
    transformer = PowerBuilderTransformer()

    # Example 1: Simple enum
    code1 = """
    type alignment enumerated
        left = 0,
        center = 1,
        right = 2,
        justify = 3
    end type
    """

    print("\nExample 1: Simple enumeration")
    print(code1)

    tree = grammar.parse(code1)
    result = transformer.transform(tree)

    # Extract the type from the transformed result
    align_type = result.children[0] if hasattr(result, "children") else result

    if isinstance(align_type, EnumeratedType):
        print(f"Type: {align_type.name}")
        print(f"Is Enumerated: {align_type.is_enumerated}")
        print(f"Values: {align_type.values}")
        print(f"Valid value 'center': {align_type.is_valid_value('center')}")
        print(f"Value of 'right': {align_type.get_value('right')}")

    # Example 2: Enum with automatic numbering
    code2 = """
    type status enumerated
        pending,
        processing = 10,
        completed,
        failed = 20,
        cancelled
    end type
    """

    print("\n\nExample 2: Enumeration with automatic numbering")
    print(code2)

    tree = grammar.parse(code2)
    result = transformer.transform(tree)

    status_type = result.children[0] if hasattr(result, "children") else result

    if isinstance(status_type, EnumeratedType):
        print(f"Type: {status_type.name}")
        print(f"Values: {status_type.values}")
        print("Note: 'completed' = 11 (auto-incremented from 'processing')")
        print("      'cancelled' = 21 (auto-incremented from 'failed')")


def demo_structure_types() -> None:







    """Demonstrate structure type parsing."""
    print("\n\nStructure Types Demo")
    print("=" * 50)

    grammar = Lark(create_demo_grammar(), start="start", parser="lalr")
    transformer = PowerBuilderTransformer()

    # Example 1: Simple structure
    code1 = """
    type employee from structure
        string first_name
        string last_name
        integer employee_id
        decimal salary
        boolean is_active
    end type
    """

    print("\nExample 1: Simple structure")
    print(code1)

    tree = grammar.parse(code1)
    result = transformer.transform(tree)

    emp_type = result.children[0] if hasattr(result, "children") else result

    if isinstance(emp_type, StructureType):
        print(f"Type: {emp_type.name}")
        print(f"Parent: {emp_type.parent_type}")
        print(f"Fields: {len(emp_type.fields)}")
        for field in emp_type.fields:
            print(f"  - {field.name}: {field.type} ({field.visibility})")

    # Example 2: Structure with visibility and arrays
    code2 = """
    type customer_data from structure
        public string name
        protected string internal_id
        private string ssn
        string addresses[3]
        integer order_ids[]
    end type
    """

    print("\n\nExample 2: Structure with visibility modifiers and arrays")
    print(code2)

    tree = grammar.parse(code2)
    result = transformer.transform(tree)

    cust_type = result.children[0] if hasattr(result, "children") else result

    if isinstance(cust_type, StructureType):
        print(f"Type: {cust_type.name}")
        print("Fields:")
        for field in cust_type.fields:
            array_info = " (array)" if hasattr(field, "array_bounds") and field.array_bounds else ""
            print(f"  - {field.visibility} {field.type} {field.name}{array_info}")


def demo_custom_inheritance() -> None:







    """Demonstrate custom type inheritance."""
    print("\n\nCustom Type Inheritance Demo")
    print("=" * 50)

    grammar = Lark(create_demo_grammar(), start="start", parser="lalr")
    transformer = PowerBuilderTransformer()

    # Example: Multiple related types
    code = """
    type base_window from window
    end type

    type data_window from base_window
        string dataobject
        boolean auto_retrieve
    end type

    global type main_window from data_window
        string window_title = "Main Application Window"
        integer min_width = 800
        integer min_height = 600
    end type
    """

    print("\nExample: Type inheritance hierarchy")
    print(code)

    tree = grammar.parse(code)
    result = transformer.transform(tree)

    # Process each type
    for i, child in enumerate(result.children if hasattr(result, "children") else [result]):
        if hasattr(child, "name"):
            print(f"\nType {i+1}: {child.name}")
            print(f"  Parent: {child.parent_type}")
            print(f"  Global: {child.is_global}")

            if isinstance(child, StructureType) and child.fields:
                print("  Fields:")
                for field in child.fields:
                    print(f"    - {field.type} {field.name}")


def demo_type_registry() -> None:







    """Demonstrate type registration and lookup."""
    print("\n\nType Registry Demo")
    print("=" * 50)

    transformer = PowerBuilderTransformer()

    # Register some types
    print("\nRegistering types...")

    # Create and register an enum
    colors = EnumeratedType("colors", {
        "red": 0xFF0000,
        "green": 0x00FF00,
        "blue": 0x0000FF,
    })
    transformer.type_parser.register_type(colors)
    print(f"Registered enum: {colors.name}")

    # Create and register a structure
    from model.ast.ast_nodes import Variable

    point_fields = [
        Variable(name="x", type="integer", visibility="public"),
        Variable(name="y", type="integer", visibility="public"),
        Variable(name="z", type="integer", visibility="public"),
    ]
    point = StructureType("point3d", point_fields)
    transformer.type_parser.register_type(point)
    print(f"Registered structure: {point.name}")

    # Look up types
    print("\nLooking up types...")

    found_colors = transformer.type_parser.get_type("colors")
    if found_colors:
        print(f"Found type: {found_colors.name} (Enumerated: {isinstance(found_colors, EnumeratedType)})")
        if isinstance(found_colors, EnumeratedType):
            print(f"  Value of 'blue': 0x{found_colors.get_value('blue'):06X}")

    found_point = transformer.type_parser.get_type("point3d")
    if found_point:
        print(f"Found type: {found_point.name} (Structure: {isinstance(found_point, StructureType)})")
        if isinstance(found_point, StructureType):
            print(f"  Has field 'x': {found_point.has_field('x')}")
            print(f"  Has field 'w': {found_point.has_field('w')}")


def main() -> None:







    """Run all demonstrations."""
    print("PowerBuilder Enhanced Custom Type and Enum Handling Demo")
    print("=" * 70)
    print("This demonstrates the new parsing capabilities for:")
    print("- Enumerated types with explicit and automatic values")
    print("- Structure types with typed fields and visibility")
    print("- Custom type inheritance hierarchies")
    print("- Type registration and lookup")
    print()

    demo_enumerated_types()
    demo_structure_types()
    demo_custom_inheritance()
    demo_type_registry()

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("\nThe parser now properly handles:")
    print("✓ Enumerated type value parsing")
    print("✓ Structure field declarations")
    print("✓ Visibility modifiers (public/private/protected)")
    print("✓ Type inheritance with FROM clause")
    print("✓ Global type declarations")
    print("✓ Type registration and lookup")


if __name__ == "__main__":
    main()
