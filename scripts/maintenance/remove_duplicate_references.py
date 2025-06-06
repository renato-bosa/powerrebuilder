#!/usr/bin/env python3
"""Script to remove duplicate reference implementations."""

import shutil
from pathlib import Path


def remove_duplicate_references():
    """Remove duplicate reference implementations."""
    project_root = Path(__file__).parent.parent.parent
    
    # Remove duplicate pbdviewer (keep the one in decompilers/)
    duplicate_pbdviewer = project_root / "reference" / "pbdviewer"
    if duplicate_pbdviewer.exists():
        print(f"Removing duplicate pbdviewer: {duplicate_pbdviewer}")
        shutil.rmtree(duplicate_pbdviewer)
        print("✓ Removed reference/pbdviewer (keeping reference/decompilers/pbdviewer)")
    
    print("\nReference consolidation complete!")


if __name__ == "__main__":
    remove_duplicate_references()