#!/usr/bin/env python3
"""Debug test to see what's being generated."""

from decompile.core.pcode_decoder import DecodedObject
from decompile.core.simple_formatter import SimpleFormatter
from extract.pbd.utils.version_detector import PowerBuilderVersion
from tests.test_decompile.test_simple_formatter_enhanced import create_instruction


def test_debug_function_calls():


    formatter = SimpleFormatter()

    decoded_obj = DecodedObject(
        name="call_functions",
        type="function",
        version=PowerBuilderVersion(10, 5, True),
        instructions=[
            create_instruction(0, 0x30, "GLOBFUNCCALL", [100]),
            create_instruction(2, 0x31, "CALL_FUNCTION", [200]),
            create_instruction(4, 0x32, "DLLFUNCCALL", [0]),  # MessageBoxA
            create_instruction(14, 0x99, "RETURN", [0]),
        ],
    )

    result = formatter.format_object(decoded_obj, "test.fun")
    print("\n".join(result))

def test_debug_database():


    formatter = SimpleFormatter()

    decoded_obj = DecodedObject(
        name="database_operations",
        type="function",
        version=PowerBuilderVersion(10, 5, True),
        instructions=[
            create_instruction(0, 0x50, "DBSELECT"),
            create_instruction(2, 0x51, "DBFETCH"),
            create_instruction(14, 0x99, "RETURN", [0]),
        ],
    )

    result = formatter.format_object(decoded_obj, "test.fun")
    print("\n=== Database Output ===")
    print("\n".join(result))

if __name__ == "__main__":
    test_debug_function_calls()
    test_debug_database()
