#!/usr/bin/env python3
"""Add minimal docstrings to methods that are missing them."""

import ast
import re
import sys
from pathlib import Path


def generate_docstring(method_name: str, params: list[str], return_type: str | None = None) -> str:
    """Generate a minimal docstring based on method name and parameters."""
    # Generate summary based on method name
    summary = generate_summary(method_name)
    
    # Build docstring parts
    docstring_parts = [f'"""{summary}']
    
    # Add parameter documentation if there are non-self params
    non_self_params = [p for p in params if p != 'self']
    if non_self_params:
        docstring_parts.append('')
        docstring_parts.append('Args:')
        for param in non_self_params:
            docstring_parts.append(f'    {param}: TODO: Add description')
    
    # Add return documentation if return type is specified and not None
    if return_type and return_type != 'None':
        docstring_parts.append('')
        docstring_parts.append('Returns:')
        docstring_parts.append(f'    TODO: Add return description')
    
    docstring_parts.append('"""')
    
    return '\n'.join(docstring_parts)


def generate_summary(method_name: str) -> str:
    """Generate a method summary from its name."""
    # Remove common prefixes
    name = method_name
    for prefix in ['get_', 'set_', 'is_', 'has_', 'can_', 'should_', 'add_', 'remove_', 'update_', 'delete_']:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    
    # Convert snake_case to words
    words = name.split('_')
    
    # Generate summary based on method pattern
    method_lower = method_name.lower()
    
    if method_lower.startswith('get_'):
        return f"Get {' '.join(words)}."
    elif method_lower.startswith('set_'):
        return f"Set {' '.join(words)}."
    elif method_lower.startswith('is_'):
        return f"Check if {' '.join(words)}."
    elif method_lower.startswith('has_'):
        return f"Check if has {' '.join(words)}."
    elif method_lower.startswith('can_'):
        return f"Check if can {' '.join(words)}."
    elif method_lower.startswith('add_'):
        return f"Add {' '.join(words)}."
    elif method_lower.startswith('remove_'):
        return f"Remove {' '.join(words)}."
    elif method_lower.startswith('update_'):
        return f"Update {' '.join(words)}."
    elif method_lower.startswith('delete_'):
        return f"Delete {' '.join(words)}."
    elif method_lower.startswith('create_'):
        return f"Create {' '.join(words)}."
    elif method_lower.startswith('build_'):
        return f"Build {' '.join(words)}."
    elif method_lower.startswith('parse_'):
        return f"Parse {' '.join(words)}."
    elif method_lower.startswith('process_'):
        return f"Process {' '.join(words)}."
    elif method_lower.startswith('handle_'):
        return f"Handle {' '.join(words)}."
    elif method_lower.startswith('validate_'):
        return f"Validate {' '.join(words)}."
    elif method_lower.startswith('convert_'):
        return f"Convert {' '.join(words)}."
    elif method_lower.startswith('transform_'):
        return f"Transform {' '.join(words)}."
    elif method_lower.startswith('extract_'):
        return f"Extract {' '.join(words)}."
    elif method_lower.startswith('find_'):
        return f"Find {' '.join(words)}."
    elif method_lower.startswith('search_'):
        return f"Search for {' '.join(words)}."
    elif method_lower.startswith('load_'):
        return f"Load {' '.join(words)}."
    elif method_lower.startswith('save_'):
        return f"Save {' '.join(words)}."
    elif method_lower.startswith('read_'):
        return f"Read {' '.join(words)}."
    elif method_lower.startswith('write_'):
        return f"Write {' '.join(words)}."
    elif method_lower == '__str__':
        return "Return string representation."
    elif method_lower == '__repr__':
        return "Return detailed string representation."
    elif method_lower == '__len__':
        return "Return length."
    elif method_lower == '__bool__':
        return "Return boolean value."
    elif method_lower == '__enter__':
        return "Enter context manager."
    elif method_lower == '__exit__':
        return "Exit context manager."
    elif method_lower == '__iter__':
        return "Return iterator."
    elif method_lower == '__next__':
        return "Return next item."
    elif method_lower == '__call__':
        return "Call instance as function."
    elif method_lower == '__eq__':
        return "Check equality."
    elif method_lower == '__lt__':
        return "Check less than."
    elif method_lower == '__gt__':
        return "Check greater than."
    elif method_lower == '__hash__':
        return "Return hash value."
    elif method_lower == '__getitem__':
        return "Get item by key."
    elif method_lower == '__setitem__':
        return "Set item by key."
    elif method_lower == '__delitem__':
        return "Delete item by key."
    elif method_lower == '__contains__':
        return "Check if contains item."
    else:
        # Default: capitalize first letter and join words
        return f"{method_name.replace('_', ' ').capitalize()}."


