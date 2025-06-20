"""Common utility functions for the PowerBuilder model."""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union

T = TypeVar('T')


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    # Insert underscore before uppercase letters (except first)
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Insert underscore before uppercase letters followed by lowercase
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split('_')
    # Capitalize all components except the first
    return components[0] + ''.join(x.title() for x in components[1:])


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def filter_dict(d: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
    """Filter dictionary to only include specified keys."""
    return {k: v for k, v in d.items() if k in keys}


def find_duplicates(lst: List[T]) -> List[T]:
    """Find duplicate items in a list."""
    seen = set()
    duplicates = []
    for item in lst:
        if item in seen and item not in duplicates:
            duplicates.append(item)
        seen.add(item)
    return duplicates


def format_timestamp(timestamp: Optional[float] = None) -> str:
    """Format a timestamp as ISO 8601 string."""
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).isoformat()


def get_file_extension(path: Union[str, Path]) -> str:
    """Get file extension without the dot."""
    return Path(path).suffix.lstrip('.')


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, later values override earlier ones."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def normalize_path(path: Union[str, Path]) -> str:
    """Normalize a path to use forward slashes."""
    return str(Path(path)).replace('\\', '/')


def pluralize(word: str, count: int) -> str:
    """Simple pluralization (adds 's' if count != 1)."""
    return word if count == 1 else f"{word}s"


def read_file_safe(path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """Read file contents safely, returning None on error."""
    try:
        return Path(path).read_text(encoding=encoding)
    except Exception:
        return None


def safe_cast(value: Any, target_type: type, default: Any = None) -> Any:
    """Safely cast a value to a target type, returning default on failure."""
    if value is None:
        return default
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely parse JSON, returning default on error."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def to_bool(value: Any) -> bool:
    """Convert various values to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 'on')
    return bool(value)


def truncate(text: str, max_length: int, suffix: str = '...') -> str:
    """Truncate text to maximum length, adding suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix