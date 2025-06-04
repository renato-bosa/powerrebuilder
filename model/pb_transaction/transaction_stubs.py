"""Transaction stub classes for PowerBuilder AST.

This module contains stub classes for transaction handling.
"""

from dataclasses import dataclass, field
from typing import Any

from ..utils.base import PBNode


@dataclass
class TransactionObject(PBNode):
    """Transaction object reference."""

    name: str


@dataclass
class TransactionBlock(PBNode):
    """Transaction block with statements."""

    transaction: TransactionObject
    statements: list[Any] = field(default_factory=list)


@dataclass
class TransactionStatement(PBNode):
    """Transaction statement (COMMIT, ROLLBACK, etc.)."""

    type: str  # COMMIT, ROLLBACK, CONNECT, DISCONNECT
    transaction: TransactionObject | None = None
