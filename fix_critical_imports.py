#!/usr/bin/env python3
"""Fix critical imports after refactoring and consolidation."""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Define import mappings
IMPORT_MAPPINGS = [
    # Interface consolidation - All interfaces moved to src/contracts/interfaces.py
    (r'from src\.core\.pipeline_interfaces import', 'from src.contracts.interfaces import'),
    (r'from src\.common\.interfaces import', 'from src.contracts.interfaces import'),
    (r'from src\.base\.interfaces import', 'from src.contracts.interfaces import'),
    
    # Exception consolidation - Unified in src/core/exceptions.py
    (r'from src\.core\.exception_hierarchy import', 'from src.core.exceptions import'),
    (r'from src\.common\.exceptions_hierarchy import', 'from src.core.exceptions import'),
    (r'from src\.common\.exceptions import', 'from src.core.exceptions import'),
    
    # PBD consolidation - Multiple files merged into structures.py
    (r'from src\.extract\.pbd\.header import', 'from src.extract.pbd.structures import'),
    (r'from src\.extract\.pbd\.extraction import', 'from src.extract.pbd.extraction import'),
    (r'from src\.extract\.pbd\.recovery import', 'from src.extract.pbd.recovery import'),
    (r'from src\.extract\.pbd\.io_operations import', 'from src.extract.pbd.io import'),
    
    # Flattened directories
    (r'from src\.decompile\.utils\.version import', 'from src.decompile.version import'),
    (r'from src\.parse\.utils\.loader import', 'from src.parse.grammar_loader import'),
    (r'from src\.parse\.error_recovery\.strategy import', 'from src.parse.recovery_strategy import'),
    (r'from src\.decompile\.visualization\.visualizer import', 'from src.decompile.cfg_visualizer import'),
    
    # Removed re-exports
    (r'from src\.extract\.security\.limits import', 'from src.core.resource_limits import'),
    (r'from src\.common\.utils\.logging import', 'from src.common.logging import'),
    
    # Common module consolidations
    (r'from src\.common\.pipeline_streaming import', 'from src.common.pipeline.streaming import'),
    (r'from src\.common\.parallel_pipeline import', 'from src.common.pipeline.modes.parallel import'),
    (r'from src\.common\.streaming_pipeline import', 'from src.common.pipeline.modes.streaming import'),
    
    # Base module consolidations
    (r'from src\.base\.types import', 'from src.contracts.models import'),
    
    # Coordinator consolidations
    (r'from src\.common\.async_coordinators import', 'from src.common.coordinators import'),
    
    # DI consolidations
    (r'from src\.common\.dependency_injection import', 'from src.core.dependency_injection import'),
    
    # Event bus consolidations
    (r'from src\.common\.event_bus import', 'from src.core.events import'),
    
    # Security consolidations
    (r'from src\.common\.security import', 'from src.core.security import'),
    
    # State management consolidations
    (r'from src\.common\.state_management import', 'from src.core.state_management import'),
    
    # Circuit breaker consolidations
    (r'from src\.common\.circuit_breaker import', 'from src.core.circuit_breaker import'),
    
    # Cache consolidations
    (r'from src\.common\.cache import', 'from src.core.cache import'),
    
    # Distributed consolidations
    (r'from src\.common\.distributed import', 'from src.core.distributed import'),
    
    # Limits consolidations
    (r'from src\.common\.limits import', 'from src.core.resource_limits import'),
    
    # Error handling consolidations
    (r'from src\.common\.error_handling import', 'from src.core.errors import'),
]

def fix_imports_in_file(filepath: Path) -> Tuple[bool, List[str]]:
    """Fix imports in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, [f"Error reading file: {e}"]
    
    original_content = content
    changes = []
    
    for old_pattern, new_import in IMPORT_MAPPINGS:
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_import, content)
            changes.append(f"  {old_pattern} -> {new_import}")
    
    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        except Exception as e:
            return False, [f"Error writing file: {e}"]
    
    return False, []

def main():
    """Main function to fix imports across the codebase."""
    print("Fixing critical imports after refactoring...")
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('src'):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    # Also check main.py and test files
    if Path('main.py').exists():
        python_files.append(Path('main.py'))
    
    for root, dirs, files in os.walk('tests'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    # Fix imports
    files_modified = 0
    total_changes = 0
    
    for filepath in python_files:
        modified, changes = fix_imports_in_file(filepath)
        if modified:
            files_modified += 1
            total_changes += len(changes)
            print(f"\nFixed {filepath}:")
            for change in changes:
                print(change)
    
    print(f"\nSummary:")
    print(f"- Total files scanned: {len(python_files)}")
    print(f"- Files modified: {files_modified}")
    print(f"- Total import changes: {total_changes}")
    
    # Verify imports by attempting to import key modules
    print("\nVerifying imports...")
    verification_errors = []
    
    try:
        import src.contracts.interfaces
        print("✓ src.contracts.interfaces imports successfully")
    except ImportError as e:
        verification_errors.append(f"✗ src.contracts.interfaces: {e}")
    
    try:
        import src.core.exceptions
        print("✓ src.core.exceptions imports successfully")
    except ImportError as e:
        verification_errors.append(f"✗ src.core.exceptions: {e}")
    
    try:
        import src.extract.pbd.structures
        print("✓ src.extract.pbd.structures imports successfully")
    except ImportError as e:
        verification_errors.append(f"✗ src.extract.pbd.structures: {e}")
    
    if verification_errors:
        print("\nImport verification errors:")
        for error in verification_errors:
            print(error)
    else:
        print("\nAll critical imports verified successfully!")

if __name__ == "__main__":
    main()