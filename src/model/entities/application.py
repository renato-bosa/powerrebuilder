"""PowerBuilder application model stubs."""

from dataclasses import field
from typing import Optional

from src.model.types.base import PBNode
from .event import PBEventDeclarationNode


class PBApplication(PBNode):
    """PowerBuilder application."""

    description: str = ""
    app_name: str = ""  # Application display name
    libraries: list["PBLibrary"] = field(default_factory=list)
    global_variables: list = field(default_factory=list)
    shared_variables: list = field(default_factory=list)
    global_functions: list = field(default_factory=list)
    open_event: Optional[PBEventDeclarationNode] = None

    def __init__(self, name: str = "", description: str = "", app_name: str = "", **kwargs):
        super().__init__()
        self.name = name  # Use inherited property
        self.description = description
        self.app_name = app_name
        self.libraries = []
        self.global_variables = []
        self.shared_variables = []
        self.global_functions = []
        self.open_event = None

    def add_library(self, library: "PBLibrary") -> None:
        """Add a library to the application."""
        self.libraries.append(library)

    def get_library(self, name: str) -> Optional["PBLibrary"]:
        """Get a library by name."""
        for lib in self.libraries:
            if lib.name == name:
                return lib
        return None


class PBLibrary(PBNode):
    """PowerBuilder library."""

    path: str = ""
    is_system: bool = False
    objects: list = field(default_factory=list)

    def __init__(self, name: str = "", path: str = "", is_system: bool = False, **kwargs):
        super().__init__()
        self.name = name  # Use inherited property
        self.path = path
        self.is_system = is_system
        self.objects = []

    def add_object(self, obj) -> None:
        """Add an object to the library."""
        self.objects.append(obj)

    def get_object(self, name: str):
        """Get an object by name."""
        for obj in self.objects:
            if hasattr(obj, 'name') and obj.name == name:
                return obj
        return None
