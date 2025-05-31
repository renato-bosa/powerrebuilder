"""PowerBuilder SQL model stubs."""

from dataclasses import dataclass
from typing import Any

from .utils.base import PBNode


@dataclass
class PBCloseSqlCursorNode(PBNode):
    """Close SQL cursor node."""
    identifier: Any = None


@dataclass
class PBDeclareCursorNode(PBNode):
    """Declare cursor node."""
    identifier: Any = None
    target: Any = None


@dataclass
class PBDeclareProcedureNode(PBNode):
    """Declare procedure node."""
    procedure_name: Any = None


@dataclass
class PBExecuteProcedureNode(PBNode):
    """Execute procedure node."""
    procedure_name: Any = None
    using_clause: Any = None
