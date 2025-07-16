"""PowerBuilder Transaction implementation.

This module contains classes for representing PowerBuilder transaction objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from src.base import PBNode

if TYPE_CHECKING:
    from .savepoint import PBSavepoint
    from .statement import PBTransactionStatement


class TransactionIsolationLevel(Enum):
    """Transaction isolation levels."""

    READ_UNCOMMITTED = "read uncommitted"
    READ_COMMITTED = "read committed"
    REPEATABLE_READ = "repeatable read"
    SERIALIZABLE = "serializable"


@dataclass
class PBTransactionObject(PBNode):
    """PowerBuilder transaction object declaration.

    Attributes:
        name: Name of the transaction object (e.g., sqlca)
        dbms: Database management system type
        database: Database name
        userid: User ID for database connection
        dbpass: Password for database connection
        server: Database server name
        autocommit: Whether to use autocommit mode
        isolation_level: Transaction isolation level
        connection_options: Additional connection options
    """

    name: str
    dbms: str | None = None
    database: str | None = None
    userid: str | None = None
    dbpass: str | None = None
    server: str | None = None
    autocommit: bool = False
    isolation_level: TransactionIsolationLevel = field(
        default=TransactionIsolationLevel.READ_COMMITTED, )
    connection_options: dict[str, Any] = field(default_factory=dict)


@dataclass
class PBTransactionState(PBNode):
    """Transaction state.

    Attributes:
        is_connected: Whether the transaction is connected
        savepoints: List of active savepoints
        error_code: Current error code if any
        error_message: Current error message if any
        in_progress: Whether a transaction is in progress
        distributed: Whether this is part of a distributed transaction
        coordinator: Transaction coordinator name if part of distributed tx
    """

    is_connected: bool = False
    savepoints: list[str] = field(default_factory=list)
    error_code: int | None = None
    error_message: str | None = None
    in_progress: bool = False
    distributed: bool = False
    coordinator: str | None = None


@dataclass
class PBTransaction(PBNode):
    """PowerBuilder transaction.

    Represents a transaction or a transaction block in PowerBuilder.

    Attributes:
        transaction_object: Name of the transaction object
        statements: List of statements in the transaction
        savepoints: List of savepoint operations
        has_error_handling: Whether the transaction has error handling
        state: Current state of the transaction
    """

    transaction_object: str
    statements: list[PBTransactionStatement] = field(default_factory=list)
    savepoints: list[PBSavepoint] = field(default_factory=list)
    has_error_handling: bool = False
    state: PBTransactionState = field(default_factory=PBTransactionState)

    def add_statement(self, statement: PBTransactionStatement) -> None:




        """Add a statement to the transaction.

        Args:
            statement: The statement to add
        """
        self.statements.append(statement)

    def add_savepoint(self, savepoint: PBSavepoint) -> None:




        """Add a savepoint to the transaction.

        Args:
            savepoint: The savepoint to add
        """
        self.savepoints.append(savepoint)
        self.state.savepoints.append(savepoint.name)
