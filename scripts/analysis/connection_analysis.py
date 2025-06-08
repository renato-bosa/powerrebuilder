#!/usr/bin/env python3
"""Analyze where connection pooling and circuit breakers would be beneficial."""

import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple

class ConnectionAnalyzer(ast.NodeVisitor):
    """Analyze code for database and external service connections."""
    
    def __init__(self):
        self.db_operations = []
        self.file_operations = []
        self.network_operations = []
        self.external_calls = []
        
    def visit_Call(self, node: ast.Call):
        """Visit function calls."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            # Database operations
            if func_name in ['connect', 'execute', 'cursor', 'query']:
                self.db_operations.append((func_name, node.lineno))
            # File operations
            elif func_name in ['open']:
                self.file_operations.append((func_name, node.lineno))
            # Network operations
            elif func_name in ['urlopen', 'request', 'get', 'post']:
                self.network_operations.append((func_name, node.lineno))
                
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            # SQLAlchemy patterns
            if attr_name in ['connect', 'execute', 'query', 'session']:
                self.db_operations.append((attr_name, node.lineno))
            # Requests library patterns
            elif attr_name in ['get', 'post', 'put', 'delete', 'request']:
                self.network_operations.append((attr_name, node.lineno))
                
        self.generic_visit(node)

def analyze_connections(root_path: Path) -> Dict[str, List[Tuple[Path, str, int]]]:
    """Analyze all Python files for connection patterns."""
    results = {
        'database': [],
        'file_io': [],
        'network': [],
        'external': []
    }
    
    py_files = list(root_path.rglob("*.py"))
    py_files = [f for f in py_files if ".venv" not in str(f) and "reference" not in str(f)]
    
    for file_path in py_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Quick text-based checks first
            has_db = any(word in content.lower() for word in ['database', 'sql', 'connection', 'cursor'])
            has_network = any(word in content.lower() for word in ['http', 'request', 'api', 'url'])
            
            if not (has_db or has_network):
                continue
                
            tree = ast.parse(content)
            analyzer = ConnectionAnalyzer()
            analyzer.visit(tree)
            
            if analyzer.db_operations:
                for op_name, line_no in analyzer.db_operations:
                    results['database'].append((file_path, op_name, line_no))
                    
            if analyzer.network_operations:
                for op_name, line_no in analyzer.network_operations:
                    results['network'].append((file_path, op_name, line_no))
                    
        except Exception as e:
            continue
            
    return results

def main():
    """Main analysis function."""
    print("Analyzing codebase for connection pooling and circuit breaker opportunities...\n")
    
    results = analyze_connections(Path.cwd())
    
    print("## Connection Pooling Opportunities\n")
    
    # Database connections
    if results['database']:
        print(f"### Database Operations ({len(results['database'])} found)")
        print("These would benefit from connection pooling:\n")
        
        # Group by file
        db_by_file = {}
        for file_path, op, line in results['database']:
            if file_path not in db_by_file:
                db_by_file[file_path] = []
            db_by_file[file_path].append((op, line))
            
        for file_path, ops in list(db_by_file.items())[:5]:  # Show top 5 files
            rel_path = file_path.relative_to(Path.cwd())
            print(f"📄 {rel_path}")
            for op, line in ops[:3]:  # Show first 3 operations
                print(f"   Line {line}: {op}()")
            if len(ops) > 3:
                print(f"   ... and {len(ops) - 3} more operations")
            print()
    else:
        print("### Database Operations")
        print("✅ No direct database operations found (good for this type of tool)\n")
    
    # Network operations
    print("\n## Circuit Breaker Opportunities\n")
    
    if results['network']:
        print(f"### Network Operations ({len(results['network'])} found)")
        print("These would benefit from circuit breakers:\n")
        
        # Group by file
        net_by_file = {}
        for file_path, op, line in results['network']:
            if file_path not in net_by_file:
                net_by_file[file_path] = []
            net_by_file[file_path].append((op, line))
            
        for file_path, ops in list(net_by_file.items())[:5]:
            rel_path = file_path.relative_to(Path.cwd())
            print(f"📄 {rel_path}")
            for op, line in ops[:3]:
                print(f"   Line {line}: {op}()")
            print()
    else:
        print("### Network Operations")
        print("✅ No external network calls found\n")
    
    # Recommendations
    print("\n## Recommendations\n")
    
    if not results['database'] and not results['network']:
        print("✅ This codebase is primarily file-based and doesn't require connection pooling")
        print("✅ No external service calls detected that would benefit from circuit breakers")
        print("\nThe tool processes local PowerBuilder files, so the current architecture is appropriate.")
    else:
        if results['database']:
            print("🔧 Database Connection Pooling:")
            print("   - Implement SQLAlchemy connection pool")
            print("   - Set pool_size=5, max_overflow=10")
            print("   - Add connection timeout handling")
            
        if results['network']:
            print("\n🔧 Circuit Breaker Implementation:")
            print("   - Use py-breaker or similar library")
            print("   - Set failure threshold at 5 failures")
            print("   - Implement exponential backoff")
            print("   - Add fallback mechanisms")

if __name__ == "__main__":
    main()