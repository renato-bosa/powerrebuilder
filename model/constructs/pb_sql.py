"""PowerBuilder SQL model classes.

This module provides AST nodes for representing SQL statements and constructs
in PowerBuilder code, including SELECT, INSERT, UPDATE, DELETE, cursors, and transactions.
"""

from dataclasses import dataclass, field
from typing import Any

from ..utils.base import PBNode


@dataclass
class PBSQLNode(PBNode):
    """Base class for all SQL nodes."""

    sql_type: str = ""


@dataclass
class PBSQLStatementNode(PBSQLNode):
    """Base class for SQL statement nodes."""

    statement: str = ""
    statement_type: str = ""


@dataclass
class PBSelectNode(PBSQLStatementNode):
    """SELECT statement node."""

    columns: list[str] = field(default_factory=list)
    from_table: str = ""
    where_clause: str | None = None
    joins: list[dict[str, str | None]] = None
    group_by: list[str | None] = None
    having_clause: str | None = None
    order_by: list[str | None] = None

    def __post_init__(self) -> None:


        

        """Initialize statement type."""
        self.statement_type = "SELECT"


@dataclass
class PBInsertNode(PBSQLStatementNode):
    """INSERT statement node."""

    table: str = ""
    columns: list[str | None] = None
    values: list[Any] = field(default_factory=list)
    select_statement: str | None = None

    def __post_init__(self) -> None:


        

        """Initialize statement type."""
        self.statement_type = "INSERT"


@dataclass
class PBUpdateNode(PBSQLStatementNode):
    """UPDATE statement node."""

    table: str = ""
    assignments: list[tuple[str, Any]] = field(default_factory=list)
    where_clause: str | None = None

    def __post_init__(self) -> None:


        

        """Initialize statement type."""
        self.statement_type = "UPDATE"


@dataclass
class PBDeleteNode(PBSQLStatementNode):
    """DELETE statement node."""

    table: str = ""
    where_clause: str | None = None

    def __post_init__(self) -> None:


        

        """Initialize statement type."""
        self.statement_type = "DELETE"


@dataclass
class PBCursorNode(PBSQLNode):
    """SQL cursor node."""

    name: str = ""
    select_statement: str | None = None
    parameters: list[str | None] = None
    for_update: bool = False

    def __post_init__(self) -> None:


        

        """Initialize SQL type."""
        self.sql_type = "CURSOR"


@dataclass
class PBTransactionNode(PBSQLNode):
    """SQL transaction node."""

    action: str = ""  # COMMIT, ROLLBACK, CONNECT, SAVEPOINT, etc.
    transaction_object: str | None = None
    connection_string: str | None = None
    savepoint_name: str | None = None

    def __post_init__(self) -> None:


        

        """Initialize SQL type."""
        self.sql_type = "TRANSACTION"


@dataclass
class PBCloseSqlCursorNode(PBNode):
    """Close SQL cursor node."""

    identifier: Any = None


@dataclass
class PBDeclareCursorNode(PBNode):
    """Declare cursor node."""

    identifier: Any = None
    target: Any = None


@dataclass
class PBDeclareProcedureNode(PBNode):
    """Declare procedure node."""

    procedure_name: Any = None


@dataclass
class PBExecuteProcedureNode(PBNode):
    """Execute procedure node."""

    procedure_name: Any = None
    using_clause: Any = None