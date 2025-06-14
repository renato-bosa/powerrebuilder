"""PowerBuilder Transaction Statement implementation.

This module contains classes for representing PowerBuilder transaction statements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from model.utils.base import PBNode


class PBStatementType(Enum):
    """Transaction statement types."""

    CONNECT = "CONNECT"
    DISCONNECT = "DISCONNECT"
    COMMIT = "COMMIT"
    ROLLBACK = "ROLLBACK"
    EXECUTE = "EXECUTE"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SELECT = "SELECT"
    PREPARE = "PREPARE"
    EXECUTE_IMMEDIATE = "EXECUTE IMMEDIATE"
    DECLARE_CURSOR = "DECLARE CURSOR"
    OPEN_CURSOR = "OPEN"
    FETCH = "FETCH"
    CLOSE_CURSOR = "CLOSE"
    SAVEPOINT = "SAVEPOINT"
    LOCK_TABLE = "LOCK TABLE"


@dataclass
class PBTransactionStatement(PBNode):
    """PowerBuilder transaction statement.

    Represents a SQL statement or transaction operation.

    Attributes:
        statement_type: Type of statement
        transaction_object: Name of the transaction object
        sql_text: SQL text if applicable
        parameters: SQL parameters if applicable
        options: Statement options
        cursor_name: Cursor name if applicable
        savepoint_name: Savepoint name if applicable
        in_catch_block: Whether the statement is in a catch block
    """

    statement_type: PBStatementType | str
    transaction_object: str
    sql_text: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    cursor_name: str | None = None
    savepoint_name: str | None = None
    in_catch_block: bool = False

    def __post_init__(self):
        """Convert string statement_type to enum if needed."""
        if isinstance(self.statement_type, str):
            try:
                self.statement_type = PBStatementType[self.statement_type]
            except KeyError:
                # Keep as string if not in enum
                pass
