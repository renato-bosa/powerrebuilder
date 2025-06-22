"""Tests for PowerBuilder model utility functions."""

import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from common.exceptions import (
    DecompileError,
    ExtractError,
    GenerateError,
    ModelError,
    ParseError,
    PowerBuilderError,
    SimeFinchError,
    TypeValidationError,
    ValidationError,
)
from model.utils.base import PBNode
from model.utils.common import (
    camel_to_snake,
    chunk_list,
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


class TestPBNodeBase:
    """Test the PBNode base class functionality."""

    def test_pbnode_equality(self):




        """Test PBNode equality comparison."""
        node1 = PBNode()
        node2 = PBNode()

        # Equal nodes
        assert node1 == node2

        # Different position
        node1.start_position = 10
        assert node1 != node2

        # Same values again
        node2.start_position = 10
        assert node1 == node2

    def test_pbnode_hash(self):




        """Test PBNode hashing."""
        node1 = PBNode()
        node2 = PBNode()

        # Equal nodes have same hash
        assert hash(node1) == hash(node2)

        # Can be used in sets
        node_set = {node1, node2}
        assert len(node_set) == 1  # Same node

        # Different nodes have different hashes
        node1.start_position = 10
        assert hash(node1) != hash(node2)

    def test_pbnode_validate(self):




        """Test PBNode validation."""
        node = PBNode()

        # Base validation always passes
        assert node.validate() is True
        assert node.validate({"some": "context"}) is True


class TestCommonUtils:
    """Test common utility functions."""

    def test_camel_to_snake(self):




        """Test camelCase to snake_case conversion."""
        assert camel_to_snake("CamelCase") == "camel_case"
        assert camel_to_snake("myVariableName") == "my_variable_name"
        assert camel_to_snake("XMLParser") == "xml_parser"
        assert camel_to_snake("already_snake") == "already_snake"
        assert camel_to_snake("") == ""

    def test_snake_to_camel(self):




        """Test snake_case to camelCase conversion."""
        assert snake_to_camel("snake_case") == "snakeCase"
        assert snake_to_camel("snake_case", capitalize_first=True) == "SnakeCase"
        assert snake_to_camel("my_variable_name") == "myVariableName"
        assert snake_to_camel("already_camel") == "alreadyCamel"
        assert snake_to_camel("") == ""

    def test_pluralize(self):




        """Test word pluralization."""
        assert pluralize("item", 0) == "items"
        assert pluralize("item", 1) == "item"
        assert pluralize("item", 2) == "items"
        assert pluralize("item", 100) == "items"

    def test_truncate(self):




        """Test string truncation."""
        assert truncate("short", 10) == "short"
        assert truncate("this is a long string", 10) == "this is..."
        assert truncate("this is a long string", 10, "…") == "this is a…"
        assert truncate("", 10) == ""

    def test_get_file_extension(self):




        """Test file extension extraction."""
        assert get_file_extension("file.txt") == "txt"
        assert get_file_extension("archive.tar.gz") == "gz"
        assert get_file_extension("/path/to/file.py") == "py"
        assert get_file_extension("no_extension") == ""
        assert get_file_extension(Path("file.md")) == "md"

    def test_merge_dicts(self):




        """Test dictionary merging."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 3, "c": 4}

        # Basic merge (overwrite=True by default)
        result = merge_dicts(dict1, dict2)
        assert result == {"a": 1, "b": 3, "c": 4}

        # Merge without overwrite
        result = merge_dicts(dict1, dict2, overwrite=False)
        assert result == {"a": 1, "b": 2, "c": 4}

        # Empty dictionaries
        assert merge_dicts({}, {}) == {}
        assert merge_dicts(dict1, {}) == dict1
        assert merge_dicts({}, dict2) == dict2

    def test_filter_dict(self):




        """Test dictionary filtering."""
        data = {"a": 1, "b": 2, "c": 3, "d": 4}

        # Filter by keys to include
        result = filter_dict(data, keys=["a", "b"])
        assert result == {"a": 1, "b": 2}

        # Filter by keys to exclude
        result = filter_dict(data, exclude_keys=["c", "d"])
        assert result == {"a": 1, "b": 2}

        # Both include and exclude
        result = filter_dict(data, keys=["a", "b", "c"], exclude_keys=["c"])
        assert result == {"a": 1, "b": 2}

        # No filtering
        result = filter_dict(data)
        assert result == data

    def test_chunk_list(self):




        """Test list chunking."""
        lst = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        # Even chunks
        assert chunk_list(lst, 3) == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

        # Uneven chunks
        assert chunk_list(lst, 4) == [[1, 2, 3, 4], [5, 6, 7, 8], [9]]

        # Chunk size larger than list
        assert chunk_list(lst, 20) == [[1, 2, 3, 4, 5, 6, 7, 8, 9]]

        # Empty list
        assert chunk_list([], 3) == []

    def test_find_duplicates(self):




        """Test duplicate finding."""
        assert find_duplicates([1, 2, 3, 2, 4, 3, 3]) == [2, 3]
        assert find_duplicates([1, 2, 3, 4, 5]) == []
        assert find_duplicates([]) == []
        assert find_duplicates(["a", "b", "a", "c"]) == ["a"]

    def test_to_bool(self):




        """Test boolean conversion."""
        # True values
        assert to_bool(True) is True
        assert to_bool(1) is True
        assert to_bool("true") is True
        assert to_bool("True") is True
        assert to_bool("yes") is True
        assert to_bool("1") is True

        # False values
        assert to_bool(False) is False
        assert to_bool(0) is False
        assert to_bool("false") is False
        assert to_bool("False") is False
        assert to_bool("no") is False
        assert to_bool("0") is False
        assert to_bool("") is False
        assert to_bool(None) is False

    def test_safe_json_loads(self):




        """Test safe JSON loading."""
        # Valid JSON
        assert safe_json_loads('{"key": "value"}') == {"key": "value"}
        assert safe_json_loads("[1, 2, 3]") == [1, 2, 3]

        # Invalid JSON with default
        assert safe_json_loads("invalid json", default={}) == {}
        assert safe_json_loads("", default=None) is None

        # Invalid JSON without default
        assert safe_json_loads("invalid json") is None

    def test_safe_cast(self):




        """Test safe type casting."""
        # Successful casts
        assert safe_cast("123", int) == 123
        assert safe_cast("45.6", float) == 45.6
        assert safe_cast("true", lambda x: x.lower() == "true") is True

        # Failed casts with default
        assert safe_cast("abc", int, default=0) == 0
        assert safe_cast(None, str, default="") == ""

        # Failed casts without default
        assert safe_cast("abc", int) is None


class TestModelErrors:
    """Test model error classes."""

    def test_error_hierarchy(self):




        """Test error class inheritance."""
        # Base hierarchy
        assert issubclass(PowerBuilderError, SimeFinchError)
        assert issubclass(ModelError, PowerBuilderError)
        assert issubclass(ValidationError, PowerBuilderError)
        assert issubclass(TypeValidationError, ValidationError)
        assert issubclass(ParseError, PowerBuilderError)
        assert issubclass(DecompileError, PowerBuilderError)
        assert issubclass(ExtractError, PowerBuilderError)
        assert issubclass(GenerateError, PowerBuilderError)

    def test_error_creation(self):




        """Test creating various error types."""
        # Base error
        error = SimeFinchError("Base error")
        assert str(error) == "Base error"

        # PowerBuilder error
        error = PowerBuilderError("PB error")
        assert str(error) == "PB error"

        # Model error
        error = ModelError("Model error")
        assert str(error) == "Model error"

        # Validation error
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"

        # Type validation error
        error = TypeValidationError("Type mismatch")
        assert str(error) == "Type mismatch"


@dataclass
class MockNode(PBNode):
    """Mock node for testing."""

    value: int = 0
    name: str = "test"


class TestPBNodeExtended:
    """Test extended PBNode functionality with mock subclass."""

    def test_mock_node_creation(self):




        """Test creating mock nodes."""
        node = MockNode(value=42, name="answer")
        assert node.value == 42
        assert node.name == "answer"
        assert node.start_position is None

    def test_mock_node_equality(self):




        """Test mock node equality."""
        node1 = MockNode(value=10, name="test")
        node2 = MockNode(value=10, name="test")
        node3 = MockNode(value=20, name="test")

        assert node1 == node2
        assert node1 != node3

    def test_mock_node_position_tracking(self):




        """Test position tracking in mock nodes."""
        node = MockNode()

        # Set positions
        node.start_position = 100
        node.stop_position = 150
        node.source_file = "test.pb"

        assert node.start_position == 100
        assert node.stop_position == 150
        assert node.source_file == "test.pb"


class TestFileOperations:
    """Test file operation utilities."""

    def test_ensure_directory_creates_new(self):




        """Test ensure_directory creates a new directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "dir"
            result = ensure_directory(new_dir)

            assert result == new_dir
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_ensure_directory_existing(self):




        """Test ensure_directory with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = Path(tmpdir)
            result = ensure_directory(existing)

            assert result == existing
            assert existing.exists()

    def test_normalize_path_basic(self):




        """Test basic path normalization."""
        path = normalize_path("dir/../file.txt")
        assert path.name == "file.txt"

    def test_normalize_path_relative_to(self):




        """Test path normalization relative to base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            full_path = base / "subdir" / "file.txt"
            full_path.parent.mkdir(exist_ok=True)
            full_path.touch()

            result = normalize_path(full_path, relative_to=base)
            assert result == Path("subdir/file.txt")

    def test_get_file_extension(self):




        """Test getting file extensions."""
        assert get_file_extension("file.txt") == "txt"
        assert get_file_extension("file.TXT") == "txt"
        assert get_file_extension("file.tar.gz") == "gz"
        assert get_file_extension("file") == ""
        assert get_file_extension(Path("dir/file.py")) == "py"

    def test_read_file_safe_existing(self):




        """Test reading existing file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            f.flush()

            content = read_file_safe(f.name)
            assert content == "test content"

            Path(f.name).unlink()

    def test_read_file_safe_missing_default(self):




        """Test reading missing file with default."""
        content = read_file_safe("nonexistent.txt", default="default")
        assert content == "default"

    def test_read_file_safe_missing_raise(self):




        """Test reading missing file with raise_error."""
        with pytest.raises(FileNotFoundError):
            read_file_safe("nonexistent.txt", raise_error=True)


class TestStringOperations:
    """Test string operation utilities."""

    def test_camel_to_snake(self):




        """Test camelCase to snake_case conversion."""
        assert camel_to_snake("camelCase") == "camel_case"
        assert camel_to_snake("CamelCase") == "camel_case"
        assert camel_to_snake("HTTPRequest") == "http_request"
        assert camel_to_snake("getHTTPResponse") == "get_http_response"
        assert camel_to_snake("IOError") == "io_error"
        assert camel_to_snake("") == ""
        assert camel_to_snake("a") == "a"

    def test_snake_to_camel(self):




        """Test snake_case to camelCase conversion."""
        assert snake_to_camel("snake_case") == "snakeCase"
        assert snake_to_camel("snake_case", capitalize_first=True) == "SnakeCase"
        assert snake_to_camel("single") == "single"
        assert snake_to_camel("single", capitalize_first=True) == "Single"
        assert snake_to_camel("") == ""

    def test_pluralize(self):




        """Test word pluralization."""
        assert pluralize("apple", 1) == "apple"
        assert pluralize("apple", 2) == "apples"
        assert pluralize("box", 2) == "boxes"
        assert pluralize("buzz", 2) == "buzzes"
        assert pluralize("church", 2) == "churches"
        assert pluralize("dish", 2) == "dishes"
        assert pluralize("baby", 2) == "babies"
        assert pluralize("city", 0) == "cities"

    def test_truncate(self):




        """Test text truncation."""
        assert truncate("short", 10) == "short"
        assert truncate("This is a long text", 10) == "This is..."
        assert truncate("Exactly 10", 10) == "Exactly 10"
        assert truncate("Custom suffix", 10, " [...]") == "Cust [...]"


class TestCollectionOperations:
    """Test collection operation utilities."""

    def test_merge_dicts_basic(self):




        """Test basic dictionary merging."""
        result = merge_dicts({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_merge_dicts_overwrite(self):




        """Test dictionary merging with overwrite."""
        result = merge_dicts({"a": 1}, {"a": 2})
        assert result == {"a": 2}

    def test_merge_dicts_no_overwrite(self):




        """Test dictionary merging without overwrite."""
        result = merge_dicts({"a": 1}, {"a": 2}, overwrite=False)
        assert result == {"a": 1}

    def test_filter_dict_include_keys(self):




        """Test dictionary filtering with included keys."""
        d = {"a": 1, "b": 2, "c": 3}
        result = filter_dict(d, keys=["a", "b"])
        assert result == {"a": 1, "b": 2}

    def test_filter_dict_exclude_keys(self):




        """Test dictionary filtering with excluded keys."""
        d = {"a": 1, "b": 2, "c": 3}
        result = filter_dict(d, exclude_keys=["c"])
        assert result == {"a": 1, "b": 2}

    def test_filter_dict_both(self):




        """Test dictionary filtering with both include and exclude."""
        d = {"a": 1, "b": 2, "c": 3}
        result = filter_dict(d, keys=["a", "b", "c"], exclude_keys=["b"])
        assert result == {"a": 1, "c": 3}

    def test_chunk_list(self):




        """Test list chunking."""
        assert chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
        assert chunk_list([1, 2, 3], 3) == [[1, 2, 3]]
        assert chunk_list([1, 2, 3], 1) == [[1], [2], [3]]
        assert chunk_list([], 5) == []

    def test_find_duplicates(self):




        """Test finding duplicates in a list."""
        assert set(find_duplicates([1, 2, 3, 2, 4, 1])) == {1, 2}
        assert find_duplicates([1, 2, 3, 4]) == []
        assert find_duplicates([]) == []
        assert set(find_duplicates(["a", "b", "a", "c", "b"])) == {"a", "b"}


class TestConversionUtilities:
    """Test conversion utilities."""

    def test_to_bool(self):




        """Test boolean conversion."""
        # Boolean values
        assert to_bool(True) is True
        assert to_bool(False) is False

        # Numeric values
        assert to_bool(1) is True
        assert to_bool(0) is False
        assert to_bool(1.5) is True
        assert to_bool(0.0) is False

        # String values
        assert to_bool("true") is True
        assert to_bool("TRUE") is True
        assert to_bool("yes") is True
        assert to_bool("YES") is True
        assert to_bool("y") is True
        assert to_bool("1") is True
        assert to_bool("on") is True

        assert to_bool("false") is False
        assert to_bool("no") is False
        assert to_bool("0") is False
        assert to_bool("") is False

        # Other values
        assert to_bool([1, 2]) is True
        assert to_bool([]) is False
        assert to_bool(None) is False

    def test_safe_json_loads(self):




        """Test safe JSON parsing."""
        assert safe_json_loads('{"a": 1}') == {"a": 1}
        assert safe_json_loads("[1, 2, 3]") == [1, 2, 3]
        assert safe_json_loads("invalid", default={}) == {}
        assert safe_json_loads("invalid") is None
        assert safe_json_loads(None, default=[]) == []

    def test_format_timestamp(self):




        """Test timestamp formatting."""
        # Fixed timestamp
        timestamp = time.mktime(
            time.strptime("2023-01-01 12:00:00", "%Y-%m-%d %H:%M:%S"),
        )
        assert format_timestamp(timestamp) == "2023-01-01 12:00:00"
        assert format_timestamp(timestamp, fmt="%Y-%m-%d") == "2023-01-01"

        # Current time (just check format)
        current = format_timestamp()
        assert len(current) == 19  # YYYY-MM-DD HH:MM:SS
        assert current[4] == "-"
        assert current[7] == "-"

    def test_safe_cast(self):




        """Test safe type casting."""
        # Successful casts
        assert safe_cast("123", int) == 123
        assert safe_cast("123.45", float) == 123.45
        assert safe_cast(123, str) == "123"
        assert safe_cast([1, 2, 3], tuple) == (1, 2, 3)

        # Failed casts with defaults
        assert safe_cast("abc", int, 0) == 0
        assert safe_cast("abc", float, 0.0) == 0.0
        assert safe_cast(None, int, -1) == -1
        assert safe_cast(None, str, "") == ""

        # Failed casts without defaults
        assert safe_cast("abc", int) is None
        assert safe_cast(None, list) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
