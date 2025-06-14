"""Tests for the consolidated error classes."""

import pytest

from common.exceptions import (
    DecompilationError,
    Error,
    ExtractionError,
    GenerationError,
    ParseError,
    ParsingError,
    PowerBuilderError,
    PowerBuilderToolError,
    TransformError,
    TypeValidationError,
    ValidationError,
)

# Test deprecated error classes from utils.py
try:
    from model.utils.utils import (
        ParseError as UtilsParseError,
    )
    from model.utils.utils import (
        TransformError as UtilsTransformError,
    )
    from model.utils.utils import (
        ValidationError as UtilsValidationError,
    )
except ImportError:
    # If utils.py is removed, use the main error classes
    UtilsParseError = ParseError
    UtilsTransformError = TransformError
    UtilsValidationError = ValidationError


def test_error_hierarchy():
    """Test the error hierarchy."""
    # Base error class
    error = Error("Test error")
    assert isinstance(error, Exception)
    assert error.message == "Test error"
    assert error.details == {}

    # PowerBuilderError is a subclass of Error
    pb_error = PowerBuilderError("Test PB error")
    assert isinstance(pb_error, Error)
    assert pb_error.message == "Test PB error"

    # PowerBuilderToolError is a subclass of PowerBuilderError
    tool_error = PowerBuilderToolError("Test tool error", "test")
    assert isinstance(tool_error, PowerBuilderError)
    assert tool_error.message == "Test tool error"
    assert tool_error.component == "test"

    # Specific error types are subclasses of PowerBuilderError
    validation_error = ValidationError("Invalid value", "test_field", "bad_value")
    assert isinstance(validation_error, PowerBuilderError)
    assert validation_error.message == "Invalid value"
    assert validation_error.field == "test_field"
    assert validation_error.value == "bad_value"

    # TypeValidationError is a subclass of ValidationError
    type_error = TypeValidationError("Invalid type", "badtype")
    assert isinstance(type_error, ValidationError)
    assert type_error.message == "Invalid type"
    assert type_error.field == "type"
    assert type_error.value == "badtype"
    assert type_error.type_name == "badtype"


def test_compatibility_with_deprecated_errors():
    """Test compatibility with deprecated error classes in utils.py."""
    # ParseError
    with pytest.warns(DeprecationWarning):
        error = UtilsParseError("Parse error", 10, 20)
    assert isinstance(error, ParseError)
    assert error.line == 10
    assert error.column == 20

    # ValidationError
    with pytest.warns(DeprecationWarning):
        error = UtilsValidationError("Validation error", "field", "value")
    assert isinstance(error, ValidationError)
    assert error.field == "field"
    assert error.value == "value"

    # TransformError
    with pytest.warns(DeprecationWarning):
        error = UtilsTransformError("Transform error", "node_type")
    assert isinstance(error, TransformError)
    assert error.node_type == "node_type"


def test_tool_error_types():
    """Test PowerBuilderToolError subclasses."""
    # ParsingError
    error = ParsingError("Parsing error", "test.pb", 10)
    assert isinstance(error, PowerBuilderToolError)
    assert error.component == "parsing"
    assert error.file == "test.pb"
    assert error.line == 10

    # DecompilationError
    error = DecompilationError("Decompilation error", "test.pb", "test_func")
    assert isinstance(error, PowerBuilderToolError)
    assert error.component == "decompilation"
    assert error.file == "test.pb"
    assert error.function == "test_func"

    # ExtractionError
    error = ExtractionError("Extraction error", "test.pb")
    assert isinstance(error, PowerBuilderToolError)
    assert error.component == "extraction"
    assert error.file == "test.pb"

    # GenerationError
    error = GenerationError("Generation error", "test.jinja2", "test.py")
    assert isinstance(error, PowerBuilderToolError)
    assert error.component == "generation"
    assert error.template == "test.jinja2"
    assert error.output_file == "test.py"


def test_error_details():
    """Test error details."""
    details = {"key": "value", "nested": {"inner": "data"}}
    error = Error("Test error", details)
    assert error.details == details

    # Details should be preserved in subclasses
    pb_error = PowerBuilderError("Test PB error", details)
    assert pb_error.details == details

    validation_error = ValidationError(
        "Invalid value", "test_field", "bad_value", details
    )
    assert validation_error.details == details
