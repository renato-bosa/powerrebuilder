#!/usr/bin/env python
"""Fix remaining logging format issues."""

import re
from pathlib import Path


def fix_logging_fstring(line: str) -> str:






    """Convert f-string logging to % formatting."""
    # Pattern to match logging calls with f-strings
    logging_pattern = r'((?:logger|logging|self\.logger|log)\.\w+\()\s*(f"[^"]*"|\bf\'[^\']*\')'

    def replace_fstring(match) -> str:


        prefix = match.group(1)
        fstring = match.group(2)

        # Remove the f prefix
        string_content = fstring[2:-1]  # Remove f" and "

        # Find all {expr} patterns
        expr_pattern = r"\{([^}]+)\}"
        expressions = []

        def collect_expr(m) -> str:


            expr = m.group(1)
            expressions.append(expr)
            return "%s"

        # Replace {expr} with %s and collect expressions
        new_string = re.sub(expr_pattern, collect_expr, string_content)

        # Build the result
        if expressions:
            return f'{prefix}"{new_string}", ' + ", ".join(expressions)
        else:
            return f'{prefix}"{new_string}"'

    # Apply the replacement
    return re.sub(logging_pattern, replace_fstring, line)

def process_file(filepath: Path) -> int:






    """Process a single file."""
    try:
        content = filepath.read_text()
        lines = content.splitlines(keepends=True)

        modified = False
        new_lines = []

        for line in lines:
            if "logger" in line and 'f"' in line:
                new_line = fix_logging_fstring(line)
                if new_line != line:
                    modified = True
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        if modified:
            filepath.write_text("".join(new_lines))
            return 1
        return 0

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return 0

# Specific files with remaining issues
files_to_fix = [
    "decompile/analysis/enhanced_datawindow_integration.py",
    "decompile/core/advanced_expression_reconstructor.py",
    "decompile/core/expression_reconstructor.py",
    "decompile/core/post_processor.py",
    "decompile/decompile_coordinator.py",
    "extract/pbd/extraction/extractor.py",
    "generate/sql_generator.py",
    "parse/parser_coordinator.py",
    "model/decompiler_output.py",
    "tests/integration/test_full_pipeline.py",
]

total_fixed = 0
for file_path in files_to_fix:
    path = Path(file_path)
    if path.exists():
        fixed = process_file(path)
        if fixed:
            print(f"Fixed {file_path}")
            total_fixed += fixed

print(f"\nTotal files fixed: {total_fixed}")
