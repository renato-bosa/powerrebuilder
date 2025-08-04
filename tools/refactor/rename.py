#!/usr/bin/env python3
"""File renaming script to enforce naming conventions.
Renames files according to the project's naming standards:
- Common module files to adjective_noun pattern
- Contracts module files to add _contracts suffix
- coordinator.py files to module_coordinator.py
- factory.py files to module_factory.py.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


class FileRenamer:
    def __init__(self, project_root: Path, dry_run: bool = True) -> None:
        self.project_root = project_root
        self.dry_run = dry_run
        self.renamed_files: list[tuple[Path, Path]] = []
        self.import_updates: dict[str, list[tuple[str, str]]] = {}
        self.critical_warnings: list[str] = []

    def get_module_name(self, file_path: Path) -> str:
        """Extract module name from file path."""
        try:
            parts = file_path.relative_to(self.project_root / "src").parts
            if len(parts) > 1:
                return parts[0]
        except ValueError:
            pass
        return ""

    def get_new_name(self, file_path: Path) -> Path:
        """Determine new name based on naming conventions."""
        filename = file_path.name
        parent = file_path.parent
        module = self.get_module_name(file_path)

        # Handle coordinator.py files
        if filename == "coordinator.py" and module:
            return parent / f"{module}_coordinator.py"

        # Handle factory.py files
        if filename == "factory.py" and module:
            return parent / f"{module}_factory.py"

        # Handle common module files - only in root common directory
        if str(file_path.parent) == str(
            self.project_root / "src" / "common"
        ) and filename not in ["__init__.py", "constants.py"]:
            # Check if it needs adjective_noun pattern
            if self.needs_adjective_noun_rename(filename):
                new_name = self.convert_to_adjective_noun(filename)
                return parent / new_name

        # Handle contracts module files
        if "contracts" in str(file_path) and filename not in ["__init__.py"]:
            # Check if it needs _contracts suffix
            if not filename.endswith("_contracts.py") and not filename.endswith(".pyi"):
                base_name = filename.replace(".py", "")
                return parent / f"{base_name}_contracts.py"

        return file_path

    def needs_adjective_noun_rename(self, filename: str) -> bool:
        """Check if common module file needs renaming."""
        # Files that follow the pattern already
        adjective_noun_pattern = re.compile(r"^[a-z]+_[a-z]+\.py$")
        if adjective_noun_pattern.match(filename):
            return False

        # Special cases that don't need renaming
        special_files = {
            "exceptions.py",
            "exceptions_hierarchy.py",
            "interfaces.py",
            "types.py",
            "limits.py",
            "security.py",
            "cache.py",
            "constants.py",
        }
        if filename in special_files:
            return False

        # Files that need renaming - only in the root common directory
        rename_needed = {
            "state_management.py": "state_manager.py",
            "async_coordinators.py": "async_coordinator.py",
            "streaming.py": "stream_handler.py",
            "circuit_breaker.py": "circuit_handler.py",
            "distributed.py": "distributed_manager.py",
            "event_bus.py": "event_handler.py",
            "error_handling.py": "error_handler.py",
            "core_utils.py": "core_utilities.py",
            "dependency_injection.py": "dependency_injector.py",
        }

        return filename in rename_needed

    def convert_to_adjective_noun(self, filename: str) -> str:
        """Convert filename to adjective_noun pattern."""
        rename_map = {
            "state_management.py": "state_manager.py",
            "async_coordinators.py": "async_coordinator.py",
            "streaming.py": "stream_handler.py",
            "circuit_breaker.py": "circuit_handler.py",
            "distributed.py": "distributed_manager.py",
            "event_bus.py": "event_handler.py",
            "error_handling.py": "error_handler.py",
            "core_utils.py": "core_utilities.py",
            "dependency_injection.py": "dependency_injector.py",
        }

        return rename_map.get(filename, filename)

    def find_files_to_rename(self) -> list[tuple[Path, Path]]:
        """Find all files that need renaming."""
        files_to_rename = []

        # Search for Python files in src directory
        src_dir = self.project_root / "src"
        for file_path in src_dir.rglob("*.py"):
            # Skip cache and archive directories
            if "__pycache__" in str(file_path) or "archive" in str(file_path):
                continue

            # Skip files that don't exist (may have been moved)
            if not file_path.exists():
                continue

            new_path = self.get_new_name(file_path)
            if new_path != file_path:
                files_to_rename.append((file_path, new_path))

        return files_to_rename

    def update_imports(self, old_path: Path, new_path: Path) -> None:
        """Update import statements across the codebase."""
        old_module = self.path_to_module(old_path)
        new_module = self.path_to_module(new_path)

        # Find all Python files
        for py_file in self.project_root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                original_content = content

                # Update various import patterns
                patterns = [
                    (f"from {old_module} import", f"from {new_module} import"),
                    (f"import {old_module}", f"import {new_module}"),
                    (f'"{old_module}"', f'"{new_module}"'),
                    (f"'{old_module}'", f"'{new_module}'"),
                ]

                for old_pattern, new_pattern in patterns:
                    content = content.replace(old_pattern, new_pattern)

                if content != original_content:
                    if py_file not in self.import_updates:
                        self.import_updates[py_file] = []
                    self.import_updates[py_file].append((old_module, new_module))

                    if not self.dry_run:
                        with open(py_file, "w", encoding="utf-8") as f:
                            f.write(content)

            except Exception:
                pass

    def path_to_module(self, path: Path) -> str:
        """Convert file path to module import path."""
        try:
            # Get relative path from src directory
            rel_path = path.relative_to(self.project_root / "src")
            # Remove .py extension and convert to module path
            module_parts = [*list(rel_path.parts[:-1]), rel_path.stem]
            return ".".join(module_parts)
        except ValueError:
            # If not in src, try from project root
            rel_path = path.relative_to(self.project_root)
            module_parts = [*list(rel_path.parts[:-1]), rel_path.stem]
            return ".".join(module_parts)

    def rename_files(self) -> None:
        """Perform the file renaming."""
        files_to_rename = self.find_files_to_rename()

        if not files_to_rename:
            return

        for old_path, new_path in files_to_rename:
            old_path.relative_to(self.project_root)
            new_path.relative_to(self.project_root)

        if self.dry_run:
            # Simulate import updates to show what would change
            import_preview = {}
            for old_path, new_path in files_to_rename:
                old_module = self.path_to_module(old_path)
                new_module = self.path_to_module(new_path)

                # Find all Python files that might import this module
                for py_file in self.project_root.rglob("*.py"):
                    if "__pycache__" in str(py_file):
                        continue

                    try:
                        with open(py_file, encoding="utf-8") as f:
                            content = f.read()

                        # Check if this file imports the module
                        if old_module in content:
                            if py_file not in import_preview:
                                import_preview[py_file] = []
                            import_preview[py_file].append((old_module, new_module))
                    except Exception:
                        pass

            if import_preview:
                for file_path, updates in list(import_preview.items())[
                    :10
                ]:  # Show first 10
                    file_path.relative_to(self.project_root)
                    for _old_import, _new_import in updates[
                        :3
                    ]:  # Show first 3 updates per file
                        pass
                if len(import_preview) > 10:
                    pass

            # Check for potential issues
            self.check_for_warnings(files_to_rename)
            if self.critical_warnings:
                for _warning in self.critical_warnings:
                    pass

            return

        # First pass: rename files
        for old_path, new_path in files_to_rename:
            try:
                if new_path.exists():
                    continue

                # Create parent directory if needed
                new_path.parent.mkdir(parents=True, exist_ok=True)

                # Rename the file
                shutil.move(str(old_path), str(new_path))
                self.renamed_files.append((old_path, new_path))

            except Exception:
                pass

        # Second pass: update imports
        for old_path, new_path in self.renamed_files:
            self.update_imports(old_path, new_path)

        # Report import updates
        if self.import_updates:
            for file_path, updates in self.import_updates.items():
                file_path.relative_to(self.project_root)
                for _old_import, _new_import in updates:
                    pass

    def create_backup(self) -> bool:
        """Create a backup of files before renaming."""
        backup_dir = self.project_root / "backup_before_rename"

        if backup_dir.exists():
            response = input("Overwrite? (y/n): ")
            if response.lower() != "y":
                return False
            shutil.rmtree(backup_dir)

        # Copy src directory
        src_dir = self.project_root / "src"
        backup_src = backup_dir / "src"
        shutil.copytree(
            src_dir, backup_src, ignore=shutil.ignore_patterns("__pycache__")
        )

        return True

    def verify_imports(self) -> None:
        """Run a quick import check after renaming."""
        # Try importing main modules
        test_imports = [
            "src.common",
            "src.contracts",
            "src.extract",
            "src.parse",
            "src.decompile",
            "src.generate",
        ]

        failed_imports = []
        for module in test_imports:
            try:
                cmd = [sys.executable, "-c", f"import {module}"]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    check=False,
                )
                if result.returncode != 0:
                    failed_imports.append((module, result.stderr))
            except Exception as e:
                failed_imports.append((module, str(e)))

        if failed_imports:
            for module, _error in failed_imports:
                pass
        else:
            pass

    def check_for_warnings(self, files_to_rename: list[tuple[Path, Path]]) -> None:
        """Check for potential issues with the renaming."""
        # Check for __init__.py files that might reference these modules
        for old_path, _new_path in files_to_rename:
            init_file = old_path.parent / "__init__.py"
            if init_file.exists():
                try:
                    with open(init_file, encoding="utf-8") as f:
                        content = f.read()
                    if old_path.stem in content:
                        self.critical_warnings.append(
                            f"{init_file.relative_to(self.project_root)} references {old_path.stem} - needs manual update"
                        )
                except Exception:
                    pass

        # Check for dynamic imports or string-based imports
        for py_file in self.project_root.rglob("*.py"):
            if (
                "__pycache__" in str(py_file)
                or ".venv" in str(py_file)
                or "venv" in str(py_file)
            ):
                continue
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()

                # Look for dynamic imports
                if "importlib.import_module" in content or "__import__" in content:
                    for old_path, _ in files_to_rename:
                        module_name = old_path.stem
                        if (
                            f'"{module_name}"' in content
                            or f"'{module_name}'" in content
                        ):
                            self.critical_warnings.append(
                                f"{py_file.relative_to(self.project_root)} may have dynamic imports of {module_name}"
                            )
                            break
            except Exception:
                pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rename files to follow naming conventions"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the renaming (default is dry-run)",
    )
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup")
    parser.add_argument(
        "--verify", action="store_true", help="Verify imports after renaming"
    )
    parser.add_argument(
        "--project-root", type=Path, default=Path.cwd(), help="Project root directory"
    )

    args = parser.parse_args()

    # Ensure we're in the right directory
    if not (args.project_root / "src").exists():
        sys.exit(1)

    renamer = FileRenamer(args.project_root, dry_run=not args.execute)

    # Create backup if executing
    if args.execute and not args.no_backup and not renamer.create_backup():
        sys.exit(1)

    # Perform renaming
    renamer.rename_files()

    # Verify imports if requested
    if args.execute and args.verify:
        renamer.verify_imports()

    if args.execute:
        pass


if __name__ == "__main__":
    main()
