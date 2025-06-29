"""Parser-specific exceptions.

This module re-exports parser-specific exceptions from src.common.exceptions
for backward compatibility. All exceptions are now consolidated in the common module.

DEPRECATED: Import directly from src.common.exceptions instead.
"""

# Re-export parser-specific exceptions from common module
from src.common.exceptions import (
    ConditionalError,
    GrammarError,
    GrammarLoadError,
    GrammarNotFoundError,
    GrammarParseError,
    IncludeError,
    MacroError,
    ModelGenerationError,
    ParseError,
    PreprocessorError,
    TransformerError,
    VisitorError,
)
from src.common.exceptions import (
    PowerBuilderSyntaxError as SyntaxError,
)

__all__ = [
    "ConditionalError",
    "GrammarError",
    "GrammarLoadError",
    "GrammarNotFoundError",
    "GrammarParseError",
    "IncludeError",
    "MacroError",
    "ModelGenerationError",
    "ParseError",
    "PreprocessorError",
    "SyntaxError",
    "TransformerError",
    "VisitorError",
]
