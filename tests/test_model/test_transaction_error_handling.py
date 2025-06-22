"""Test PowerBuilder transaction error handling."""

from model.pb_transaction import (
    ErrorHandlingStrategy,
    PBErrorHandlerAction,
    PBTransactionError,
    PBTransactionErrorHandler,
)


def test_transaction_error():






    """Test transaction error class."""
    error = PBTransactionError(
        error_code=1234,
        sql_state="23000",
        message="Integrity constraint violation",
        transaction_object="sqlca",
        statement="INSERT INTO customers (id) VALUES (1)",
    )

    assert error.error_code == 1234
    assert error.sql_state == "23000"
    assert "Integrity constraint" in error.message
    assert error.transaction_object == "sqlca"
    assert "INSERT INTO" in error.statement


def test_error_handler_action():






    """Test error handler action class."""
    # Test with rollback strategy
    action_rollback = PBErrorHandlerAction(
        strategy=ErrorHandlingStrategy.ROLLBACK,
        log_error=True,
    )
    assert action_rollback.strategy == ErrorHandlingStrategy.ROLLBACK
    assert action_rollback.log_error is True

    # Test with retry strategy
    action_retry = PBErrorHandlerAction(
        strategy=ErrorHandlingStrategy.RETRY,
        max_retries=5,
        log_error=True,
    )
    assert action_retry.strategy == ErrorHandlingStrategy.RETRY
    assert action_retry.max_retries == 5

    # Test with custom handler
    def custom_handler(error) -> str:

        return f"Handled error {error.error_code}"

    action_custom = PBErrorHandlerAction(
        strategy=ErrorHandlingStrategy.CUSTOM,
        custom_handler=custom_handler,
    )
    assert action_custom.strategy == ErrorHandlingStrategy.CUSTOM
    assert action_custom.custom_handler is not None


def test_transaction_error_handler():






    """Test transaction error handler class."""
    handler = PBTransactionErrorHandler(transaction_object="sqlca")

    # Add error handlers for specific error codes
    action1 = PBErrorHandlerAction(strategy=ErrorHandlingStrategy.ROLLBACK)
    action2 = PBErrorHandlerAction(strategy=ErrorHandlingStrategy.RETRY, max_retries=3)
    action3 = PBErrorHandlerAction(strategy=ErrorHandlingStrategy.IGNORE)

    handler.add_error_handler(1001, action1)
    handler.add_error_handler(1002, action2)
    handler.add_error_handler(1003, action3)

    # Verify handlers were added
    assert len(handler.error_codes) == 3
    assert handler.error_codes[1001].strategy == ErrorHandlingStrategy.ROLLBACK
    assert handler.error_codes[1002].strategy == ErrorHandlingStrategy.RETRY
    assert handler.error_codes[1002].max_retries == 3

    # Test get_action_for_error - with registered error code
    action = handler.get_action_for_error(1001)
    assert action.strategy == ErrorHandlingStrategy.ROLLBACK

    # Test get_action_for_error - with unregistered error code (uses default)
    action = handler.get_action_for_error(9999)
    assert action.strategy == ErrorHandlingStrategy.ROLLBACK  # Default strategy

    # Test handle_error
    error = PBTransactionError(error_code=1002, message="Test error")
    action = handler.handle_error(error)
    assert action.strategy == ErrorHandlingStrategy.RETRY
    assert action.max_retries == 3
