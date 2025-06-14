#!/usr/bin/env python3
"""Script to consolidate opcode implementations."""

from pathlib import Path


def consolidate_opcodes() -> None:
    """Consolidate duplicate opcode implementations."""
    project_root = Path(__file__).parent.parent.parent

    # The decompile version is more comprehensive and actively used
    # We'll remove the extract version and update imports

    extract_opcodes = project_root / "extract" / "pbd_core" / "opcodes.py"
    extract_opcodes_yaml = project_root / "extract" / "pbd_core" / "opcodes.yaml"

    if extract_opcodes.exists():
        extract_opcodes.unlink()

    if extract_opcodes_yaml.exists():
        extract_opcodes_yaml.unlink()

    # Update extract/pbd_core/__init__.py to not import opcodes
    init_file = project_root / "extract" / "pbd_core" / "__init__.py"
    if init_file.exists():
        with open(init_file) as f:
            content = f.read()

        # Remove opcode-related imports and exports
        lines = content.split("\n")
        new_lines = []
        skip_until_close = False

        for line in lines:
            if "from .opcodes import" in line:
                skip_until_close = True
                continue
            if skip_until_close and ")" in line:
                skip_until_close = False
                continue
            if skip_until_close:
                continue

            # Remove from __all__ list
            if any(
                item in line
                for item in [
                    '"load_opcodes"',
                    '"get_opcode_info"',
                    '"log_unknown_opcode"',
                    '"attempt_symbolic_fallback"',
                    '"SymbolicStack"',
                    '"CFGNode"',
                    '"FallbackResult"',
                ]
            ):
                continue

            new_lines.append(line)

        # Write updated content
        with open(init_file, "w") as f:
            f.write("\n".join(new_lines))

    # Check if any files need to be updated to import from decompile.opcodes instead


if __name__ == "__main__":
    consolidate_opcodes()
