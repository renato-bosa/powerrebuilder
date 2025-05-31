"""PowerBuilder Transaction Savepoint implementation.

This module contains classes for representing PowerBuilder transaction savepoints.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..utils.base import PBNode


class SavepointOperationType(Enum):
    """Savepoint operation types."""

    CREATE = "CREATE"
    ROLLBACK_TO = "ROLLBACK_TO"
    RELEASE = "RELEASE"


@dataclass
class PBSavepointOperation(PBNode):
    """Savepoint operation.

    Attributes:
        operation_type: Type of savepoint operation
        savepoint_name: Name of the savepoint
    """

    operation_type: SavepointOperationType
    savepoint_name: str


@dataclass
class PBSavepoint(PBNode):
    """PowerBuilder savepoint.

    Attributes:
        name: Name of the savepoint
        transaction_object: Name of the transaction object
        operations: List of operations performed on this savepoint
        is_active: Whether the savepoint is active
    """

    name: str
    transaction_object: str
    operations: list[PBSavepointOperation] = field(default_factory=list)
    is_active: bool = True

    def add_operation(self, operation_type: SavepointOperationType) -> None:
        """Add an operation to this savepoint.

        Args:
            operation_type: Type of operation to add
        """
        operation = PBSavepointOperation(
            operation_type=operation_type, savepoint_name=self.name,
        )
        self.operations.append(operation)

        # Update savepoint state based on operation
        if operation_type == SavepointOperationType.RELEASE:
            self.is_active = False
