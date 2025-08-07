"""PowerBuilder transaction savepoint models.

This module contains models for representing transaction savepoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from src.model.types.base import PBNode


class SavepointOperationType(Enum):
    """Types of savepoint operations."""

    CREATE = auto()
    RELEASE = auto()
    ROLLBACK = auto()


@dataclass
class PBSavepoint(PBNode):
    """Represents a transaction savepoint."""

    transaction_id: str | None = None


    def __str__(self) -> str:


        return f"SAVEPOINT {self.name}"


@dataclass
class PBSavepointOperation(PBNode):
    """Represents a savepoint operation."""

    operation_type: SavepointOperationType
    savepoint_name: str
    transaction_id: str | None = None

    def __str__(self) -> str:


        if self.operation_type == SavepointOperationType.CREATE:
            return f"SAVEPOINT {self.savepoint_name}"
        elif self.operation_type == SavepointOperationType.RELEASE:
            return f"RELEASE SAVEPOINT {self.savepoint_name}"
        elif self.operation_type == SavepointOperationType.ROLLBACK:
            return f"ROLLBACK TO SAVEPOINT {self.savepoint_name}"
