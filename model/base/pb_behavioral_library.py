"""PowerBuilder behavioral library."""

from dataclasses import dataclass
from pathlib import Path

from ..utils.base import PBNode


@dataclass
class PBBehavioralLibrary(PBNode):
    """Behavioral library."""

    name: str = ""
    library_path: str | Path = ""
    is_system: bool = False
    
    def __str__(self) -> str:
        
    
        prefix = "system library" if self.is_system else "library"
        return f"{prefix} {self.library_path}"