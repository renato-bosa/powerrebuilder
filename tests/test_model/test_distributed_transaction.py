"""Test PowerBuilder distributed transaction handling."""

from model.pb_transaction import (
    PBDistributedTransaction,
    PBTransaction,
    PBTransactionCoordinator,
    PBTransactionParticipant,
)


def test_transaction_coordinator():






    """Test transaction coordinator functionality."""
    coordinator = PBTransactionCoordinator(name="coord1")

    # Add participants
    participant1 = PBTransactionParticipant(transaction_object="sqlca1")
    participant2 = PBTransactionParticipant(transaction_object="sqlca2")

    coordinator.add_participant(participant1)
    coordinator.add_participant(participant2)

    assert len(coordinator.participants) == 2
    assert coordinator.participants[0].transaction_object == "sqlca1"

    # Test prepare_all
    result = coordinator.prepare_all()
    assert result is True
    assert coordinator.participants[0].state.value == "prepared"
    assert coordinator.participants[1].state.value == "prepared"

    # Test commit_all
    result = coordinator.commit_all()
    assert result is True
    assert coordinator.participants[0].state.value == "committed"
    assert coordinator.participants[1].state.value == "committed"

    # Test abort_all
    coordinator.abort_all()
    assert coordinator.participants[0].state.value == "aborted"
    assert coordinator.participants[1].state.value == "aborted"


def test_distributed_transaction():






    """Test distributed transaction functionality."""
    # Create coordinator
    coordinator = PBTransactionCoordinator(name="coord1")

    # Create distributed transaction
    dist_tx = PBDistributedTransaction(coordinator=coordinator)

    # Create and add regular transactions
    tx1 = PBTransaction(transaction_object="sqlca1")
    tx2 = PBTransaction(transaction_object="sqlca2")

    dist_tx.add_transaction(tx1)
    dist_tx.add_transaction(tx2)

    # Verify transactions were added
    assert len(dist_tx.transactions) == 2
    assert dist_tx.transactions[0].transaction_object == "sqlca1"
    assert dist_tx.transactions[1].transaction_object == "sqlca2"

    # Verify participant tracking in coordinator
    assert len(dist_tx.coordinator.participants) == 2
    assert dist_tx.coordinator.participants[0].transaction_object == "sqlca1"

    # Verify distributed flag set on transactions
    assert dist_tx.transactions[0].state.distributed is True
    assert dist_tx.transactions[0].state.coordinator == "coord1"

    # Test prepare
    result = dist_tx.prepare()
    assert result is True
    assert dist_tx.is_active is True

    # Test commit
    result = dist_tx.commit()
    assert result is True
    assert dist_tx.is_active is False

    # Reset and test rollback
    dist_tx.is_active = True
    dist_tx.rollback()
    assert dist_tx.is_active is False
