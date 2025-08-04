#!/usr/bin/env python3
"""Final syntax error fixer targeting specific issues found in the analysis.
This script fixes the most common patterns found in the codebase.
"""

import ast
import os
import re
import shutil
from datetime import datetime
from pathlib import Path


class FinalSyntaxFixer:
    def __init__(self, backup_dir: str = "syntax_backup_final") -> None:
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.log_file = (
            f"final_syntax_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        self.fixed_files = []
        self.failed_files = []

    def backup_file(self, filepath: Path) -> Path:
        """Create a backup of the file before modification."""
        backup_path = self.backup_dir / filepath.relative_to("src")
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(filepath, backup_path)
        return backup_path

    def log(self, message: str) -> None:
        """Log messages to both console and file."""
        with open(self.log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()}: {message}\n")

    def fix_misaligned_elif_else(self, lines: list[str]) -> list[str]:
        """Fix elif/else that should be aligned with if."""
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.lstrip()

            # Check for elif/else at wrong indentation
            if stripped.startswith(("elif ", "else:")):
                current_indent = len(line) - len(stripped)

                # Look backwards for the matching if
                for j in range(i - 1, max(0, i - 20), -1):
                    prev_line = lines[j]
                    prev_stripped = prev_line.lstrip()

                    if prev_stripped.startswith("if "):
                        # Found a potential matching if
                        prev_indent = len(prev_line) - len(prev_stripped)

                        # Check if this elif/else is indented more than the if
                        if current_indent > prev_indent:
                            # Fix the indentation
                            line = " " * prev_indent + stripped
                            self.log(f"  Fixed elif/else indentation at line {i + 1}")
                        break

            fixed_lines.append(line)

        return fixed_lines

    def fix_unmatched_parentheses(self, lines: list[str]) -> list[str]:
        """Fix unmatched parentheses in function calls and definitions."""
        fixed_lines = []

        for i, line in enumerate(lines):
            # Count parentheses
            open_count = line.count("(")
            close_count = line.count(")")

            # Fix extra closing parentheses
            if close_count > open_count:
                # Check if this is a continuation of a previous line
                total_open = open_count
                total_close = close_count

                # Look back for opening parentheses
                for j in range(i - 1, max(0, i - 5), -1):
                    total_open += lines[j].count("(")
                    total_close += lines[j].count(")")

                if total_close > total_open:
                    # Remove extra closing parentheses
                    extra = total_close - total_open
                    for _ in range(extra):
                        if ")" in line:
                            line = line.replace(")", "", 1)
                            self.log(
                                f"  Removed extra closing parenthesis at line {i + 1}"
                            )

            # Fix missing closing parentheses in function definitions
            if line.strip().startswith("def ") and "(" in line and ")" not in line:
                line = line.rstrip() + "):\n"
                self.log(
                    f"  Added missing closing parenthesis to function at line {i + 1}"
                )

            fixed_lines.append(line)

        return fixed_lines

    def fix_incorrect_indentation_after_except(self, lines: list[str]) -> list[str]:
        """Fix indentation issues with except blocks."""
        fixed_lines = []

        for i, line in enumerate(lines):
            # Check if this line has "except" at wrong indentation level
            if "except" in line and ":" in line:
                # Check if it's indented too far
                current_indent = len(line) - len(line.lstrip())

                # Look for the try block
                for j in range(i - 1, max(0, i - 20), -1):
                    if lines[j].strip().startswith("try:"):
                        try_indent = len(lines[j]) - len(lines[j].lstrip())
                        if current_indent > try_indent:
                            # Fix the indentation
                            line = " " * try_indent + line.lstrip()
                            self.log(f"  Fixed except indentation at line {i + 1}")
                        break

            fixed_lines.append(line)

        return fixed_lines

    def fix_missing_closing_parenthesis_in_call(self, lines: list[str]) -> list[str]:
        """Fix missing closing parenthesis in function calls."""
        fixed_lines = []

        for i, line in enumerate(lines):
            # Pattern: function call with opening parenthesis but no closing
            if re.match(r"^\s*\w+\s*=\s*\w+\([^)]+$", line):
                # Check if next line continues the call
                if i + 1 < len(lines) and ")" not in lines[i + 1]:
                    line = line.rstrip() + ")\n"
                    self.log(
                        f"  Added missing closing parenthesis to call at line {i + 1}"
                    )

            fixed_lines.append(line)

        return fixed_lines

    def fix_file(self, filepath: Path) -> bool:
        """Fix syntax errors in a single file."""
        try:
            # Read file
            with open(filepath, encoding="utf-8") as f:
                original_content = f.read()
                lines = original_content.splitlines(True)

            # Check if file has syntax errors
            try:
                ast.parse(original_content)
                return True  # No syntax errors
            except SyntaxError as e:
                self.log(f"\nProcessing {filepath}")
                self.log(f"  Error: {e.msg} at line {e.lineno}")

            # Create backup
            backup_path = self.backup_file(filepath)
            self.log(f"  Backup: {backup_path}")

            # Apply fixes based on specific file patterns
            fixed_lines = lines

            # Apply fixes in order
            fixed_lines = self.fix_misaligned_elif_else(fixed_lines)
            fixed_lines = self.fix_unmatched_parentheses(fixed_lines)
            fixed_lines = self.fix_incorrect_indentation_after_except(fixed_lines)
            fixed_lines = self.fix_missing_closing_parenthesis_in_call(fixed_lines)

            # Special fixes for specific files
            if filepath.name == "parser.py" and "analyzers" in str(filepath):
                # Fix the specific elif issue at line 46
                for i, line in enumerate(fixed_lines):
                    if i == 45 and line.strip().startswith("elif"):
                        # This elif should be if (no matching if before it)
                        fixed_lines[i] = line.replace("elif", "if", 1)
                        self.log(f"  Converted elif to if at line {i + 1}")

            elif filepath.name == "control.py" and "analysis" in str(filepath):
                # Fix missing closing parenthesis in FunctionBoundary call
                for i, line in enumerate(fixed_lines):
                    if "FunctionBoundary(" in line and ")" not in line:
                        # Look for the end of the call
                        j = i + 1
                        while j < len(fixed_lines) and ")" not in fixed_lines[j]:
                            j += 1
                        if j < len(fixed_lines):
                            fixed_lines[j] = fixed_lines[j].rstrip() + ")\n"
                            self.log(f"  Added closing parenthesis at line {j + 1}")

            elif filepath.name == "expression.py" and "reconstruction" in str(filepath):
                # Fix incorrect except indentation
                for i, line in enumerate(fixed_lines):
                    if i == 131 and "except" in line:
                        # This except is indented too far
                        fixed_lines[i] = line[4:]  # Remove 4 spaces
                        self.log(f"  Fixed except indentation at line {i + 1}")

            # Write fixed content
            fixed_content = "".join(fixed_lines)

            # Verify the fix
            try:
                ast.parse(fixed_content)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(fixed_content)
                self.log("  ✓ Successfully fixed!")
                self.fixed_files.append(filepath)
                return True
            except SyntaxError as e:
                self.log(f"  Still has errors: {e.msg} at line {e.lineno}")
                # Restore from backup
                shutil.copy2(backup_path, filepath)
                self.failed_files.append((filepath, f"{e.msg} at line {e.lineno}"))
                return False

        except Exception as e:
            self.log(f"  Error: {e}")
            self.failed_files.append((filepath, str(e)))
            return False

    def run(self):
        """Run the fixer on all files with syntax errors."""
        self.log("Scanning for Python files with syntax errors...")

        error_files = []
        for root, _dirs, files in os.walk("src"):
            for file in files:
                if file.endswith(".py"):
                    filepath = Path(root) / file
                    try:
                        with open(filepath, encoding="utf-8") as f:
                            ast.parse(f.read())
                    except SyntaxError:
                        error_files.append(filepath)
                    except:
                        pass

        self.log(f"Found {len(error_files)} files with syntax errors\n")

        # Process each file
        for filepath in error_files:
            self.fix_file(filepath)

        # Summary
        self.log("\n" + "=" * 60)
        self.log("SUMMARY")
        self.log("=" * 60)
        self.log(f"Successfully fixed: {len(self.fixed_files)} files")
        for f in self.fixed_files:
            self.log(f"  ✓ {f}")

        if self.failed_files:
            self.log(f"\nNeed manual fixes: {len(self.failed_files)} files")
            for f, error in self.failed_files:
                self.log(f"  ✗ {f}: {error}")

            self.log("\nManual fix suggestions:")
            self.log(
                "1. For 'unmatched )' errors: Look for incomplete function/class definitions"
            )
            self.log(
                "2. For 'invalid syntax' errors: Check for missing colons or commas"
            )
            self.log(
                "3. For 'unexpected indent' errors: Ensure consistent 4-space indentation"
            )
            self.log("4. Use 'python3 -m py_compile <file>' to verify fixes")

        self.log(f"\nBackups saved to: {self.backup_dir}")
        self.log(f"Log saved to: {self.log_file}")

        return len(self.fixed_files), len(self.failed_files)


def main() -> int:
    """Main entry point."""
    fixer = FinalSyntaxFixer()
    fixed, failed = fixer.run()

    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
