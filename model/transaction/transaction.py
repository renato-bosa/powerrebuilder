"""Transaction classes for PowerBuilder.

This module contains classes for handling PowerBuilder database transactions.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto

from ..utils.base import PBNode


# ─── Transaction States ────────────────────────────────────────────────
class TransactionStatus(Enum):
    """Transaction status enumeration."""

    INACTIVE = auto()
    ACTIVE = auto()
    PENDING_COMMIT = auto()
    PENDING_ROLLBACK = auto()
    PREPARED = auto()  # For two-phase commit protocol
    COMMITTED = auto()
    ROLLED_BACK = auto()
    ERROR = auto()


class IsolationLevel(Enum):
    """Transaction isolation levels."""

    READ_UNCOMMITTED = auto()
    READ_COMMITTED = auto()
    REPEATABLE_READ = auto()
    SERIALIZABLE = auto()


# ─── Transaction Core ────────────────────────────────────────────────────
@dataclass
class Transaction(PBNode):
    """PowerBuilder transaction object."""

    name: str
    dbms: str
    database: str
    userid: str | None = None
    dbpass: str | None = None
    server: str | None = None
    autocommit: bool = False
    isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED
    timeout: int = 0  # Timeout in seconds, 0 means no timeout
    lock_mode: str = "Cursor Stability"  # Default for PowerBuilder


@dataclass
class TransactionState(PBNode):
    """Transaction state tracking."""

    transaction: Transaction
    status: TransactionStatus = TransactionStatus.INACTIVE
    savepoints: set[str] = field(default_factory=set)
    current_savepoint: str | None = None
    error_code: int | None = None
    error_message: str | None = None
    dbpass_encrypted: bool = True  # Whether the password is stored encrypted
    connection_id: str | None = None
    connection_time: float | None = None
    last_sql: str | None = None
    active_cursors: set[str] = field(default_factory=set)
    prepared_statements: dict[str, str] = field(
        default_factory=dict,
    )  # ID -> SQL mapping

    def is_connected(self) -> bool:
        """Check if the transaction is connected to the database."""
        return self.status != TransactionStatus.INACTIVE

    def has_error(self) -> bool:
        """Check if the transaction has an error."""
        return self.error_code is not None or self.status == TransactionStatus.ERROR

    def clear_error(self) -> None:
        """Clear any error state."""
        self.error_code = None
        self.error_message = None
        if self.status == TransactionStatus.ERROR:
            self.status = TransactionStatus.ACTIVE

    def reset(self) -> None:
        """Reset the transaction state."""
        self.status = TransactionStatus.INACTIVE
        self.savepoints.clear()
        self.current_savepoint = None
        self.error_code = None
        self.error_message = None
        self.connection_id = None
        self.connection_time = None
        self.last_sql = None
        self.active_cursors.clear()
        self.prepared_statements.clear()


# ─── Transaction Operations ─────────────────────────────────────────────
@dataclass
class Connect(PBNode):
    """Database connect operation."""

    transaction: Transaction
    using_profile: str | None = None
    is_async: bool = False  # Whether the connection is asynchronous
    timeout: int | None = None  # Override transaction timeout


@dataclass
class Disconnect(PBNode):
    """Database disconnect operation."""

    transaction: Transaction
    close_cursors: bool = True  # Whether to close all open cursors


@dataclass
class Commit(PBNode):
    """Transaction commit operation."""

    transaction: Transaction
    using_savepoint: str | None = None
    is_async: bool = False  # Whether the commit is asynchronous


@dataclass
class Rollback(PBNode):
    """Transaction rollback operation."""

    transaction: Transaction
    to_savepoint: str | None = None
    is_async: bool = False  # Whether the rollback is asynchronous


@dataclass
class Savepoint(PBNode):
    """Transaction savepoint operation."""

    transaction: Transaction
    name: str


# ─── Distributed Transactions ───────────────────────────────────────────
@dataclass
class DistributedTransaction(PBNode):
    """Two-phase commit coordinator for distributed transactions."""

    coordinator_name: str
    participant_transactions: list[Transaction] = field(default_factory=list)
    status: TransactionStatus = TransactionStatus.INACTIVE
    timeout: int = 30  # Timeout in seconds
    error_code: int | None = None
    error_message: str | None = None

    def add_participant(self, transaction: Transaction) -> bool:
        """Add a participant to the distributed transaction.

        Args:
            transaction: The transaction to add

        Returns:
            True if added successfully, False if already exists
        """
        if transaction in self.participant_transactions:
            return False

        self.participant_transactions.append(transaction)
        return True

    def prepare(self) -> bool:
        """Prepare all participants for commit (phase 1).

        Returns:
            True if all participants prepared successfully, False otherwise
        """
        # In a real implementation, this would communicate with all participants
        # to ensure they're ready to commit
        self.status = TransactionStatus.PREPARED
        return True

    def commit(self) -> bool:
        """Commit all participants (phase 2).

        Returns:
            True if all participants committed successfully, False otherwise
        """
        # In a real implementation, this would tell all participants to commit
        self.status = TransactionStatus.COMMITTED
        return True

    def rollback(self) -> bool:
        """Rollback all participants.

        Returns:
            True if all participants rolled back successfully, False otherwise
        """
        # In a real implementation, this would tell all participants to rollback
        self.status = TransactionStatus.ROLLED_BACK
        return True


@dataclass
class PrepareStatement(PBNode):
    """Phase 1 of two-phase commit protocol for a distributed transaction."""

    distributed_transaction: DistributedTransaction


@dataclass
class CommitDistributed(PBNode):
    """Phase 2 of two-phase commit protocol for a distributed transaction."""

    distributed_transaction: DistributedTransaction


@dataclass
class RollbackDistributed(PBNode):
    """Rollback a distributed transaction."""

    distributed_transaction: DistributedTransaction


# ─── Error Handling ─────────────────────────────────────────────────────
@dataclass
class TransactionErrorHandler(PBNode):
    """Custom error handling for transactions."""

    transaction: Transaction
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: int = 1000  # Milliseconds
    auto_rollback: bool = True
    auto_disconnect: bool = False
    error_callbacks: dict[int, Callable] = field(
        default_factory=dict,
    )  # Error code -> callback

    def handle_error(self, error_code: int, error_message: str) -> bool:
        """Handle a transaction error.

        Args:
            error_code: The error code
            error_message: The error message

        Returns:
            True if error was handled, False if unhandled
        """
        # Set error in transaction state
        state = TransactionState(transaction=self.transaction)
        state.error_code = error_code
        state.error_message = error_message
        state.status = TransactionStatus.ERROR

        # Check for specific error handler
        if error_code in self.error_callbacks:
            # Call the specific handler
            return self.error_callbacks[error_code](
                self.transaction,
                error_code,
                error_message,
            )

        # Default handling
        if self.auto_rollback:
            # Rollback the transaction
            Rollback(transaction=self.transaction)
            # In a real implementation, this would actually execute the rollback

        if self.auto_disconnect:
            # Disconnect from the database
            Disconnect(transaction=self.transaction)
            # In a real implementation, this would actually execute the disconnect

        return False  # Unhandled error

    def register_error_handler(self, error_code: int, callback: Callable) -> None:
        """Register a callback for a specific error code.

        Args:
            error_code: The error code to handle
            callback: The callback function to call when this error occurs
                     Signature: callback(transaction, error_code, error_message) -> bool
        """
        self.error_callbacks[error_code] = callback
