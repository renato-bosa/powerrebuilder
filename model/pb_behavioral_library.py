"""PowerBuilder behavioral library stub."""

from dataclasses import dataclass

from .utils.base import PBNode


@dataclass
class PBBehavioralLibrary(PBNode):
    """Behavioral library stub."""
    name: str = ""
    path: str = ""
