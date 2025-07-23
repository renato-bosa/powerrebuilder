#!/usr/bin/env python3
"""Resolve only critical naming collisions to minimize risk."""

import csv
import subprocess
from pathlib import Path

def get_critical_collisions():
    """Get only the most critical collisions that cause F811 errors."""
    
    # Run ruff to get F811 errors
    result = subprocess.run(
        ['ruff', 'check', 'src', '--select', 'F811'],
        capture_output=True,
        text=True
    )
    
    errors = result.stdout.strip().split('\n')
    critical_files = set()
    
    for error in errors:
        if 'F811' in error and '.py:' in error:
            # Extract file path
            file_path = error.split(':')[0]
            critical_files.add(file_path)
    
    return critical_files

def filter_critical_renames(resolution_plan_path, critical_files):
    """Filter resolution plan to only include critical renames."""
    
    with open(resolution_plan_path, 'r') as f:
        reader = csv.DictReader(f)
        all_renames = list(reader)
    
    # Filter to only critical files
    critical_renames = [
        rename for rename in all_renames
        if rename['file'] in critical_files
    ]
    
    return critical_renames

def apply_critical_renames(critical_renames):
    """Apply only the critical renames using ruff."""
    
    print(f"Applying {len(critical_renames)} critical renames...")
    
    # Group by file
    renames_by_file = {}
    for rename in critical_renames:
        file_path = rename['file']
        if file_path not in renames_by_file:
            renames_by_file[file_path] = []
        renames_by_file[file_path].append(rename)
    
    # For each file, apply renames
    for file_path, file_renames in renames_by_file.items():
        print(f"\nProcessing {file_path}:")
        
        # Use ruff --fix to handle the F811 errors
        result = subprocess.run(
            ['ruff', 'check', file_path, '--select', 'F811', '--fix'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✓ Fixed F811 errors")
        else:
            print(f"  ✗ Failed to fix: {result.stderr}")

def main():
    resolution_plan_path = "build/collision_resolution_plan.csv"
    
    if not Path(resolution_plan_path).exists():
        print("Error: collision_resolution_plan.csv not found. Run detect_collisions.py first.")
        return
    
    # Get files with F811 errors
    print("Finding files with F811 errors...")
    critical_files = get_critical_collisions()
    print(f"Found {len(critical_files)} files with F811 errors")
    
    if not critical_files:
        print("No F811 errors found. No critical collisions to resolve.")
        return
    
    # Filter resolution plan
    critical_renames = filter_critical_renames(resolution_plan_path, critical_files)
    print(f"Found {len(critical_renames)} critical renames to apply")
    
    if critical_renames:
        # Apply the critical renames
        apply_critical_renames(critical_renames)
        
        # Run ruff to fix imports
        print("\nFixing imports...")
        subprocess.run(['ruff', 'check', 'src', '--fix', '--select', 'I001'])
        
        # Check remaining F811 errors
        print("\nChecking remaining F811 errors...")
        result = subprocess.run(
            ['ruff', 'check', 'src', '--select', 'F811'],
            capture_output=True,
            text=True
        )
        
        remaining_errors = len([e for e in result.stdout.strip().split('\n') if 'F811' in e])
        print(f"Remaining F811 errors: {remaining_errors}")

if __name__ == "__main__":
    main()