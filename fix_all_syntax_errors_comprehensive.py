#!/usr/bin/env python3
"""Comprehensive syntax error fixer for PowerRebuilder codebase."""

import ast
from pathlib import Path


class SyntaxErrorFixer:
    def __init__(self) -> None:
        self.fixed_count = 0
        self.error_count = 0
        self.files_with_errors = []

    def detect_syntax_error(self, filepath: Path) -> dict:
        """Detect syntax error in a file."""
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            ast.parse(content)
            return None
        except SyntaxError as e:
            return {
                "file": str(filepath),
                "line": e.lineno,
                "col": e.offset,
                "error": e.msg,
                "text": e.text.strip() if e.text else "",
                "content": content,
            }
        except Exception:
            return None

    def fix_unmatched_else(self, lines: list[str], error_line: int) -> list[str]:
        """Fix unmatched else statement by checking indentation."""
        if error_line > 0 and error_line <= len(lines):
            # Find the corresponding if/elif/try block
            indent_level = len(lines[error_line - 1]) - len(
                lines[error_line - 1].lstrip()
            )

            # Look backwards for matching if/elif/try
            for i in range(error_line - 2, -1, -1):
                line = lines[i]
                if line.strip() and not line.strip().startswith("#"):
                    line_indent = len(line) - len(line.lstrip())
                    if line_indent < indent_level and any(
                        line.strip().startswith(kw)
                        for kw in ["if ", "elif ", "try:", "except"]
                    ):
                        # Found the matching block, fix else indentation
                        lines[error_line - 1] = (
                            " " * line_indent + lines[error_line - 1].strip()
                        )
                        return lines
        return lines

    def fix_unexpected_indent(self, lines: list[str], error_line: int) -> list[str]:
        """Fix unexpected indent by aligning with previous line."""
        if error_line > 1 and error_line <= len(lines):
            # Get previous non-empty line
            prev_indent = 0
            for i in range(error_line - 2, -1, -1):
                if lines[i].strip() and not lines[i].strip().startswith("#"):
                    prev_indent = len(lines[i]) - len(lines[i].lstrip())
                    break

            # Fix current line indentation
            lines[error_line - 1] = " " * prev_indent + lines[error_line - 1].strip()
        return lines

    def fix_unmatched_parenthesis(
        self, lines: list[str], error_line: int, error_type: str
    ) -> list[str]:
        """Fix unmatched parenthesis/bracket."""
        if error_line > 0 and error_line <= len(lines):
            line = lines[error_line - 1]

            # Count parentheses/brackets
            open_parens = line.count("(")
            close_parens = line.count(")")
            open_brackets = line.count("[")
            close_brackets = line.count("]")

            if "unmatched ')'" in error_type and close_parens > open_parens:
                # Look for multi-line expression
                total_open = open_parens
                total_close = close_parens

                # Check previous lines
                for i in range(error_line - 2, max(0, error_line - 10), -1):
                    prev_line = lines[i]
                    total_open += prev_line.count("(")
                    total_close += prev_line.count(")")

                    if total_open >= total_close:
                        # Found enough opening parens
                        break

                if total_open < total_close:
                    # Remove extra closing paren
                    lines[error_line - 1] = line.rstrip().rstrip(")")

            elif "unmatched ']'" in error_type and close_brackets > open_brackets:
                # Similar logic for brackets
                lines[error_line - 1] = line.rstrip().rstrip("]")

        return lines

    def fix_invalid_syntax(
        self, lines: list[str], error_line: int, error_info: dict
    ) -> list[str]:
        """Fix various invalid syntax errors."""
        if error_line > 0 and error_line <= len(lines):
            line = lines[error_line - 1]

            # Check for missing colons
            if any(
                keyword in line
                for keyword in [
                    "if ",
                    "elif ",
                    "else",
                    "try",
                    "except",
                    "finally",
                    "def ",
                    "class ",
                    "for ",
                    "while ",
                    "with ",
                ]
            ):
                if not line.rstrip().endswith(":") and not line.strip().startswith("#"):
                    # Add missing colon
                    lines[error_line - 1] = line.rstrip() + ":"
                    return lines

            # Check for elif/else without proper indentation
            if line.strip().startswith(("elif ", "else:")):
                # Fix by looking at previous if/elif
                for i in range(error_line - 2, -1, -1):
                    prev = lines[i]
                    if prev.strip() and (
                        prev.strip().startswith("if ")
                        or prev.strip().startswith("elif ")
                    ):
                        indent = len(prev) - len(prev.lstrip())
                        lines[error_line - 1] = " " * indent + line.strip()
                        return lines

        return lines

    def fix_file(self, filepath: Path) -> bool:
        """Fix syntax errors in a single file."""
        error_info = self.detect_syntax_error(filepath)
        if not error_info:
            return True

        lines = error_info["content"].splitlines(keepends=True)
        original_lines = lines.copy()

        # Apply fixes based on error type
        if "unexpected indent" in error_info["error"]:
            lines = self.fix_unexpected_indent(lines, error_info["line"])
        elif "unmatched" in error_info["error"]:
            lines = self.fix_unmatched_parenthesis(
                lines, error_info["line"], error_info["error"]
            )
        elif "invalid syntax" in error_info["error"]:
            if error_info["text"] and error_info["text"].strip() == "else:":
                lines = self.fix_unmatched_else(lines, error_info["line"])
            else:
                lines = self.fix_invalid_syntax(lines, error_info["line"], error_info)
        elif "unindent does not match" in error_info["error"]:
            lines = self.fix_unexpected_indent(lines, error_info["line"])

        # Write back if changed
        if lines != original_lines:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                # Verify fix
                if self.detect_syntax_error(filepath) is None:
                    self.fixed_count += 1
                    return True
                with open(filepath, "w", encoding="utf-8") as f:
                    f.writelines(original_lines)
            except Exception:
                self.error_count += 1
        else:
            self.files_with_errors.append(str(filepath))

        return False

    def fix_all(self) -> None:
        """Fix all Python files with syntax errors."""
        src_path = Path("src")

        # First pass: collect all files with errors
        error_files = []

        for py_file in sorted(src_path.rglob("*.py")):
            if self.detect_syntax_error(py_file):
                error_files.append(py_file)

        # Fix files in multiple passes (some fixes may enable others)
        max_passes = 3
        for _pass_num in range(max_passes):
            remaining_errors = []
            for filepath in error_files:
                if not self.fix_file(filepath):
                    remaining_errors.append(filepath)

            error_files = remaining_errors
            if not error_files:
                break

        # Report results

        if self.files_with_errors:
            for _f in sorted(self.files_with_errors):
                pass


def main() -> None:
    fixer = SyntaxErrorFixer()
    fixer.fix_all()


if __name__ == "__main__":
    main()
