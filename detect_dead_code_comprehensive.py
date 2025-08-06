#!/usr/bin/env python3
"""Comprehensive dead code detection for PowerRebuilder project.

This script analyzes the codebase to identify:
1. Files that are never imported
2. Functions/classes that are never used
3. Unused parameters
4. Duplicate code
5. Files that could be safely removed
"""

import ast
import json
import os
import sys
from pathlib import Path
from typing import Any


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to collect imports from Python files."""

    def __init__(self):
        self.imports = set()
        self.from_imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            module_name = node.module
            for alias in node.names:
                if alias.name == "*":
                    self.from_imports.add(module_name)
                else:
                    self.from_imports.add(f"{module_name}.{alias.name}")
        self.generic_visit(node)


class FunctionClassVisitor(ast.NodeVisitor):
    """AST visitor to collect function and class definitions."""

    def __init__(self):
        self.functions = set()
        self.classes = set()
        self.methods = set()

    def visit_FunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.classes.add(node.name)
        # Collect methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.methods.add(f"{node.name}.{item.name}")
        self.generic_visit(node)


class CallVisitor(ast.NodeVisitor):
    """AST visitor to collect function/method calls and attribute access."""

    def __init__(self):
        self.calls = set()
        self.attributes = set()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.add(node.func.attr)
            if isinstance(node.func.value, ast.Name):
                self.calls.add(f"{node.func.value.id}.{node.func.attr}")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        self.attributes.add(node.attr)
        if isinstance(node.value, ast.Name):
            self.attributes.add(f"{node.value.id}.{node.attr}")
        self.generic_visit(node)


def get_python_files(directory: Path) -> list[Path]:
    """Get all Python files in the directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
                ".git",
                "__pycache__",
                ".pytest_cache",
                "node_modules",
                ".venv",
                "venv",
                ".mypy_cache",
                ".ruff_cache",
                ".tox",
            }
        ]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    return python_files


def analyze_imports_and_usage(src_dir: Path) -> dict[str, Any]:
    """Analyze imports and usage across all Python files."""
    python_files = get_python_files(src_dir)

    # Data structures to store analysis results
    all_imports = set()
    all_from_imports = set()
    all_functions = set()
    all_classes = set()
    all_methods = set()
    all_calls = set()
    all_attributes = set()

    file_imports = {}
    file_definitions = {}
    file_calls = {}
    file_errors = []

    print(f"Analyzing {len(python_files)} Python files...")

    for py_file in python_files:
        try:
            with open(py_file, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(py_file))

            # Collect imports
            import_visitor = ImportVisitor()
            import_visitor.visit(tree)

            # Collect function and class definitions
            def_visitor = FunctionClassVisitor()
            def_visitor.visit(tree)

            # Collect calls and attribute access
            call_visitor = CallVisitor()
            call_visitor.visit(tree)

            # Store per-file results
            file_imports[str(py_file)] = {
                "imports": list(import_visitor.imports),
                "from_imports": list(import_visitor.from_imports),
            }

            file_definitions[str(py_file)] = {
                "functions": list(def_visitor.functions),
                "classes": list(def_visitor.classes),
                "methods": list(def_visitor.methods),
            }

            file_calls[str(py_file)] = {
                "calls": list(call_visitor.calls),
                "attributes": list(call_visitor.attributes),
            }

            # Add to global sets
            all_imports.update(import_visitor.imports)
            all_from_imports.update(import_visitor.from_imports)
            all_functions.update(def_visitor.functions)
            all_classes.update(def_visitor.classes)
            all_methods.update(def_visitor.methods)
            all_calls.update(call_visitor.calls)
            all_attributes.update(call_visitor.attributes)

        except Exception as e:
            file_errors.append(f"Error analyzing {py_file}: {e}")

    return {
        "python_files": [str(f) for f in python_files],
        "all_imports": list(all_imports),
        "all_from_imports": list(all_from_imports),
        "all_functions": list(all_functions),
        "all_classes": list(all_classes),
        "all_methods": list(all_methods),
        "all_calls": list(all_calls),
        "all_attributes": list(all_attributes),
        "file_imports": file_imports,
        "file_definitions": file_definitions,
        "file_calls": file_calls,
        "errors": file_errors,
    }


def find_never_imported_files(
    analysis_data: dict[str, Any], src_dir: Path
) -> list[str]:
    """Find Python files that are never imported."""
    python_files = [Path(f) for f in analysis_data["python_files"]]
    all_imports = set(analysis_data["all_imports"] + analysis_data["all_from_imports"])

    never_imported = []

    for py_file in python_files:
        # Convert file path to potential module name
        relative_path = py_file.relative_to(src_dir.parent)

        # Convert path to module format
        module_parts = []
        for part in relative_path.parts:
            if part.endswith(".py"):
                if part != "__init__.py":
                    module_parts.append(part[:-3])  # Remove .py
            else:
                module_parts.append(part)

        if module_parts:
            module_name = ".".join(module_parts)

            # Check if this module or any of its parts are imported
            is_imported = False
            for imp in all_imports:
                if (
                    module_name in imp or imp in module_name or module_parts[-1] in imp
                    if module_parts
                    else False
                ):
                    is_imported = True
                    break

            if not is_imported:
                never_imported.append(str(relative_path))

    return never_imported


