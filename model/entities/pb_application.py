"""PowerBuilder application model stubs."""

from dataclasses import dataclass, field

from model.utils.base import PBNode


@dataclass
class PBApplication(PBNode):
    """PowerBuilder application."""

    name: str = ""
    libraries: list["PBLibrary"] = field(default_factory=list)


@dataclass
class PBLibrary(PBNode):
    """PowerBuilder library."""

    name: str = ""
    path: str = ""
