"""Pipeline exceptions for error handling."""


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class ExtractError(PipelineError):
    """Exception raised during extraction phase."""
    pass


class ParseError(PipelineError):
    """Exception raised during parsing phase."""
    pass


class DecompileError(PipelineError):
    """Exception raised during decompilation phase."""
    pass


class GenerateError(PipelineError):
    """Exception raised during generation phase."""
    pass


class ValidationError(PipelineError):
    """Exception raised during validation."""
    pass