def add_docstrings(content: str) -> tuple[str, bool]:
    """Add docstrings to methods that are missing them."""
    try:
        tree = ast.parse(content)
    except:
        return content, False
        
    lines = content.split('\n')
    modified = False
    
    # Track methods to update (store in reverse order to avoid offset issues)
    updates = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Skip private methods and already documented methods
            if node.name.startswith('_') and not node.name.startswith('__'):
                continue
                
            # Check if already has docstring
            has_docstring = (
                node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)
            )
            
            if has_docstring:
                continue
                
            # Get parameters
            params = [arg.arg for arg in node.args.args]
            
            # Get return type if available
            return_type = None
            if node.returns:
                if isinstance(node.returns, ast.Name):
                    return_type = node.returns.id
                elif isinstance(node.returns, ast.Constant):
                    return_type = str(node.returns.value)
                # Handle more complex return types simply
                else:
                    return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else None
            
            # Generate docstring
            docstring = generate_docstring(node.name, params, return_type)
            
            # Find the line after the function definition
            func_line = node.lineno - 1  # ast uses 1-based indexing
            
            # Find the actual end of the function definition (handling multi-line defs)
            colon_line = func_line
            while colon_line < len(lines) and not lines[colon_line].rstrip().endswith(':'):
                colon_line += 1
                
            if colon_line < len(lines):
                # Get the indentation of the function body
                body_indent = None
                for i in range(colon_line + 1, len(lines)):
                    line = lines[i]
                    if line.strip():  # Non-empty line
                        body_indent = len(line) - len(line.lstrip())
                        break
                
                if body_indent is None:
                    # Empty function, use function indent + 4
                    func_indent = len(lines[func_line]) - len(lines[func_line].lstrip())
                    body_indent = func_indent + 4
                
                # Add the docstring with proper indentation
                indent = ' ' * body_indent
                docstring_lines = docstring.split('\n')
                indented_docstring = [indent + line if line else '' for line in docstring_lines]
                
                updates.append((colon_line + 1, indented_docstring))
    
    # Apply updates in reverse order to maintain line numbers
    for insert_line, docstring_lines in reversed(updates):
        lines[insert_line:insert_line] = docstring_lines
        modified = True
        
    return '\n'.join(lines), modified


def process_file(file_path: Path) -> bool:
    """Process a single Python file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        updated_content, was_changed = add_docstrings(content)
        
        if was_changed:
            file_path.write_text(updated_content, encoding='utf-8')
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
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist', '.eggs', 'htmlcov', 'tests', 'reference'}
    
    # Focus on specific high-priority files first
    priority_patterns = [
        'model/ast/additional_nodes.py',
        'model/ast/types.py',
        'model/base/pb_behavioral.py',
        'parse/powerbuilder_transformer.py',
        'benchmarks/*.py',
    ]
    
    for pattern in priority_patterns:
        for py_file in root.glob(pattern):
            if py_file.is_file() and not any(part in exclude_dirs for part in py_file.parts):
                python_files.append(py_file)
    
    print(f"Found {len(python_files)} high-priority Python files to check")
    
    updated_count = 0
    for file_path in python_files:
        if process_file(file_path):
            updated_count += 1
    
    print(f"\nCompleted! Updated {updated_count} files.")
    
    return updated_count


if __name__ == "__main__":
    updated = main()
    sys.exit(0 if updated > 0 else 1)