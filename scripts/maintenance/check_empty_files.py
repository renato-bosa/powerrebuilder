#!/usr/bin/env python3
"""Check for empty or nearly empty files in the project."""

from pathlib import Path


def check_empty_files(root_dir: Path):
    """Find empty or nearly empty Python files."""
    empty_files = []
    small_files = []

    for path in root_dir.rglob("*.py"):
        # Skip hidden directories and __pycache__
        if any(part.startswith(".") for part in path.parts) or "__pycache__" in str(
            path
        ):
            continue

        try:
            size = path.stat().st_size

            if size == 0:
                empty_files.append(path)
            elif size < 50:  # Less than 50 bytes is essentially empty
                with open(path) as f:
                    content = f.read().strip()
                    # Check if it's just imports or docstring
                    if (
                        not content
                        or content == '""""""'
                        or content.startswith("from __future__")
                    ):
                        small_files.append((path, size, content[:50]))
        except Exception:
            pass

    return empty_files, small_files


def main() -> None:
    """Main function."""
    project_root = Path(__file__).parent.parent.parent

    empty_files, small_files = check_empty_files(project_root)

    if empty_files:
        for f in sorted(empty_files):
            f.relative_to(project_root)

    if small_files:
        for f, _size, _preview in sorted(small_files):
            f.relative_to(project_root)

    if not empty_files and not small_files:
        pass

    # Check specifically for empty __init__.py files
    empty_inits = [f for f in empty_files if f.name == "__init__.py"]
    if empty_inits:
        for f in sorted(empty_inits):
            f.relative_to(project_root)


if __name__ == "__main__":
    main()
