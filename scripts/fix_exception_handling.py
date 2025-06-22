#!/usr/bin/env python3
"""Fix exception handling patterns - replace bare except and add proper logging."""

import re
import sys
from pathlib import Path


def needs_logger_import(content: str) -> bool:
    """Check if file already has logger import."""
    return 'logger = logging.getLogger(__name__)' not in content


def add_logger_imports(content: str) -> str:
    """Add logging imports if not present."""
    if 'import logging' not in content:
        # Find the right place to add import
        lines = content.split('\n')
        import_line = -1
        
        # Find existing imports
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_line = i
            elif import_line >= 0 and line and not line.startswith((' ', '\t', 'import', 'from')):
                # Found the end of imports
                break
        
        if import_line >= 0:
            # Add after last import
            lines.insert(import_line + 1, 'import logging')
        else:
            # Add after module docstring
            docstring_end = -1
            in_docstring = False
            for i, line in enumerate(lines):
                if line.strip().startswith('"""'):
                    if not in_docstring:
                        in_docstring = True
                    else:
                        docstring_end = i
                        break
            
            if docstring_end >= 0:
                lines.insert(docstring_end + 1, '\nimport logging')
            else:
                lines.insert(0, 'import logging')
        
        content = '\n'.join(lines)
    
    # Add logger declaration after imports if needed
    if needs_logger_import(content):
        lines = content.split('\n')
        
        # Find where to add logger
        import_section_end = -1
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_section_end = i
            elif import_section_end >= 0 and line and not line.startswith((' ', '\t', 'import', 'from')):
                break
        
        if import_section_end >= 0:
            # Add logger after imports
            insert_pos = import_section_end + 1
            while insert_pos < len(lines) and not lines[insert_pos].strip():
                insert_pos += 1
            
            lines.insert(insert_pos, '\nlogger = logging.getLogger(__name__)\n')
            content = '\n'.join(lines)
    
    return content


def fix_bare_except_patterns(content: str) -> tuple[str, bool]:
    """Fix bare except clauses and add logging.
    
    Returns:
        Tuple of (updated_content, was_changed)
    """
    original = content
    lines = content.split('\n')
    fixed_lines = []
    changed = False
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check for bare except
        if stripped == 'except:':
            indent = len(line) - len(line.lstrip())
            # Replace with except Exception:
            fixed_lines.append(' ' * indent + 'except Exception as e:')
            changed = True
            i += 1
            
            # Check what follows the except
            if i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                if next_stripped == 'pass':
                    # Replace pass with logging
                    next_indent = len(next_line) - len(next_line.lstrip())
                    fixed_lines.append(' ' * next_indent + 'logger.debug("Exception caught: %s", e)')
                    changed = True
                    i += 1
                elif next_stripped.startswith('pass  #') or next_stripped.startswith('pass #'):
                    # Replace pass with comment with logging
                    comment = next_stripped[4:].strip()
                    next_indent = len(next_line) - len(next_line.lstrip())
                    fixed_lines.append(' ' * next_indent + f'logger.debug("Exception caught: %s", e)  {comment}')
                    changed = True
                    i += 1
                else:
                    # Just continue with existing code
                    pass
        
        # Check for except Exception: followed by pass
        elif stripped == 'except Exception:' or re.match(r'^except\s+Exception\s*:\s*$', stripped):
            fixed_lines.append(line)
            i += 1
            
            # Check if followed by pass
            if i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                if next_stripped == 'pass':
                    # Add logging before pass
                    next_indent = len(next_line) - len(next_line.lstrip())
                    fixed_lines.append(' ' * next_indent + 'logger.debug("Generic exception caught")')
                    fixed_lines.append(next_line)
                    changed = True
                    i += 1
        
        # Check for except Exception as e: followed by pass
        elif re.match(r'^except\s+Exception\s+as\s+\w+\s*:\s*$', stripped):
            indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            i += 1
            
            # Extract variable name
            match = re.match(r'^except\s+Exception\s+as\s+(\w+)\s*:\s*$', stripped)
            var_name = match.group(1) if match else 'e'
            
            # Check if followed by pass
            if i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                if next_stripped == 'pass':
                    # Replace pass with logging
                    next_indent = len(next_line) - len(next_line.lstrip())
                    fixed_lines.append(' ' * next_indent + f'logger.debug("Exception caught: %s", {var_name})')
                    changed = True
                    i += 1
                elif next_stripped.startswith('# ') or not next_stripped:
                    # Empty or comment - add logging
                    next_indent = indent + 4
                    fixed_lines.append(' ' * next_indent + f'logger.debug("Exception caught: %s", {var_name})')
                    fixed_lines.append(next_line)
                    changed = True
                    i += 1
        else:
            fixed_lines.append(line)
            i += 1
    
    content = '\n'.join(fixed_lines)
    
    # Add logging imports if we made changes
    if changed and 'logger' in content:
        content = add_logger_imports(content)
    
    return content, content != original


def process_file(file_path: Path) -> bool:
    """Process a single Python file.
    
    Returns:
        True if file was updated, False otherwise.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        updated_content, was_changed = fix_bare_except_patterns(content)
        
        if was_changed:
            file_path.write_text(updated_content, encoding='utf-8')
            print(f"✓ Fixed: {file_path.relative_to(Path.cwd())}")
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
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist', '.eggs', 'htmlcov', 'tests'}
    
    for py_file in root.rglob("*.py"):
        # Skip excluded directories and test files
        if any(part in exclude_dirs for part in py_file.parts):
            continue
        if 'test_' in py_file.name or '_test.py' in py_file.name:
            continue
        python_files.append(py_file)
    
    print(f"Found {len(python_files)} Python files to check")
    
    updated_count = 0
    for file_path in python_files:
        if process_file(file_path):
            updated_count += 1
    
    print(f"\nCompleted! Fixed {updated_count} files.")
    
    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)