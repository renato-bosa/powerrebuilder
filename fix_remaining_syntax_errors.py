#!/usr/bin/env python3
"""Fix remaining syntax errors in PowerRebuilder project."""

import re
from pathlib import Path


def fix_file(file_path, fixes) -> bool:
    """Apply fixes to a file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original = content
        for fix in fixes:
            content = fix(content)

        if content != original:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
    except Exception:
        pass
    return False


# Fix specific files
fixes_map = {
    "src/model/entities/method_call.py": [
        lambda c: c.replace(
            "dynamic_class_expr: | None = None", "dynamic_class_expr: Any | None = None"
        )
    ],
    "src/model/services/ast_processor.py": [
        lambda c: c.replace("with file_path.open(, 'r'", "with file_path.open('r'")
    ],
    "src/model/services/model_persistence.py": [
        lambda c: c.replace("with file_path.open(, 'w'", "with file_path.open('w'")
    ],
    "src/decompile/pcode/decoder.py": [
        # Fix the else indentation issue around line 160
        lambda c: re.sub(
            r"\n(\s*)else:\n(\s+)# Calculate", r"\n\1else:\n\1    # Calculate", c
        ),
        # Fix missing if statement
        lambda c: re.sub(
            r"(\s+)pcode_bytes = object_data\[pcode_offset.*?\]\n(\s+)instructions",
            r"\1pcode_bytes = object_data[pcode_offset: pcode_offset + pcode_size]\n\1if pcode_size > 0:\n\1    instructions",
            c,
        ),
    ],
    "src/decompile/pcode/opcodes/definitions.py": [
        # Fix unexpected indent
        lambda c: re.sub(
            r"\n\s+import logging\n\s+from functools",
            r"\nimport logging\nfrom functools",
            c,
        )
    ],
    "src/decompile/pcode/recovery.py": [
        # Fix line 178 while condition
        lambda c: c.replace("while (:", "while ("),
        lambda c: re.sub(r"while \(\s*:\s*\n", "while (\n", c),
    ],
    "src/decompile/pcode/opcodes/variants.py": [
        # Fix elif without matching if
        lambda c: re.sub(
            r"(\s+)elif low_nibble == 0x09:\n(\s+)values\.append",
            r"\1elif low_nibble == 0x09:\n\1    values.append",
            c,
        )
    ],
    "src/extract/components/resources.py": [
        # Fix unmatched parenthesis
        lambda c: re.sub(
            r"found_resources\):\s*$", "found_resources):", c, flags=re.MULTILINE
        )
    ],
    "src/extract/components/statistics.py": [
        # Fix unmatched parenthesis
        lambda c: re.sub(r"\s*\):\s*$", "):", c, flags=re.MULTILINE)
    ],
    "src/model/analysis/security.py": [
        # Fix unmatched bracket
        lambda c: re.sub(r"^\s*\]\s*$", "", c, flags=re.MULTILINE)
    ],
    "src/decompile/core/formatter.py": [
        # Fix line 623
        lambda c: c.replace(
            ") and i + 1 < len(decoded_obj.instructions):",
            " and i + 1 < len(decoded_obj.instructions):",
        )
    ],
    "src/decompile/pcode/detector.py": [
        # Fix unmatched parenthesis in function parameter
        lambda c: re.sub(
            r"confidence: float = 0\.0\) -> None:",
            "confidence: float = 0.0) -> None:",
            c,
        )
    ],
    "src/model/types/powerbuilder.py": [
        # Fix indentation issue
        lambda c: re.sub(r"\n\s{0,4}return False", "\n        return False", c)
    ],
    "src/decompile/analysis/control.py": [
        # Fix line 344 unmatched )
        lambda c: re.sub(r"^\s*\)\s*$", "", c, flags=re.MULTILINE)
    ],
}

# Additional generic fixes for common patterns
generic_fixes = [
    # Fix else: without matching if
    (
        r"(\n\s+)else:\s*\n",
        lambda m: m.group(0)
        if any(
            kw in m.string[max(0, m.start() - 200) : m.start()]
            for kw in ["if ", "elif "]
        )
        else "",
    ),
    # Fix elif without matching if
    (
        r"(\n\s+)elif\s+",
        lambda m: m.group(0)
        if any(
            kw in m.string[max(0, m.start() - 200) : m.start()]
            for kw in ["if ", "elif "]
        )
        else "\n" + m.group(1) + "if ",
    ),
    # Fix except without try
    (
        r"(\n\s+)except\s+",
        lambda m: m.group(0)
        if "try:" in m.string[max(0, m.start() - 500) : m.start()]
        else "",
    ),
]


def apply_generic_fixes(content):
    """Apply generic pattern-based fixes."""
    for pattern, replacement in generic_fixes:
        content = re.sub(pattern, replacement, content)
    return content


def main() -> None:
    """Fix all remaining syntax errors."""
    fixed_count = 0

    # Apply specific fixes
    for file_path, fixes in fixes_map.items():
        if Path(file_path).exists() and fix_file(file_path, fixes):
            fixed_count += 1

    # Apply generic fixes to files not in specific map
    error_files = [
        "src/decompile/analyzers/parser.py",
        "src/decompile/reconstruction/expression.py",
        "src/extract/components/recovery.py",
        "src/extract/components/validator.py",
        "src/extract/utils/encoding.py",
        "src/model/entities/library.py",
        "src/model/symbols/resolver.py",
        "src/model/types/validation.py",
        "src/parse/parser/specialized/transactions.py",
        "src/parse/parser/specialized/types.py",
        "src/parse/preprocessor/imports.py",
        "src/parse/preprocessor/preprocessor.py",
    ]

    for file_path in error_files:
        if Path(file_path).exists() and file_path not in fixes_map:
            if fix_file(file_path, [apply_generic_fixes]):
                fixed_count += 1


if __name__ == "__main__":
    main()
