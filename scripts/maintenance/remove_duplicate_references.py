#!/usr/bin/env python3
"""Script to remove duplicate reference implementations."""

import shutil
from pathlib import Path


def remove_duplicate_references() -> None:



    
    


    """Remove duplicate reference implementations."""
    project_root = Path(__file__).parent.parent.parent

    # Remove duplicate pbdviewer (keep the one in decompilers/)
    duplicate_pbdviewer = project_root / "reference" / "pbdviewer"
    if duplicate_pbdviewer.exists():
        shutil.rmtree(duplicate_pbdviewer)


if __name__ == "__main__":
    remove_duplicate_references()
