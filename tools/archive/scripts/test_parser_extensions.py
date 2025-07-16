#!/usr/bin/env python3
"""Test parser support for .dwo and .sql files."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parse.parsers.base_parser import PowerBuilderBaseParser
from src.parse.parse_coordinator import PowerBuilderDataWindowParser
from src.parse.parsers.sql_parser import PowerBuilderSQLParser


def test_parser_registration():




    """Test that parsers are registered for new extensions."""
    print("Testing parser registration...")
    print("=" * 60)

    # Check registered parsers
    print("\nRegistered parsers:")
    for ext, parser_cls in PowerBuilderBaseParser._parsers.items():
        print(f"  .{ext} -> {parser_cls.__name__}")

    # Test extension support
    extensions_to_test = ["srd", "dwo", "sql", "srq"]

    print("\nTesting extension support:")
    for ext in extensions_to_test:
        try:
            parser_cls = PowerBuilderBaseParser.get_parser_for_extension(ext)
            print(f"  .{ext}: ✓ {parser_cls.__name__}")
        except ValueError as e:
            print(f"  .{ext}: ✗ {e}")

    # Check DataWindow parser
    print("\nDataWindow parser supports:", PowerBuilderDataWindowParser.supported_extensions())

    # Check SQL parser
    print("SQL parser supports:", PowerBuilderSQLParser.supported_extensions())

def test_parser_instantiation():




    """Test that parsers can be instantiated."""
    print("\n\nTesting parser instantiation...")
    print("=" * 60)

    # Test DataWindow parser for .dwo
    try:
        dw_parser = PowerBuilderDataWindowParser()
        print("DataWindow parser: ✓ Created successfully")
    except Exception as e:
        print(f"DataWindow parser: ✗ {e}")

    # Test SQL parser for .sql
    try:
        sql_parser = PowerBuilderSQLParser()
        print("SQL parser: ✓ Created successfully")
    except Exception as e:
        print(f"SQL parser: ✗ {e}")

if __name__ == "__main__":
    test_parser_registration()
    test_parser_instantiation()
