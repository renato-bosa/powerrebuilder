"""Tests for common utility functions."""

import os
import tempfile
from pathlib import Path

import pytest

from model.utils.common import (
    # String operations
    camel_to_snake,
    # Collection operations
    chunk_list,
    # File operations
    ensure_directory,
    filter_dict,
    find_duplicates,
    format_timestamp,
    get_file_extension,
    merge_dicts,
    normalize_path,
    pluralize,
    read_file_safe,
    safe_cast,
    safe_json_loads,
    snake_to_camel,
    to_bool,
    truncate,
)


def test_camel_to_snake():
    """Test camelCase to snake_case conversion."""
    assert camel_to_snake("camelCase") == "camel_case"
    assert camel_to_snake("PascalCase") == "pascal_case"
    assert camel_to_snake("ALLCAPS") == "allcaps"
    assert camel_to_snake("mixedUPPERCase") == "mixed_upper_case"


def test_ensure_directory():
    """Test ensure_directory function."""
    with tempfile.TemporaryDirectory() as tempdir:
        # Create nested directory
        test_path = Path(tempdir) / "nested" / "dir"
        result = ensure_directory(test_path)
        assert result == test_path
        assert test_path.exists()
        assert test_path.is_dir()


def test_normalize_path():
    """Test normalize_path function."""
    # Normalize paths - should return string with forward slashes
    assert normalize_path("foo\\bar\\baz") == "foo/bar/baz"
    assert normalize_path(Path("foo/bar")) == "foo/bar"
    
    # Test with Path objects containing backslashes (Windows-style)
    assert normalize_path("C:\\Users\\test") == "C:/Users/test"
    
    # Test that it handles Path objects correctly
    path_obj = Path("some/path/here")
    assert normalize_path(path_obj) == "some/path/here"
    
    # Test empty path
    assert normalize_path("") == "."
    
    # Test current directory
    assert normalize_path(".") == "."


def test_chunk_list():
    """Test chunk_list function."""
    lst = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    # Chunk into groups of 3
    chunks = chunk_list(lst, 3)
    assert chunks == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    
    # Chunk with remainder
    chunks = chunk_list(lst, 4)
    assert chunks == [[1, 2, 3, 4], [5, 6, 7, 8], [9]]
    
    # Empty list
    assert chunk_list([], 3) == []
    
    # Chunk size larger than list
    assert chunk_list([1, 2], 5) == [[1, 2]]


def test_filter_dict():
    """Test filter_dict function."""
    d = {"a": 1, "b": 2, "c": 3, "d": 4}
    
    # Filter specific keys
    filtered = filter_dict(d, ["a", "c"])
    assert filtered == {"a": 1, "c": 3}
    
    # Filter non-existent keys
    filtered = filter_dict(d, ["x", "y"])
    assert filtered == {}
    
    # Filter mix of existing and non-existing
    filtered = filter_dict(d, ["a", "x", "d"])
    assert filtered == {"a": 1, "d": 4}


def test_find_duplicates():
    """Test find_duplicates function."""
    # List with duplicates
    lst = [1, 2, 3, 2, 4, 3, 3]
    duplicates = find_duplicates(lst)
    assert set(duplicates) == {2, 3}
    
    # No duplicates
    assert find_duplicates([1, 2, 3, 4]) == []
    
    # All duplicates
    assert find_duplicates([1, 1, 1, 1]) == [1]
    
    # String duplicates
    assert find_duplicates(["a", "b", "a", "c", "b"]) == ["a", "b"]


def test_snake_to_camel():
    """Test snake_case to camelCase conversion."""
    assert snake_to_camel("snake_case") == "snakeCase"
    assert snake_to_camel("long_snake_case_name") == "longSnakeCaseName"
    assert snake_to_camel("single") == "single"
    assert snake_to_camel("_private") == "Private"


def test_get_file_extension():
    """Test get_file_extension function."""
    assert get_file_extension("file.txt") == "txt"
    assert get_file_extension("path/to/file.py") == "py"
    assert get_file_extension(Path("file.tar.gz")) == "gz"
    assert get_file_extension("no_extension") == ""
    assert get_file_extension(".hidden") == ""


def test_merge_dicts():
    """Test merge_dicts function."""
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 3, "c": 4}
    d3 = {"c": 5, "d": 6}
    
    # Merge two dicts
    merged = merge_dicts(d1, d2)
    assert merged == {"a": 1, "b": 3, "c": 4}
    
    # Merge multiple dicts
    merged = merge_dicts(d1, d2, d3)
    assert merged == {"a": 1, "b": 3, "c": 5, "d": 6}
    
    # Empty dicts
    assert merge_dicts({}, {}) == {}
    assert merge_dicts(d1, {}) == d1


def test_pluralize():
    """Test pluralize function."""
    assert pluralize("item", 0) == "items"
    assert pluralize("item", 1) == "item"
    assert pluralize("item", 2) == "items"
    assert pluralize("box", 5) == "boxs"  # Simple pluralization


def test_safe_cast():
    """Test safe_cast function."""
    # Successful casts
    assert safe_cast("123", int) == 123
    assert safe_cast("3.14", float) == 3.14
    assert safe_cast(1, str) == "1"
    
    # Failed casts with default
    assert safe_cast("abc", int, default=-1) == -1
    assert safe_cast(None, int, default=0) == 0
    
    # Failed casts without default
    assert safe_cast("xyz", int) is None


def test_to_bool():
    """Test to_bool function."""
    # Boolean values
    assert to_bool(True) is True
    assert to_bool(False) is False
    
    # String values
    assert to_bool("true") is True
    assert to_bool("True") is True
    assert to_bool("yes") is True
    assert to_bool("1") is True
    assert to_bool("on") is True
    assert to_bool("false") is False
    assert to_bool("no") is False
    assert to_bool("0") is False
    assert to_bool("off") is False
    
    # Other values
    assert to_bool(1) is True
    assert to_bool(0) is False
    assert to_bool([1]) is True
    assert to_bool([]) is False


def test_truncate():
    """Test truncate function."""
    # No truncation needed
    assert truncate("short", 10) == "short"
    
    # Truncation needed
    assert truncate("this is a long string", 10) == "this is..."
    assert truncate("this is a long string", 15) == "this is a lo..."
    
    # Custom suffix
    assert truncate("truncate me", 8, suffix="~") == "truncat~"
    
    # Edge cases
    assert truncate("", 5) == ""
    assert truncate("x", 1) == "x"


def test_format_timestamp():
    """Test format_timestamp function."""
    # Specific timestamp
    ts = 1609459200.0  # 2021-01-01 00:00:00 UTC
    formatted = format_timestamp(ts)
    assert "2021" in formatted
    
    # Current timestamp (just check format)
    current = format_timestamp()
    assert len(current) > 10
    assert "T" in current  # ISO format


def test_read_file_safe():
    """Test read_file_safe function."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        # Successful read
        content = read_file_safe(temp_path)
        assert content == "test content"
        
        # Non-existent file
        assert read_file_safe("/non/existent/file.txt") is None
    finally:
        os.unlink(temp_path)


def test_safe_json_loads():
    """Test safe_json_loads function."""
    # Valid JSON
    assert safe_json_loads('{"a": 1, "b": 2}') == {"a": 1, "b": 2}
    assert safe_json_loads('[1, 2, 3]') == [1, 2, 3]
    
    # Invalid JSON with default
    assert safe_json_loads("invalid json", default={}) == {}
    assert safe_json_loads("{incomplete", default=None) is None
    
    # Type error
    assert safe_json_loads(None, default=[]) == []