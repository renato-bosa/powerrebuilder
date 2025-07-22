"""File and path utility functions."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any


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


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely parse JSON, returning default on error.

    Args:
        text: JSON text to parse
        default: Default value on error

    Returns:
        Parsed JSON or default value
    """
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
