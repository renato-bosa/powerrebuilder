#!/usr/bin/env python3
"""Find functions that exceed 200 lines and need refactoring."""

import ast
from pathlib import Path
from typing import List, Tuple

class LargeFunctionFinder(ast.NodeVisitor):
    """Find functions that are too large."""
    
    def __init__(self, threshold: int = 200):
        self.threshold = threshold
        self.large_functions = []
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            lines = node.end_lineno - node.lineno + 1
            if lines >= self.threshold:
                self.large_functions.append((node.name, node.lineno, lines))
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions."""
        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
            lines = node.end_lineno - node.lineno + 1
            if lines >= self.threshold:
                self.large_functions.append((node.name, node.lineno, lines))
        self.generic_visit(node)

def find_large_functions(root_path: Path, threshold: int = 200) -> List[Tuple[Path, str, int, int]]:
    """Find all functions exceeding the threshold."""
    results = []
    
    py_files = list(root_path.rglob("*.py"))
    py_files = [f for f in py_files if ".venv" not in str(f) and "reference" not in str(f)]
    
    for file_path in py_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            finder = LargeFunctionFinder(threshold)
            finder.visit(tree)
            
            for func_name, line_no, line_count in finder.large_functions:
                results.append((file_path, func_name, line_no, line_count))
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            
    return sorted(results, key=lambda x: x[3], reverse=True)  # Sort by line count

def main():
    """Main function."""
    print("Finding functions with 200+ lines...\n")
    
    large_functions = find_large_functions(Path.cwd(), threshold=200)
    
    if not large_functions:
        print("✅ No functions exceed 200 lines!")
        return
        
    print(f"Found {len(large_functions)} functions that need refactoring:\n")
    
    for file_path, func_name, line_no, line_count in large_functions:
        rel_path = file_path.relative_to(Path.cwd())
        print(f"📍 {rel_path}:{line_no}")
        print(f"   Function: {func_name}()")
        print(f"   Lines: {line_count}")
        print(f"   Suggested actions:")
        
        # Provide specific refactoring suggestions based on function name
        if "parse" in func_name.lower():
            print(f"   - Extract parsing logic into helper methods")
        if "transform" in func_name.lower():
            print(f"   - Split transformation stages into separate methods")
        if "process" in func_name.lower() or "handle" in func_name.lower():
            print(f"   - Extract processing steps into dedicated handlers")
        if line_count > 300:
            print(f"   - Consider splitting into a separate class")
            
        print()

if __name__ == "__main__":
    main()