#!/usr/bin/env python3
"""Safely fix quote consistency using Python's tokenizer."""

import ast
import io
import token
import tokenize
from pathlib import Path


def fix_quotes_safe(file_path: Path) -> bool:

    """Safely convert single quotes to double quotes using tokenizer."""
    try:
        with open(file_path, "rb") as f:
            original_bytes = f.read()

        # Decode to text
        try:
            original_text = original_bytes.decode("utf-8")
        except UnicodeDecodeError:
            print(f"⚠️  Unable to decode {file_path}, skipping")
            return False

        # Verify original file parses correctly
        try:
            ast.parse(original_text)
        except SyntaxError:
            print(f"⚠️  Syntax error in {file_path}, skipping")
            return False

        # Tokenize the file
        tokens = []
        try:
            with io.StringIO(original_text) as f:
                tokens = list(tokenize.generate_tokens(f.readline))
        except tokenize.TokenError:
            print(f"⚠️  Tokenization error in {file_path}, skipping")
            return False

        # Build new content by replacing string tokens
        result_lines = original_text.split("\n")
        changes_made = False

        for tok in tokens:
            if tok.type == token.STRING:
                start_line, start_col = tok.start
                end_line, end_col = tok.end

                # Get the token string
                token_string = tok.string

                # Only process single-quoted strings (not already double-quoted)
                if token_string.startswith(("'", "r'", "u'", "f'", "rf'", "fr'")):
                    # Skip triple quotes for now (more complex)
                    if token_string.startswith(("'''", 'r"""', 'u"""', 'f"""')):
                        continue

                    # Check if the string contains double quotes
                    string_content = get_string_content(token_string)
                    if '"' in string_content:
                        # Skip strings that contain double quotes to avoid conflicts
                        continue

                    # Convert to double quotes
                    new_token = convert_to_double_quotes(token_string)
                    if new_token != token_string:
                        # Replace in the source
                        line_idx = start_line - 1  # 0-based
                        if line_idx < len(result_lines):
                            line = result_lines[line_idx]
                            # Replace the token in the line
                            new_line = line[:start_col] + new_token + line[end_col:]
                            result_lines[line_idx] = new_line
                            changes_made = True

        if not changes_made:
            return False

        # Join back into text
        new_content = "\n".join(result_lines)

        # Verify the result still parses
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            print(f"✗ Conversion broke syntax in {file_path}: {e}")
            return False

        # Write the result
        file_path.write_text(new_content, encoding="utf-8")
        return True

    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False


def get_string_content(token_string: str) -> str:

    """Extract the actual string content from a token."""
    # Remove prefixes and quotes
    if token_string.startswith(('r"', "r'")):
        return token_string[2:-1]
    elif token_string.startswith(('f"', "f'", 'u"', "u'")):
        return token_string[2:-1]
    elif token_string.startswith(('rf"', "rf'", 'fr"', "fr'")):
        return token_string[3:-1]
    else:
        return token_string[1:-1]


def convert_to_double_quotes(token_string: str) -> str:

    """Convert a single-quoted string token to double quotes."""
    if token_string.startswith("r'"):
        return f'r"{get_string_content(token_string)}"'
    elif token_string.startswith("f'"):
        return f'f"{get_string_content(token_string)}"'
    elif token_string.startswith("u'"):
        return f'u"{get_string_content(token_string)}"'
    elif token_string.startswith("rf'"):
        return f'rf"{get_string_content(token_string)}"'
    elif token_string.startswith("fr'"):
        return f'fr"{get_string_content(token_string)}"'
    elif token_string.startswith("'"):
        return f'"{get_string_content(token_string)}"'

    return token_string


def main():
    """Fix quotes in all Python files."""
    root = Path(__file__).parent.parent

    # Find all Python files
    python_files = []
    exclude_dirs = {".venv", "venv", "__pycache__", ".git", "build", "dist", ".eggs", "htmlcov", "tests", "reference", "scripts"}

    for py_file in root.rglob("*.py"):
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        python_files.append(py_file)

    print(f"Processing {len(python_files)} Python files...")

    updated_count = 0
    for file_path in python_files:
        if fix_quotes_safe(file_path):
            print(f"✓ Fixed quotes in: {file_path.relative_to(root)}")
            updated_count += 1

    print(f"\n✓ Fixed quotes in {updated_count} files")
    return updated_count


if __name__ == "__main__":
    main()
