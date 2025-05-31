"""PowerBuilder type model stubs."""

from dataclasses import dataclass
from typing import Any

from .utils.base import PBNode


@dataclass
class PBBasicTypeNode(PBNode):
    """Basic type node."""
    basic_type: str = "integer"


@dataclass
class PBCustomTypeNode(PBNode):
    """Custom type node."""
    identifier: Any = None


# Additional type classes for tests
@dataclass
class PBBasicType(PBNode):
    """Basic type for tests."""
    name: str = "integer"


@dataclass
class PBArrayType(PBNode):
    """Array type for tests."""
    element_type: Any = None
    dimensions: list[int] = None
