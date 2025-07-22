#!/usr/bin/env python3
"""Fix imports after file renaming - comprehensive import updater."""

import re
from pathlib import Path

# Mapping of old names to new names
RENAME_MAPPING = {
    "decompile.decompile_coordinator": "decompile.decompile_coordinator",
    "decompile.decompile_factory": "decompile.decompile_factory",
    "contracts.models_contracts": "contracts.models_contracts",
    "contracts.extractors_contracts": "contracts.extractors_contracts",
    "contracts.events_contracts": "contracts.events_contracts",
    "contracts.decompilers_contracts": "contracts.decompilers_contracts",
    "contracts.parsers_contracts": "contracts.parsers_contracts",
    "contracts.generators_contracts": "contracts.generators_contracts",
    "contracts.pipeline_contracts": "contracts.pipeline_contracts",
    "contracts.state_contracts": "contracts.state_contracts",
    "parse.parse_coordinator": "parse.parse_coordinator",
    "parse.parse_factory": "parse.parse_factory",
    "common.distributed_manager": "common.distributed_manager",
    "common.stream_handler": "common.stream_handler",
    "model.model_coordinator": "model.model_coordinator",
    "model.model_factory": "model.model_factory",
    "generate.generate_coordinator": "generate.generate_coordinator",
    "generate.generate_factory": "generate.generate_factory",
    "extract.extract_coordinator": "extract.extract_coordinator",
    "extract.extract_factory": "extract.extract_factory",
}


def create_import_patterns() -> list[tuple[re.Pattern, str]]:
    """Create regex patterns for all import styles."""
    patterns = []

    for old_path, new_path in RENAME_MAPPING.items():
        # Pattern 1: from src.X.Y import Z
        patterns.append(
            (
                re.compile(rf"from\s+src\.{re.escape(old_path)}\s+import"),
                f"from src.{new_path} import",
            )
        )

        # Pattern 2: from X.Y import Z (without src prefix)
        patterns.append(
            (
                re.compile(rf"from\s+{re.escape(old_path)}\s+import"),
                f"from {new_path} import",
            )
        )

        # Pattern 3: import src.X.Y
        patterns.append(
            (
                re.compile(rf"import\s+src\.{re.escape(old_path)}(?![.\w])"),
                f"import src.{new_path}",
            )
        )

        # Pattern 4: import X.Y (without src prefix)
        patterns.append(
            (
                re.compile(rf"import\s+{re.escape(old_path)}(?![.\w])"),
                f"import {new_path}",
            )
        )

        # Pattern 5: Relative imports (from ..X.Y import Z)
        module_parts = old_path.split(".")
        if len(module_parts) == 2:
            old_module, old_file = module_parts
            new_module, new_file = new_path.split(".")
            # Match various relative import levels
            for dots in ["..", "...", "...."]:
                patterns.append(
                    (
                        re.compile(
                            rf"from\s+{dots}{re.escape(old_module)}\.{re.escape(old_file)}\s+import"
                        ),
                        f"from {dots}{new_module}.{new_file} import",
                    )
                )

        # Pattern 6: String references in code
        patterns.append(
            (re.compile(rf'["\']src\.{re.escape(old_path)}["\']'), f'"src.{new_path}"')
        )
        patterns.append(
            (re.compile(rf'["\']{re.escape(old_path)}["\']'), f'"{new_path}"')
        )

    return patterns


def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped."""
    skip_patterns = [
        "__pycache__",
        ".git",
        ".pytest_cache",
        "htmlcov",
        "backup_before_rename",
        "archive",
        ".pyc",
        ".pyo",
        ".egg-info",
        "node_modules",
    ]

    path_str = str(file_path)
    return any(pattern in path_str for pattern in skip_patterns)


def fix_imports_in_file(
    file_path: Path, patterns: list[tuple[re.Pattern, str]], dry_run: bool = True
) -> list[str]:
    """Fix imports in a single file."""
    changes = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return changes

    original_content = content

    # Apply all patterns
    for pattern, replacement in patterns:
        matches = pattern.findall(content)
        if matches:
            content = pattern.sub(replacement, content)
            for _match in set(matches):
                changes.append(f"  {pattern.pattern} -> {replacement}")

    # Write back if changes were made
    if content != original_content and not dry_run:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

    return changes


def fix_all_imports(project_root: Path, dry_run: bool = True) -> None:
    """Fix all imports in the project."""
    patterns = create_import_patterns()
    files_to_update = {}

    # Python files
    for py_file in project_root.rglob("*.py"):
        if should_skip_file(py_file):
            continue

        changes = fix_imports_in_file(py_file, patterns, dry_run)
        if changes:
            files_to_update[py_file] = changes

    # Documentation files (if not dry run)
    if not dry_run:
        for md_file in project_root.rglob("*.md"):
            if should_skip_file(md_file):
                continue

            changes = fix_imports_in_file(md_file, patterns, dry_run)
            if changes:
                files_to_update[md_file] = changes

    # Print summary

    for file_path, changes in sorted(files_to_update.items()):
        file_path.relative_to(project_root)
        for _change in sorted(set(changes)):
            pass

    if dry_run:
        pass
    else:
        pass


def main() -> None:
    """Main entry point."""
    import sys

    project_root = Path(__file__).parent.parent.parent
    dry_run = "--execute" not in sys.argv

    if dry_run:
        pass
    else:
        pass

    fix_all_imports(project_root, dry_run)


if __name__ == "__main__":
    main()
