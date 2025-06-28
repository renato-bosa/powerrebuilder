#!/usr/bin/env python3
"""Run all tests without fail-fast and analyze results."""

import subprocess
import re
from collections import defaultdict

def run_tests():
    """Run pytest without fail-fast and capture results."""
    print("Running all tests without fail-fast...")
    
    result = subprocess.run(
        ["python", "-m", "pytest", "--tb=short", "--no-cov", "--maxfail=0", "-v"],
        capture_output=True,
        text=True
    )
    
    return result.stdout + result.stderr

def analyze_results(output):
    """Analyze test output and categorize failures."""
    
    # Extract summary line
    summary_match = re.search(r'(\d+) failed.*?(\d+) passed', output)
    if summary_match:
        failed = summary_match.group(1)
        passed = summary_match.group(2)
        print(f"\nTest Summary: {failed} failed, {passed} passed")
    
    # Extract failed tests
    failures = defaultdict(list)
    for line in output.split('\n'):
        if line.startswith('FAILED'):
            # Extract module and test name
            match = re.match(r'FAILED tests/(.+?)::(.+?) - (.+)', line)
            if match:
                module = match.group(1).split('/')[0]
                test = match.group(2)
                error = match.group(3)
                failures[module].append({
                    'test': test,
                    'error': error
                })
    
    # Print categorized failures
    print("\nFailures by Module:")
    for module, tests in sorted(failures.items()):
        print(f"\n{module}: {len(tests)} failures")
        for test in tests[:5]:  # Show first 5
            print(f"  - {test['test']}")
            print(f"    Error: {test['error'][:80]}...")
    
    # Extract import errors
    import_errors = []
    for line in output.split('\n'):
        if 'ImportError' in line or 'ModuleNotFoundError' in line:
            import_errors.append(line.strip())
    
    if import_errors:
        print("\nImport Errors Found:")
        for error in import_errors[:10]:  # Show first 10
            print(f"  {error[:100]}...")
    
    return failures

def main():
    output = run_tests()
    
    # Save full output
    with open('full_test_results.txt', 'w') as f:
        f.write(output)
    
    print("Full test output saved to full_test_results.txt")
    
    # Analyze results
    failures = analyze_results(output)
    
    # Save summary
    with open('test_summary.txt', 'w') as f:
        f.write(f"Test Failures by Module:\n")
        for module, tests in sorted(failures.items()):
            f.write(f"\n{module}: {len(tests)} failures\n")
            for test in tests:
                f.write(f"  - {test['test']}\n")
                f.write(f"    {test['error']}\n")

if __name__ == '__main__':
    main()