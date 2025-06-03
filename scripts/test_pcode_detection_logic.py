#!/usr/bin/env python3
"""Test the P-code detection logic directly."""

import os
from pathlib import Path

# Source extensions from core.py
SOURCE_EXTENSIONS = ('.sru', '.srw', '.srd', '.srm', '.sra', '.srq', '.srs', '.srf', '.srj')

def test_pcode_detection():
    """Test various scenarios for P-code detection."""
    
    test_cases = [
        # (objectname, version, expected_result, description)
        ("n_cst_mailsession.udo", "0.6.0.0", False, "User data object with PB version"),
        ("w_mail_test.win", "0.6.0.0", False, "Window with PB version"),
        ("n_test.sru", "0.6.0.0", False, "Source file with PB version - NO function/event"),
        ("n_test.sru", "function", True, "Source file with 'function' version"),
        ("n_test.sru", "event handler", True, "Source file with 'event' in version"),
        ("test.srf", "0.6.0.0", True, "SRF file - always P-code"),
        ("test.srj", "whatever", True, "SRJ file - always P-code"),
        ("w_window.srw", "window", False, "Window source without function/event"),
        ("f_function.srf", "pfcasads", True, "Special SRF file"),
    ]
    
    print("Testing P-code detection logic")
    print("=" * 80)
    print(f"{'Object Name':<30} {'Version':<20} {'P-code?':<10} {'Description':<40}")
    print("-" * 80)
    
    for objectname, version, expected, description in test_cases:
        # Apply the exact logic from core.py
        is_potential_pcode = (objectname.lower().endswith(tuple(SOURCE_EXTENSIONS)) and
                             ("function" in version.lower() or "event" in version.lower())) or \
                             objectname.lower().endswith((".srf", ".srj"))
        
        result = "YES" if is_potential_pcode else "NO"
        expected_str = "YES" if expected else "NO"
        status = "✓" if is_potential_pcode == expected else "✗"
        
        print(f"{objectname:<30} {version:<20} {result:<10} {description:<40} {status}")
    
    print("\n" + "=" * 80)
    print("Key findings:")
    print("1. The version field in PBD entries contains the PowerBuilder version (e.g., '0.6.0.0')")
    print("2. P-code detection expects 'function' or 'event' in the version string")
    print("3. Only .srf and .srj files are always detected as P-code")
    print("4. Regular source files (.sru, .srw, etc.) won't be detected as P-code with PB version strings")
    print("\nThis explains why .fun files are not being created!")

if __name__ == "__main__":
    test_pcode_detection()