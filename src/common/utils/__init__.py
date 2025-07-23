"""Common utilities for PowerRebuilder.

This package provides shared utility functions used across the codebase.
"""

# Version detection utilities
# Import utilities from parent module
from ..utils import (
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

# DataWindow utilities
from .datawindow import DataWindowDetector

# File utilities
# Logging utilities
# Error recovery utilities
# Import datawindow utilities from submodules

# Object type detection utilities
from .type_detector import DataWindowSubtype, ObjectType, ObjectTypeDetector
from .version import PBVersionDetector, PowerBuilderVersion, detect_pb_version

__all__ = [
    # DataWindow utilities
    "DataWindowDetector",
    "DataWindowSubtype",
    "FileErrorCollector",
    # Object type detection
    "ObjectType",
    "ObjectTypeDetector",
    "PBVersionDetector",
    "PipelineCheckpoint",
    # Version detection
    "PowerBuilderVersion",
    "ResourceChecker",
    # Error recovery
    "ResourceError",
    "RetryError",
    # String utilities
    "camel_to_snake",
    # Collection utilities
    "chunk_list",
    # Logging
    "configure_pipeline_logging",
    "detect_pb_version",
    # File utilities
    "ensure_directory",
    "filter_dict",
    "find_duplicates",
    "format_timestamp",
    "get_file_extension",
    "get_logger",
    "merge_dicts",
    "normalize_path",
    "pluralize",
    "read_file_safe",
    "retry",
    "safe_cast",
    "safe_json_loads",
    "set_decompilation_progress_mode",
    "set_extraction_progress_mode",
    "snake_to_camel",
    "to_bool",
    "truncate",
]
