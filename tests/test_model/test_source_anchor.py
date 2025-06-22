"""Tests for source anchor functionality."""

from pathlib import Path

from model.source.anchor import FileAnchor, MultipleAnchor


def test_file_anchor_basic(tmp_path: Path) -> None:



    
    


    """Test basic file anchor functionality."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line 1\nline 2")

    anchor = FileAnchor(str(test_file), 1, 2)
    assert anchor.get_source() == "line 1\nline 2"


def test_file_anchor_with_columns(tmp_path: Path) -> None:



    
    


    """Test file anchor with column selection."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("line 1\nline 2")

    anchor = FileAnchor(str(test_file), 1, 2, 2, 5)
    assert anchor.get_source() == "ine 1\nine 2"


def test_file_anchor_invalid() -> None:



    
    


    """Test file anchor with invalid file."""
    anchor = FileAnchor("nonexistent.txt", 1, 2)
    assert anchor.get_source() is None


def test_multiple_anchor(tmp_path: Path) -> None:



    
    


    """Test multiple anchor functionality."""
    # Create test files
    file1 = tmp_path / "test1.txt"
    file2 = tmp_path / "test2.txt"
    file1.write_text("file1 line1\nfile1 line2")
    file2.write_text("file2 line1\nfile2 line2")

    # Create anchors
    anchor1 = FileAnchor(str(file1), 1, 2)
    anchor2 = FileAnchor(str(file2), 1, 2)
    multiple = MultipleAnchor([anchor1, anchor2])

    # Test source retrieval
    assert multiple.get_source() == "file1 line1\nfile1 line2\nfile2 line1\nfile2 line2"


def test_multiple_anchor_empty() -> None:



    
    


    """Test multiple anchor with no anchors."""
    multiple = MultipleAnchor([])
    assert multiple.get_source() is None


def test_multiple_anchor_partial_failure(tmp_path: Path) -> None:



    
    


    """Test multiple anchor with some failing anchors."""
    # Create one good file and one bad reference
    test_file = tmp_path / "test.txt"
    test_file.write_text("test line")

    good_anchor = FileAnchor(str(test_file), 1, 1)
    bad_anchor = FileAnchor("nonexistent.txt", 1, 1)
    multiple = MultipleAnchor([good_anchor, bad_anchor])

    # Should still get content from good anchor
    assert multiple.get_source() == "test line"
