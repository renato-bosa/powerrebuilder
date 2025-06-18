#!/usr/bin/env python3
"""Script to fix common mypy errors across the codebase."""

import ast
import os
import re
from pathlib import Path
from typing import List, Set, Tuple


class TypeAnnotationFixer(ast.NodeTransformer):
    """AST transformer to add missing type annotations."""
    
    def __init__(self):
        self.imports_needed: Set[str] = set()
        self.has_future_annotations = False
    
    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Check if __future__ annotations is imported."""
        for item in node.body:
            if isinstance(item, ast.ImportFrom) and item.module == "__future__":
                if any(alias.name == "annotations" for alias in item.names):
                    self.has_future_annotations = True
        return self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Add return type annotations where missing."""
        if node.returns is None:
            # Check if function has return statements
            has_return = any(
                isinstance(n, ast.Return) and n.value is not None
                for n in ast.walk(node)
            )
            
            if not has_return:
                # Function doesn't return anything
                node.returns = ast.Constant(value="None")
            else:
                # Add Any for now, can be refined later
                node.returns = ast.Name(id="Any", ctx=ast.Load())
                self.imports_needed.add("from typing import Any")
        
        # Add type annotations for arguments without them
        for arg in node.args.args:
            if arg.annotation is None and arg.arg != "self":
                arg.annotation = ast.Name(id="Any", ctx=ast.Load())
                self.imports_needed.add("from typing import Any")
        
        return self.generic_visit(node)


def fix_file_type_annotations(file_path: Path) -> bool:
    """Fix type annotations in a single file."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        fixer = TypeAnnotationFixer()
        new_tree = fixer.visit(tree)
        
        if fixer.imports_needed:
            # Add necessary imports at the top
            import_nodes = []
            
            # Add __future__ annotations if not present
            if not fixer.has_future_annotations:
                import_nodes.append(
                    ast.ImportFrom(
                        module="__future__",
                        names=[ast.alias(name="annotations", asname=None)],
                        level=0
                    )
                )
            
            # Add typing imports
            for imp in sorted(fixer.imports_needed):
                import_nodes.append(ast.parse(imp).body[0])
            
            # Insert imports after module docstring if present
            insert_pos = 0
            if (tree.body and 
                isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant)):
                insert_pos = 1
            
            tree.body[insert_pos:insert_pos] = import_nodes
            
            # Convert back to source
            import astor
            new_content = astor.to_source(new_tree)
            file_path.write_text(new_content)
            return True
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False


def add_missing_init_files(root_dir: Path) -> List[Path]:
    """Add __init__.py files to directories that need them."""
    added_files = []
    
    for dir_path in root_dir.rglob("*"):
        if dir_path.is_dir() and not dir_path.name.startswith((".", "__")):
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                # Check if directory contains Python files
                py_files = list(dir_path.glob("*.py"))
                if py_files:
                    init_file.write_text('"""Package initialization."""\n')
                    added_files.append(init_file)
    
    return added_files


def fix_common_type_errors(file_path: Path) -> bool:
    """Fix common type errors with regex replacements."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Fix "any" -> "Any"
        content = re.sub(
            r'\bany\b(?!\s*\()',  # Match 'any' not followed by '('
            'Any',
            content
        )
        
        # Add -> None to functions without return type
        content = re.sub(
            r'^(\s*def\s+\w+\s*\([^)]*\)\s*):\s*$',
            r'\1 -> None:',
            content,
            flags=re.MULTILINE
        )
        
        # Fix common import issues
        if 'from typing import' not in content and 'Any' in content:
            # Add typing import after docstring
            lines = content.split('\n')
            import_added = False
            for i, line in enumerate(lines):
                if (line.strip() and 
                    not line.strip().startswith(('"""', "'''", "#")) and
                    not import_added):
                    lines.insert(i, "from typing import Any, Optional, List, Dict, Union")
                    import_added = True
                    break
            content = '\n'.join(lines)
        
        if content != original_content:
            file_path.write_text(content)
            return True
            
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        
    return False


def install_missing_stubs() -> None:
    """Install missing type stubs."""
    stubs_to_install = [
        "types-psutil",
        "types-requests",
        "types-PyYAML",
    ]
    
    import subprocess
    
    for stub in stubs_to_install:
        print(f"Installing {stub}...")
        try:
            subprocess.run(
                ["pip", "install", stub],
                check=True,
                capture_output=True
            )
            print(f"✓ Installed {stub}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {stub}")


def main():
    """Main entry point."""
    print("Fixing mypy errors...")
    
    # Install missing stubs
    print("\n1. Installing missing type stubs...")
    install_missing_stubs()
    
    # Add missing __init__.py files
    print("\n2. Adding missing __init__.py files...")
    root_dir = Path(".")
    added_inits = add_missing_init_files(root_dir)
    print(f"Added {len(added_inits)} __init__.py files")
    
    # Fix type annotations
    print("\n3. Fixing type annotations...")
    modules = ["common", "extract", "parse", "decompile", "generate", "model"]
    
    fixed_count = 0
    for module in modules:
        module_path = root_dir / module
        if module_path.exists():
            for py_file in module_path.rglob("*.py"):
                if fix_common_type_errors(py_file):
                    fixed_count += 1
                    print(f"✓ Fixed {py_file}")
    
    print(f"\nFixed {fixed_count} files")
    
    # Run mypy to check remaining errors
    print("\n4. Running mypy to check remaining errors...")
    import subprocess
    result = subprocess.run(
        ["mypy", ".", "--config-file=pyproject.toml"],
        capture_output=True,
        text=True
    )
    
    error_count = len([line for line in result.stdout.split('\n') if ': error:' in line])
    print(f"\nRemaining mypy errors: {error_count}")
    
    if error_count < 100:
        print("\nShowing remaining errors:")
        print(result.stdout[:2000])


if __name__ == "__main__":
    main()