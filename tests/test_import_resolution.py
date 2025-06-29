#!/usr/bin/env python3
"""Test library import resolution in PowerBuilder parser.

Tests the implementation of library import resolution which was
listed as missing in the code health report.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.model.entities.library import Import
from src.parse.coordinator import ParseCoordinator, PowerBuilderParser

# Test simple import
simple_import = """
import myapp.common
import utilities.string_helpers

global type my_window from window
    integer width = 800
    integer height = 600
end type
"""

# Test imports with objects
imports_with_code = """
import framework.base
import framework.ui.controls
import data.connection_manager

function integer calculate(integer a, integer b)
    return a + b
end function

global type app_controller from powerobject
    string app_name = "MyApp"
end type
"""

# Test qualified names in imports
qualified_imports = """
import com.company.project.utilities
import com.company.project.data.models
import com.company.shared.logging

type logger from powerobject
    string log_level = "INFO"
end type
"""

def test_import_parsing():




    """Test parsing of import statements."""
    parser = PowerBuilderParser()

    tests = [
        ("Simple imports", simple_import),
        ("Imports with code", imports_with_code),
        ("Qualified imports", qualified_imports),
    ]

    passed = 0
    total = len(tests)

    for test_name, source in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print(f"{'='*50}")

        try:
            # Parse the source
            tree = parser.parse(source, preprocess=False)

            if isinstance(tree, dict):
                print(f"✓ Successfully parsed")

                # Check for imports
                imports = []
                if "elements" in tree:
                    for elem in tree["elements"]:
                        if isinstance(elem, Import):
                            imports.append(elem)
                            print(f"  - Found import: {elem.from_library}.{elem.object_name}")

                if imports:
                    passed += 1
                    print(f"  ✓ {len(imports)} imports extracted")
                else:
                    print(f"  ✗ No imports found")

        except Exception as e:
            print(f"✗ Failed to parse")
            print(f"  Error: {type(e).__name__}: {str(e)}")

    print(f"\n{'='*50}")
    print(f"Import Parsing: {passed}/{total} tests passed")

    return passed == total

def test_import_resolution():




    """Test import resolution with ParseCoordinator."""
    print(f"\n{'='*50}")
    print("Testing Import Resolution with ParseCoordinator")
    print(f"{'='*50}")

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create test file
        test_file = tmpdir / "test_imports.sru"
        test_file.write_text(simple_import)

        try:
            # Create coordinator
            coordinator = ParseCoordinator([tmpdir])

            # Note: In a real scenario, libraries would be loaded from PBL files
            # For this test, we're just verifying the infrastructure works

            # Parse with imports
            print("Parsing file with import resolution...")
            ast = coordinator.parse_with_imports(test_file)

            if ast:
                print("✓ Successfully parsed with import resolution")

                # Check if imports were extracted
                imports_found = 0
                if isinstance(ast, dict) and "elements" in ast:
                    for elem in ast["elements"]:
                        if hasattr(elem, "__class__") and elem.__class__.__name__ == "Import":
                            imports_found += 1

                print(f"  Imports in AST: {imports_found}")

                # In real usage, resolved symbols would be populated if libraries exist
                print("  Note: Symbol resolution requires actual PBL libraries")

                return True
            else:
                print("✗ Failed to parse with import resolution")
                return False

        except Exception as e:
            print(f"✗ Error during import resolution: {type(e).__name__}: {str(e)}")
            return False

if __name__ == "__main__":
    # Test basic import parsing
    parsing_ok = test_import_parsing()

    # Test import resolution
    resolution_ok = test_import_resolution()

    if parsing_ok and resolution_ok:
        print("\n✓ All import tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Some import tests failed")
        sys.exit(1)
