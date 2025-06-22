#!/usr/bin/env python3
"""Replace magic numbers with named constants."""

import ast
import re
import sys
from collections import defaultdict
from pathlib import Path


class MagicNumberFinder(ast.NodeVisitor):
    """Find magic numbers in Python code."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.magic_numbers = []
        self.in_test = "test" in file_path.lower()

    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit constant node."""
        if isinstance(node.value, (int, float)):
            # Ignore common acceptable values
            if node.value not in (0, 1, -1, 2, 10, 100, 1000):
                # Check context
                if self._is_magic_number(node):
                    self.magic_numbers.append({
                        "value": node.value,
                        "line": node.lineno,
                        "col": node.col_offset,
                        "context": self._get_context(node),
                    })
        self.generic_visit(node)

    def _is_magic_number(self, node: ast.Constant) -> bool:
        """Check if a number is a magic number."""
        value = node.value

        # Special cases that are usually okay
        # HTTP status codes
        if value in (200, 201, 204, 400, 401, 403, 404, 500):
            return False

        # Common time values
        if value in (60, 3600, 86400):  # seconds, minutes, hours
            return False

        # Common byte sizes
        if value in (1024, 1048576):  # KB, MB
            return False

        # Common percentages
        if value in (0.5, 0.25, 0.75, 0.1, 0.9):
            return False

        # Port numbers in tests
        if self.in_test and 1000 <= value <= 65535:
            return False

        # Array indices and small loop counts are usually okay
        if isinstance(value, int) and -10 <= value <= 10:
            return False

        return True

    def _get_context(self, node: ast.Constant) -> str:
        """Get the context of where the number is used."""
        # This is simplified - in a real implementation we'd walk up the AST
        return "assignment"


def create_constants_module(magic_numbers_by_file: dict) -> str:

    """Create a constants module with all magic numbers."""
    # Group by value ranges
    constants = defaultdict(list)

    for file_path, numbers in magic_numbers_by_file.items():
        for num_info in numbers:
            value = num_info["value"]

            # Categorize constants
            if isinstance(value, int):
                if value < 0:
                    category = "ERROR_CODES"
                elif value < 100:
                    category = "COUNTS"
                elif value < 1000:
                    category = "SIZES"
                elif value < 10000:
                    category = "LIMITS"
                else:
                    category = "MISC"
            else:
                category = "FACTORS"

            constants[category].append((value, file_path, num_info["line"]))

    # Generate constants module
    lines = ['"""Common constants used throughout the codebase."""', "", "# Sizes and limits"]

    # Common sizes
    lines.extend([
        "HEADER_SIZE = 32",
        "BUFFER_SIZE = 4096", 
        "MAX_PATH_LENGTH = 255",
        "MAX_NAME_LENGTH = 50",
        "",
        "# Offsets",
        "STRING_TABLE_OFFSET = 0xB20",
        "METADATA_OFFSET = 0x20",
        "",
        "# Time values",
        "DEFAULT_TIMEOUT = 120000  # 2 minutes in ms",
        "MAX_TIMEOUT = 600000  # 10 minutes in ms",
        "",
        "# File format markers",
        'PBD_HEADER_MARKER = b"HDR*"',
        'ENTRY_MARKER = b"ENT*"',
        'DATA_MARKER = b"DAT*"',
        "",
        "# Magic numbers from analysis",
    ])

    # Add found constants
    for category, values in constants.items():
        if values:
            lines.append(f"\n# {category}")
            seen = set()
            for value, file_path, line in values:
                if value not in seen:
                    seen.add(value)
                    const_name = f'{category}_{str(value).replace(".", "_").replace("-", "NEG")}'
                    lines.append(f"{const_name} = {value}  # Used in {Path(file_path).name}:{line}")

    return "\n".join(lines)


def fix_magic_number_in_file(file_path: Path, magic_numbers: list) -> bool:

    """Fix magic numbers in a single file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        modified = False

        # Add import if needed
        needs_import = bool(magic_numbers)
        has_import = "from common.constants import" in content

        if needs_import and not has_import:
            # Find where to add import
            import_line = -1
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    import_line = i
                elif import_line >= 0 and line and not line.startswith((" ", "\t", "import", "from")):
                    break

            if import_line >= 0:
                lines.insert(import_line + 1, "from common.constants import HEADER_SIZE, BUFFER_SIZE, STRING_TABLE_OFFSET")
                modified = True

        # Fix specific common patterns
        replacements = [
            # Common sizes
            (r"\b32\b(?=.*header|.*size)", "HEADER_SIZE"),
            (r"\b4096\b", "BUFFER_SIZE"),
            (r"\b0[xX]B20\b", "STRING_TABLE_OFFSET"),
            (r"\b2880\b", "STRING_TABLE_OFFSET"),  # decimal version
            (r"\b0[xX]20\b(?=.*offset|.*header)", "METADATA_OFFSET"),
            # Timeouts
            (r"\b120000\b", "DEFAULT_TIMEOUT"),
            (r"\b600000\b", "MAX_TIMEOUT"),
            # Path/name lengths
            (r"\b255\b(?=.*path|.*name)", "MAX_PATH_LENGTH"),
            (r"\b50\b(?=.*name|.*length)", "MAX_NAME_LENGTH"),
        ]

        for i, line in enumerate(lines):
            # Skip comments and strings
            if "#" in line:
                code_part = line[:line.index("#")]
            else:
                code_part = line

            # Skip string literals
            if '"' in code_part or "'" in code_part:
                continue

            for pattern, replacement in replacements:
                if re.search(pattern, code_part):
                    lines[i] = re.sub(pattern, replacement, line)
                    modified = True
                    break

        if modified:
            file_path.write_text("\n".join(lines), encoding="utf-8")
            return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

    return False


def main():
    """Main function to fix magic numbers."""
    root = Path(__file__).parent.parent

    # First create constants module if it doesn't exist
    constants_file = root / "common" / "constants.py"
    if not constants_file.exists():
        print("Creating common/constants.py...")
        constants_content = create_constants_module({})
        constants_file.write_text(constants_content)

    # Find Python files with magic numbers
    python_files = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov", "tests", "scripts"}

    for py_file in root.rglob("*.py"):
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)

    print(f"Checking {len(python_files)} Python files for magic numbers...")

    # Find all magic numbers first
    all_magic_numbers = {}
    for file_path in python_files:
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            finder = MagicNumberFinder(str(file_path))
            finder.visit(tree)

            if finder.magic_numbers:
                all_magic_numbers[str(file_path)] = finder.magic_numbers

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    print(f"\nFound magic numbers in {len(all_magic_numbers)} files")

    # Fix common patterns
    updated_count = 0
    for file_path in python_files:
        magic_nums = all_magic_numbers.get(str(file_path), [])
        if fix_magic_number_in_file(file_path, magic_nums):
            print(f"✓ Updated: {file_path.relative_to(root)}")
            updated_count += 1

    print(f"\nCompleted! Updated {updated_count} files.")

    # Update constants file with found magic numbers
    if all_magic_numbers:
        print("\nUpdating constants.py with additional magic numbers...")
        constants_content = create_constants_module(all_magic_numbers)
        constants_file.write_text(constants_content)
        print("✓ Updated common/constants.py")

    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)
