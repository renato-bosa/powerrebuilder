#!/usr/bin/env python3
"""Check for Chinese/garbled characters in output files."""

import os
import re
import sys
from pathlib import Path

# Common Chinese/garbled character patterns found in the past
CHINESE_CHARS_REGEX = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\u2000-\u2fff]")
COMMON_GARBLED = ["䅄⩔", "䑣呁", "舀", "Ƕ"]


def check_file_for_chinese(filepath: Path) -> list[tuple[int, str]]:








    """Check a file for Chinese/garbled characters and return line numbers with matches."""
    matches = []

    # Skip binary files
    if filepath.suffix in [".fun", ".dwo", ".ico", ".bmp", ".jpg", ".png", ".gif"]:
        return matches

    # Skip metadata JSON files (they're auto-generated)
    if filepath.name.endswith(".meta.json"):
        return matches

    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                # Check for Chinese characters
                if CHINESE_CHARS_REGEX.search(line) or any(
                    garbled in line for garbled in COMMON_GARBLED
                ):
                    matches.append((line_num, line.strip()))
    except Exception:
        # If we can't read it as text, it's probably binary
        pass

    return matches


def main() -> int:





    output_dir = Path("output")
    if not output_dir.exists():
        return 1

    total_files = 0
    files_with_issues = 0

    for root, _dirs, files in os.walk(output_dir):
        for filename in files:
            filepath = Path(root) / filename
            total_files += 1

            matches = check_file_for_chinese(filepath)
            if matches:
                files_with_issues += 1
                for _line_num, _line in matches[:
                    5]:  # Show first 5 matches
                    pass
                if len(matches) > 5:
                    pass

    if files_with_issues == 0:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
