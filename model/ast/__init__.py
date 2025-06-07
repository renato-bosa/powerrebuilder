from __future__ import annotations

from .node_kind import NodeKind

# Node imports from consolidated ast_nodes.py
from .ast_nodes import (
    # Base classes
    ASTNode,
    Expression,
    Statement,
    Block,
    # Literals
    Literal,
    IntegerLiteral,
    RealLiteral,
    StringLiteral,
    BooleanLiteral,
    NullLiteral,
    # Variables
    Variable,
    VariableDeclaration,
    # Operators
    BinaryExpression,
    UnaryExpression,
    Assignment as ASTAssignment,
    # Control flow
    Condition,
    BooleanOperation,
    IfStatement,
    WhileLoop,
    ForLoop,
    DoWhileLoop,
    BreakStatement,
    ContinueStatement,
    ReturnStatement,
    ExitStatement,
    # Case statements
    CaseExpression,
    CaseStatement,
    # Goto
    Label,
    GotoStatement,
    # Exception handling
    ExceptionType,
    CatchBlock,
    FinallyBlock,
    ThrowStatement,
    TryCatchStatement,
    # Events
    Event,
    EventTrigger,
    # Code generation
    ControlFlow,
)

from .types import (
    CustomType,
    Type,
    ArrayDeclaration,
    ArrayAccess,
    ArrayAssignment,
    ArraySlice,
    ArrayOperation,
)

from .functions import (
    Function,
    Parameter,
)

# SQL Node imports
from .sql import (
    Assignment,
    ColonParameter,
    ColumnReference,
    DeleteStatement,
    FromClause,
    GroupByClause,
    HavingClause,
    InsertStatement,
    JoinClause,
    LimitClause,
    OrderByClause,
    OrderingTerm,
    QuestionMarkParameter,
    ResultColumn,
    SelectStatement,
    SQLCommit,
    SQLCursor,
    SQLFromClause,
    SQLPrepare,
    SQLQuery,
    SQLRollback,
    SQLTransaction,
    SQLVariable,
    SqlParameter,
    SqlStatement,
    SubqueryExpression,
    TableReference,
    UpdateStatement,
    WhereClause,
    WithClause,
    WithExpression,
)

__all__ = [
    "NodeKind",
    "ControlFlow",
    # Nodes
    "BinaryExpression",
    "CustomType",
    "Event",
    "EventTrigger",
    "Expression",
    "Function",
    "Literal",
    "Parameter",
    "Statement",
    "Type",
    "UnaryExpression",
    "Variable",
    "VariableDeclaration",
    # SQL Nodes
    "Assignment",
    "ColonParameter",
    "ColumnReference",
    "DeleteStatement",
    "FromClause",
    "GroupByClause",
    "HavingClause",
    "InsertStatement",
    "JoinClause",
    "LimitClause",
    "OrderByClause",
    "OrderingTerm",
    "QuestionMarkParameter",
    "ResultColumn",
    "SelectStatement",
    "SQLCommit",
    "SQLCursor",
    "SQLFromClause",
    "SQLPrepare",
    "SQLQuery",
    "SQLRollback",
    "SQLTransaction",
    "SQLVariable",
    "SqlParameter",
    "SqlStatement",
    "SubqueryExpression",
    "TableReference",
    "UpdateStatement",
    "WhereClause",
    "WithClause",
    "WithExpression",
]
