#!/usr/bin/env python3
"""Find pure functions that would benefit from lru_cache."""

import ast
import re
from pathlib import Path
from typing import List, Tuple, Set

class PureFunctionFinder(ast.NodeVisitor):
    """Find functions that appear to be pure and could benefit from caching."""
    
    def __init__(self, content: str):
        self.content = content
        self.functions = []
        self.current_class = None
        
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track current class context."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Analyze function for purity."""
        # Skip private methods and special methods
        if node.name.startswith('_'):
            self.generic_visit(node)
            return
            
        # Check if it's likely pure
        is_likely_pure = self._is_likely_pure(node)
        
        if is_likely_pure:
            class_prefix = f"{self.current_class}." if self.current_class else ""
            self.functions.append({
                'name': f"{class_prefix}{node.name}",
                'line': node.lineno,
                'has_self': any(arg.arg == 'self' for arg in node.args.args),
                'args': len(node.args.args),
                'returns': node.returns is not None,
                'docstring': ast.get_docstring(node),
                'is_property': any(
                    isinstance(dec, ast.Name) and dec.id == 'property'
                    for dec in node.decorator_list
                ),
                'has_cache': any(
                    isinstance(dec, ast.Name) and 'cache' in dec.id
                    for dec in node.decorator_list
                )
            })
            
        self.generic_visit(node)
        
    def _is_likely_pure(self, node: ast.FunctionDef) -> bool:
        """Determine if a function is likely pure."""
        # Already has cache decorator
        if any(isinstance(dec, ast.Name) and 'cache' in dec.id for dec in node.decorator_list):
            return False
            
        # Check for side effects
        for n in ast.walk(node):
            # Modifies instance state
            if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store):
                if isinstance(n.value, ast.Name) and n.value.id == 'self':
                    return False
                    
            # Global assignments
            if isinstance(n, ast.Global) or isinstance(n, ast.Nonlocal):
                return False
                
            # I/O operations
            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Name):
                    if n.func.id in ['print', 'open', 'write']:
                        return False
                elif isinstance(n.func, ast.Attribute):
                    if n.func.attr in ['write', 'append', 'extend', 'update', 'add', 'remove']:
                        return False
                        
        # Check for pure indicators
        doc = ast.get_docstring(node) or ""
        pure_indicators = [
            'calculate', 'compute', 'get', 'find', 'check', 'validate',
            'parse', 'convert', 'transform', 'format', 'is_', 'has_'
        ]
        
        # Function name suggests purity
        if any(node.name.startswith(ind) for ind in pure_indicators):
            return True
            
        # Has return annotation
        if node.returns is not None:
            return True
            
        # Short function with return
        if hasattr(node, 'end_lineno'):
            lines = node.end_lineno - node.lineno
            if lines < 20:
                for n in node.body:
                    if isinstance(n, ast.Return) and n.value is not None:
                        return True
                        
        return False

def find_cacheable_functions(root_path: Path) -> List[Tuple[Path, dict]]:
    """Find all functions that could benefit from caching."""
    results = []
    
    py_files = list(root_path.rglob("*.py"))
    py_files = [f for f in py_files if ".venv" not in str(f) and "reference" not in str(f)]
    
    for file_path in py_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            finder = PureFunctionFinder(content)
            finder.visit(tree)
            
            for func_info in finder.functions:
                results.append((file_path, func_info))
                
        except Exception as e:
            continue
            
    return results

def main():
    """Main function."""
    print("Finding pure functions that would benefit from @lru_cache...\n")
    
    functions = find_cacheable_functions(Path.cwd())
    
    # Filter and categorize
    high_priority = []  # Functions called frequently
    medium_priority = []  # Utility functions
    low_priority = []  # Others
    
    for file_path, func_info in functions:
        rel_path = file_path.relative_to(Path.cwd())
        
        # Skip test files
        if 'test' in str(rel_path):
            continue
            
        # Categorize based on various factors
        if any(keyword in func_info['name'].lower() for keyword in ['parse', 'decode', 'convert', 'validate']):
            high_priority.append((rel_path, func_info))
        elif any(keyword in func_info['name'].lower() for keyword in ['get', 'find', 'check', 'calculate']):
            medium_priority.append((rel_path, func_info))
        else:
            low_priority.append((rel_path, func_info))
    
    # Print recommendations
    print("## High Priority Functions (frequently called, expensive operations)\n")
    for path, func in high_priority[:10]:
        print(f"📍 {path}:{func['line']}")
        print(f"   Function: {func['name']}()")
        if func['has_self']:
            print(f"   Note: Instance method - use @lru_cache if instances are long-lived")
        print(f"   Benefit: Cache parsing/decoding results")
        print()
        
    print("\n## Medium Priority Functions (utility functions)\n")
    for path, func in medium_priority[:10]:
        print(f"📍 {path}:{func['line']}")
        print(f"   Function: {func['name']}()")
        print(f"   Benefit: Avoid repeated computations")
        print()
        
    print(f"\nTotal cacheable functions found: {len(functions)}")
    print(f"High priority: {len(high_priority)}")
    print(f"Medium priority: {len(medium_priority)}")
    print(f"Low priority: {len(low_priority)}")

if __name__ == "__main__":
    main()