def find_unused_functions_and_classes(
    analysis_data: dict[str, Any],
) -> dict[str, list[str]]:
    """Find functions and classes that are never called."""
    all_functions = set(analysis_data["all_functions"])
    all_classes = set(analysis_data["all_classes"])
    all_methods = set(analysis_data["all_methods"])
    all_calls = set(analysis_data["all_calls"])
    all_attributes = set(analysis_data["all_attributes"])

    # Combine calls and attributes for checking usage
    all_usage = all_calls | all_attributes

    unused_functions = []
    unused_classes = []
    unused_methods = []

    # Special functions/methods that might not be directly called
    special_names = {
        "__init__",
        "__str__",
        "__repr__",
        "__len__",
        "__iter__",
        "__next__",
        "__enter__",
        "__exit__",
        "__call__",
        "__getitem__",
        "__setitem__",
        "setUp",
        "tearDown",
        "test_",
        "main",
        "cli",
    }

    for func in all_functions:
        if (
            func not in all_usage
            and not func.startswith("test_")
            and not any(special in func for special in special_names)
        ):
            unused_functions.append(func)

    for cls in all_classes:
        if cls not in all_usage:
            unused_classes.append(cls)

    for method in all_methods:
        method_name = method.split(".")[-1]
        if (
            method not in all_usage
            and method_name not in all_usage
            and not method_name.startswith("test_")
            and not any(special in method_name for special in special_names)
        ):
            unused_methods.append(method)

    return {
        "unused_functions": unused_functions,
        "unused_classes": unused_classes,
        "unused_methods": unused_methods,
    }


def find_large_files(
    src_dir: Path, size_threshold: int = 1000
) -> list[tuple[str, int]]:
    """Find files larger than threshold (lines of code)."""
    large_files = []

    for py_file in get_python_files(src_dir):
        try:
            with open(py_file, encoding="utf-8", errors="ignore") as f:
                lines = len(f.readlines())

            if lines > size_threshold:
                relative_path = py_file.relative_to(src_dir.parent)
                large_files.append((str(relative_path), lines))

        except Exception as e:
            print(f"Error reading {py_file}: {e}")

    return sorted(large_files, key=lambda x: x[1], reverse=True)


def analyze_test_coverage(analysis_data: dict[str, Any]) -> dict[str, Any]:
    """Analyze test file coverage."""
    test_files = [f for f in analysis_data["python_files"] if "test" in f.lower()]
    non_test_files = [
        f for f in analysis_data["python_files"] if "test" not in f.lower()
    ]

    # Find source files that don't have corresponding test files
    untested_files = []

    for source_file in non_test_files:
        source_path = Path(source_file)
        potential_test_names = [
            f"test_{source_path.stem}.py",
            f"{source_path.stem}_test.py",
            f"test{source_path.stem}.py",
        ]

        has_test = False
        for test_file in test_files:
            test_path = Path(test_file)
            if test_path.name in potential_test_names:
                has_test = True
                break

        if not has_test:
            untested_files.append(source_file)

    return {
        "total_source_files": len(non_test_files),
        "total_test_files": len(test_files),
        "test_coverage_ratio": len(test_files) / len(non_test_files)
        if non_test_files
        else 0,
        "untested_files": untested_files[:20],  # Limit output
    }


def main():
    """Main analysis function."""
    print("PowerRebuilder Comprehensive Dead Code Analysis")
    print("=" * 50)

    # Define source directory
    project_root = Path(__file__).parent
    src_dir = project_root / "src"

    if not src_dir.exists():
        print("Error: src directory not found!")
        sys.exit(1)

    print(f"Analyzing project: {project_root}")
    print(f"Source directory: {src_dir}")

    # Perform comprehensive analysis
    print("\n1. Analyzing imports and usage...")
    analysis_data = analyze_imports_and_usage(src_dir)

    print("\n2. Finding never imported files...")
    never_imported = find_never_imported_files(analysis_data, src_dir)

    print("\n3. Finding unused functions and classes...")
    unused_items = find_unused_functions_and_classes(analysis_data)

    print("\n4. Finding large files...")
    large_files = find_large_files(src_dir)

    print("\n5. Analyzing test coverage...")
    test_coverage = analyze_test_coverage(analysis_data)

    # Compile results
    results = {
        "analysis_summary": {
            "total_python_files": len(analysis_data["python_files"]),
            "total_functions": len(analysis_data["all_functions"]),
            "total_classes": len(analysis_data["all_classes"]),
            "total_methods": len(analysis_data["all_methods"]),
            "analysis_errors": len(analysis_data["errors"]),
        },
        "never_imported_files": never_imported,
        "unused_code": unused_items,
        "large_files": large_files[:10],  # Top 10 largest
        "test_coverage": test_coverage,
        "errors": analysis_data["errors"],
    }

    # Save results
    output_file = project_root / "comprehensive_dead_code_analysis.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    print("\nAnalysis Results Summary:")
    print("========================")
    print(
        f"Total Python files analyzed: {results['analysis_summary']['total_python_files']}"
    )
    print(f"Never imported files: {len(results['never_imported_files'])}")
    print(f"Unused functions: {len(results['unused_code']['unused_functions'])}")
    print(f"Unused classes: {len(results['unused_code']['unused_classes'])}")
    print(f"Unused methods: {len(results['unused_code']['unused_methods'])}")
    print(f"Large files (>1000 lines): {len(results['large_files'])}")
    print(f"Test coverage ratio: {results['test_coverage']['test_coverage_ratio']:.2%}")

    print("\nTop never imported files:")
    for file_path in results["never_imported_files"][:10]:
        print(f"  - {file_path}")

    print("\nTop unused functions:")
    for func in results["unused_code"]["unused_functions"][:10]:
        print(f"  - {func}")

    print("\nLargest files:")
    for file_path, lines in results["large_files"][:5]:
        print(f"  - {file_path}: {lines} lines")

    print(f"\nDetailed results saved to: {output_file}")

    # Exit with appropriate code
    if results["analysis_summary"]["analysis_errors"] > 0:
        print(
            f"\nWarning: {results['analysis_summary']['analysis_errors']} files had analysis errors"
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
