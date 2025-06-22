#!/usr/bin/env python3
"""Find methods missing type annotations or docstrings."""

import ast
import os
from pathlib import Path
from typing import List, Tuple


class MethodAnalyzer(ast.NodeVisitor):
    """Analyze methods for missing annotations and docstrings."""
    
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.missing_return_type = []
        self.missing_param_types = []
        self.missing_docstrings = []
        self.current_class = None
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        # Skip private methods and special methods
        if node.name.startswith('_') and not node.name.startswith('__'):
            return
            
        # Check for docstring
        has_docstring = (
            node.body and 
            isinstance(node.body[0], ast.Expr) and 
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)
        )
        
        if not has_docstring and node.name != '__init__':
            location = f"{self.current_class}.{node.name}" if self.current_class else node.name
            self.missing_docstrings.append((location, node.lineno))
        
        # Check return type annotation
        if node.returns is None and node.name != '__init__':
            location = f"{self.current_class}.{node.name}" if self.current_class else node.name
            self.missing_return_type.append((location, node.lineno))
            
        # Check parameter type annotations
        for arg in node.args.args:
            if arg.arg != 'self' and arg.annotation is None:
                location = f"{self.current_class}.{node.name}" if self.current_class else node.name
                self.missing_param_types.append((location, arg.arg, node.lineno))
                
        self.generic_visit(node)


def analyze_file(file_path: Path) -> Tuple[List, List, List]:
    """Analyze a Python file for missing annotations."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        analyzer = MethodAnalyzer(str(file_path))
        analyzer.visit(tree)
        
        return (
            analyzer.missing_return_type,
            analyzer.missing_param_types,
            analyzer.missing_docstrings
        )
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return [], [], []


def main() -> None:
    """Main function to analyze all Python files."""
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
        # Skip scripts directory
        if 'scripts' in py_file.parts:
            continue
        python_files.append(py_file)
    
    print(f"Analyzing {len(python_files)} Python files...")
    
    # Aggregate results
    total_missing_return = 0
    total_missing_params = 0
    total_missing_docs = 0
    
    files_by_issue = {
        'return_type': [],
        'param_types': [],
        'docstrings': []
    }
    
    for file_path in python_files:
        missing_return, missing_params, missing_docs = analyze_file(file_path)
        
        if missing_return:
            total_missing_return += len(missing_return)
            files_by_issue['return_type'].append((file_path, missing_return))
            
        if missing_params:
            total_missing_params += len(missing_params)
            files_by_issue['param_types'].append((file_path, missing_params))
            
        if missing_docs:
            total_missing_docs += len(missing_docs)
            files_by_issue['docstrings'].append((file_path, missing_docs))
    
    # Print summary
    print(f"\nSummary:")
    print(f"- Methods missing return type annotations: {total_missing_return}")
    print(f"- Methods with missing parameter types: {total_missing_params}")
    print(f"- Methods missing docstrings: {total_missing_docs}")
    
    # Show top files needing attention
    print(f"\nTop 10 files needing return type annotations:")
    sorted_return = sorted(files_by_issue['return_type'], key=lambda x: len(x[1]), reverse=True)
    for file_path, issues in sorted_return[:10]:
        print(f"  {file_path.relative_to(root)}: {len(issues)} methods")
        
    print(f"\nTop 10 files needing parameter type annotations:")
    sorted_params = sorted(files_by_issue['param_types'], key=lambda x: len(x[1]), reverse=True)
    for file_path, issues in sorted_params[:10]:
        print(f"  {file_path.relative_to(root)}: {len(issues)} parameters")
        
    print(f"\nTop 10 files needing docstrings:")
    sorted_docs = sorted(files_by_issue['docstrings'], key=lambda x: len(x[1]), reverse=True)
    for file_path, issues in sorted_docs[:10]:
        print(f"  {file_path.relative_to(root)}: {len(issues)} methods")
    
    # Write detailed report
    report_path = root / "scripts" / "annotation_report.txt"
    with open(report_path, 'w') as f:
        f.write("Missing Type Annotations and Docstrings Report\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("Files with missing return type annotations:\n")
        for file_path, issues in sorted_return:
            if issues:
                f.write(f"\n{file_path.relative_to(root)}:\n")
                for method, line in issues[:5]:  # Show first 5
                    f.write(f"  Line {line}: {method}\n")
                if len(issues) > 5:
                    f.write(f"  ... and {len(issues) - 5} more\n")


if __name__ == "__main__":
    main()