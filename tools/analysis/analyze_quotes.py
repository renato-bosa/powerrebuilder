#!/usr/bin/env python3
"""Analyze quote usage in the codebase."""

import ast
from collections import Counter
from pathlib import Path


def analyze_file(file_path: Path) -> dict:

    """Analyze quote usage in a single file."""
    try:
        content = file_path.read_text(encoding="utf-8")

        # Count raw occurrences (rough estimate)
        single_quotes = content.count("'")
        double_quotes = content.count('"')

        # Try to parse AST to count string literals
        string_count = 0
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    string_count += 1
        except:
            pass

        return {
            "single_quotes": single_quotes,
            "double_quotes": double_quotes,
            "string_literals": string_count,
            "mixed": single_quotes > 0 and double_quotes > 0,
        }
    except:
        return None


def main():
    """Analyze all Python files."""
    root = Path(__file__).parent.parent

    # Find all Python files
    python_files = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov", "tests", "reference", "scripts"}

    for py_file in root.rglob("*.py"):
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)

    print(f"Analyzing {len(python_files)} Python files...")

    total_single = 0
    total_double = 0
    mixed_files = 0
    single_only_files = 0
    double_only_files = 0

    for file_path in python_files:
        result = analyze_file(file_path)
        if result:
            total_single += result["single_quotes"]
            total_double += result["double_quotes"]

            if result["mixed"]:
                mixed_files += 1
            elif result["single_quotes"] > 0:
                single_only_files += 1
            elif result["double_quotes"] > 0:
                double_only_files += 1

    print(f"\nResults:")
    print(f"Total single quotes: {total_single}")
    print(f"Total double quotes: {total_double}")
    print(f"Files using only single quotes: {single_only_files}")
    print(f"Files using only double quotes: {double_only_files}")
    print(f"Files using mixed quotes: {mixed_files}")

    # Conclusion
    if double_only_files > single_only_files:
        print(f"\n✓ Most files ({double_only_files}/{len(python_files)}) already use double quotes consistently")
    else:
        print(f"\n⚠️ Quote usage is mixed across the codebase")


if __name__ == "__main__":
    main()
