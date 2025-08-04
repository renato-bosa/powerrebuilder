#!/usr/bin/env python3
"""Fix common type errors automatically."""

import re
import subprocess
from pathlib import Path

def fix_missing_imports(filepath):
    """Fix missing typing imports."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find what typing imports we need
    needs_imports = set()
    
    # Check for missing imports
    if 'TypeVar' in content and 'from typing import' not in content:
        needs_imports.add('TypeVar')
    if 'Protocol' in content and 'from typing import' not in content:
        needs_imports.add('Protocol')
    if 'Optional' in content and 'Optional' not in content:
        needs_imports.add('Optional')
    if 'Generic' in content and 'from typing import' not in content:
        needs_imports.add('Generic')
    if 'Any' in content and 'from typing import' not in content:
        needs_imports.add('Any')
    if 'List' in content and 'from typing import' not in content:
        needs_imports.add('List')
    if 'Dict' in content and 'from typing import' not in content:
        needs_imports.add('Dict')
    if 'Tuple' in content and 'from typing import' not in content:
        needs_imports.add('Tuple')
    if 'Union' in content and 'from typing import' not in content:
        needs_imports.add('Union')
    
    if not needs_imports:
        return False
    
    # Find where to insert imports
    import_line = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            import_line = i
    
    # Build import line
    if import_line >= 0:
        # Check if there's already a typing import
        typing_import_idx = -1
        for i, line in enumerate(lines):
            if 'from typing import' in line:
                typing_import_idx = i
                break
        
        if typing_import_idx >= 0:
            # Add to existing import
            existing_imports = re.findall(r'from typing import (.+)', lines[typing_import_idx])[0]
            existing_items = [item.strip() for item in existing_imports.split(',')]
            all_items = sorted(set(existing_items) | needs_imports)
            lines[typing_import_idx] = f"from typing import {', '.join(all_items)}"
        else:
            # Add new import
            lines.insert(import_line + 1, f"from typing import {', '.join(sorted(needs_imports))}")
    
    # Write back
    with open(filepath, 'w') as f:
        f.write('\n'.join(lines))
    
    return True

def add_return_none(filepath):
    """Add 'return None' to functions with missing return statements."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    modified = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a function definition
        if re.match(r'^\s*def\s+\w+.*:$', line):
            indent = len(line) - len(line.lstrip())
            func_indent = ' ' * (indent + 4)
            
            # Look for the function body
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].startswith(func_indent)):
                j += 1
            
            # Check if the last line is pass or ...
            last_line_idx = j - 1
            while last_line_idx > i and not lines[last_line_idx].strip():
                last_line_idx -= 1
            
            if last_line_idx > i:
                last_line = lines[last_line_idx].strip()
                if last_line in ('pass', '...'):
                    lines[last_line_idx] = func_indent + 'return None'
                    modified = True
        
        i += 1
    
    if modified:
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
    
    return modified

def fix_protocol_class(filepath):
    """Fix Protocol class definitions."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace runtime_checkable import if needed
    if '@runtime_checkable' in content and 'runtime_checkable' not in content:
        content = re.sub(
            r'from typing import (.+)',
            lambda m: f"from typing import {m.group(1)}, runtime_checkable",
            content,
            count=1
        )
    
    # Fix Protocol inheritance
    content = re.sub(
        r'class (\w+)\(Protocol\):',
        r'class \1(Protocol):',
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Fix type errors in all files."""
    # Get all Python files
    files_to_fix = []
    
    # Run mypy to find files with errors
    result = subprocess.run(
        ['mypy', 'src', '--ignore-missing-imports', '--no-error-summary'],
        capture_output=True,
        text=True
    )
    
    # Parse mypy output
    for line in result.stdout.split('\n'):
        if ':' in line and 'error:' in line:
            filepath = line.split(':')[0]
            if filepath not in files_to_fix:
                files_to_fix.append(filepath)
    
    print(f"Found {len(files_to_fix)} files with type errors")
    
    fixed_count = 0
    for filepath in files_to_fix[:20]:  # Fix first 20 files
        if Path(filepath).exists():
            changed = False
            
            # Fix missing imports
            if fix_missing_imports(filepath):
                changed = True
            
            # Fix missing returns
            if add_return_none(filepath):
                changed = True
            
            # Fix protocol classes
            if fix_protocol_class(filepath):
                changed = True
            
            if changed:
                fixed_count += 1
                print(f"Fixed {filepath}")
    
    print(f"\nFixed {fixed_count} files")
    
    # Re-run mypy to check remaining errors
    result = subprocess.run(
        ['mypy', 'src', '--ignore-missing-imports', '--no-error-summary'],
        capture_output=True,
        text=True
    )
    
    remaining = len([line for line in result.stdout.split('\n') if 'error:' in line])
    print(f"Remaining type errors: {remaining}")

if __name__ == "__main__":
    main()