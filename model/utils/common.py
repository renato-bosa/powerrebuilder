"""Common utility functions for PowerBuilder model.

This module provides general-purpose utility functions organized by category:
- File Operations: Working with files and paths
- String Operations: String manipulation and formatting
- Collection Operations: Working with lists, dictionaries, etc.
- Conversion Utilities: Type conversions and serialization
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


# ─── File Operations ────────────────────────────────────────────────────
def ensure_directory(directory: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        directory: Directory path to ensure

    Returns:
        Path object of the ensured directory

    Examples:
        >>> ensure_directory("output")  # Creates output directory if it doesn't exist
        PosixPath('output')
    """
    directory_path = Path(directory)
    os.makedirs(directory_path, exist_ok=True)
    return directory_path


def normalize_path(
    path: str | Path,
    relative_to: str | Path | None = None,
) -> Path:
    """Normalize a path to a standard format.

    Args:
        path: The path to normalize
        relative_to: Optional base path to make the path relative to

    Returns:
        Normalized path

    Examples:
        >>> normalize_path("dir/../file.txt")
        PosixPath('file.txt')
    """
    normalized = Path(path).expanduser().resolve()
    if relative_to:
        base = Path(relative_to).expanduser().resolve()
        try:
            return normalized.relative_to(base)
        except ValueError:
            return normalized
    return normalized


def get_file_extension(filename: str | Path) -> str:
    """Get the extension of a file, normalized to lowercase without the dot.

    Args:
        filename: Filename to get extension from

    Returns:
        Lowercase extension without the dot

    Examples:
        >>> get_file_extension("file.TXT")
        'txt'
        >>> get_file_extension("file")
        ''
    """
    return Path(filename).suffix.lower().lstrip(".")


def read_file_safe(
    filename: str | Path,
    encoding: str = "utf-8",
    default: str = "",
    raise_error: bool = False,
) -> str:
    """Read a file safely, returning default value if it doesn't exist.

    Args:
        filename: File to read
        encoding: File encoding
        default: Default value to return if file doesn't exist
        raise_error: Whether to raise an error if the file doesn't exist

    Returns:
        File contents or default value

    Raises:
        FileNotFoundError: If raise_error is True and the file doesn't exist

    Examples:
        >>> read_file_safe("nonexistent.txt", default="Empty")
        'Empty'
    """
    try:
        with open(filename, encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        if raise_error:
            raise
        return default


# ─── String Operations ───────────────────────────────────────────────────
def camel_to_snake(text: str) -> str:
    """Convert camelCase to snake_case.

    Handles special cases like consecutive capital letters (e.g., HTTPRequest -> http_request).

    Args:
        text: camelCase string

    Returns:
        snake_case string

    Examples:
        >>> camel_to_snake("camelCaseText")
        'camel_case_text'
        >>> camel_to_snake("HTTPRequest")
        'http_request'
    """
    if not text:
        return ""

    # First handle acronyms (consecutive uppercase letters)
    # Insert underscore before uppercase letter only if the previous char
    # is lowercase, or if it's uppercase and the next char is lowercase
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)

    # Handle consecutive uppercase followed by lowercase
    # Example: 'HTTPRequest' -> 'HTTP_Request'
    s2 = re.sub(r"([A-Z])([A-Z][a-z])", r"\1_\2", s1)

    # Convert to lowercase for the final result
    return s2.lower()


def snake_to_camel(text: str, capitalize_first: bool = False) -> str:
    """Convert snake_case to camelCase or PascalCase.

    Args:
        text: snake_case string
        capitalize_first: Whether to capitalize the first letter (PascalCase vs camelCase)

    Returns:
        camelCase or PascalCase string

    Examples:
        >>> snake_to_camel("snake_case_text")
        'snakeCaseText'
        >>> snake_to_camel("snake_case_text", capitalize_first=True)
        'SnakeCaseText'
    """
    components = text.split("_")
    if not capitalize_first:
        return components[0] + "".join(x.title() for x in components[1:])
    return "".join(x.title() for x in components)


def pluralize(word: str, count: int) -> str:
    """Return singular or plural form of word based on count.

    Uses simple English pluralization rules.

    Args:
        word: Word to pluralize
        count: Count to base pluralization on

    Returns:
        Pluralized word

    Examples:
        >>> pluralize("apple", 1)
        'apple'
        >>> pluralize("apple", 2)
        'apples'
    """
    if count == 1:
        return word

    # Special cases
    if word.endswith("y"):
        return word[:-1] + "ies"
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    return word + "s"


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max_length adding a suffix if truncated.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text

    Examples:
        >>> truncate("This is a long text", 10)
        'This is...'
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


