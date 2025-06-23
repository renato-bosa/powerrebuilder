#!/usr/bin/env python3
"""Script to fix G004 and G201 logging issues automatically."""

import re
import sys
from pathlib import Path


def fix_g004_issues(content: str) -> str:








    """Fix G004: Replace f-strings in logging with % formatting."""

    # Pattern to match logging calls with f-strings
    # This handles multi-line logging calls
    patterns = [
        # logger.info(f"...")
        (r'(logger\.\w+)\s*\(\s*f"([^"]+)"\s*\)', fix_simple_fstring),
        # logger.info(f'...')  
        (r"(logger\.\w+)\s*\(\s*f'([^']+)'\s*\)", fix_simple_fstring),
        # Multi-line with f-string
        (r'(logger\.\w+)\s*\(\s*\n\s*f"([^"]+)"\s*\n\s*\)', fix_multiline_fstring),
        (r"(logger\.\w+)\s*\(\s*\n\s*f'([^']+)'\s*\n\s*\)", fix_multiline_fstring),
        # logging.info(f"...")
        (r'(logging\.\w+)\s*\(\s*f"([^"]+)"\s*\)', fix_simple_fstring),
        (r"(logging\.\w+)\s*\(\s*f'([^']+)'\s*\)", fix_simple_fstring),
    ]

    for pattern, fixer in patterns:
        content = re.sub(pattern, fixer, content, flags=re.MULTILINE | re.DOTALL)

    return content


def fix_simple_fstring(match):






    """Fix simple f-string logging calls."""
    method = match.group(1)
    message = match.group(2)

    # Extract variables from f-string
    vars_pattern = r"\{([^}:]+)(?::[^}]+)?\}"
    variables = re.findall(vars_pattern, message)

    # Replace {var} with %s in message
    new_message = re.sub(vars_pattern, "%s", message)

    # Build the new logging call
    if variables:
        vars_str = ", ".join(variables)
        return f'{method}("{new_message}", {vars_str})'
    else:
        return f'{method}("{new_message}")'


def fix_multiline_fstring(match):






    """Fix multi-line f-string logging calls."""
    method = match.group(1)
    message = match.group(2)

    # Extract variables from f-string
    vars_pattern = r"\{([^}:]+)(?::[^}]+)?\}"
    variables = re.findall(vars_pattern, message)

    # Replace {var} with %s in message
    new_message = re.sub(vars_pattern, "%s", message)

    # Build the new logging call
    if variables:
        vars_str = ", ".join(variables)
        return f'{method}(\n        "{new_message}",\n        {vars_str}\n    )'
    else:
        return f'{method}(\n        "{new_message}"\n    )'


def fix_g201_issues(content: str) -> str:








    """Fix G201: Replace .error(..., exc_info=True) with .exception(...)."""

    # Pattern to match logger.error with exc_info=True
    patterns = [
        # Single line
        (r"(logger\.error)\s*\(([^)]+),\s*exc_info=True\s*\)", r"logger.exception(\2)"),
        # Multi-line
        (r"(logger\.error)\s*\(\s*\n([^)]+),\s*\n\s*exc_info=True,?\s*\n\s*\)", r"logger.exception(\n\2\n    )"),
        # logging.error
        (r"(logging\.error)\s*\(([^)]+),\s*exc_info=True\s*\)", r"logging.exception(\2)"),
        (r"(logging\.error)\s*\(\s*\n([^)]+),\s*\n\s*exc_info=True,?\s*\n\s*\)", r"logging.exception(\n\2\n    )"),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

    return content


def process_file(file_path: Path) -> bool:








    """Process a single Python file to fix logging issues."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Apply fixes
        content = fix_g004_issues(content)
        content = fix_g201_issues(content)

        # Write back if changed
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            print(f"Fixed: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main() -> None:







    """Main function to process all Python files in extract directory."""
    extract_dir = Path("extract")
    if not extract_dir.exists():
        print("Error: extract directory not found")
        sys.exit(1)

    fixed_count = 0
    total_count = 0

    # Process all Python files
    for py_file in extract_dir.rglob("*.py"):
        total_count += 1
        if process_file(py_file):
            fixed_count += 1

    print(f"\nProcessed {total_count} files, fixed {fixed_count} files")


if __name__ == "__main__":
    main()
