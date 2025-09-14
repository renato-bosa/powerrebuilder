#!/usr/bin/env python3
"""Inspect the compiled opcodes.pyc file to see what's in it."""

import marshal


def inspect_pyc(pyc_path):
    """Inspect a .pyc file and extract any opcode definitions."""
    try:
        with open(pyc_path, "rb") as f:
            # Skip Python version header (varies by version)
            # Python 3.7+ has 16 byte header, earlier versions have 12
            f.read(16)

            # Read the marshalled code object
            code = marshal.load(f)

            # Get the module's globals by executing it
            module_globals = {}
            exec(code, module_globals)

            # Look for opcode-related variables
            opcode_vars = {}
            for name, value in module_globals.items():
                if "OPCODE" in name or "opcode" in name.lower():
                    opcode_vars[name] = value

            return opcode_vars

    except Exception:
        return None


if __name__ == "__main__":
    pyc_file = (
        "archive/old_modules/decompile/opcodes/__pycache__/opcodes.cpython-313.pyc"
    )

    result = inspect_pyc(pyc_file)

    if result:
        for value in result.values():
            if isinstance(value, dict):
                # Show first few entries
                for i, (_k, _v) in enumerate(value.items()):
                    if i >= 5:
                        break
            else:
                pass
