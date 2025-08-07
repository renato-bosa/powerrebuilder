"""PowerBuilder Transaction Error Handling implementation.

This module contains classes for representing PowerBuilder transaction error handling.
"""

from __future__ import annotations

from dataclasses import field
from enum import Enum
from typing import TYPE_CHECKING

from src.model.types.base import PBNode

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.core.exceptions import TransactionError as PBTransactionError


class ErrorHandlingStrategy(Enum):
    """Error handling strategies."""

    ROLLBACK = "rollback"
    RETRY = "retry"
    IGNORE = "ignore"
    RAISE = "raise"
    CUSTOM = "custom"


class PBErrorHandlerAction(PBNode):
    """Error handler action.

    Attributes: strategy: Error handling strategy to use
        max_retries: Maximum number of retries if strategy is RETRY
        custom_handler: Custom handler function or name
        log_error: Whether to log the error
"""

    strategy: ErrorHandlingStrategy = ErrorHandlingStrategy.ROLLBACK
    max_retries: int = 3
    custom_handler: str | Callable | None = None
    log_error: bool = True


class PBTransactionErrorHandler(PBNode):
    """PowerBuilder transaction error handler.

    Attributes: transaction_object: Name of the transaction object
    error_codes: Dictionary mapping error codes to handler actions
    default_action: Default action for errors not explicitly handled
    is_global: Whether this is a global error handler
"""

    transaction_object: str
    error_codes: dict[int, PBErrorHandlerAction] = field(default_factory=dict)
    default_action: PBErrorHandlerAction = field(
        default_factory=lambda: PBErrorHandlerAction(
            strategy=ErrorHandlingStrategy.ROLLBACK, ), )
    is_global: bool = False

    def add_error_handler(
            self,
            error_code: int,
            action: PBErrorHandlerAction) -> None:
        """Add an error handler for a specific error code.

        Args:
            error_code: The error code to handle
            action: The action to take for this error code
            """
        self.error_codes[error_code] = action

    def get_action_for_error(self, error_code: int) -> PBErrorHandlerAction:
        """Get the action to take for a specific error code.

        Args:
            error_code: The error code to handle

            Returns:
                The action to take for this error code
                """
        return self.error_codes.get(error_code, self.default_action)

    def handle_error(self, error: PBTransactionError) -> PBErrorHandlerAction:
        """Handle a transaction error.

        Args:
            error: The error to handle

            Returns:
                The action that was taken for this error
                """
        return self.get_action_for_error(error.error_code)

# In a real implementation, this would execute the action
        # For now, we just return it
