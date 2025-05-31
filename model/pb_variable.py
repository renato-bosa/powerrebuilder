"""PowerBuilder variable model stubs."""

from dataclasses import dataclass

from .utils.base import PBNode


@dataclass
class PBDefaultVariableNode(PBNode):
    """Default variable node."""
    default_variable: str = "" 