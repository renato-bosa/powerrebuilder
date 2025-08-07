"""PowerBuilder Transaction implementation.

This module contains classes for representing PowerBuilder transaction objects
and related database operations that are used in the original PowerBuilder application.
"""

from __future__ import annotations

from .distributed import (
    PBDistributedTransaction,
    PBTransactionCoordinator,
    PBTransactionParticipant,
    TransactionParticipantState,
)
from .error_handling import ErrorHandlingStrategy, PBErrorHandlerAction, PBTransactionErrorHandler
from .savepoint import PBSavepoint, PBSavepointOperation, SavepointOperationType
from .statement import PBStatementType, PBTransactionStatement
from .transaction import PBTransaction, PBTransactionObject, PBTransactionState
from src.core.exceptions import TransactionError as PBTransactionError

__all__ = [
    "ErrorHandlingStrategy",
    "PBDistributedTransaction",
    "PBErrorHandlerAction",
    "PBSavepoint",
    "PBSavepointOperation",
    "PBStatementType",
    "PBTransaction",
    "PBTransactionCoordinator",
    "PBTransactionError",
    "PBTransactionErrorHandler",
    "PBTransactionObject",
    "PBTransactionParticipant",
    "PBTransactionState",
    "PBTransactionStatement",
    "SavepointOperationType",
    "TransactionParticipantState",
]
