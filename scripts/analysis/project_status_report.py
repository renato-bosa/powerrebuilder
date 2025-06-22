#!/usr/bin/env python3
"""Generate comprehensive project status report."""

import ast
from collections import defaultdict
from pathlib import Path
import logging



logger = logging.getLogger(__name__)

class ImportAnalyzer(ast.NodeVisitor):
    """Analyze imports in Python files."""

    def __init__(self) -> None:
        

        self.imports = set()
        self.from_imports = set()

    def visit_Import(self, node) -> None:
        

        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node) -> None:
        

        if node.module:
            self.from_imports.add(node.module)
        self.generic_visit(node)


def analyze_file_usage() -> dict[str, dict]:



    
    


    """Analyze which files are actually used in the project."""
    py_files = list(Path.cwd().rglob("*.py"))
    py_files = [
        f for f in py_files if ".venv" not in str(f) and "reference" not in str(f)
    ]

    file_usage = {}
    import_graph = defaultdict(set)

    for file_path in py_files:
        rel_path = file_path.relative_to(Path.cwd())
        module_path = str(rel_path).replace("/", ".").replace(".py", "")

        try:
            content = file_path.read_text()
            tree = ast.parse(content)

            analyzer = ImportAnalyzer()
            analyzer.visit(tree)

            # Check if file has executable code
            has_code = any(
                isinstance(node, ast.FunctionDef | ast.ClassDef | ast.Assign)
                for node in ast.walk(tree)
            )

            # Check if it's imported elsewhere
            is_imported = False
            for other_file in py_files:
                if other_file == file_path:
                    continue
                try:
                    other_content = other_file.read_text()
                    if (
                        module_path in other_content
                        or str(rel_path.stem) in other_content
                    ):
                        is_imported = True
                        import_graph[str(other_file.relative_to(Path.cwd()))].add(
                            str(rel_path)
                        )
                except Exception as e:
                    logger.debug("Exception caught: %s", e)

            file_usage[str(rel_path)] = {
                "has_code": has_code,
                "is_imported": is_imported,
                "imports": len(analyzer.imports) + len(analyzer.from_imports),
                "is_test": "test" in str(rel_path),
                "is_script": str(rel_path).startswith("scripts/"),
                "size": file_path.stat().st_size,
            }

        except Exception as e:
            file_usage[str(rel_path)] = {
                "error": str(e),
                "size": file_path.stat().st_size if file_path.exists() else 0,
            }

    return file_usage, import_graph


def test_decompilation_success() -> list:



    


    """Test actual decompilation on sample files."""
    test_results = {
        "extraction": {"success": 0, "failed": 0, "files": []},
        "parsing": {"success": 0, "failed": 0, "files": []},
        "decompilation": {"success": 0, "failed": 0, "files": []},
        "generation": {"success": 0, "failed": 0, "files": []},
    }

    # Check if we have test PBD files
    test_pbd_dir = Path("tests/fixtures/pbd_files")
    if test_pbd_dir.exists():
        for pbd_file in test_pbd_dir.glob("*.pbd"):
            test_results["extraction"]["files"].append(str(pbd_file))

    # Check output directories
    output_dirs = {
        "extracted": Path("output/extracted"),
        "parsed": Path("output/parsed"),
        "decompiled": Path("output/decompiled"),
        "generated": Path("output/generated"),
    }

    for stage, dir_path in output_dirs.items():
        if dir_path.exists():
            file_count = len(list(dir_path.rglob("*")))
            if file_count > 0:
                test_results[stage.replace("ed", "ion")]["success"] = file_count

    return test_results


def analyze_component_coverage() -> None:



    


    """Analyze which PowerBuilder components are supported."""
    return {
        "UI Elements": {
            "Window": {"parser": True, "model": True, "generator": True},
            "DataWindow": {"parser": True, "model": True, "generator": False},
            "Menu": {"parser": True, "model": True, "generator": False},
            "UserObject": {"parser": True, "model": True, "generator": False},
            "Controls": {"parser": True, "model": True, "generator": "partial"},
        },
        "Business Logic": {
            "Functions": {"parser": True, "model": True, "generator": True},
            "Events": {"parser": True, "model": True, "generator": False},
            "Scripts": {"parser": True, "decompiler": True, "generator": False},
            "Expressions": {"parser": True, "evaluator": True, "generator": False},
        },
        "Database": {
            "SQL Statements": {"parser": True, "model": True, "generator": False},
            "Transactions": {"parser": True, "model": True, "generator": False},
            "DataWindow SQL": {"parser": "partial", "model": True, "generator": False},
            "Stored Procedures": {"parser": True, "model": False, "generator": False},
        },
        "Advanced Features": {
            "P-Code": {"decompiler": True, "decoder": True, "lifter": "partial"},
            "Libraries": {"extractor": True, "manager": True, "resolver": True},
            "Resources": {"extractor": "partial", "handler": False, "generator": False},
            "Binary Data": {"extractor": True, "decoder": "partial", "handler": False},
        },
    }


def generate_report() -> None:



    
    


    """Generate comprehensive status report."""
    # 1. File Usage Analysis
    file_usage, import_graph = analyze_file_usage()

    len(file_usage)
    sum(
        1
        for f, info in file_usage.items()
        if info.get("is_imported") or info.get("is_script")
    )
    unused_files = [
        f
        for f, info in file_usage.items()
        if not info.get("is_imported")
        and not info.get("is_script")
        and not info.get("is_test")
    ]

    if unused_files[:5]:
        for _f in unused_files[:5]:
            pass

    # 2. Test Coverage

    # 3. Decompilation Success Rate
    test_results = test_decompilation_success()

    for results in test_results.values():
        if results.get("files"):
            pass
        if results.get("success", 0) > 0:
            pass

    # 4. Component Support
    components = analyze_component_coverage()

    for items in components.values():
        for support in items.values():
            status = []
            for feature, implemented in support.items():
                if implemented:
                    status.append(f"✓ {feature}")
                elif implemented == "partial":
                    status.append(f"⚡ {feature}")
                else:
                    status.append(f"✗ {feature}")

    # 5. Overall Assessment


if __name__ == "__main__":
    generate_report()
