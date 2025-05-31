"""Test PowerBuilder file functionality."""

from pathlib import Path

from model.pb_file import PBCommonFile, PBSourceFile


def test_common_file():
    """Test common file functionality.

    Ported from reference/moose-pb-parser/PowerBuilder-Parser-AST/PWBASTCommonFile.class.st
    """
    # Create common file
    file = PBCommonFile(
        name="test_file",
        file_path=Path("common.pbl"),
    )

    # Add statements
    file.add_statement("global string gs_version = '1.0'")
    file.add_statement("global integer gi_count = 0")

    expected = """// common.pbl
global string gs_version = '1.0'
global integer gi_count = 0"""

    assert str(file) == expected
    assert len(file.get_statements()) == 2


def test_source_file():
    """Test source file functionality."""
    # Create source file
    file = PBSourceFile(
        name="test_source",
        file_path=Path("window.srw"),
        content="""window w_main
type(window)
end""",
    )

    expected = """// window.srw
window w_main
type(window)
end"""

    assert str(file) == expected
