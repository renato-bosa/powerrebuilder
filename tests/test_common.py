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
    # Conversion utilities
    safe_cast,
    safe_json_loads,
    snake_to_camel,
    to_bool,
    truncate,
)


# ─── Tests for File Operations ─────────────────────────────────────────────
def test_ensure_directory():

    
    """Test ensure_directory function."""
    with tempfile.TemporaryDirectory() as tempdir:
        # Create a new directory
        test_dir = os.path.join(tempdir, "test_dir")
        result = ensure_directory(test_dir)
        assert os.path.isdir(test_dir)
        assert isinstance(result, Path)

        # Creating an existing directory should work
        result2 = ensure_directory(test_dir)
        assert os.path.isdir(test_dir)
        assert isinstance(result2, Path)


def test_normalize_path():



    


    """Test normalize_path function."""
    # Normalize paths
    assert normalize_path("foo/./bar/../baz").name == "baz"

    # Test relative_to
    with tempfile.TemporaryDirectory() as tempdir:
        base_dir = Path(tempdir)
        child_dir = base_dir / "child"
        os.makedirs(child_dir)

        # Path is relative to base
        rel_path = normalize_path(child_dir, base_dir)
        assert rel_path == Path("child")

        # Path is not relative to base
        # Account for macOS symlinks where /tmp might resolve to /private/tmp
        other_dir = Path("/tmp")
        normalized_path = normalize_path(other_dir, base_dir)

        # There are different ways to handle this:
        # 1. Check that paths resolve to the same location
        assert normalized_path.resolve() == other_dir.resolve()

        # 2. On macOS, /tmp might be a symlink to /private/tmp
        # If not on macOS or if the paths match directly, this will still pass
        is_macos_tmp = (
            str(normalized_path) == "/private/tmp" and str(other_dir) == "/tmp"
        )
        assert normalized_path == other_dir or is_macos_tmp


def test_get_file_extension():



    


    """Test get_file_extension function."""
    # Standard cases
    assert get_file_extension("file.txt") == "txt"
    assert get_file_extension("file.TXT") == "txt"  # Case insensitive
    assert get_file_extension("file") == ""  # No extension
    assert get_file_extension("file.tar.gz") == "gz"  # Multiple dots

    # Path objects
    assert get_file_extension(Path("file.jpg")) == "jpg"


def test_read_file_safe():



    


    """Test read_file_safe function."""
    with tempfile.TemporaryDirectory() as tempdir:
        # Create a test file
        test_file = os.path.join(tempdir, "test.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Test content")

        # Read existing file
        assert read_file_safe(test_file) == "Test content"

        # Read non-existent file with default
        non_existent = os.path.join(tempdir, "nonexistent.txt")
        assert read_file_safe(non_existent, default="Default") == "Default"

        # Read non-existent file with raise_error=True
        with pytest.raises(FileNotFoundError):
            read_file_safe(non_existent, raise_error=True)


# ─── Tests for String Operations ────────────────────────────────────────────
def test_camel_to_snake():

    
    """Test camel_to_snake function."""
    assert camel_to_snake("camelCase") == "camel_case"
    assert camel_to_snake("CamelCase") == "camel_case"
    assert camel_to_snake("camelCaseText") == "camel_case_text"
    assert camel_to_snake("HTTPRequest") == "http_request"
    assert camel_to_snake("simpleText") == "simple_text"
    assert camel_to_snake("simple") == "simple"
    assert camel_to_snake("") == ""


def test_snake_to_camel():



    


    """Test snake_to_camel function."""
    assert snake_to_camel("snake_case") == "snakeCase"
    assert snake_to_camel("snake_case_text") == "snakeCaseText"
    assert snake_to_camel("simple") == "simple"
    assert snake_to_camel("") == ""

    # PascalCase
    assert snake_to_camel("snake_case", capitalize_first=True) == "SnakeCase"
    assert snake_to_camel("simple", capitalize_first=True) == "Simple"


def test_pluralize():



    


    """Test pluralize function."""
    # Count = 1 (singular)
    assert pluralize("apple", 1) == "apple"
    assert pluralize("box", 1) == "box"
    assert pluralize("city", 1) == "city"

    # Count != 1 (plural)
    assert pluralize("apple", 0) == "apples"
    assert pluralize("apple", 2) == "apples"

    # Special cases
    assert pluralize("box", 2) == "boxes"  # Ends with 's', 'x', 'z', 'ch', 'sh'
    assert pluralize("city", 2) == "cities"  # Ends with 'y'
    assert pluralize("quiz", 2) == "quizes"
    assert pluralize("match", 2) == "matches"
    assert pluralize("dish", 2) == "dishes"


def test_truncate():



    


    """Test truncate function."""
    # No truncation needed
    assert truncate("short text", 20) == "short text"

    # Truncation needed
    assert truncate("This is a long text", 10) == "This is..."

    # Custom suffix
    assert truncate("This is a long text", 10, suffix="…") == "This is a…"

    # Edge cases
    assert truncate("", 10) == ""
    assert truncate("short", 5) == "short"
    assert truncate("exactly", 7) == "exactly"


