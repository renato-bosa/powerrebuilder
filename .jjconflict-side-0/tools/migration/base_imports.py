#!/usr/bin/env python3
"""Fix imports of base classes to use the new base module."""

import re
from pathlib import Path


def fix_imports_func(file_path: Path) -> bool:
    """Fix imports in a single file."""
    content = file_path.read_text()
    original_content = content

    # Patterns to replace
    replacements = [
        # Direct imports from src.model.utils.base
        (r"from src\.model\.utils\.base import ([^;\n]+)", r"from src.base import \1"),
        # Relative imports from model.utils.base
        (r"from \.\.\.utils\.base import ([^;\n]+)", r"from src.base import \1"),
        (r"from \.\.utils\.base import ([^;\n]+)", r"from src.base import \1"),
        # Import NodeKind from model.ast.node_kind
        (
            r"from src\.model\.ast\.node_kind import NodeKind",
            r"from src.base import NodeKind",
        ),
        (
            r"from \.\.\.ast\.node_kind import NodeKind",
            r"from src.base import NodeKind",
        ),
        (r"from \.\.ast\.node_kind import NodeKind", r"from src.base import NodeKind"),
        (r"from \.ast\.node_kind import NodeKind", r"from src.base import NodeKind"),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        file_path.write_text(content)
        return True
    return False


def main() -> None:
    """Fix all imports in the src directory."""
    src_dir = Path("/Users/michael/Projects/powerrebuilder/src")

    fixed_files = []
    for py_file in src_dir.rglob("*.py"):
        # Skip the base module itself and the re-export files
        if py_file.parent.name == "base" or py_file.name in ["node_kind.py", "base.py"]:
            if py_file.parent.parent.name == "model":
                continue

        if fix_imports_func(py_file):
            fixed_files.append(py_file)

    for _file in sorted(fixed_files):
        pass


if __name__ == "__main__":
    main()
