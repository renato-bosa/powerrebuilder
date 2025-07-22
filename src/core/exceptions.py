"""PowerRebuilder Exception Hierarchy.

This module provides a comprehensive exception hierarchy for the PowerRebuilder project.
All exceptions inherit from BaseError and support error codes for better categorization.

Usage:
    from src.core.exceptions import ExtractError, ParseError, ValidationError

    # Basic usage
    raise ExtractError("Failed to extract PBL file")

    # With error code and context
    raise ParseError(
        "Syntax error in PowerScript",
        filename="main.srw",
        line=42,
        column=15,
        error_code="PARSE_002"
    )
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class BaseError(Exception):
    """Base exception for all PowerRebuilder errors.

    All exceptions in the project should inherit from this class to ensure
    consistent error handling and proper error hierarchy.

    Attributes:
        message: Human-readable error description
        error_code: Optional error code for categorization (e.g., "EXT_001")
        context: Dictionary with additional error context
    """

    def __init__(
        self, message: str, error_code: str | None = None, **kwargs: Any
    ) -> None:
        """Initialize the error with a message and optional context.

        Args:
            message: Error message
            error_code: Optional error code for categorization
            **kwargs: Additional context (e.g., line, column, filename)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = kwargs

    def __str__(self) -> str:
        """Return formatted error message."""
        parts = []
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        parts.append(self.message)

        if self.context:
            # Special handling for common context fields
            context_parts = []
            if "filename" in self.context:
                context_parts.append(f"file='{self.context['filename']}'")
            if "line" in self.context:
                if "column" in self.context:
                    context_parts.append(
                        f"line={self.context['line']}:{self.context['column']}"
                    )
                else:
                    context_parts.append(f"line={self.context['line']}")

            # Add remaining context
            for k, v in self.context.items():
                if k not in ("filename", "line", "column"):
                    context_parts.append(f"{k}={v}")

            if context_parts:
                parts.append(f"({', '.join(context_parts)})")

        return " ".join(parts)

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"context={self.context!r})"
        )


# Backward compatibility aliases
PowerRebuilderError = BaseError
SimeFinchError = BaseError
Error = BaseError


# =============================================================================
# Core Component Errors
# =============================================================================


class ExtractError(BaseError):
    """Error during extraction phase.

    Raised when extracting source code from PBL/PBD files fails.
    """



class DecompileError(BaseError):
    """Error during decompilation phase.

    Raised when decompiling P-code to higher-level code fails.
    """



