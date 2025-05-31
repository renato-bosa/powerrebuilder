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
from .error_handling import (
    ErrorHandlingStrategy,
    PBErrorHandlerAction,
    PBTransactionError,
    PBTransactionErrorHandler,
)
from .savepoint import PBSavepoint, PBSavepointOperation, SavepointOperationType
from .statement import PBStatementType, PBTransactionStatement
from .transaction import PBTransaction, PBTransactionObject, PBTransactionState

__all__ = [
    "PBTransaction",
    "PBTransactionObject",
    "PBTransactionState",
    "PBTransactionStatement",
    "PBStatementType",
    "PBSavepoint",
    "PBSavepointOperation",
    "SavepointOperationType",
    "PBDistributedTransaction",
    "PBTransactionCoordinator",
    "PBTransactionParticipant",
    "TransactionParticipantState",
    "PBTransactionError",
    "PBTransactionErrorHandler",
    "PBErrorHandlerAction",
    "ErrorHandlingStrategy",
]
