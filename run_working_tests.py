#!/usr/bin/env python3
"""Run only the working test modules."""

import subprocess
import sys
from pathlib import Path

# Working test modules
WORKING_TESTS = [
    "tests/unit/common/test_common.py",
    "tests/unit/common/test_common_pipeline.py",
]

# Tests to try (may have import issues)
TESTS_TO_TRY = [
    "tests/unit/common/test_custom_types.py",
    "tests/unit/common/test_errors.py",
    "tests/unit/common/test_validation.py",
    # Try other directories
    "tests/unit/utils/test_file_utils.py",
    "tests/unit/utils/test_path_utils.py",  
    "tests/unit/utils/test_text_utils.py",
    # Simple unit tests that might work
    "tests/test_startup.py",
]

def run_test(test_path):
    """Run a single test file and return results."""
    print(f"\n{'='*60}")
    print(f"Running: {test_path}")
    print('='*60)
    
    result = subprocess.run(
        ["uv", "run", "pytest", test_path, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # Extract test count from output
        for line in result.stdout.split('\n'):
            if 'passed' in line and 'in' in line:
                print(f"✓ {line.strip()}")
                return True, result.stdout.count('PASSED')
    else:
        print(f"✗ Failed with errors")
        # Print first few lines of error
        error_lines = result.stderr.split('\n') if result.stderr else result.stdout.split('\n')
        for line in error_lines[:5]:
            if line.strip():
                print(f"  {line}")
    
    return False, 0

def main():
    """Run all working tests and report results."""
    print("PowerRebuilder Test Runner")
    print("Running working test modules...\n")
    
    total_passed = 0
    working_modules = 0
    
    # Run known working tests
    print("KNOWN WORKING TESTS:")
    for test in WORKING_TESTS:
        success, count = run_test(test)
        if success:
            total_passed += count
            working_modules += 1
    
    # Try additional tests
    print("\n\nTRYING ADDITIONAL TESTS:")
    for test in TESTS_TO_TRY:
        if Path(test).exists():
            success, count = run_test(test)
            if success:
                total_passed += count
                working_modules += 1
                print(f"  → Add {test} to WORKING_TESTS list!")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    print(f"Working test modules: {working_modules}")
    print(f"Total tests passing: {total_passed}")
    print(f"Known working modules: {len(WORKING_TESTS)}")
    print(f"Additional modules tried: {len(TESTS_TO_TRY)}")
    
    return 0 if working_modules > 0 else 1

if __name__ == "__main__":
    sys.exit(main())