"""PowerBuilder SQL model classes.

This module provides AST nodes for representing SQL statements and constructs
in PowerBuilder code, including SELECT, INSERT, UPDATE, DELETE, cursors, and transactions.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional

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

    columns: List[str] = field(default_factory=list)
    from_table: str = ""
    where_clause: Optional[str] = None
    joins: Optional[List[dict[str, str]]] = None
    group_by: Optional[List[str]] = None
    having_clause: Optional[str] = None
    order_by: Optional[List[str]] = None

    def __post_init__(self):
        """Initialize statement type."""
        self.statement_type = "SELECT"


@dataclass
class PBInsertNode(PBSQLStatementNode):
    """INSERT statement node."""

    table: str = ""
    columns: Optional[List[str]] = None
    values: List[Any] = field(default_factory=list)
    select_statement: Optional[str] = None

    def __post_init__(self):
        """Initialize statement type."""
        self.statement_type = "INSERT"


@dataclass
class PBUpdateNode(PBSQLStatementNode):
    """UPDATE statement node."""

    table: str = ""
    assignments: List[tuple[str, Any]] = field(default_factory=list)
    where_clause: Optional[str] = None

    def __post_init__(self):
        """Initialize statement type."""
        self.statement_type = "UPDATE"


@dataclass
class PBDeleteNode(PBSQLStatementNode):
    """DELETE statement node."""

    table: str = ""
    where_clause: Optional[str] = None

    def __post_init__(self):
        """Initialize statement type."""
        self.statement_type = "DELETE"


@dataclass
class PBCursorNode(PBSQLNode):
    """SQL cursor node."""

    name: str = ""
    select_statement: Optional[str] = None
    parameters: Optional[List[str]] = None
    for_update: bool = False

    def __post_init__(self):
        """Initialize SQL type."""
        self.sql_type = "CURSOR"


@dataclass
class PBTransactionNode(PBSQLNode):
    """SQL transaction node."""

    action: str = ""  # COMMIT, ROLLBACK, CONNECT, SAVEPOINT, etc.
    transaction_object: Optional[str] = None
    connection_string: Optional[str] = None
    savepoint_name: Optional[str] = None

    def __post_init__(self):
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
