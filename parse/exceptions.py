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
from common.exceptions import (
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
