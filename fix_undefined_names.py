#!/usr/bin/env python3
"""Fix undefined names (F821 errors) in the codebase."""

import os
import re
import subprocess
from pathlib import Path

# Map of undefined names to their proper imports
IMPORT_FIXES = {
    # Expression classes
    "PBBinaryOperator": "from src.model.ast.nodes.expressions import BinaryOperator as PBBinaryOperator",
    "PBUnaryOperator": "from src.model.ast.nodes.expressions import UnaryOperator as PBUnaryOperator",
    "PBConcatenationOperator": "from src.model.ast.nodes.expressions import ConcatenationOperator as PBConcatenationOperator",
    "PBPowerOperator": "from src.model.ast.nodes.expressions import PowerOperator as PBPowerOperator",
    "PBTernaryExpression": "from src.model.ast.nodes.expressions import TernaryExpression as PBTernaryExpression",
    "PBBooleanLiteral": "from src.model.ast.nodes.literals import BooleanLiteral as PBBooleanLiteral",
    "PBNumberLiteral": "from src.model.ast.nodes.literals import NumberLiteral as PBNumberLiteral",
    "PBStringLiteral": "from src.model.ast.nodes.literals import StringLiteral as PBStringLiteral",
    "PBNullLiteral": "from src.model.ast.nodes.literals import NullLiteral as PBNullLiteral",
    "PBVariable": "from src.model.ast.nodes.variables import Variable as PBVariable",
    
    # Missing logger imports
    "logger": "logger = logging.getLogger(__name__)",
    
    # Factory imports
    "ExtractCoordinatorFactory": "from src.extract.factory import ExtractCoordinatorFactory",
    "create_extract_coordinator": "from src.extract.factory import create_extract_coordinator",
    
    # Magic numbers
    "MagicNumbers": "from src.extract.utils.encoding import MagicNumbers",
    
    # SQL transformer
    "Expression": "from src.model.ast.nodes.base import Expression",
}

def get_undefined_names():
    """Get all F821 errors from ruff."""
    result = subprocess.run(
        ["ruff", "check", "src", "--select", "F821"],
        capture_output=True,
        text=True
    )
    
    errors = []
    for line in result.stdout.strip().split('\n'):
        # Parse error line
        match = re.match(r'(.*?):(\d+):(\d+): F821 Undefined name `([^`]+)`', line)
        if match:
            errors.append({
                'file': match.group(1),
                'line': int(match.group(2)),
                'col': int(match.group(3)),
                'name': match.group(4)
            })
    
    return errors

def fix_file(filepath, undefined_names):
    """Fix undefined names in a single file."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Group undefined names by type
    names_to_import = set()
    needs_logging = False
    
    for error in undefined_names:
        name = error['name']
        if name in IMPORT_FIXES:
            if name == 'logger':
                needs_logging = True
            else:
                names_to_import.add(IMPORT_FIXES[name])
    
    if not names_to_import and not needs_logging:
        return False
    
    # Find where to insert imports (after existing imports)
    import_end = 0
    in_docstring = False
    docstring_delim = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Handle docstrings
        if i < 10 and (stripped.startswith('"""') or stripped.startswith("'''")):
            if not in_docstring:
                in_docstring = True
                docstring_delim = '"""' if stripped.startswith('"""') else "'''"
                if stripped.count(docstring_delim) == 2:  # Single line docstring
                    in_docstring = False
            elif docstring_delim in stripped:
                in_docstring = False
            continue
            
        if in_docstring:
            continue
            
        # Track imports
        if stripped.startswith(('import ', 'from ')) and not in_docstring:
            import_end = i + 1
        elif import_end > 0 and stripped and not stripped.startswith(('import ', 'from ')):
            break
    
    # Insert missing imports
    if names_to_import or needs_logging:
        new_lines = lines[:import_end]
        
        # Add logging import if needed
        if needs_logging and not any('import logging' in line for line in lines):
            new_lines.append('import logging\n')
            
        # Add missing imports
        for imp in sorted(names_to_import):
            if imp not in ''.join(lines):
                new_lines.append(imp + '\n')
        
        # Add blank line if we added imports
        if len(new_lines) > import_end:
            new_lines.append('\n')
            
        # Add logger definition if needed
        if needs_logging and not any('logger =' in line for line in lines):
            new_lines.append('logger = logging.getLogger(__name__)\n')
            new_lines.append('\n')
        
        # Add rest of file
        new_lines.extend(lines[import_end:])
        
        # Write back
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
        
        return True
    
    return False

def main():
    """Fix all undefined names."""
    errors = get_undefined_names()
    
    # Group errors by file
    errors_by_file = {}
    for error in errors:
        if error['file'] not in errors_by_file:
            errors_by_file[error['file']] = []
        errors_by_file[error['file']].append(error)
    
    print(f"Found {len(errors)} undefined names in {len(errors_by_file)} files")
    
    fixed = 0
    for filepath, file_errors in errors_by_file.items():
        if fix_file(filepath, file_errors):
            fixed += 1
            print(f"Fixed {filepath}")
    
    print(f"\nFixed {fixed} files")
    
    # Re-check for remaining errors
    remaining = get_undefined_names()
    print(f"Remaining undefined names: {len(remaining)}")

if __name__ == "__main__":
    main()