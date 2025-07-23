"""Core utilities with no domain dependencies.

This module contains utilities that can be used anywhere without creating
circular dependencies. Domain-specific utilities should be in their own modules.
"""

import hashlib
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


# =============================================================================
# String Utilities
# =============================================================================


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case.

    Args:
        name: camelCase string

    Returns:
        snake_case string
    """
    # Insert underscore before uppercase letters (except first)
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscore before uppercase letters followed by lowercase
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase.

    Args:
        name: snake_case string

    Returns:
        camelCase string
    """
    components = name.split("_")
    # Capitalize all components except the first
    return components[0] + "".join(x.title() for x in components[1:])


def to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase.

    Args:
        snake_str: Snake case string

    Returns:
        Pascal case string
    """
    return "".join(x.title() for x in snake_str.split("_"))


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length, adding suffix if truncated.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    if max_length <= len(suffix):
        return text[:max_length]

    return text[: max_length - len(suffix)] + suffix


def pluralize(word: str, count: int) -> str:
    """Simple pluralization.

    Args:
        word: Word to pluralize
        count: Count for determining plural

    Returns:
        Pluralized word if count != 1
    """
    if count == 1:
        return word

    # Simple rules
    if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
        return word[:-1] + "ies"
    if word.endswith(("s", "ss", "sh", "ch", "x", "z")):
        return word + "es"
    return word + "s"


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """Sanitize filename for filesystem compatibility.

    Args:
        filename: Original filename
        replacement: Character to replace invalid characters with

    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, replacement, filename)

    # Remove trailing dots and spaces (Windows)
    sanitized = sanitized.rstrip(". ")

    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed"

    return sanitized


def normalize_line_endings(text: str, target: str = "\n") -> str:
    """Normalize line endings in text.

    Args:
        text: Text to normalize
        target: Target line ending

    Returns:
        Text with normalized line endings
    """
    # Replace all types of line endings
    text = text.replace("\r\n", "\n")  # Windows
    text = text.replace("\r", "\n")  # Old Mac

    if target != "\n":
        text = text.replace("\n", target)

    return text


def indent_text(text: str, indent: int = 4, indent_char: str = " ") -> str:
    """Indent text by specified amount.

    Args:
        text: Text to indent
        indent: Number of indent characters
        indent_char: Character to use for indentation

    Returns:
        Indented text
    """
    prefix = indent_char * indent
    lines = text.splitlines(True)
    return "".join(prefix + line if line.strip() else line for line in lines)


def is_valid_identifier(name: str) -> bool:
    """Check if string is valid identifier.

    Args:
        name: String to check

    Returns:
        True if valid identifier
    """
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))


def split_qualified_name(name: str) -> list[str]:
    """Split qualified name into parts.

    Args:
        name: Qualified name (e.g., "namespace.class.member")

    Returns:
        List of name parts
    """
    return name.split(".")


def join_qualified_name(parts: list[str]) -> str:
    """Join name parts into qualified name.

    Args:
        parts: Name parts

    Returns:
        Qualified name
    """
    return ".".join(parts)


# =============================================================================
# Collection Utilities
# =============================================================================


def chunk_list(lst: list[T], chunk_size: int) -> list[list[T]]:
    """Split a list into chunks of specified size.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def find_duplicates(lst: list[T]) -> list[T]:
    """Find duplicate items in a list.

    Args:
        lst: List to check for duplicates

    Returns:
        List of duplicate items
    """
    seen = set()
    duplicates = []
    for item in lst:
        if item in seen and item not in duplicates:
            duplicates.append(item)
        seen.add(item)
    return duplicates


def filter_dict(d: dict[str, T], keys: list[str]) -> dict[str, T]:
    """Filter dictionary to only include specified keys.

    Args:
        d: Dictionary to filter
        keys: Keys to include

    Returns:
        Filtered dictionary
    """
    return {k: v for k, v in d.items() if k in keys}


def merge_dicts(*dicts: dict[str, T]) -> dict[str, T]:
    """Merge multiple dictionaries, later values override earlier ones.

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_get(dictionary: dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value.

    Args:
        dictionary: Dictionary to search
        key_path: Dot-separated key path (e.g., "a.b.c")
        default: Default value if not found

    Returns:
        Value at key path or default
    """
    keys = key_path.split(".")
    value = dictionary

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value


def safe_set(dictionary: dict[str, Any], key_path: str, value: Any) -> None:
    """Safely set nested dictionary value.

    Args:
        dictionary: Dictionary to update
        key_path: Dot-separated key path (e.g., "a.b.c")
        value: Value to set
    """
    keys = key_path.split(".")
    current = dictionary

    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def _deep_merge(base: dict[str, Any], update: dict[str, Any]) -> None:
    """Deep merge update into base."""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# =============================================================================
# File/Path Utilities
# =============================================================================


def ensure_directory(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object for the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_path(path: str | Path, create_parents: bool = True) -> Path:
    """Ensure path exists and return as Path object.

    Args:
        path: Path to ensure
        create_parents: Whether to create parent directories

    Returns:
        Path object
    """
    path = Path(path)

    parent = path.parent if path.is_file() else path

    if create_parents and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)

    return path


def get_file_extension(path: str | Path) -> str:
    """Get file extension without the dot.

    Args:
        path: File path

    Returns:
        File extension without dot
    """
    return Path(path).suffix.lstrip(".")


def normalize_path(path: str | Path) -> str:
    """Normalize a path to use forward slashes.

    Args:
        path: Path to normalize

    Returns:
        Normalized path string
    """
    return str(Path(path)).replace("\\", "/")


def read_file_safe(path: str | Path, encoding: str = "utf-8") -> str | None:
    """Read file contents safely, returning None on error.

    Args:
        path: File path
        encoding: Text encoding

    Returns:
        File contents or None on error
    """
    try:
        return Path(path).read_text(encoding=encoding)
    except Exception:
        return None


def format_timestamp(timestamp: float | None = None) -> str:
    """Format a timestamp as ISO 8601 string.

    Args:
        timestamp: Unix timestamp (uses current time if None)

    Returns:
        ISO 8601 formatted timestamp
    """
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).isoformat()


# =============================================================================
# Other Utilities
# =============================================================================


def calculate_hash(data: str | bytes, algorithm: str = "sha256") -> str:
    """Calculate hash of data.

    Args:
        data: Data to hash
        algorithm: Hash algorithm to use

    Returns:
        Hex digest of hash
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def format_bytes(num_bytes: int) -> str:
    """Format bytes as human-readable string.

    Args:
        num_bytes: Number of bytes

    Returns:
        Formatted string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration as human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    if seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{hours}h {mins}m"


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely parse JSON, returning default on error.

    Args:
        text: JSON text to parse
        default: Default value on error

    Returns:
        Parsed JSON or default value
    """
    import json
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_cast(value: Any, target_type: type, default: Any = None) -> Any:
    """Safely cast a value to a target type, returning default on failure.

    Args:
        value: Value to cast
        target_type: Target type
        default: Default value on failure

    Returns:
        Cast value or default
    """
    if value is None:
        return default
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default


def to_bool(value: Any) -> bool:
    """Convert various values to boolean.

    Args:
        value: Value to convert

    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")
    return bool(value)
