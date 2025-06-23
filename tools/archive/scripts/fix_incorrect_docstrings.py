#!/usr/bin/env python3
"""Fix incorrectly formatted docstrings with quadruple quotes."""

import re
from pathlib import Path


def fix_docstrings(content: str) -> tuple[str, bool]:

    """Fix docstrings with incorrect quote formatting."""
    # Fix quadruple quotes at start
    content = re.sub(r'""""([^"]+)', r'"""\1', content)
    # Fix quadruple quotes at end
    content = re.sub(r'([^"]+)""""', r'\1"""', content)

    # Check if we made changes
    changed = '""""' not in content

    return content, changed


def main():
    """Fix docstrings in recently modified files."""
    files_to_fix = [
        "benchmarks/benchmark_end_to_end.py",
        "benchmarks/benchmark_extraction.py",
        "benchmarks/benchmark_generation.py",
        "benchmarks/benchmark_parsing.py",
        "model/ast/additional_nodes.py",
        "model/ast/types.py",
        "model/base/pb_behavioral.py",
    ]

    root = Path(__file__).parent.parent

    for file_path in files_to_fix:
        full_path = root / file_path
        if full_path.exists():
            content = full_path.read_text(encoding="utf-8")
            if '""""' in content:
                fixed_content, _ = fix_docstrings(content)
                full_path.write_text(fixed_content, encoding="utf-8")
                print(f"✓ Fixed: {file_path}")

    print("Done!")


if __name__ == "__main__":
    main()
