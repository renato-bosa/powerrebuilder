"""Parser-specific exceptions.

This module re-exports parser-specific exceptions from common.exceptions
for backward compatibility. All exceptions are now consolidated in the common module.

DEPRECATED: Import directly from common.exceptions instead.
"""

# Re-export parser-specific exceptions from common module
from common.exceptions import (
    ConditionalError,
    GrammarError,
    GrammarLoadError,
    GrammarParseError,
    IncludeError,
    MacroError,
    ModelGenerationError,
    ParseError,
    PreprocessorError,
    SimeFinchError,
    SyntaxError,
    TransformError,
    TransformerError,
    VisitorError,
)

__all__ = [
    "ParseError",
    "GrammarError",
    "GrammarLoadError",
    "GrammarParseError",
    "SyntaxError",
    "PreprocessorError",
    "MacroError",
    "IncludeError",
    "ConditionalError",
    "TransformerError",
    "VisitorError",
    "ModelGenerationError",
]