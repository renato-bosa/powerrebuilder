"""PowerBuilder access node definition.

This module defines the PBAccessNode class for representing access to PowerBuilder objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from ..utils.base import PBNode


class AccessType(Enum):
    READ = auto()
    WRITE = auto()
    READ_WRITE = auto()


@dataclass
class PBAccess:
    name: str
    variable_name: str
    access_type: AccessType
    is_instance_access: bool = False
    is_array_access: bool = False
    array_indices: list[str] = field(default_factory=list)
    container: Any = None  # PBSourcedEntity
    attribute_access: Any = None  # PBAttributeAccess

    @property
    def is_instance_variable_access(self) -> bool:
        """Check if this is an instance variable access (not a literal)."""
        if not self.is_instance_access:
            return False
        # Boolean literals should not be considered instance variables
        return self.variable_name.lower() not in {"true", "false"}

    def get_full_access_path(self) -> str:
        """Get the full access path including array indices and attribute access."""
        path = self.variable_name
        if self.is_array_access and self.array_indices:
            for idx in self.array_indices:
                path += f"[{idx}]"
        if self.attribute_access:
            path += f".{self.attribute_access}"
        return path


@dataclass
class PBAccessTracker:
    """Tracks variable accesses across a codebase."""

    accesses: list[PBAccess] = field(default_factory=list)
    variable_accesses: dict[str, list[PBAccess]] = field(default_factory=dict)
    container_accesses: dict[str, list[PBAccess]] = field(default_factory=dict)

    def add_access(self, access: PBAccess) -> None:
        """Add an access to the tracker."""
        self.accesses.append(access)

        # Track by variable name
        if access.variable_name not in self.variable_accesses:
            self.variable_accesses[access.variable_name] = []
        self.variable_accesses[access.variable_name].append(access)

        # Track by container
        if access.container:
            container_name = access.container.qualified_name
            if container_name not in self.container_accesses:
                self.container_accesses[container_name] = []
            self.container_accesses[container_name].append(access)

    def get_variable_accesses(self, variable_name: str) -> list[PBAccess]:
        """Get all accesses to a specific variable."""
        return self.variable_accesses.get(variable_name, [])

    def get_read_accesses(self, variable_name: str) -> list[PBAccess]:
        """Get all read accesses to a specific variable."""
        return [
            access
            for access in self.get_variable_accesses(variable_name)
            if access.access_type in (AccessType.READ, AccessType.READ_WRITE)
        ]

    def get_write_accesses(self, variable_name: str) -> list[PBAccess]:
        """Get all write accesses to a specific variable."""
        return [
            access
            for access in self.get_variable_accesses(variable_name)
            if access.access_type in (AccessType.WRITE, AccessType.READ_WRITE)
        ]

    def get_container_accesses(self, container_name: str) -> list[PBAccess]:
        """Get all accesses within a specific container."""
        return self.container_accesses.get(container_name, [])

    def get_instance_variable_accesses(self) -> list[PBAccess]:
        """Get all instance variable accesses."""
        return [
            access for access in self.accesses if access.is_instance_variable_access
        ]

    def get_array_accesses(self) -> list[PBAccess]:
        """Get all array accesses."""
        return [access for access in self.accesses if access.is_array_access]

    def clear(self) -> None:
        """Clear all tracked accesses."""
        self.accesses.clear()
        self.variable_accesses.clear()
        self.container_accesses.clear()


@dataclass
class PBAccessNode(PBNode):
    """PowerBuilder access node.

    Represents access to a PowerBuilder object, which could be a variable,
    property, or array element.

    Attributes:
        accessed: The accessed object
        array_position: Optional array position for array access
    """

    accessed: Any
    array_position: Any | None = None

    def accept_visitor(self, visitor):
        """Accept a visitor according to the visitor pattern.

        Args:
            visitor: The visitor object

        Returns:
            Result of visitor.visit_access(self)
        """
        return visitor.visit_access(self)
