#!/usr/bin/env python3
"""Fix import statements in tools directory after src/ reorganization."""

import re
from pathlib import Path


def get_python_files(directory: Path) -> list[Path]:
    """Get all Python files in directory recursively."""
    return list(directory.rglob("*.py"))


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a single file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return False

    original_content = content

    # Pattern to match imports from old structure
    old_import_patterns = [
        # Fix absolute imports
        (r"from (common|extract|parse|decompile|model|generate)\.", r"from src.\1."),
        (
            r"import (common|extract|parse|decompile|model|generate)\.",
            r"import src.\1.",
        ),
        (
            r"from (common|extract|parse|decompile|model|generate) import",
            r"from src.\1 import",
        ),
        (
            r"import (common|extract|parse|decompile|model|generate)(\s|$)",
            r"import src.\1\2",
        ),
        # Fix imports that were already partially corrected
        (
            r"from src\.(common|extract|parse|decompile|model|generate)\.",
            r"from src.\1.",
        ),
        # Fix specific problematic imports
        (r"from decompile\.constants import", r"from src.decompile.opcodes import"),
        (
            r"from src\.decompile\.constants import",
            r"from src.decompile.pcode.opcodes.definitions import",
        ),
        (
            r"from extract\.pbd\.extractors\.extractor import",
            r"from src.extract.pbd.extractor_base import",
        ),
    ]

    for pattern, replacement in old_import_patterns:
        content = re.sub(pattern, replacement, content)

    # Fix any double src. (in case file already had some fixes)
    content = re.sub(r"src\.src\.", "src.", content)

    if content != original_content:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    return False


def main() -> None:
    """Main function to fix all imports in tools directory."""
    tools_dir = Path(__file__).parent.parent

    python_files = get_python_files(tools_dir)

    fixed_count = 0
    error_files = []

    for file_path in python_files:
        # Skip this script itself and migration directory
        if file_path.name == "imports.py" or "migration" in str(file_path):
            continue

        try:
            if fix_imports_in_file(file_path):
                fixed_count += 1
        except Exception as e:
            error_files.append((file_path, str(e)))

    if error_files:
        for file_path, _error in error_files:
            pass


if __name__ == "__main__":
    main()
