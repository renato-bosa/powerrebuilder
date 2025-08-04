#!/usr/bin/env python3
"""Fix systematic indentation errors in Python files.

This tool analyzes Python files for common indentation issues and applies
intelligent fixes based on Python syntax rules.
"""

import re
import shutil
import sys
from pathlib import Path


class IndentationFixer:
    """Fix indentation errors in Python files."""

    def __init__(self, indent_size: int = 4) -> None:
        self.indent_size = indent_size
        self.indent_str = " " * indent_size
        self.changes_made: list[str] = []

    def fix_file(self, file_path: Path) -> bool:
        """Fix indentation in a Python file.

        Returns True if fixes were applied, False otherwise.
        """
        # Read the original content
        try:
            with open(file_path, encoding="utf-8") as f:
                original_content = f.read()
        except Exception:
            return False

        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")
        shutil.copy2(file_path, backup_path)

        # Apply fixes
        fixed_content = self._fix_indentation(original_content)

        if fixed_content == original_content:
            backup_path.unlink()  # Remove unnecessary backup
            return False

        # Write fixed content
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)

            # Verify the file compiles
            if self._verify_syntax(file_path):
                self._report_changes()
                return True
            # Restore from backup if still has syntax errors
            shutil.copy2(backup_path, file_path)
            return False

        except Exception:
            shutil.copy2(backup_path, file_path)
            return False

    def _fix_indentation(self, content: str) -> str:
        """Apply indentation fixes to the content."""
        lines = content.split("\n")
        fixed_lines = []
        self.changes_made = []

        # Track indentation levels
        indent_stack = [0]  # Stack of indentation levels
        current_indent = 0
        in_class = False
        in_function = False
        expecting_indent = False
        last_line_was_decorator = False
        in_multiline_string = False
        multiline_string_delim = None
        in_multiline_def = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                fixed_lines.append(line)
                i += 1
                continue

            # Check for multi-line strings
            if '"""' in line or "'''" in line:
                if not in_multiline_string:
                    # Check if it starts and ends on same line
                    if line.count('"""') == 2 or line.count("'''") == 2:
                        # Single line triple-quoted string
                        new_line = (
                            self.indent_str * (current_indent // self.indent_size)
                            + stripped
                        )
                        fixed_lines.append(new_line)
                        if new_line != line:
                            self.changes_made.append(
                                f"Line {i + 1}: Fixed string indentation"
                            )
                    else:
                        # Start of multi-line string
                        in_multiline_string = True
                        multiline_string_delim = '"""' if '"""' in line else "'''"
                        new_line = (
                            self.indent_str * (current_indent // self.indent_size)
                            + stripped
                        )
                        fixed_lines.append(new_line)
                        if new_line != line:
                            self.changes_made.append(
                                f"Line {i + 1}: Fixed multi-line string start"
                            )
                else:
                    # End of multi-line string
                    if multiline_string_delim in line:
                        in_multiline_string = False
                        multiline_string_delim = None
                    fixed_lines.append(line)  # Keep original indentation in strings
                i += 1
                continue

            # If in multi-line string, keep original formatting
            if in_multiline_string:
                fixed_lines.append(line)
                i += 1
                continue

            # Skip comments
            if stripped.startswith("#"):
                fixed_lines.append(line)
                i += 1
                continue

            # Calculate current line's indentation
            line_indent = len(line) - len(line.lstrip())

            # Check if we're in a multi-line function definition
            if in_multiline_def:
                if stripped.endswith(("):", ") -> None:")) or re.match(
                    r".*\)\s*->\s*\w+.*:$", stripped
                ):
                    # End of multi-line function definition
                    in_multiline_def = False
                    new_line = (
                        self.indent_str * (current_indent // self.indent_size)
                        + stripped
                    )
                    fixed_lines.append(new_line)

                    # Next lines should be indented
                    current_indent += self.indent_size
                    indent_stack.append(current_indent)
                    in_function = True
                    expecting_indent = True

                    if new_line != line:
                        self.changes_made.append(
                            f"Line {i + 1}: Fixed multi-line function end"
                        )
                else:
                    # Continuation of function parameters
                    new_line = (
                        self.indent_str * (current_indent // self.indent_size)
                        + stripped
                    )
                    fixed_lines.append(new_line)
                    if new_line != line:
                        self.changes_made.append(
                            f"Line {i + 1}: Fixed function parameter line"
                        )
                i += 1
                continue

            # Handle decorators
            if stripped.startswith("@"):
                last_line_was_decorator = True
                fixed_lines.append(line)
                i += 1
                continue

            # Handle class definitions
            if re.match(r"^class\s+\w+.*:$", stripped):
                # Class should be at current indentation level
                if last_line_was_decorator:
                    # Keep decorator's indentation
                    new_line = line
                    current_indent = line_indent
                else:
                    # Adjust to current indent level
                    new_line = (
                        self.indent_str * (current_indent // self.indent_size)
                        + stripped
                    )

                fixed_lines.append(new_line)

                # Next lines should be indented
                current_indent += self.indent_size
                indent_stack.append(current_indent)
                in_class = True
                expecting_indent = True

                if new_line != line:
                    self.changes_made.append(
                        f"Line {i + 1}: Fixed class definition indentation"
                    )

                last_line_was_decorator = False
                i += 1
                continue

            # Handle function/method definitions
            # Check if this is part of a multi-line function definition
            if re.match(r"^(async\s+)?def\s+\w+.*:$", stripped):
                # Function should be at current indentation level
                if last_line_was_decorator:
                    new_line = line
                    current_indent = line_indent
                else:
                    new_line = (
                        self.indent_str * (current_indent // self.indent_size)
                        + stripped
                    )

                fixed_lines.append(new_line)

                # Next lines should be indented
                current_indent += self.indent_size
                indent_stack.append(current_indent)
                in_function = True
                expecting_indent = True

                if new_line != line:
                    self.changes_made.append(
                        f"Line {i + 1}: Fixed function definition indentation"
                    )

                last_line_was_decorator = False
                i += 1
                continue
            if re.match(r"^(async\s+)?def\s+\w+.*\($", stripped):
                # Multi-line function definition
                new_line = (
                    self.indent_str * (current_indent // self.indent_size) + stripped
                )
                fixed_lines.append(new_line)

                if new_line != line:
                    self.changes_made.append(
                        f"Line {i + 1}: Fixed multi-line function start"
                    )

                # Mark that we're in a multi-line definition
                in_multiline_def = True
                last_line_was_decorator = False
                i += 1
                continue

            # Handle if/elif/else
            if_match = re.match(r"^(if|elif|else)\s*.*:$", stripped)
            if if_match:
                keyword = if_match.group(1)

                if keyword == "if":
                    # if should be at current indentation
                    new_line = (
                        self.indent_str * (current_indent // self.indent_size)
                        + stripped
                    )
                elif keyword in ("elif", "else"):
                    # elif/else should align with previous if
                    # Look back for the matching if
                    matching_indent = self._find_matching_if_indent(
                        fixed_lines, current_indent
                    )
                    if matching_indent is not None:
                        new_line = (
                            self.indent_str * (matching_indent // self.indent_size)
                            + stripped
                        )
                    else:
                        new_line = (
                            self.indent_str * (current_indent // self.indent_size)
                            + stripped
                        )

                fixed_lines.append(new_line)

                # Body should be indented
                if keyword == "if":
                    current_indent += self.indent_size
                    indent_stack.append(current_indent)
                expecting_indent = True

                if new_line != line:
                    self.changes_made.append(
                        f"Line {i + 1}: Fixed {keyword} statement indentation"
                    )

                last_line_was_decorator = False
                i += 1
                continue

            # Handle try/except/finally
            try_match = re.match(r"^(try|except|finally)\s*.*:$", stripped)
            if try_match:
                keyword = try_match.group(1)

                if keyword == "try":
                    new_line = (
                        self.indent_str * (current_indent // self.indent_size)
                        + stripped
                    )
                else:
                    # except/finally should align with try
                    matching_indent = self._find_matching_try_indent(
                        fixed_lines, current_indent
                    )
                    if matching_indent is not None:
                        new_line = (
                            self.indent_str * (matching_indent // self.indent_size)
                            + stripped
                        )
                    else:
                        new_line = (
                            self.indent_str * (current_indent // self.indent_size)
                            + stripped
                        )

                fixed_lines.append(new_line)

                # Body should be indented
                if keyword == "try":
                    current_indent += self.indent_size
                    indent_stack.append(current_indent)
                expecting_indent = True

                if new_line != line:
                    self.changes_made.append(
                        f"Line {i + 1}: Fixed {keyword} block indentation"
                    )

                last_line_was_decorator = False
                i += 1
                continue

            # Handle with statements
            if re.match(r"^with\s+.*:$", stripped):
                new_line = (
                    self.indent_str * (current_indent // self.indent_size) + stripped
                )
                fixed_lines.append(new_line)

                current_indent += self.indent_size
                indent_stack.append(current_indent)
                expecting_indent = True

                if new_line != line:
                    self.changes_made.append(
                        f"Line {i + 1}: Fixed with statement indentation"
                    )

                last_line_was_decorator = False
                i += 1
                continue

            # Handle for/while loops
            if re.match(r"^(for|while)\s+.*:$", stripped):
                new_line = (
                    self.indent_str * (current_indent // self.indent_size) + stripped
                )
                fixed_lines.append(new_line)

                current_indent += self.indent_size
                indent_stack.append(current_indent)
                expecting_indent = True

                if new_line != line:
                    self.changes_made.append(f"Line {i + 1}: Fixed loop indentation")

                last_line_was_decorator = False
                i += 1
                continue

            # Handle dedentation indicators
            if stripped in (
                "pass",
                "return",
                "break",
                "continue",
                "raise",
            ) or stripped.startswith(("return ", "raise ", "yield ")):
                # These often indicate end of a block
                new_line = (
                    self.indent_str * (current_indent // self.indent_size) + stripped
                )
                fixed_lines.append(new_line)

                if new_line != line:
                    self.changes_made.append(
                        f"Line {i + 1}: Fixed {stripped.split()[0]} statement indentation"
                    )

                # After these, we might dedent
                if len(indent_stack) > 1:
                    # Check if next non-empty line has less indentation
                    next_indent = self._get_next_line_indent(lines, i + 1)
                    if next_indent is not None and next_indent < current_indent:
                        indent_stack.pop()
                        current_indent = indent_stack[-1]

                last_line_was_decorator = False
                i += 1
                continue

            # Handle import statements
            if re.match(r"^(from|import)\s+", stripped):
                # Imports at module level should have no indentation
                if current_indent == 0 or (
                    len(indent_stack) == 1 and not in_class and not in_function
                ):
                    new_line = stripped
                else:
                    new_line = (
                        self.indent_str * (current_indent // self.indent_size)
                        + stripped
                    )

                fixed_lines.append(new_line)

                if new_line != line:
                    self.changes_made.append(
                        f"Line {i + 1}: Fixed import statement indentation"
                    )

                last_line_was_decorator = False
                i += 1
                continue

            # Handle regular code lines
            if expecting_indent:
                # This line should be indented
                new_line = (
                    self.indent_str * (current_indent // self.indent_size) + stripped
                )
                expecting_indent = False
            else:
                # Check if we need to dedent
                if line_indent < current_indent and len(indent_stack) > 1:
                    # Dedent to the appropriate level
                    while len(indent_stack) > 1 and indent_stack[-1] > line_indent:
                        indent_stack.pop()
                    current_indent = indent_stack[-1]

                new_line = (
                    self.indent_str * (current_indent // self.indent_size) + stripped
                )

            fixed_lines.append(new_line)

            if new_line != line:
                self.changes_made.append(f"Line {i + 1}: Adjusted indentation")

            last_line_was_decorator = False
            i += 1

        return "\n".join(fixed_lines)

    def _find_matching_if_indent(
        self, lines: list[str], current_indent: int
    ) -> int | None:
        """Find the indentation of the matching if statement."""
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            stripped = line.strip()
            if stripped.startswith("if ") and stripped.endswith(":"):
                return len(line) - len(line.lstrip())
        return None

    def _find_matching_try_indent(
        self, lines: list[str], current_indent: int
    ) -> int | None:
        """Find the indentation of the matching try statement."""
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i]
            stripped = line.strip()
            if stripped == "try:":
                return len(line) - len(line.lstrip())
        return None

    def _get_next_line_indent(self, lines: list[str], start_idx: int) -> int | None:
        """Get the indentation of the next non-empty line."""
        for i in range(start_idx, len(lines)):
            line = lines[i]
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return len(line) - len(line.lstrip())
        return None

    def _verify_syntax(self, file_path: Path) -> bool:
        """Verify that the file has valid Python syntax."""
        try:
            with open(file_path, encoding="utf-8") as f:
                compile(f.read(), str(file_path), "exec")
            return True
        except SyntaxError:
            return False

    def _report_changes(self) -> None:
        """Report the changes made."""
        if self.changes_made:
            for _change in self.changes_made[:10]:  # Show first 10 changes
                pass
            if len(self.changes_made) > 10:
                pass
        else:
            pass


def main() -> None:
    """Main entry point."""
    if len(sys.argv) != 2:
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        sys.exit(1)

    if file_path.suffix != ".py":
        sys.exit(1)

    fixer = IndentationFixer()
    success = fixer.fix_file(file_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
