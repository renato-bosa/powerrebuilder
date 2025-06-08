#!/usr/bin/env python3
"""Script to consolidate grammar files in the parse/grammar directory."""

import shutil
from pathlib import Path
import sys

def main():
    """Execute grammar consolidation plan."""
    
    # Define paths
    grammar_dir = Path("parse/grammar")
    experimental_dir = grammar_dir / "experimental"
    
    if not grammar_dir.exists():
        print(f"Error: Grammar directory '{grammar_dir}' not found!")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    print("Grammar Consolidation Script")
    print("=" * 50)
    
    # Step 1: Create experimental directory
    print("\n1. Creating experimental directory...")
    experimental_dir.mkdir(exist_ok=True)
    print(f"   ✓ Created {experimental_dir}")
    
    # Step 2: Move experimental grammars
    experimental_grammars = [
        "powerbuilder_fixed.lark",
        "powerbuilder_fixed_v2.lark", 
        "powerbuilder_simple.lark",
        "powerbuilder_core.lark",
        "powerbuilder_js.lark"
    ]
    
    print("\n2. Moving experimental grammars...")
    moved_count = 0
    for grammar in experimental_grammars:
        src = grammar_dir / grammar
        dst = experimental_dir / grammar
        if src.exists():
            shutil.move(str(src), str(dst))
            print(f"   ✓ Moved {grammar}")
            moved_count += 1
        else:
            print(f"   ⚠ {grammar} not found, skipping")
    
    print(f"   Moved {moved_count} experimental grammars")
    
    # Step 3: Create README in experimental directory
    print("\n3. Creating README in experimental directory...")
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
    print(f"   ✓ Created {readme_path}")
    
    # Step 4: Update test files that reference moved grammars
    print("\n4. Updating test files...")
    test_updates = [
        ("test_fixed_grammar.py", 
         'grammar_path = Path("parse/grammar/powerbuilder_fixed_v2.lark")',
         'grammar_path = Path("parse/grammar/experimental/powerbuilder_fixed_v2.lark")'),
        
        ("test_simple_parser.py",
         'grammar_path = Path("parse/grammar/powerbuilder_simple.lark")',
         'grammar_path = Path("parse/grammar/experimental/powerbuilder_simple.lark")'),
        
        ("tests/test_parse/test_pb_js_transformer.py",
         'with open("parse/grammar/powerbuilder_js.lark"',
         'with open("parse/grammar/experimental/powerbuilder_js.lark"'),
    ]
    
    updated_count = 0
    for file_path, old_line, new_line in test_updates:
        file = Path(file_path)
        if file.exists():
            content = file.read_text()
            if old_line in content:
                new_content = content.replace(old_line, new_line)
                file.write_text(new_content)
                print(f"   ✓ Updated {file_path}")
                updated_count += 1
            else:
                print(f"   ⚠ Pattern not found in {file_path}")
        else:
            print(f"   ⚠ File {file_path} not found")
    
    print(f"   Updated {updated_count} test files")
    
    # Step 5: Report on remaining grammars
    print("\n5. Production grammars remaining:")
    production_grammars = [
        "powerbuilder.lark",
        "datawindow.lark", 
        "sql.lark",
        "pseudocode.lark",
        "common_grammar.lark"  # Will be addressed in next phase
    ]
    
    for grammar in production_grammars:
        if (grammar_dir / grammar).exists():
            print(f"   ✓ {grammar}")
    
    # Step 6: Next steps
    print("\n" + "=" * 50)
    print("Consolidation Phase 1 Complete!")
    print("\nNext steps:")
    print("1. Run tests to ensure everything still works")
    print("2. Review common_grammar.lark for potential removal")
    print("3. Update parse_coordinator.py to use GrammarManager")
    print("4. Fix datawindow.lark imports")
    print("\nRun: pytest tests/test_parse/ -v")

if __name__ == "__main__":
    main()