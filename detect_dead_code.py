#!/usr/bin/env python3
"""Detect dead code and potential merge candidates in the codebase."""

import ast
import json
import os
from collections import defaultdict
from pathlib import Path


def find_python_files(root_dir: str) -> list[Path]:
    """Find all Python files in the given directory."""
    python_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("test_"):
                python_files.append(Path(root) / file)
    return python_files


def extract_definitions(file_path: Path) -> tuple[set[str], set[str], set[str]]:
    """Extract function, class, and variable definitions from a Python file."""
    functions = set()
    classes = set()
    variables = set()

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.add(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                variables.add(node.id)

    except Exception:
        pass

    return functions, classes, variables


def extract_imports(file_path: Path) -> dict[str, set[str]]:
    """Extract imports from a Python file."""
    imports = defaultdict(set)

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.name].add("*")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports[module].add(alias.name)

    except Exception:
        pass

    return dict(imports)


def find_unused_files(root_dir: str) -> dict[str, list[str]]:
    """Find potentially unused files in the codebase."""
    python_files = find_python_files(root_dir)

    # Build import graph
    import_graph = defaultdict(set)
    file_imports = {}

    for file_path in python_files:
        imports = extract_imports(file_path)
        file_imports[str(file_path)] = imports

        # Track which files import this module
        module_path = (
            str(file_path).replace("/", ".").replace("\\", ".").replace(".py", "")
        )
        module_path = module_path.removeprefix("src.")

        for imp_module in imports:
            if imp_module.startswith(
                (
                    "src.",
                    "extract.",
                    "decompile.",
                    "parse.",
                    "generate.",
                    "model.",
                    "common.",
                )
            ):
                import_graph[imp_module].add(str(file_path))

    # Find files that are never imported
    never_imported = []
    for file_path in python_files:
        module_path = (
            str(file_path).replace("/", ".").replace("\\", ".").replace(".py", "")
        )
        module_path = module_path.removeprefix("src.")

        # Skip __init__ files and main entry points
        if file_path.name in ("__init__.py", "main.py", "__main__.py"):
            continue

        # Check if this module is imported anywhere
        imported = False
        for possible_name in [
            module_path,
            module_path.replace(".", "/"),
            file_path.stem,
        ]:
            if any(possible_name in imports for imports in import_graph.values()):
                imported = True
                break

        if not imported:
            never_imported.append(str(file_path))

    return {
        "never_imported": never_imported,
        "import_graph": {k: list(v) for k, v in import_graph.items()},
    }


def find_single_use_modules(import_graph: dict[str, list[str]]) -> list[str]:
    """Find modules that are only imported by one other module."""
    single_use = []
    for module, importers in import_graph.items():
        if len(importers) == 1:
            single_use.append((module, importers[0]))
    return single_use


def analyze_file_sizes(root_dir: str) -> dict[str, int]:
    """Analyze file sizes to find small files that could be merged."""
    file_sizes = {}
    python_files = find_python_files(root_dir)

    for file_path in python_files:
        try:
            file_path.stat().st_size
            lines = len(file_path.read_text().splitlines())
            if lines < 100:  # Small files
                file_sizes[str(file_path)] = lines
        except Exception:
            pass

    return file_sizes


def find_duplicate_names(root_dir: str) -> dict[str, list[str]]:
    """Find duplicate function/class names across files."""
    name_locations = defaultdict(list)
    python_files = find_python_files(root_dir)

    for file_path in python_files:
        functions, classes, _ = extract_definitions(file_path)
        for name in functions | classes:
            name_locations[name].append(str(file_path))

    # Find duplicates
    return {
        name: locations
        for name, locations in name_locations.items()
        if len(locations) > 1
    }


def main() -> None:
    """Run dead code analysis."""
    # Analyze unused files
    unused_data = find_unused_files("src")
    never_imported = unused_data["never_imported"]
    import_graph = unused_data["import_graph"]

    for file_path in sorted(never_imported)[:20]:  # Show first 20
        pass
    if len(never_imported) > 20:
        pass

    # Find single-use modules
    single_use = find_single_use_modules(import_graph)
    for module, importer in sorted(single_use)[:20]:
        pass
    if len(single_use) > 20:
        pass

    # Analyze small files
    small_files = analyze_file_sizes("src")
    for file_path, _lines in sorted(small_files.items(), key=lambda x: x[1])[:20]:
        pass
    if len(small_files) > 20:
        pass

    # Find duplicate names
    duplicates = find_duplicate_names("src")
    for _name, locations in sorted(duplicates.items())[:10]:
        for _loc in locations:
            pass
    if len(duplicates) > 10:
        pass

    # Write detailed results
    results = {
        "never_imported": never_imported,
        "single_use_modules": single_use,
        "small_files": small_files,
        "duplicate_names": duplicates,
        "summary": {
            "total_files_analyzed": len(find_python_files("src")),
            "never_imported_count": len(never_imported),
            "single_use_count": len(single_use),
            "small_files_count": len(small_files),
            "duplicate_names_count": len(duplicates),
        },
    }

    os.makedirs("build", exist_ok=True)
    with open("build/dead_code_analysis.json", "w") as f:
        json.dump(results, f, indent=2)

    # Create categorized lists
    with open("build/delete_list.txt", "w") as f:
        f.write("# Files that are never imported and can be safely deleted\n")
        for file_path in sorted(never_imported):
            f.write(f"{file_path}\n")

    with open("build/inline_candidates.txt", "w") as f:
        f.write("# Modules that are only used by one file and could be inlined\n")
        for module, importer in sorted(single_use):
            f.write(f"{module} -> {importer}\n")

    with open("build/consolidate_configs.txt", "w") as f:
        f.write("# Configuration and data files to review for consolidation\n")
        config_files = []
        for root, _, files in os.walk("src"):
            for file in files:
                if file.endswith((".yaml", ".yml", ".json", ".txt", ".md")):
                    config_files.append(os.path.join(root, file))
        for file_path in sorted(config_files):
            f.write(f"{file_path}\n")


if __name__ == "__main__":
    main()
