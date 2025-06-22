#!/usr/bin/env python3
"""Script to clean up the SIME Finch project directory."""

import shutil
from pathlib import Path


def cleanup_project() -> None:



    
    


    """Perform comprehensive project cleanup."""
    project_root = Path(__file__).parent.parent.parent

    # Phase 1: Remove backup directory
    backup_dir = project_root / "backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    # Phase 2: Remove empty directories
    empty_dirs = [
        "scripts/opcode_analysis",
        "tests/test_extract",
        "extract/cli",
    ]

    for dir_path in empty_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            # Check if directory is truly empty
            if not any(full_path.iterdir()):
                full_path.rmdir()
            else:
                pass

    # Phase 3: Remove main.py.backup
    main_backup = project_root / "main.py.backup"
    if main_backup.exists():
        main_backup.unlink()

    # Phase 4: Remove stub files
    stub_files = [
        "model/pb_datawindow/datawindow_stubs.py",
        "model/pb_transaction/transaction_stubs.py",
    ]

    for stub_path in stub_files:
        full_path = project_root / stub_path
        if full_path.exists():
            full_path.unlink()

    # Phase 5: Remove duplicate reference implementations
    duplicate_refs = [
        "reference/powerbuilder-decompile",  # Keep only in decompilers/
    ]

    for ref_path in duplicate_refs:
        full_path = project_root / ref_path
        if full_path.exists():
            shutil.rmtree(full_path)


if __name__ == "__main__":
    cleanup_project()
