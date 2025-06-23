#!/usr/bin/env python3
"""Demonstration of parser error recovery capabilities."""

import sys

from common.constants import BUFFER_SIZE, HEADER_SIZE, STRING_TABLE_OFFSET

sys.path.insert(0, ".")

from parse.parse_coordinator import PowerBuilderParser


def demonstrate_error_recovery() -> None:







    """Show error recovery in action."""

    print("PowerBuilder Parser Error Recovery Demonstration")
    print("=" * 50)

    # Example 1: Missing 'then' keyword
    print("\n1. Missing 'then' keyword:")
    code1 = """
function integer example1()
    integer x
    x = 1
    if x = 1
        return 1
    end if
    return 0
end function
"""

    parser = PowerBuilderParser(enable_error_recovery=True)
    ast1 = parser.parse(code1)

    print(f"   Parsed successfully: {ast1 is not None}")
    if parser.get_parse_errors():
        print(f"   Errors found: {len(parser.get_parse_errors())}")
        for error in parser.get_parse_errors():
            print(f"     - Line {error.line}: {error.message[:60]}...")

    # Example 2: Multiple syntax errors
    print("\n2. Multiple syntax errors:")
    code2 = """
public function integer test_multiple()
    // Error 1: Missing variable type declaration
    x = 10

    // Error 2: Incomplete assignment
    integer y
    y = 

    // Error 3: Missing expression after 'if'
    if then
        return 1
    end if

    // Valid code continues
    integer z
    z = 20
    return z
end function
"""

    parser.clear_errors()
    ast2 = parser.parse(code2)

    print(f"   Parsed successfully: {ast2 is not None}")
    print(f"   Number of errors: {len(parser.get_parse_errors())}")
    for i, error in enumerate(parser.get_parse_errors()[:
        3]):  # Show first 3
        print(f"   Error {i+1}: Line {error.line}: {error.message}")

    # Example 3: Comparison with recovery disabled
    print("\n3. Same code without error recovery:")
    parser_no_recovery = PowerBuilderParser(enable_error_recovery=False)

    try:
        ast3 = parser_no_recovery.parse(code1)
        print("   Unexpected: parsing succeeded")
    except Exception as e:
        print(f"   Expected exception: {type(e).__name__}: {str(e)[:60]}...")

    # Example 4: Recovery in complex code
    print("\n4. Recovery in complex nested structures:")
    code4 = """
type w_main from window
end type

event w_main.clicked()
    // Error: Missing declaration
    undeclared_var = 100

    // Nested error  
    integer i
    for i = 1 to 10
        if i > 5
            // Missing 'then'
            message = "Greater than 5"
        end if
    next

    // Valid code continues
    return 0
end event
"""

    parser.clear_errors()
    ast4 = parser.parse(code4)

    print(f"   Parsed successfully: {ast4 is not None}")
    print(f"   Total errors found: {len(parser.get_parse_errors())}")

    # Group errors by type
    errors_by_type = {}
    for error in parser.get_parse_errors():
        error_type = error.error_type
        if error_type not in errors_by_type:
            errors_by_type[error_type] = 0
        errors_by_type[error_type] += 1

    print("   Errors by type:")
    for error_type, count in errors_by_type.items():
        print(f"     - {error_type}: {count}")

    # Example 5: Show AST structure with errors
    print("\n5. AST structure with error markers:")
    simple_code = """
function integer simple()
    integer valid_statement
    valid_statement = 1
    @#$%^&*  // Garbage
    return valid_statement
end function
"""

    parser.clear_errors()
    ast5 = parser.parse(simple_code)

    if isinstance(ast5, dict):
        print(f"   AST type: {ast5.get("type", "unknown")}")
        print(f"   Has errors: {ast5.get("has_errors", False)}")
        if "elements" in ast5:
            print(f"   Number of elements: {len(ast5["elements"])}")
            for elem in ast5["elements"]:
                if isinstance(elem, dict):
                    elem_type = elem.get("type", "unknown")
                    recovered = elem.get("recovered", False)
                    print(f"     - Element type: {elem_type}, Recovered: {recovered}")


if __name__ == "__main__":
    demonstrate_error_recovery()
