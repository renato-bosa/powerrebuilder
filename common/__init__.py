"""Common utilities and shared functionality for SIME Finch.

This module contains shared components used across the project:
- Exception hierarchy
- File utilities
- Type system
- Common utilities
"""

from .exceptions import (
    ConfigurationError,
    DecompileError,
    ExtractError,
    GenerateError,
    GrammarError,
    ModelError,
    ParseError,
    PbdError,
    PowerBuilderError,
    SimeFinchError,
    TransactionError,
    TransformError,
    TypeValidationError,
    ValidationError,
)
from .extraction_utils import (
    BinaryReader,
    calculate_checksum,
    decode_powerbuilder_string,
    extract_file_safely,
    extract_metadata_from_header,
    extract_pcode_section,
    find_pcode_markers,
    read_variable_length_int,
    validate_pcode_structure,
)
from .types.types import (
    create_type_from_info,
    format_type_info,
    is_boolean_type,
    is_date_time_type,
    is_numeric_type,
    is_object_type,
    is_string_type,
    normalize_type_name,
    validate_simple_type,
    validate_type_compatibility,
    validate_value_type,
)

__all__ = [
    # Exceptions - re-export all
    "SimeFinchError",
    "ConfigurationError",
    "DecompileError",
    "ExtractError",
    "GenerateError",
    "GrammarError",
    "ModelError",
    "ParseError",
    "PbdError",
    "PowerBuilderError",
    "TransactionError",
    "TransformError",
    "TypeValidationError",
    "ValidationError",
    # Extraction utilities
    "BinaryReader",
    "calculate_checksum",
    "decode_powerbuilder_string",
    "extract_file_safely",
    "extract_metadata_from_header",
    "extract_pcode_section",
    "find_pcode_markers",
    "read_variable_length_int",
    "validate_pcode_structure",
    # Type utilities
    "create_type_from_info",
    "format_type_info",
    "is_boolean_type",
    "is_date_time_type",
    "is_numeric_type",
    "is_object_type",
    "is_string_type",
    "normalize_type_name",
    "validate_simple_type",
    "validate_type_compatibility",
    "validate_value_type",
]
