"""PowerRebuilder Exception Hierarchy.

This module defines a comprehensive exception hierarchy for the PowerRebuilder project.
Each exception class is designed to handle specific error scenarios with clear error
messages, optional error codes, and context data.

Usage: from src.common.hierarchy import ExtractionError, ParseError

# Raise with basic message
raise ExtractionError("Failed to extract PBL file")

# Raise with error code and context
raise ParseError(
"Syntax error in PowerScript",
error_code="PARSE_001",
context={"line": 42, "column": 15}
)
"""

from pathlib import Path
from typing import Any


class PowerRebuilderError(Exception):
    """Base exception class for all PowerRebuilder errors.

    All custom exceptions in PowerRebuilder should inherit from this class.
    Provides consistent error formatting and context handling.

    Attributes: message: Human-readable error description
    error_code: Optional error code for categorization (e.g., "EXT_001")
    context: Optional dictionary with additional error context
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}

    def __str__(self) -> str:
        """Return formatted error message."""
        parts = []
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        parts.append(self.message)

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"({context_str})")

        return " ".join(parts)

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"context={self.context!r})"
        )


# Extraction Errors


class ExtractionError(PowerRebuilderError):
    """Base class for all extraction-related errors.

    Raised during PBL/PBD file extraction and resource reading operations.
    """



class FileNotFoundError(ExtractionError):
    """Raised when a required file cannot be found.

    Common scenarios:
    - PBL/PBD file doesn't exist
    - Resource file is missing
    - Configuration file not found
    """

    def __init__(self, filepath: Path, **kwargs: Any) -> None:
        super().__init__(
            f"File not found: {filepath}",
            error_code="EXT_001",
            context={"filepath": str(filepath), **kwargs.get("context", {})},
        )


class InvalidFileFormatError(ExtractionError):
    """Raised when file format is invalid or corrupted.

    Common scenarios:
    - Invalid PBL/PBD header
    - Corrupted resource data
    - Unsupported file version
    """

    def __init__(self, filepath: Path, expected_format: str, **kwargs: Any) -> None:
        super().__init__(
            f"Invalid file format for {filepath}. Expected: {expected_format}",
            error_code="EXT_002",
            context={
                "filepath": str(filepath),
                "expected_format": expected_format,
                **kwargs.get("context", {}),
            },
        )


class ResourceExtractionError(ExtractionError):
    """Raised when extracting resources from PBL/PBD fails.

    Common scenarios:
    - Resource header is corrupted
    - Resource data size mismatch
    - Decompression failure
    """

    def __init__(self, resource_name: str, reason: str, **kwargs: Any) -> None:
        super().__init__(
            f"Failed to extract resource '{resource_name}': {reason}",
            error_code="EXT_003",
            context={
                "resource": resource_name,
                "reason": reason,
                **kwargs.get("context", {}),
            },
        )


class LibraryCorruptedError(ExtractionError):
    """Raised when PowerBuilder library is corrupted.

    Common scenarios:
    - Checksum mismatch
    - Missing directory entries
    - Invalid library structure
    """

    def __init__(self, library_path: Path, details: str, **kwargs: Any) -> None:
        super().__init__(
            f"Library '{library_path}' is corrupted: {details}",
            error_code="EXT_004",
            context={
                "library": str(library_path),
                "details": details,
                **kwargs.get("context", {}),
            },
        )


# Parse Errors
class ParseError(PowerRebuilderError):
    """Base class for all parsing-related errors.

    Raised during PowerScript parsing and AST construction.
    """



class GrammarError(ParseError):
    """Raised when grammar definition is invalid or missing.

    Common scenarios:
    - Grammar file not found
    - Invalid grammar syntax
    - Ambiguous grammar rules
    """

    def __init__(self, grammar_name: str, details: str, **kwargs: Any) -> None:
        super().__init__(
            f"Grammar error in '{grammar_name}': {details}",
            error_code="PARSE_001",
            context={
                "grammar": grammar_name,
                "details": details,
                **kwargs.get("context", {}),
            },
        )


class SyntaxError(ParseError):
    """Raised when PowerScript syntax is invalid.

    Common scenarios:
    - Missing semicolon
    - Unmatched parentheses
    - Invalid keyword usage
    """

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        source_file: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = {}
        if line is not None:
            context["line"] = line
        if column is not None:
            context["column"] = column
        if source_file:
            context["file"] = source_file

        super().__init__(
            message,
            error_code="PARSE_002",
            context={**context, **kwargs.get("context", {})},
        )


class ParseRecoveryError(ParseError):
    """Raised when parser cannot recover from errors.

    Common scenarios:
    - Too many syntax errors
    - Unrecoverable parser state
    - Maximum recovery attempts exceeded
    """

    def __init__(
        self, attempted_recoveries: int, last_error: str, **kwargs: Any
    ) -> None:
        super().__init__(
            f"Parser recovery failed after {attempted_recoveries} attempts. Last error: {last_error}",
            error_code="PARSE_003",
            context={
                "attempts": attempted_recoveries,
                "last_error": last_error,
                **kwargs.get("context", {}),
            },
        )


class ASTConstructionError(ParseError):
    """Raised when AST construction fails.

    Common scenarios:
    - Invalid node type
    - Missing required attributes
    - Circular references
    """

    def __init__(self, node_type: str, reason: str, **kwargs: Any) -> None:
        super().__init__(
            f"Failed to construct AST node '{node_type}': {reason}",
            error_code="PARSE_004",
            context={
                "node_type": node_type,
                "reason": reason,
                **kwargs.get("context", {}),
            },
        )


# Decompile Errors
class DecompileError(PowerRebuilderError):
    """Base class for all decompilation-related errors.

    Raised during P-code decompilation to PowerScript.
    """



class OpcodeError(DecompileError):
    """Raised when encountering invalid or unknown opcodes.

    Common scenarios:
    - Unknown opcode value
    - Invalid opcode sequence
    - Unsupported opcode version
    """

    def __init__(self, opcode: int, offset: int, **kwargs: Any) -> None:
        super().__init__(
            f"Invalid opcode 0x{opcode:02X} at offset 0x{offset:04X}",
            error_code="DEC_001",
            context={"opcode": opcode, "offset": offset, **kwargs.get("context", {})},
        )


class ControlFlowError(DecompileError):
    """Raised when control flow reconstruction fails.

    Common scenarios:
    - Invalid jump targets
    - Unreachable code blocks
    - Malformed loop structures
    """

    def __init__(self, structure_type: str, details: str, **kwargs: Any) -> None:
        super().__init__(
            f"Control flow error in {structure_type}: {details}",
            error_code="DEC_002",
            context={
                "structure": structure_type,
                "details": details,
                **kwargs.get("context", {}),
            },
        )


class StackUnderflowError(DecompileError):
    """Raised when P-code stack operations are invalid.

    Common scenarios:
    - Pop from empty stack
    - Insufficient operands
    - Stack size mismatch
    """

    def __init__(
        self, operation: str, required: int, available: int, **kwargs: Any
    ) -> None:
        super().__init__(
            f"Stack underflow in {operation}: required {required} items, but only {available} available",
            error_code="DEC_003",
            context={
                "operation": operation,
                "required": required,
                "available": available,
                **kwargs.get("context", {}),
            },
        )


class DecompilationLimitError(DecompileError):
    """Raised when decompilation limits are exceeded.

    Common scenarios:
    - Maximum recursion depth
    - Instruction count limit
    - Time limit exceeded
    """

    def __init__(self, limit_type: str, limit_value: int, **kwargs: Any) -> None:
        super().__init__(
            f"Decompilation limit exceeded: {limit_type} (limit: {limit_value})",
            error_code="DEC_004",
            context={
                "limit_type": limit_type,
                "limit": limit_value,
                **kwargs.get("context", {}),
            },
        )


# Coordinator Errors
class CoordinatorError(PowerRebuilderError):
    """Base class for coordinator-related errors.

    Raised when coordinator operations fail.
    """



# Pipeline Errors
class PipelineError(PowerRebuilderError):
    """Base class for pipeline-related errors.

    Raised when pipeline operations fail.
    """



# Model Errors
class ModelError(PowerRebuilderError):
    """Base class for all model-related errors.

    Raised during AST modeling and semantic analysis.
    """



class ValidationError(ModelError):
    """Raised when model validation fails.

    Common scenarios:
    - Invalid model structure
    - Missing required fields
    - Constraint violations
    """

    def __init__(
        self, model_type: str, validation_errors: list[str], **kwargs: Any
    ) -> None:
        errors_str = "; ".join(validation_errors)
        super().__init__(
            f"Validation failed for {model_type}: {errors_str}",
            error_code="MODEL_001",
            context={
                "model_type": model_type,
                "errors": validation_errors,
                **kwargs.get("context", {}),
            },
        )


class TypeResolutionError(ModelError):
    """Raised when type resolution fails.

    Common scenarios:
    - Unknown type reference
    - Circular type dependencies
    - Incompatible type constraints
    """

    def __init__(self, type_name: str, reason: str, **kwargs: Any) -> None:
        super().__init__(
            f"Cannot resolve type '{type_name}': {reason}",
            error_code="MODEL_002",
            context={"type": type_name, "reason": reason, **kwargs.get("context", {})},
        )


class SemanticError(ModelError):
    """Raised when semantic analysis detects errors.

    Common scenarios:
    - Undefined variables
    - Type mismatches
    - Invalid method calls
    """

    def __init__(
        self, element: str, error_type: str, details: str, **kwargs: Any
    ) -> None:
        super().__init__(
            f"Semantic error in '{element}' ({error_type}): {details}",
            error_code="MODEL_003",
            context={
                "element": element,
                "error_type": error_type,
                "details": details,
                **kwargs.get("context", {}),
            },
        )


class DependencyError(ModelError):
    """Raised when dependency resolution fails.

    Common scenarios:
    - Circular dependencies
    - Missing dependencies
    - Version conflicts
    """

    def __init__(self, source: str, target: str, reason: str, **kwargs: Any) -> None:
        super().__init__(
            f"Dependency error from '{source}' to '{target}': {reason}",
            error_code="MODEL_004",
            context={
                "source": source,
                "target": target,
                "reason": reason,
                **kwargs.get("context", {}),
            },
        )


# Generation Errors
class GenerationError(PowerRebuilderError):
    """Base class for all code generation errors.

    Raised during target language code generation.
    """



class TemplateError(GenerationError):
    """Raised when template processing fails.

    Common scenarios:
    - Template not found
    - Invalid template syntax
    - Missing template variables
    """

    def __init__(self, template_name: str, error_details: str, **kwargs: Any) -> None:
        super().__init__(
            f"Template error in '{template_name}': {error_details}",
            error_code="GEN_001",
            context={
                "template": template_name,
                "details": error_details,
                **kwargs.get("context", {}),
            },
        )


class ConversionError(GenerationError):
    """Raised when type/construct conversion fails.

    Common scenarios:
    - Unsupported PowerBuilder feature
    - No equivalent in target language
    - Complex type mapping failure
    """

    def __init__(
        self, source_type: str, target_language: str, reason: str, **kwargs: Any
    ) -> None:
        super().__init__(
            f"Cannot convert '{source_type}' to {target_language}: {reason}",
            error_code="GEN_002",
            context={
                "source": source_type,
                "target": target_language,
                "reason": reason,
                **kwargs.get("context", {}),
            },
        )


class CodeGenerationLimitError(GenerationError):
    """Raised when generation limits are exceeded.

    Common scenarios:
    - Output file too large
    - Maximum class count exceeded
    - Circular generation detected
    """

    def __init__(
        self, limit_type: str, limit_value: int, actual_value: int, **kwargs: Any
    ) -> None:
        super().__init__(
            f"Code generation limit exceeded for {limit_type}: {actual_value} > {limit_value}",
            error_code="GEN_003",
            context={
                "limit_type": limit_type,
                "limit": limit_value,
                "actual": actual_value,
                **kwargs.get("context", {}),
            },
        )


class TargetLanguageError(GenerationError):
    """Raised when target language specific errors occur.

    Common scenarios:
    - Invalid identifier for target language
    - Reserved keyword conflict
    - Language-specific constraint violation
    """

    def __init__(
        self, language: str, issue: str, suggestion: str = "", **kwargs: Any
    ) -> None:
        message = f"{language} language error: {issue}"
        if suggestion:
            message += f". Suggestion: {suggestion}"

        super().__init__(
            message,
            error_code="GEN_004",
            context={
                "language": language,
                "issue": issue,
                "suggestion": suggestion,
                **kwargs.get("context", {}),
            },
        )


# Security Errors
class SecurityError(PowerRebuilderError):
    """Base class for all security-related errors.

    Raised when security constraints are violated.
    """



class PathTraversalError(SecurityError):
    """Raised when path traversal is detected.

    Common scenarios:
    - Relative paths with ../
    - Symlink escape attempts
    - Access outside project boundary
    """

    def __init__(self, requested_path: str, safe_path: str, **kwargs: Any) -> None:
        super().__init__(
            f"Path traversal detected: '{requested_path}' (safe path: '{safe_path}')",
            error_code="SEC_001",
            context={
                "requested": requested_path,
                "safe": safe_path,
                **kwargs.get("context", {}),
            },
        )


class ResourceLimitError(SecurityError):
    """Raised when resource limits are exceeded.

    Common scenarios:
    - Memory limit exceeded
    - File size limit exceeded
    - Operation count limit exceeded
    """

    def __init__(
        self, resource: str, limit: int, requested: int, **kwargs: Any
    ) -> None:
        super().__init__(
            f"Resource limit exceeded for {resource}: requested {requested}, limit {limit}",
            error_code="SEC_002",
            context={
                "resource": resource,
                "limit": limit,
                "requested": requested,
                **kwargs.get("context", {}),
            },
        )


class UntrustedInputError(SecurityError):
    """Raised when untrusted input is detected.

    Common scenarios:
    - SQL injection attempts
    - Script injection in templates
    - Malformed input data
    """

    def __init__(self, input_type: str, reason: str, **kwargs: Any) -> None:
        super().__init__(
            f"Untrusted {input_type} input detected: {reason}",
            error_code="SEC_003",
            context={
                "input_type": input_type,
                "reason": reason,
                **kwargs.get("context", {}),
            },
        )


# Configuration Errors
class ConfigurationError(PowerRebuilderError):
    """Raised when configuration is invalid or missing.

    Common scenarios:
    - Missing required configuration
    - Invalid configuration values
    - Configuration file parse errors
    """

    def __init__(self, config_key: str, issue: str, **kwargs: Any) -> None:
        super().__init__(
            f"Configuration error for '{config_key}': {issue}",
            error_code="CFG_001",
            context={"key": config_key, "issue": issue, **kwargs.get("context", {})},
        )


# Exception Factory Methods
class ExceptionFactory:
    """Factory methods for creating common exceptions with consistent formatting."""

    @staticmethod
    def file_not_found(filepath: Path) -> FileNotFoundError:
        """Create a FileNotFoundError with standard formatting."""
        return FileNotFoundError(filepath)

    @staticmethod
    def syntax_error(
        message: str, line: int, column: int, source_file: str | None = None
    ) -> SyntaxError:
        """Create a SyntaxError with location information."""
        return SyntaxError(message, line=line, column=column, source_file=source_file)

    @staticmethod
    def validation_errors(model_type: str, errors: list) -> ValidationError:
        """Create a ValidationError from a list of validation issues."""
        return ValidationError(model_type, errors)

    @staticmethod
    def type_not_found(type_name: str) -> TypeResolutionError:
        """Create a TypeResolutionError for unknown type."""
        return TypeResolutionError(type_name, "Type not found in registry")

    @staticmethod
    def unsupported_feature(feature: str, target_language: str) -> ConversionError:
        """Create a ConversionError for unsupported features."""
        return ConversionError(
            feature,
            target_language,
            f"This PowerBuilder feature has no equivalent in {target_language}",
        )

    @staticmethod
    def resource_limit_exceeded(
        resource: str, limit: int, requested: int
    ) -> ResourceLimitError:
        """Create a ResourceLimitError for exceeded limits."""
        return ResourceLimitError(resource, limit, requested)

    @staticmethod
    def invalid_opcode(opcode: int, offset: int) -> OpcodeError:
        """Create an OpcodeError for invalid opcodes."""
        return OpcodeError(opcode, offset)

    @staticmethod
    def template_not_found(template_name: str) -> TemplateError:
        """Create a TemplateError for missing templates."""
        return TemplateError(template_name, "Template file not found")

    @staticmethod
    def circular_dependency(source: str, target: str) -> DependencyError:
        """Create a DependencyError for circular dependencies."""
        return DependencyError(source, target, "Circular dependency detected")


# Error code registry for documentation
ERROR_CODES = {
    # Extraction errors
    "EXT_001": "File not found",
    "EXT_002": "Invalid file format",
    "EXT_003": "Resource extraction failed",
    "EXT_004": "Library corrupted",
    # Parse errors
    "PARSE_001": "Grammar error",
    "PARSE_002": "Syntax error",
    "PARSE_003": "Parse recovery failed",
    "PARSE_004": "AST construction failed",
    # Decompile errors
    "DEC_001": "Invalid opcode",
    "DEC_002": "Control flow error",
    "DEC_003": "Stack underflow",
    "DEC_004": "Decompilation limit exceeded",
    # Model errors
    "MODEL_001": "Validation failed",
    "MODEL_002": "Type resolution failed",
    "MODEL_003": "Semantic error",
    "MODEL_004": "Dependency error",
    # Generation errors
    "GEN_001": "Template error",
    "GEN_002": "Conversion error",
    "GEN_003": "Generation limit exceeded",
    "GEN_004": "Target language error",
    # Security errors
    "SEC_001": "Path traversal detected",
    "SEC_002": "Resource limit exceeded",
    "SEC_003": "Untrusted input detected",
    # Configuration errors
    "CFG_001": "Configuration error",
}


def get_error_description(error_code: str) -> str:
    """Get human-readable description for an error code.

    Args:
        error_code: The error code to look up

    Returns:
        Description of the error code, or "Unknown error code" if not found
    """
    return ERROR_CODES.get(error_code, "Unknown error code")
