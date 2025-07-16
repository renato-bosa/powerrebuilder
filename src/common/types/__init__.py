"""Common type definitions for PowerRebuilder."""

from .errors import ErrorCollector, ParseError
from .types import *

# Re-export all types
__all__ = ["ErrorCollector", "ParseError"]