def test_format_timestamp():



    


    """Test format_timestamp function."""
    # Test with specific timestamp
    timestamp = 1640995200  # 2022-01-01 00:00:00 UTC

    # Test with custom format - just check the date which is safe regardless of timezone
    assert format_timestamp(timestamp, fmt="%Y-%m-%d") == "2022-01-01"

    # Test the format rather than exact time (to handle timezone differences)
    formatted = format_timestamp(timestamp)
    assert formatted.startswith("2022-01-01")  # Date should be correct
    assert len(formatted) == 19  # Should be in format "YYYY-MM-DD HH:MM:SS"
    assert formatted[10] == " "  # Space between date and time
    assert formatted[13] == ":"  # Hours/minutes separator
    assert formatted[16] == ":"  # Minutes/seconds separator

    # Test without timestamp (current time)
    # Just check format to avoid timing issues
    current = format_timestamp()
    assert len(current) == 19  # YYYY-MM-DD HH:MM:SS format
    assert current.count("-") == 2
    assert current.count(":") == 2


# ─── Tests for Collection Operations ─────────────────────────────────────────
def test_merge_dicts():

    
    """Test merge_dicts function."""
    # Basic merge
    d1 = {"a": 1, "b": 2}
    d2 = {"c": 3, "d": 4}
    assert merge_dicts(d1, d2) == {"a": 1, "b": 2, "c": 3, "d": 4}

    # Merge with overlap (default: overwrite=True)
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 3, "c": 4}
    assert merge_dicts(d1, d2) == {"a": 1, "b": 3, "c": 4}

    # Merge with overlap (overwrite=False)
    assert merge_dicts(d1, d2, overwrite=False) == {"a": 1, "b": 2, "c": 4}

    # Original dicts unchanged
    assert d1 == {"a": 1, "b": 2}
    assert d2 == {"b": 3, "c": 4}


def test_filter_dict():



    


    """Test filter_dict function."""
    d = {"a": 1, "b": 2, "c": 3, "d": 4}

    # Include specific keys
    assert filter_dict(d, keys=["a", "c"]) == {"a": 1, "c": 3}

    # Include non-existent keys
    assert filter_dict(d, keys=["a", "x"]) == {"a": 1}

    # Exclude specific keys
    assert filter_dict(d, exclude_keys=["b", "d"]) == {"a": 1, "c": 3}

    # Include and exclude
    assert filter_dict(d, keys=["a", "b", "c"], exclude_keys=["b"]) == {"a": 1, "c": 3}

    # Original dict unchanged
    assert d == {"a": 1, "b": 2, "c": 3, "d": 4}


def test_chunk_list():



    


    """Test chunk_list function."""
    # Even chunks
    assert chunk_list([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

    # Uneven chunks
    assert chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

    # Chunk size larger than list
    assert chunk_list([1, 2, 3], 5) == [[1, 2, 3]]

    # Empty list
    assert chunk_list([], 2) == []


def test_find_duplicates():



    


    """Test find_duplicates function."""
    # No duplicates
    assert find_duplicates([1, 2, 3, 4]) == []

    # Single duplicate
    assert sorted(find_duplicates([1, 2, 3, 2, 4])) == [2]

    # Multiple duplicates
    assert sorted(find_duplicates([1, 2, 3, 1, 2, 4])) == [1, 2]

    # String duplicates
    assert sorted(find_duplicates(["a", "b", "a", "c"])) == ["a"]

    # Empty list
    assert find_duplicates([]) == []


# ─── Tests for Conversion Utilities ─────────────────────────────────────────
def test_to_bool():

    
    """Test to_bool function."""
    # True values
    assert to_bool(True) is True
    assert to_bool(1) is True
    assert to_bool("yes") is True
    assert to_bool("true") is True
    assert to_bool("True") is True
    assert to_bool("YES") is True
    assert to_bool("y") is True
    assert to_bool("1") is True
    assert to_bool("on") is True

    # False values
    assert to_bool(False) is False
    assert to_bool(0) is False
    assert to_bool("no") is False
    assert to_bool("false") is False
    assert to_bool("False") is False
    assert to_bool("NO") is False
    assert to_bool("n") is False
    assert to_bool("0") is False
    assert to_bool("off") is False
    assert to_bool("") is False

    # Other values (bool() coercion)
    assert to_bool([]) is False
    assert to_bool([1, 2]) is True


def test_safe_json_loads():



    


    """Test safe_json_loads function."""
    # Valid JSON
    assert safe_json_loads('{"a": 1, "b": 2}') == {"a": 1, "b": 2}
    assert safe_json_loads('["a", "b", "c"]') == ["a", "b", "c"]
    assert safe_json_loads("123") == 123

    # Invalid JSON
    assert safe_json_loads('{"a": 1,}') is None
    assert safe_json_loads("invalid") is None

    # Invalid JSON with default
    assert safe_json_loads("invalid", default=[]) == []
    assert safe_json_loads("invalid", default={"error": True}) == {"error": True}


def test_safe_cast():



    


    """Test safe_cast function."""
    # Successful casts
    assert safe_cast("123", int) == 123
    assert safe_cast("3.14", float) == 3.14
    assert safe_cast(123, str) == "123"

    # Failed casts with default=None
    assert safe_cast("abc", int) is None
    assert safe_cast("abc", float) is None

    # Failed casts with custom default
    assert safe_cast("abc", int, 0) == 0
    assert safe_cast(None, str, "") == ""
