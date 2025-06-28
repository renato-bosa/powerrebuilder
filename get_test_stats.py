#!/usr/bin/env python3
"""Get test statistics from pytest run."""

import subprocess
import re

def get_test_stats():
    """Run pytest and extract statistics."""
    print("Running tests...")
    
    # Run pytest with minimal output
    result = subprocess.run(
        ["python", "-m", "pytest", "--tb=no", "--no-cov", "-q"],
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    output = result.stdout + result.stderr
    
    # Extract statistics from output
    lines = output.strip().split('\n')
    
    # Look for the summary line
    for line in lines:
        if 'failed' in line or 'passed' in line:
            print(line)
    
    # Count test files
    test_files = subprocess.run(
        ["find", "tests", "-name", "test_*.py", "-type", "f"],
        capture_output=True,
        text=True
    )
    
    test_count = len(test_files.stdout.strip().split('\n'))
    print(f"\nTotal test files: {test_count}")
    
    # Show failed tests
    print("\nFailed tests:")
    for line in lines:
        if line.startswith("FAILED"):
            print(f"  {line}")

if __name__ == "__main__":
    get_test_stats()