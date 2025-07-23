#!/usr/bin/env python3
"""Detect dead code and potential merge candidates in the codebase."""

import ast
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


def find_python_files(root_dir: str) -> List[Path]:
    """Find all Python files in the given directory."""
    python_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                python_files.append(Path(root) / file)
    return python_files


def extract_definitions(file_path: Path) -> Tuple[Set[str], Set[str], Set[str]]:
    """Extract function, class, and variable definitions from a Python file."""
    functions = set()
    classes = set()
    variables = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.add(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                variables.add(node.id)
                
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        
    return functions, classes, variables


def extract_imports(file_path: Path) -> Dict[str, Set[str]]:
    """Extract imports from a Python file."""
    imports = defaultdict(set)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.name].add('*')
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports[module].add(alias.name)
                    
    except Exception as e:
        print(f"Error parsing imports from {file_path}: {e}")
        
    return dict(imports)


def find_unused_files(root_dir: str) -> Dict[str, List[str]]:
    """Find potentially unused files in the codebase."""
    python_files = find_python_files(root_dir)
    
    # Build import graph
    import_graph = defaultdict(set)
    file_imports = {}
    
    for file_path in python_files:
        imports = extract_imports(file_path)
        file_imports[str(file_path)] = imports
        
        # Track which files import this module
        module_path = str(file_path).replace('/', '.').replace('\\', '.').replace('.py', '')
        if module_path.startswith('src.'):
            module_path = module_path[4:]
            
        for imp_module in imports:
            if imp_module.startswith(('src.', 'extract.', 'decompile.', 'parse.', 'generate.', 'model.', 'common.')):
                import_graph[imp_module].add(str(file_path))
    
    # Find files that are never imported
    never_imported = []
    for file_path in python_files:
        module_path = str(file_path).replace('/', '.').replace('\\', '.').replace('.py', '')
        if module_path.startswith('src.'):
            module_path = module_path[4:]
            
        # Skip __init__ files and main entry points
        if file_path.name in ('__init__.py', 'main.py', '__main__.py'):
            continue
            
        # Check if this module is imported anywhere
        imported = False
        for possible_name in [module_path, module_path.replace('.', '/'), file_path.stem]:
            if any(possible_name in imports for imports in import_graph.values()):
                imported = True
                break
                
        if not imported:
            never_imported.append(str(file_path))
    
    return {
        'never_imported': never_imported,
        'import_graph': {k: list(v) for k, v in import_graph.items()}
    }


def find_single_use_modules(import_graph: Dict[str, List[str]]) -> List[str]:
    """Find modules that are only imported by one other module."""
    single_use = []
    for module, importers in import_graph.items():
        if len(importers) == 1:
            single_use.append((module, importers[0]))
    return single_use


def analyze_file_sizes(root_dir: str) -> Dict[str, int]:
    """Analyze file sizes to find small files that could be merged."""
    file_sizes = {}
    python_files = find_python_files(root_dir)
    
    for file_path in python_files:
        try:
            size = file_path.stat().st_size
            lines = len(file_path.read_text().splitlines())
            if lines < 100:  # Small files
                file_sizes[str(file_path)] = lines
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
    return file_sizes


def find_duplicate_names(root_dir: str) -> Dict[str, List[str]]:
    """Find duplicate function/class names across files."""
    name_locations = defaultdict(list)
    python_files = find_python_files(root_dir)
    
    for file_path in python_files:
        functions, classes, _ = extract_definitions(file_path)
        for name in functions | classes:
            name_locations[name].append(str(file_path))
    
    # Find duplicates
    duplicates = {name: locations for name, locations in name_locations.items() if len(locations) > 1}
    return duplicates


def main():
    """Run dead code analysis."""
    print("=== Dead Code Analysis ===\n")
    
    # Analyze unused files
    print("1. Finding potentially unused files...")
    unused_data = find_unused_files('src')
    never_imported = unused_data['never_imported']
    import_graph = unused_data['import_graph']
    
    print(f"\nFiles never imported ({len(never_imported)}):")
    for file_path in sorted(never_imported)[:20]:  # Show first 20
        print(f"  - {file_path}")
    if len(never_imported) > 20:
        print(f"  ... and {len(never_imported) - 20} more")
    
    # Find single-use modules
    print("\n2. Finding single-use modules (merge candidates)...")
    single_use = find_single_use_modules(import_graph)
    print(f"\nModules imported by only one file ({len(single_use)}):")
    for module, importer in sorted(single_use)[:20]:
        print(f"  - {module} <- {importer}")
    if len(single_use) > 20:
        print(f"  ... and {len(single_use) - 20} more")
    
    # Analyze small files
    print("\n3. Finding small files (< 100 lines)...")
    small_files = analyze_file_sizes('src')
    print(f"\nSmall files that could be merged ({len(small_files)}):")
    for file_path, lines in sorted(small_files.items(), key=lambda x: x[1])[:20]:
        print(f"  - {file_path}: {lines} lines")
    if len(small_files) > 20:
        print(f"  ... and {len(small_files) - 20} more")
    
    # Find duplicate names
    print("\n4. Finding duplicate function/class names...")
    duplicates = find_duplicate_names('src')
    print(f"\nDuplicate names found ({len(duplicates)}):")
    for name, locations in sorted(duplicates.items())[:10]:
        print(f"  - {name}:")
        for loc in locations:
            print(f"    - {loc}")
    if len(duplicates) > 10:
        print(f"  ... and {len(duplicates) - 10} more")
    
    # Write detailed results
    results = {
        'never_imported': never_imported,
        'single_use_modules': single_use,
        'small_files': small_files,
        'duplicate_names': duplicates,
        'summary': {
            'total_files_analyzed': len(find_python_files('src')),
            'never_imported_count': len(never_imported),
            'single_use_count': len(single_use),
            'small_files_count': len(small_files),
            'duplicate_names_count': len(duplicates)
        }
    }
    
    os.makedirs('build', exist_ok=True)
    with open('build/dead_code_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create categorized lists
    with open('build/delete_list.txt', 'w') as f:
        f.write("# Files that are never imported and can be safely deleted\n")
        for file_path in sorted(never_imported):
            f.write(f"{file_path}\n")
    
    with open('build/inline_candidates.txt', 'w') as f:
        f.write("# Modules that are only used by one file and could be inlined\n")
        for module, importer in sorted(single_use):
            f.write(f"{module} -> {importer}\n")
    
    with open('build/consolidate_configs.txt', 'w') as f:
        f.write("# Configuration and data files to review for consolidation\n")
        config_files = []
        for root, _, files in os.walk('src'):
            for file in files:
                if file.endswith(('.yaml', '.yml', '.json', '.txt', '.md')):
                    config_files.append(os.path.join(root, file))
        for file_path in sorted(config_files):
            f.write(f"{file_path}\n")
    
    print(f"\n=== Summary ===")
    print(f"Total Python files analyzed: {results['summary']['total_files_analyzed']}")
    print(f"Never imported: {results['summary']['never_imported_count']}")
    print(f"Single-use modules: {results['summary']['single_use_count']}")
    print(f"Small files (<100 lines): {results['summary']['small_files_count']}")
    print(f"Duplicate names: {results['summary']['duplicate_names_count']}")
    print(f"\nDetailed results saved to:")
    print(f"  - build/dead_code_analysis.json")
    print(f"  - build/delete_list.txt")
    print(f"  - build/inline_candidates.txt")
    print(f"  - build/consolidate_configs.txt")


if __name__ == '__main__':
    main()