# ─── Collection Operations ───────────────────────────────────────────────
def merge_dicts(
    dict1: dict[Any, Any],
    dict2: dict[Any, Any],
    overwrite: bool = True,
) -> dict[Any, Any]:
    """Merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary
        overwrite: Whether to overwrite values in dict1 with values from dict2

    Returns:
        Merged dictionary

    Examples:
        >>> merge_dicts({'a': 1}, {'b': 2})
        {'a': 1, 'b': 2}
        >>> merge_dicts({'a': 1}, {'a': 2})
        {'a': 2}
        >>> merge_dicts({'a': 1}, {'a': 2}, overwrite=False)
        {'a': 1}
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key not in result or overwrite:
            result[key] = value
    return result


def filter_dict(
    d: dict[Any, Any],
    keys: list[Any] | None = None,
    exclude_keys: list[Any] | None = None,
) -> dict[Any, Any]:
    """Filter a dictionary by keys to include or exclude.

    Args:
        d: Dictionary to filter
        keys: Keys to include (if None, include all)
        exclude_keys: Keys to exclude

    Returns:
        Filtered dictionary

    Examples:
        >>> filter_dict({'a': 1, 'b': 2, 'c': 3}, keys=['a', 'b'])
        {'a': 1, 'b': 2}
        >>> filter_dict({'a': 1, 'b': 2, 'c': 3}, exclude_keys=['c'])
        {'a': 1, 'b': 2}
    """
    exclude_keys = exclude_keys or []

    if keys is None:
        # Exclude specified keys
        return {k: v for k, v in d.items() if k not in exclude_keys}
    # Include only specified keys, but exclude excluded keys
    return {k: d[k] for k in keys if k in d and k not in exclude_keys}


def chunk_list[T](lst: list[T], chunk_size: int) -> list[list[T]]:
    """Split a list into chunks of specified size.

    Args:
        lst: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks

    Examples:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def find_duplicates(items: list[Any]) -> list[Any]:
    """Find duplicate items in a list.

    Args:
        items: List to check for duplicates

    Returns:
        List of duplicate items

    Examples:
        >>> find_duplicates([1, 2, 3, 2, 4, 1])
        [1, 2]
    """
    seen = set()
    duplicates = set()

    for item in items:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)

    return list(duplicates)


# ─── Conversion Utilities ────────────────────────────────────────────────
def to_bool(value: Any) -> bool:
    """Convert a value to bool.

    Recognizes various string representations of true/false.

    Args:
        value: Value to convert

    Returns:
        Boolean value

    Examples:
        >>> to_bool("yes")
        True
        >>> to_bool("no")
        False
        >>> to_bool(1)
        True
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return bool(value)
    if isinstance(value, str):
        value = value.lower().strip()
        return value in {"true", "yes", "y", "1", "on"}
    return bool(value)


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string.

    Args:
        json_str: JSON string to parse
        default: Default value to return on error

    Returns:
        Parsed JSON or default value

    Examples:
        >>> safe_json_loads('{"a": 1}')
        {'a': 1}
        >>> safe_json_loads('invalid', default={})
        {}
    """
    try:
        return json.loads(json_str)
    except (ValueError, TypeError):
        return default


def format_timestamp(
    timestamp: float | None = None,
    fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """Format a timestamp as a string.

    Args:
        timestamp: Unix timestamp (default: current time)
        fmt: Date format

    Returns:
        Formatted timestamp

    Examples:
        >>> import time
        >>> t = time.mktime(time.strptime('2023-01-01 12:00:00', '%Y-%m-%d %H:%M:%S'))
        >>> format_timestamp(t)
        '2023-01-01 12:00:00'
    """
    dt = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
    return dt.strftime(fmt)


def safe_cast(value: Any, to_type: Callable[[Any], T], default: T = None) -> T:
    """Safely cast a value to a specified type.

    Args:
        value: Value to cast
        to_type: Type constructor function
        default: Default value to return on error

    Returns:
        Cast value or default

    Examples:
        >>> safe_cast("123", int)
        123
        >>> safe_cast("abc", int, 0)
        0
        >>> safe_cast(None, str, "")
        ''
    """
    # Handle None explicitly
    if value is None:
        return default

    try:
        return to_type(value)
    except (ValueError, TypeError):
        return default
