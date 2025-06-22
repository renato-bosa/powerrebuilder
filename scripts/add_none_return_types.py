#!/usr/bin/env python3
"""Add -> None return type annotations to methods that clearly return None."""

import re
import sys
from pathlib import Path


def add_none_return_type(content: str) -> tuple[str, bool]:

    """Add -> None return type annotations where missing."""
    lines = content.split("\n")
    modified_lines = []
    changed = False

    for i, line in enumerate(lines):
        # Match function/method definitions without return type
        # Look for patterns like "def method_name(...):"
        match = re.match(r"^(\s*def\s+\w+\s*\([^)]*\))\s*:\s*$", line)

        if match:
            # Check if it already has a return type
            if "->" not in line:
                # Get the method name for analysis
                method_match = re.search(r"def\s+(\w+)\s*\(", line)
                if method_match:
                    method_name = method_match.group(1)

                    # Methods that typically return None
                    none_patterns = [
                        "__init__", "__del__", 
                        "set_", "add_", "remove_", "clear_", "update_", "delete_",
                        "write_", "save_", "load_", "close_", "open_", "reset_",
                        "register_", "unregister_", "enable_", "disable_",
                        "start_", "stop_", "pause_", "resume_",
                        "push_", "pop_", "append_", "extend_",
                        "__post_init__", "setup", "teardown",
                        "visit_", "enter_", "exit_",  # visitor pattern methods
                        "handle_", "process_",  # handler methods
                        "on_",  # event handlers
                        "init_", "cleanup_", "dispose_",
                        "parse_", "analyze_", "validate_",  # often void
                        "log_", "debug_", "info_", "warn_", "error_",
                        "output_", "print_", "display_", "show_",
                        "__enter__", "__exit__",
                        "increase_", "decrease_",
                        "emit_", "trigger_", "fire_",
                    ]

                    # Check if method name matches any pattern
                    should_add_none = False
                    for pattern in none_patterns:
                        if method_name == pattern or method_name.startswith(pattern):
                            should_add_none = True
                            break

                    # Also check the method body for explicit return patterns
                    if not should_add_none and i + 1 < len(lines):
                        # Look ahead in the method body for return statements
                        body_has_return_value = False
                        j = i + 1
                        base_indent = len(match.group(1)) - len(match.group(1).lstrip())

                        while j < len(lines) and j < i + 50:  # Check up to 50 lines
                            body_line = lines[j]
                            body_indent = len(body_line) - len(body_line.lstrip())

                            # If we've dedented back to or past the method level, stop
                            if body_line.strip() and body_indent <= base_indent:
                                break

                            # Check for return statements with values
                            if re.match(r"^\s*return\s+\S", body_line):
                                body_has_return_value = True
                                break
                            # Check for bare return
                            elif re.match(r"^\s*return\s*$", body_line):
                                # Bare return suggests -> None
                                should_add_none = True
                                break

                            j += 1

                        # If no return with value found, it likely returns None
                        if not body_has_return_value and not should_add_none:
                            should_add_none = True

                    if should_add_none:
                        # Add -> None before the colon
                        new_line = match.group(1) + " -> None:"
                        modified_lines.append(new_line)
                        changed = True
                        continue

        modified_lines.append(line)

    return "\n".join(modified_lines), changed


def process_file(file_path: Path) -> bool:

    """Process a single Python file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        updated_content, was_changed = add_none_return_type(content)

        if was_changed:
            file_path.write_text(updated_content, encoding="utf-8")
            print(f"✓ Updated: {file_path.relative_to(Path.cwd())}")
            return True
        else:
            return False

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def main():
    """Main function to process all Python files."""
    root = Path(__file__).parent.parent

    # Find all Python files
    python_files = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov", "tests"}

    for py_file in root.rglob("*.py"):
        # Skip excluded directories and test files
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        if "test_" in py_file.name or "_test.py" in py_file.name:
            continue
        python_files.append(py_file)

    print(f"Found {len(python_files)} Python files to check")

    updated_count = 0
    for file_path in python_files:
        if process_file(file_path):
            updated_count += 1

    print(f"\nCompleted! Updated {updated_count} files.")

    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)
