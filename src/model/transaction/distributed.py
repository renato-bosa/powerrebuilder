"""PowerBuilder Distributed Transaction implementation.

This module contains classes for representing PowerBuilder distributed transactions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from src.base import PBNode

if TYPE_CHECKING:
    from .transaction import PBTransaction


class TransactionParticipantState(Enum):
    """Transaction participant states."""

    INITIAL = "initial"
    PREPARED = "prepared"
    COMMITTED = "committed"
    ABORTED = "aborted"


@dataclass
class PBTransactionParticipant(PBNode):
    """Distributed transaction participant.

    Attributes:
        transaction_object: Name of the transaction object
        state: Current state of the participant
        has_voted: Whether the participant has voted
        vote_commit: Whether the participant voted to commit
    """

    transaction_object: str
    state: TransactionParticipantState = field(
        default=TransactionParticipantState.INITIAL, )
    has_voted: bool = False
    vote_commit: bool = False


@dataclass
class PBTransactionCoordinator(PBNode):
    """Distributed transaction coordinator.

    Attributes:
        name: Name of the coordinator
        participants: List of transaction participants
        is_active: Whether the coordinator is active
        timeout: Timeout for the transaction in seconds
    """

    name: str
    participants: list[PBTransactionParticipant] = field(default_factory=list)
    is_active: bool = False
    timeout: int | None = None

    def add_participant(self, participant: PBTransactionParticipant) -> None:




        """Add a participant to the transaction.

        Args:
            participant: The participant to add
        """
        self.participants.append(participant)

    def prepare_all(self) -> bool:




        """Prepare all participants.

        Returns:
            True if all participants are prepared, False otherwise
        """
        all_prepared = True
        for participant in self.participants:
            # In a real implementation, this would send prepare messages
            participant.state = TransactionParticipantState.PREPARED
            if participant.state != TransactionParticipantState.PREPARED:
                all_prepared = False
        return all_prepared

    def commit_all(self) -> bool:




        """Commit all participants.

        Returns:
            True if all participants committed, False otherwise
        """
        all_committed = True
        for participant in self.participants:
            # In a real implementation, this would send commit messages
            participant.state = TransactionParticipantState.COMMITTED
            if participant.state != TransactionParticipantState.COMMITTED:
                all_committed = False
        return all_committed

    def abort_all(self) -> None:




        """Abort all participants."""
        for participant in self.participants:
            # In a real implementation, this would send abort messages
            participant.state = TransactionParticipantState.ABORTED


@dataclass
class PBDistributedTransaction(PBNode):
    """PowerBuilder distributed transaction.

    Attributes:
        coordinator: Transaction coordinator
        transactions: List of transactions participating in the distributed transaction
        is_active: Whether the distributed transaction is active
    """

    coordinator: PBTransactionCoordinator
    transactions: list[PBTransaction] = field(default_factory=list)
    is_active: bool = False

    def add_transaction(self, transaction: PBTransaction) -> None:




        """Add a transaction to the distributed transaction.

        Args:
            transaction: The transaction to add
        """
        self.transactions.append(transaction)
        transaction.state.distributed = True
        transaction.state.coordinator = self.coordinator.name

        # Add transaction as participant to coordinator
        participant = PBTransactionParticipant(
            transaction_object=transaction.transaction_object, )
        self.coordinator.add_participant(participant)

    def prepare(self) -> bool:




        """Prepare the distributed transaction.

        Returns:
            True if preparation succeeded, False otherwise
        """
        self.is_active = True
        return self.coordinator.prepare_all()

    def commit(self) -> bool:




        """Commit the distributed transaction.

        Returns:
            True if commit succeeded, False otherwise
        """
        result = self.coordinator.commit_all()
        self.is_active = False
        return result

    def rollback(self) -> None:




        """Rollback the distributed transaction."""
        self.coordinator.abort_all()
        self.is_active = False
