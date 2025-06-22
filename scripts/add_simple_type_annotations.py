#!/usr/bin/env python3
"""Add simple type annotations to improve type coverage."""

import re
from pathlib import Path


def add_none_return_types(file_path: Path) -> int:








    """Add -> None to functions that don't return anything."""
    try:
        content = file_path.read_text()
        original = content

        # Pattern to match functions without return type that don't have return statements
        pattern = r"(\n\s*def\s+\w+\s*\([^)]*\))\s*:\s*\n"

        def check_and_add_type(match):




            """Check if function needs -> None annotation."""
            func_def = match.group(1)
            # Look ahead to see if there's a return statement
            rest_of_file = content[match.end():]
            # Find the next function or class definition
            next_def = re.search(r"\n\s*(def|class)\s+", rest_of_file)
            if next_def:
                func_body = rest_of_file[:next_def.start()]
            else:
                func_body = rest_of_file

            # Check if function has explicit return with value
            if re.search(r"\n\s*return\s+[^#\n]+", func_body):
                return match.group(0)  # Has return value, don't add -> None
            else:
                return func_def + " -> None:\n"

        content = re.sub(pattern, check_and_add_type, content)

        if content != original:
            file_path.write_text(content)
            return content.count("-> None") - original.count("-> None")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return 0


def add_self_types(file_path: Path) -> int:








    """Add type hints for self parameters in class methods."""
    try:
        content = file_path.read_text()
        original = content
        changes = 0

        # Add 'from __future__ import annotations' if needed
        if "def " in content and "from __future__ import annotations" not in content:
            lines = content.split("\n")
            # Find where to insert
            insert_pos = 0
            if lines[0].startswith("#!"):
                insert_pos = 1
            if lines[insert_pos].startswith('"""'):
                while insert_pos < len(lines) and not lines[insert_pos].endswith('"""'):
                    insert_pos += 1
                insert_pos += 1

            lines.insert(insert_pos, "from __future__ import annotations")
            content = "\n".join(lines)
            changes += 1

        if content != original:
            file_path.write_text(content)

        return changes

    except Exception as e:
        print(f"Error adding self types to {file_path}: {e}")

    return 0


def main() -> None:







    """Main entry point."""
    print("Adding simple type annotations...")

    modules = ["common", "model", "extract", "parse", "decompile", "generate"]
    total_changes = 0

    for module in modules:
        module_path = Path(module)
        if not module_path.exists():
            continue

        print(f"\nProcessing {module}...")
        module_changes = 0

        for py_file in module_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or py_file.name.endswith(".pyi"):
                continue

            # Add -> None annotations
            changes = add_none_return_types(py_file)
            if changes > 0:
                print(f"✓ Added {changes} '-> None' annotations to {py_file}")
                module_changes += changes

            # Add self type annotations
            changes = add_self_types(py_file)
            if changes > 0:
                print(f"✓ Added type imports to {py_file}")
                module_changes += changes

        total_changes += module_changes
        print(f"Module {module}: {module_changes} changes")

    print(f"\nTotal changes: {total_changes}")

    # Run mypy to check
    import subprocess
    result = subprocess.run(
        ["mypy", ".", "--config-file=mypy.ini"],
        capture_output=True,
        text=True,
    )

    error_count = result.stdout.count(": error:")
    print(f"\nCurrent mypy errors: {error_count}")


if __name__ == "__main__":
    main()
