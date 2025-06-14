#!/usr/bin/env python3
"""Script to consolidate grammar files in the parse/grammar directory."""

import shutil
import sys
from pathlib import Path


def main() -> None:
    """Execute grammar consolidation plan."""
    # Define paths
    grammar_dir = Path("parse/grammar")
    experimental_dir = grammar_dir / "experimental"

    if not grammar_dir.exists():
        sys.exit(1)

    # Step 1: Create experimental directory
    experimental_dir.mkdir(exist_ok=True)

    # Step 2: Move experimental grammars
    experimental_grammars = [
        "powerbuilder_fixed.lark",
        "powerbuilder_fixed_v2.lark",
        "powerbuilder_simple.lark",
        "powerbuilder_core.lark",
        "powerbuilder_js.lark",
    ]

    moved_count = 0
    for grammar in experimental_grammars:
        src = grammar_dir / grammar
        dst = experimental_dir / grammar
        if src.exists():
            shutil.move(str(src), str(dst))
            moved_count += 1
        else:
            pass

    # Step 3: Create README in experimental directory
    readme_content = """# Experimental Grammars

This directory contains experimental and test grammar files that are not used in production.

## Files
- **powerbuilder_fixed.lark** - Experimental fixes for reduce/reduce conflicts
- **powerbuilder_fixed_v2.lark** - Second iteration of conflict fixes
- **powerbuilder_simple.lark** - Simplified grammar for testing
- **powerbuilder_core.lark** - Core rules extracted for testing
- **powerbuilder_js.lark** - JavaScript-style PowerBuilder grammar experiment

## Note
These grammars are kept for reference and testing purposes. The main production grammars are in the parent directory.
"""

    readme_path = experimental_dir / "README.md"
    readme_path.write_text(readme_content)

    # Step 4: Update test files that reference moved grammars
    test_updates = [
        (
            "test_fixed_grammar.py",
            'grammar_path = Path("parse/grammar/powerbuilder_fixed_v2.lark")',
            'grammar_path = Path("parse/grammar/experimental/powerbuilder_fixed_v2.lark")',
        ),
        (
            "test_simple_parser.py",
            'grammar_path = Path("parse/grammar/powerbuilder_simple.lark")',
            'grammar_path = Path("parse/grammar/experimental/powerbuilder_simple.lark")',
        ),
        (
            "tests/test_parse/test_pb_js_transformer.py",
            'with open("parse/grammar/powerbuilder_js.lark"',
            'with open("parse/grammar/experimental/powerbuilder_js.lark"',
        ),
    ]

    updated_count = 0
    for file_path, old_line, new_line in test_updates:
        file = Path(file_path)
        if file.exists():
            content = file.read_text()
            if old_line in content:
                new_content = content.replace(old_line, new_line)
                file.write_text(new_content)
                updated_count += 1
            else:
                pass
        else:
            pass

    # Step 5: Report on remaining grammars
    production_grammars = [
        "powerbuilder.lark",
        "datawindow.lark",
        "sql.lark",
        "pseudocode.lark",
        "common_grammar.lark",  # Will be addressed in next phase
    ]

    for grammar in production_grammars:
        if (grammar_dir / grammar).exists():
            pass

    # Step 6: Next steps


if __name__ == "__main__":
    main()
