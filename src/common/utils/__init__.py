"""Common utilities for PowerRebuilder.

This package provides shared utility functions used across the codebase.
"""

# Import utilities from specific modules
from .collections import chunk_list, filter_dict, find_duplicates, merge_dicts
from .files import (
    ensure_directory,
    format_timestamp,
    get_file_extension,
    normalize_path,
    read_file_safe,
    safe_cast,
    safe_json_loads,
    to_bool,
)
from .strings import camel_to_snake, pluralize, snake_to_camel, truncate

__all__ = [
    # String utilities
    "camel_to_snake",
    # Collection utilities
    "chunk_list",
    # File utilities
    "ensure_directory",
    "filter_dict",
    "find_duplicates",
    "format_timestamp",
    "get_file_extension",
    "merge_dicts",
    "normalize_path",
    "pluralize",
    "read_file_safe",
    "safe_cast",
    "safe_json_loads",
    "snake_to_camel",
    "to_bool",
    "truncate",
]
