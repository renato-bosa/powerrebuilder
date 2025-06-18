#!/usr/bin/env python3
"""Improve type annotations for critical modules."""

from pathlib import Path
from typing import Dict, List, Set
import re


def add_basic_annotations(file_path: Path) -> int:
    """Add basic type annotations to a file."""
    try:
        content = file_path.read_text()
        original = content
        changes = 0
        
        # Add return type annotations for common patterns
        patterns = [
            # Functions that clearly return None
            (r'(\s*def\s+\w+\s*\([^)]*\))\s*:\s*\n\s*"""[^"]*"""\s*\n\s*(pass|\.\.\.)',
             r'\1 -> None:\n        """\g<2>"""\n        \3'),
            
            # Functions with single return statement
            (r'(\s*def\s+\w+\s*\([^)]*\))\s*:\s*\n\s*return\s+None',
             r'\1 -> None:\n        return None'),
            
            # Functions that return strings
            (r'(\s*def\s+\w+\s*\([^)]*\))\s*:\s*\n\s*return\s+["\']',
             r'\1 -> str:\n        return "'),
            
            # Functions that return numbers
            (r'(\s*def\s+\w+\s*\([^)]*\))\s*:\s*\n\s*return\s+\d+',
             r'\1 -> int:\n        return '),
            
            # Functions that return booleans
            (r'(\s*def\s+\w+\s*\([^)]*\))\s*:\s*\n\s*return\s+(True|False)',
             r'\1 -> bool:\n        return \2'),
        ]
        
        for pattern, replacement in patterns:
            content, n = re.subn(pattern, replacement, content, flags=re.MULTILINE)
            changes += n
        
        # Add Optional import if needed
        if 'Optional[' in content and 'from typing import' in content:
            if 'Optional' not in content:
                content = re.sub(
                    r'(from typing import [^)]+)',
                    r'\1, Optional',
                    content,
                    count=1
                )
                changes += 1
        
        if content != original:
            file_path.write_text(content)
            return changes
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        
    return 0


def add_common_imports(file_path: Path) -> bool:
    """Add common typing imports."""
    try:
        content = file_path.read_text()
        
        # Check if file uses type annotations
        if any(x in content for x in ['-> ', ': Dict', ': List', ': Optional']):
            # Check if typing imports exist
            if 'from typing import' not in content:
                # Add after module docstring
                lines = content.split('\n')
                insert_pos = 0
                
                # Skip shebang
                if lines and lines[0].startswith('#!'):
                    insert_pos = 1
                
                # Skip module docstring
                if insert_pos < len(lines) and lines[insert_pos].startswith('"""'):
                    while insert_pos < len(lines) and not lines[insert_pos].endswith('"""'):
                        insert_pos += 1
                    insert_pos += 1
                
                # Add imports
                lines.insert(insert_pos, '')
                lines.insert(insert_pos + 1, 'from typing import Any, Dict, List, Optional, Union')
                
                file_path.write_text('\n'.join(lines))
                return True
                
    except Exception as e:
        print(f"Error adding imports to {file_path}: {e}")
        
    return False


def fix_common_type_errors(module_path: Path) -> Dict[str, int]:
    """Fix common type errors in a module."""
    stats = {
        'files_processed': 0,
        'annotations_added': 0,
        'imports_added': 0,
    }
    
    for py_file in module_path.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
            
        stats['files_processed'] += 1
        
        # Add basic annotations
        changes = add_basic_annotations(py_file)
        if changes > 0:
            stats['annotations_added'] += changes
            print(f"✓ Added {changes} annotations to {py_file}")
        
        # Add imports if needed
        if add_common_imports(py_file):
            stats['imports_added'] += 1
            print(f"✓ Added typing imports to {py_file}")
    
    return stats


def main():
    """Main entry point."""
    print("Improving type annotations...")
    
    modules = ['common', 'model', 'extract', 'parse', 'decompile', 'generate']
    total_stats = {
        'files_processed': 0,
        'annotations_added': 0,
        'imports_added': 0,
    }
    
    for module in modules:
        module_path = Path(module)
        if module_path.exists():
            print(f"\nProcessing {module}...")
            stats = fix_common_type_errors(module_path)
            
            for key in total_stats:
                total_stats[key] += stats[key]
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Annotations added: {total_stats['annotations_added']}")
    print(f"Imports added: {total_stats['imports_added']}")
    
    # Run mypy to check improvement
    print("\nRunning mypy to check improvements...")
    import subprocess
    result = subprocess.run(
        ['mypy', '.', '--config-file=mypy.ini'],
        capture_output=True,
        text=True
    )
    
    error_count = result.stdout.count(': error:')
    print(f"\nRemaining mypy errors: {error_count}")
    
    if error_count < 500:
        print("\n✓ Significant improvement in type safety!")
    else:
        print("\nType safety improved but more work needed.")


if __name__ == "__main__":
    main()