class ParseError(BaseError):
    """Error during parsing phase.

    Raised when parsing PowerBuilder source code or related formats fails.
    Includes position information when available.
    """

    def __init__(
        self,
        message: str,
        filename: str | None = None,
        line: int | None = None,
        column: int | None = None,
        error_code: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize parse error with position information.

        Args:
            message: Error message
            filename: Source filename
            line: Line number (1-based)
            column: Column number (1-based)
            error_code: Optional error code
            **kwargs: Additional context
        """
        super().__init__(
            message,
            error_code=error_code,
            filename=filename,
            line=line,
            column=column,
            **kwargs,
        )
        self.filename = filename
        self.line = line
        self.column = column


class ModelError(BaseError):
    """Error in model operations.

    Raised when model creation, manipulation, or validation fails.
    """



class GenerateError(BaseError):
    """Error during code generation phase.

    Raised when generating target code (Python, Flutter, etc.) fails.
    """



class SchemaGenerationError(GenerateError):
    """Error during schema documentation generation.

    Raised when generating database schema documentation fails.
    """



class TransformError(BaseError):
    """Error during AST transformation.

    Raised when transforming parse trees to AST nodes fails.
    """



# =============================================================================
# Validation and Type Errors
# =============================================================================


class ValidationError(BaseError):
    """General validation error.

    Raised when data validation fails (e.g., invalid values, constraints).
    """

    def __init__(
        self,
        message: str,
        model_type: str | None = None,
        validation_errors: list | None = None,
        error_code: str = "MODEL_001",
        **kwargs: Any,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message (or auto-generated from validation_errors)
            model_type: Type of model being validated
            validation_errors: List of validation error messages
            error_code: Error code (defaults to MODEL_001)
            **kwargs: Additional context
        """
        # Support both interfaces
        if model_type and validation_errors:
            errors_str = "; ".join(validation_errors)
            message = f"Validation failed for {model_type}: {errors_str}"
            kwargs["model_type"] = model_type
            kwargs["errors"] = validation_errors

        super().__init__(message, error_code=error_code, **kwargs)
        self.model_type = model_type
        self.validation_errors = validation_errors


class TypeValidationError(ValidationError):
    """Type validation error.

    Raised when type checking or type validation fails.
    """

    def __init__(
        self,
        message: str,
        expected_type: str | None = None,
        actual_type: str | None = None,
        error_code: str = "MODEL_002",
        **kwargs: Any,
    ) -> None:
        """Initialize type validation error.

        Args:
            message: Error message
            expected_type: Expected type name
            actual_type: Actual type name
            error_code: Error code
            **kwargs: Additional context
        """
        super().__init__(
            message,
            error_code=error_code,
            expected_type=expected_type,
            actual_type=actual_type,
            **kwargs,
        )
        self.expected_type = expected_type
        self.actual_type = actual_type


class TypeResolutionError(ModelError):
    """Raised when type resolution fails.

    Common scenarios:
    - Unknown type reference
    - Circular type dependencies
    - Incompatible type constraints
    """

    def __init__(
        self, type_name: str, reason: str, error_code: str = "MODEL_002", **kwargs: Any
    ) -> None:
        message = f"Cannot resolve type '{type_name}': {reason}"
        super().__init__(
            message, error_code=error_code, type=type_name, reason=reason, **kwargs
        )
        self.type_name = type_name
        self.reason = reason


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(BaseError):
    """Configuration error.

    Raised when configuration is invalid or missing required values.
    """

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        issue: str | None = None,
        error_code: str = "CFG_001",
        **kwargs: Any,
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Error message (or auto-generated)
            config_key: Configuration key with issue
            issue: Description of the issue
            error_code: Error code
            **kwargs: Additional context
        """
        # Support both interfaces
        if config_key and issue:
            message = f"Configuration error for '{config_key}': {issue}"
            kwargs["key"] = config_key
            kwargs["issue"] = issue

        super().__init__(message, error_code=error_code, **kwargs)
        self.config_key = config_key
        self.issue = issue


# =============================================================================
# Parser-Specific Errors
# =============================================================================


class GrammarError(ParseError):
    """Base class for grammar-related errors."""

    def __init__(
        self,
        message: str,
        grammar_name: str | None = None,
        details: str | None = None,
        error_code: str = "PARSE_001",
        **kwargs: Any,
    ) -> None:
        """Initialize grammar error.

        Args:
            message: Error message (or auto-generated)
            grammar_name: Name of the grammar
            details: Error details
            error_code: Error code
            **kwargs: Additional context
        """
        # Support both interfaces
        if grammar_name and details:
            message = f"Grammar error in '{grammar_name}': {details}"
            kwargs["grammar"] = grammar_name
            kwargs["details"] = details

        super().__init__(message, error_code=error_code, **kwargs)
        self.grammar_name = grammar_name
        self.details = details


class GrammarLoadError(GrammarError):
    """Error loading grammar file."""



class GrammarParseError(GrammarError):
    """Error parsing grammar definition."""



class GrammarNotFoundError(GrammarError):
    """Error when a grammar file cannot be found."""



class PowerBuilderSyntaxError(ParseError):
    """Syntax error in PowerBuilder source code.

    Provides consistent error handling within our framework without
    shadowing Python's built-in SyntaxError.
    """

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        source_file: str | None = None,
        error_code: str = "PARSE_002",
        **kwargs: Any,
    ) -> None:
        filename = source_file or kwargs.get("filename")
        super().__init__(
            message,
            filename=filename,
            line=line,
            column=column,
            error_code=error_code,
            **kwargs,
        )


# Alias for compatibility
SyntaxError = PowerBuilderSyntaxError


class PreprocessorError(ParseError):
    """Error during preprocessing phase."""



class MacroError(PreprocessorError):
    """Error processing macros."""



class IncludeError(PreprocessorError):
    """Error processing include directives."""



class ConditionalError(PreprocessorError):
    """Error processing conditional compilation."""



class TransformerError(TransformError):
    """Error during tree transformation."""



class VisitorError(TransformError):
    """Error during tree visitation."""



class ModelGenerationError(ModelError):
    """Error generating model from AST."""



class ParseRecoveryError(ParseError):
    """Raised when parser cannot recover from errors.

    Common scenarios:
    - Too many syntax errors
    - Unrecoverable parser state
    - Maximum recovery attempts exceeded
    """

    def __init__(
        self,
        attempted_recoveries: int,
        last_error: str,
        error_code: str = "PARSE_003",
        **kwargs: Any,
    ) -> None:
        message = f"Parser recovery failed after {attempted_recoveries} attempts. Last error: {last_error}"
        super().__init__(
            message,
            error_code=error_code,
            attempts=attempted_recoveries,
            last_error=last_error,
            **kwargs,
        )
        self.attempted_recoveries = attempted_recoveries
        self.last_error = last_error


class ASTConstructionError(ParseError):
    """Raised when AST construction fails.

    Common scenarios:
    - Invalid node type
    - Missing required attributes
    - Circular references
    """

    def __init__(
        self, node_type: str, reason: str, error_code: str = "PARSE_004", **kwargs: Any
    ) -> None:
        message = f"Failed to construct AST node '{node_type}': {reason}"
        super().__init__(
            message, error_code=error_code, node_type=node_type, reason=reason, **kwargs
        )
        self.node_type = node_type
        self.reason = reason


# =============================================================================
# Extraction-Specific Errors
# =============================================================================


class PbdError(ExtractError):
    """Base class for PBD/PBL file errors."""



class DataExtractionError(PbdError):
    """General data extraction error from PBD/PBL files."""



class HeaderError(PbdError):
    """Error parsing PBL/PBD file header."""



class NodeError(PbdError):
    """Error parsing NOD block."""



class EntryError(PbdError):
    """Error parsing PbEntryDefinition."""



class DatError(PbdError):
    """Error parsing DAT block."""



class PfcExcludedError(PbdError):
    """Object excluded due to PFC hash match."""

    def __init__(
        self,
        object_name: str,
        hash_value: str,
        error_code: str = "EXT_005",
        **kwargs: Any,
    ) -> None:
        """Initialize PFC exclusion error.

        Args:
            object_name: Name of excluded object
            hash_value: Hash that matched PFC
            error_code: Error code
            **kwargs: Additional context
        """
        message = f"Object '{object_name}' excluded (PFC hash: {hash_value})"
        super().__init__(
            message,
            error_code=error_code,
            object_name=object_name,
            hash_value=hash_value,
            **kwargs,
        )
        self.object_name = object_name
        self.hash_value = hash_value


class FileNotFoundError(ExtractError):
    """Raised when a required file cannot be found.

    Common scenarios:
    - PBL/PBD file doesn't exist
    - Resource file is missing
    - Configuration file not found
    """

    def __init__(
        self, filepath: Path | str, error_code: str = "EXT_001", **kwargs: Any
    ) -> None:
        filepath = Path(filepath)
        message = f"File not found: {filepath}"
        super().__init__(
            message, error_code=error_code, filepath=str(filepath), **kwargs
        )
        self.filepath = filepath


class InvalidFileFormatError(ExtractError):
    """Raised when file format is invalid or corrupted.

    Common scenarios:
    - Invalid PBL/PBD header
    - Corrupted resource data
    - Unsupported file version
    """

    def __init__(
        self,
        filepath: Path | str,
        expected_format: str,
        error_code: str = "EXT_002",
        **kwargs: Any,
    ) -> None:
        filepath = Path(filepath)
        message = f"Invalid file format for {filepath}. Expected: {expected_format}"
        super().__init__(
            message,
            error_code=error_code,
            filepath=str(filepath),
            expected_format=expected_format,
            **kwargs,
        )
        self.filepath = filepath
        self.expected_format = expected_format


class ResourceExtractionError(ExtractError):
    """Raised when extracting resources from PBL/PBD fails.

    Common scenarios:
    - Resource header is corrupted
    - Resource data size mismatch
    - Decompression failure
    """

    def __init__(
        self,
        resource_name: str,
        reason: str,
        error_code: str = "EXT_003",
        **kwargs: Any,
    ) -> None:
        message = f"Failed to extract resource '{resource_name}': {reason}"
        super().__init__(
            message,
            error_code=error_code,
            resource=resource_name,
            reason=reason,
            **kwargs,
        )
        self.resource_name = resource_name
        self.reason = reason


class LibraryCorruptedError(ExtractError):
    """Raised when PowerBuilder library is corrupted.

    Common scenarios:
    - Checksum mismatch
    - Missing directory entries
    - Invalid library structure
    """

    def __init__(
        self,
        library_path: Path | str,
        details: str,
        error_code: str = "EXT_004",
        **kwargs: Any,
    ) -> None:
        library_path = Path(library_path)
        message = f"Library '{library_path}' is corrupted: {details}"
        super().__init__(
            message,
            error_code=error_code,
            library=str(library_path),
            details=details,
            **kwargs,
        )
        self.library_path = library_path
        self.details = details


# =============================================================================
# Decompilation-Specific Errors
# =============================================================================


class OpcodeError(DecompileError):
    """Raised when encountering invalid or unknown opcodes.

    Common scenarios:
    - Unknown opcode value
    - Invalid opcode sequence
    - Unsupported opcode version
    """

    def __init__(
        self, opcode: int, offset: int, error_code: str = "DEC_001", **kwargs: Any
    ) -> None:
        message = f"Invalid opcode 0x{opcode:02X} at offset 0x{offset:04X}"
        super().__init__(
            message, error_code=error_code, opcode=opcode, offset=offset, **kwargs
        )
        self.opcode = opcode
        self.offset = offset


class ControlFlowError(DecompileError):
    """Raised when control flow reconstruction fails.

    Common scenarios:
    - Invalid jump targets
    - Unreachable code blocks
    - Malformed loop structures
    """

    def __init__(
        self,
        structure_type: str,
        details: str,
        error_code: str = "DEC_002",
        **kwargs: Any,
    ) -> None:
        message = f"Control flow error in {structure_type}: {details}"
        super().__init__(
            message,
            error_code=error_code,
            structure=structure_type,
            details=details,
            **kwargs,
        )
        self.structure_type = structure_type
        self.details = details


class StackUnderflowError(DecompileError):
    """Raised when P-code stack operations are invalid.

    Common scenarios:
    - Pop from empty stack
    - Insufficient operands
    - Stack size mismatch
    """

    def __init__(
        self,
        operation: str,
        required: int,
        available: int,
        error_code: str = "DEC_003",
        **kwargs: Any,
    ) -> None:
        message = f"Stack underflow in {operation}: required {required} items, but only {available} available"
        super().__init__(
            message,
            error_code=error_code,
            operation=operation,
            required=required,
            available=available,
            **kwargs,
        )
        self.operation = operation
        self.required = required
        self.available = available


class DecompilationLimitError(DecompileError):
    """Raised when decompilation limits are exceeded.

    Common scenarios:
    - Maximum recursion depth
    - Instruction count limit
    - Time limit exceeded
    """

    def __init__(
        self,
        limit_type: str,
        limit_value: int,
        error_code: str = "DEC_004",
        **kwargs: Any,
    ) -> None:
        message = f"Decompilation limit exceeded: {limit_type} (limit: {limit_value})"
        super().__init__(
            message,
            error_code=error_code,
            limit_type=limit_type,
            limit=limit_value,
            **kwargs,
        )
        self.limit_type = limit_type
        self.limit_value = limit_value


# =============================================================================
# Model-Specific Errors
# =============================================================================


class SemanticError(ModelError):
    """Raised when semantic analysis detects errors.

    Common scenarios:
    - Undefined variables
    - Type mismatches
    - Invalid method calls
    """

    def __init__(
        self,
        element: str,
        error_type: str,
        details: str,
        error_code: str = "MODEL_003",
        **kwargs: Any,
    ) -> None:
        message = f"Semantic error in '{element}' ({error_type}): {details}"
        super().__init__(
            message,
            error_code=error_code,
            element=element,
            error_type=error_type,
            details=details,
            **kwargs,
        )
        self.element = element
        self.error_type = error_type
        self.details = details


class DependencyError(ModelError):
    """Raised when dependency resolution fails.

    Common scenarios:
    - Circular dependencies
    - Missing dependencies
    - Version conflicts
    """

    def __init__(
        self,
        source: str,
        target: str,
        reason: str,
        error_code: str = "MODEL_004",
        **kwargs: Any,
    ) -> None:
        message = f"Dependency error from '{source}' to '{target}': {reason}"
        super().__init__(
            message,
            error_code=error_code,
            source=source,
            target=target,
            reason=reason,
            **kwargs,
        )
        self.source = source
        self.target = target
        self.reason = reason


# =============================================================================
# Generation-Specific Errors
# =============================================================================


class TemplateError(GenerateError):
    """Raised when template processing fails.

    Common scenarios:
    - Template not found
    - Invalid template syntax
    - Missing template variables
    """

    def __init__(
        self,
        template_name: str,
        error_details: str,
        error_code: str = "GEN_001",
        **kwargs: Any,
    ) -> None:
        message = f"Template error in '{template_name}': {error_details}"
        super().__init__(
            message,
            error_code=error_code,
            template=template_name,
            details=error_details,
            **kwargs,
        )
        self.template_name = template_name
        self.error_details = error_details


class ConversionError(GenerateError):
    """Raised when type/construct conversion fails.

    Common scenarios:
    - Unsupported PowerBuilder feature
    - No equivalent in target language
    - Complex type mapping failure
    """

    def __init__(
        self,
        source_type: str,
        target_language: str,
        reason: str,
        error_code: str = "GEN_002",
        **kwargs: Any,
    ) -> None:
        message = f"Cannot convert '{source_type}' to {target_language}: {reason}"
        super().__init__(
            message,
            error_code=error_code,
            source=source_type,
            target=target_language,
            reason=reason,
            **kwargs,
        )
        self.source_type = source_type
        self.target_language = target_language
        self.reason = reason


class CodeGenerationLimitError(GenerateError):
    """Raised when generation limits are exceeded.

    Common scenarios:
    - Output file too large
    - Maximum class count exceeded
    - Circular generation detected
    """

    def __init__(
        self,
        limit_type: str,
        limit_value: int,
        actual_value: int,
        error_code: str = "GEN_003",
        **kwargs: Any,
    ) -> None:
        message = f"Code generation limit exceeded for {limit_type}: {actual_value} > {limit_value}"
        super().__init__(
            message,
            error_code=error_code,
            limit_type=limit_type,
            limit=limit_value,
            actual=actual_value,
            **kwargs,
        )
        self.limit_type = limit_type
        self.limit_value = limit_value
        self.actual_value = actual_value


class TargetLanguageError(GenerateError):
    """Raised when target language specific errors occur.

    Common scenarios:
    - Invalid identifier for target language
    - Reserved keyword conflict
    - Language-specific constraint violation
    """

    def __init__(
        self,
        language: str,
        issue: str,
        suggestion: str = "",
        error_code: str = "GEN_004",
        **kwargs: Any,
    ) -> None:
        message = f"{language} language error: {issue}"
        if suggestion:
            message += f". Suggestion: {suggestion}"

        super().__init__(
            message,
            error_code=error_code,
            language=language,
            issue=issue,
            suggestion=suggestion,
            **kwargs,
        )
        self.language = language
        self.issue = issue
        self.suggestion = suggestion


# =============================================================================
# PowerBuilder-Specific Errors
# =============================================================================


class PowerBuilderError(BaseError):
    """Base class for PowerBuilder-specific errors.

    Used for errors related to PowerBuilder language features, constructs, or runtime behavior.
    """



class TransactionError(PowerBuilderError):
    """Transaction-related error.

    Used for database transaction errors with optional SQL state codes.
    """

    def __init__(
        self,
        message: str,
        sql_state: str | None = None,
        error_code: int | str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize transaction error.

        Args:
            message: Error message
            sql_state: SQL state code (e.g., '23000')
            error_code: Database-specific error code or our error code
            **kwargs: Additional context
        """
        # If error_code is numeric, it's a database error code
        if isinstance(error_code, int):
            kwargs["db_error_code"] = error_code
            error_code = None  # Don't use as our error code

        super().__init__(message, error_code=error_code, sql_state=sql_state, **kwargs)
        self.sql_state = sql_state
        self.db_error_code = kwargs.get("db_error_code")

    def __str__(self) -> str:
        """Return formatted error message with SQL state."""
        parts = []

        if self.error_code:
            parts.append(f"[{self.error_code}]")

        parts.append(self.message)

        if self.sql_state:
            parts.append(f"SQLSTATE: {self.sql_state}")

        if self.db_error_code:
            parts.append(f"DB Error code: {self.db_error_code}")

        return " - ".join(parts)


# =============================================================================
# Security Errors
# =============================================================================


class SecurityError(BaseError):
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

    def __init__(
        self,
        requested_path: str,
        safe_path: str,
        error_code: str = "SEC_001",
        **kwargs: Any,
    ) -> None:
        message = (
            f"Path traversal detected: '{requested_path}' (safe path: '{safe_path}')"
        )
        super().__init__(
            message,
            error_code=error_code,
            requested=requested_path,
            safe=safe_path,
            **kwargs,
        )
        self.requested_path = requested_path
        self.safe_path = safe_path


class ResourceLimitError(SecurityError):
    """Raised when resource limits are exceeded.

    Common scenarios:
    - Memory limit exceeded
    - File size limit exceeded
    - Operation count limit exceeded
    """

    def __init__(
        self,
        resource: str,
        limit: int,
        requested: int,
        error_code: str = "SEC_002",
        **kwargs: Any,
    ) -> None:
        message = f"Resource limit exceeded for {resource}: requested {requested}, limit {limit}"
        super().__init__(
            message,
            error_code=error_code,
            resource=resource,
            limit=limit,
            requested=requested,
            **kwargs,
        )
        self.resource = resource
        self.limit = limit
        self.requested = requested


class UntrustedInputError(SecurityError):
    """Raised when untrusted input is detected.

    Common scenarios:
    - SQL injection attempts
    - Script injection in templates
    - Malformed input data
    """

    def __init__(
        self, input_type: str, reason: str, error_code: str = "SEC_003", **kwargs: Any
    ) -> None:
        message = f"Untrusted {input_type} input detected: {reason}"
        super().__init__(
            message,
            error_code=error_code,
            input_type=input_type,
            reason=reason,
            **kwargs,
        )
        self.input_type = input_type
        self.reason = reason


# =============================================================================
# Coordinator and Pipeline Errors
# =============================================================================


class CoordinatorError(BaseError):
    """Base class for coordinator-related errors.

    Raised when coordinator operations fail.
    """



class PipelineError(BaseError):
    """Base class for pipeline-related errors.

    Raised when pipeline operations fail.
    """



# =============================================================================
# Tool-Level Errors (High-level pipeline errors)
# =============================================================================


class PowerBuilderToolError(BaseError):
    """Base class for high-level tool errors.

    These represent failures at the pipeline/tool level rather than
    specific component failures.
    """



class ExtractionError(PowerBuilderToolError):
    """High-level extraction phase error."""



class ParsingError(PowerBuilderToolError):
    """High-level parsing phase error."""



class DecompilationError(PowerBuilderToolError):
    """High-level decompilation phase error."""



class GenerationError(PowerBuilderToolError):
    """High-level generation phase error."""



# =============================================================================
# Exception Factory
# =============================================================================


class ExceptionFactory:
    """Factory methods for creating common exceptions with consistent formatting."""

    @staticmethod
    def file_not_found(filepath: Path | str) -> FileNotFoundError:
        """Create a FileNotFoundError with standard formatting."""
        return FileNotFoundError(filepath)

    @staticmethod
    def syntax_error(
        message: str, line: int, column: int, source_file: str | None = None
    ) -> PowerBuilderSyntaxError:
        """Create a SyntaxError with location information."""
        return PowerBuilderSyntaxError(
            message, line=line, column=column, source_file=source_file
        )

    @staticmethod
    def validation_errors(model_type: str, errors: list) -> ValidationError:
        """Create a ValidationError from a list of validation issues."""
        return ValidationError(
            "",  # Message will be auto-generated
            model_type=model_type,
            validation_errors=errors,
        )

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


# =============================================================================
# Error Code Registry
# =============================================================================

ERROR_CODES = {
    # Extraction errors
    "EXT_001": "File not found",
    "EXT_002": "Invalid file format",
    "EXT_003": "Resource extraction failed",
    "EXT_004": "Library corrupted",
    "EXT_005": "PFC object excluded",
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


# =============================================================================
# Aliases for backward compatibility
# =============================================================================

# Parser aliases
ParserError = ParseError

# PBD-specific aliases
PBDError = PbdError
PBDHeaderError = HeaderError
PBDNodeError = NodeError
PBDEntryError = EntryError
PBDDataError = DatError

# Transaction aliases
PBTransactionError = TransactionError
