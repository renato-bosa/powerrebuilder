"""PowerBuilder file model stubs."""

from dataclasses import dataclass
from typing import Any

from ..utils.base import PBNode


@dataclass
class PBCommonFileNode(PBNode):
    """Common file node."""

    file_statements: list[Any] = None
