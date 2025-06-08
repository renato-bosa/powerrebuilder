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
    TypeCategory,
    BasicType,
    TypeBounds,
    TypeRegistry,
    CustomType,
    Type,
    ArrayType,
    ArrayDeclaration,
    ArrayAccess,
    ArrayAssignment,
    ArraySlice,
    ArrayOperation,
)

from .functions import (
    Function,
    Parameter,
    FunctionDefinition,
    ProcedureDefinition,
)

from .io import (
    FileOperation,
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
    # Type system
    "TypeCategory",
    "BasicType",
    "TypeBounds",
    "TypeRegistry",
    "ArrayType",
    # Base nodes
    "ASTNode",
    "Expression",
    "Statement",
    "Block",
    # Literals
    "Literal",
    "IntegerLiteral",
    "RealLiteral",
    "StringLiteral",
    "BooleanLiteral",
    "NullLiteral",
    # Variables and expressions
    "Variable",
    "VariableDeclaration",
    "BinaryExpression",
    "UnaryExpression",
    "ASTAssignment",
    # Control flow
    "Condition",
    "BooleanOperation",
    "IfStatement",
    "WhileLoop",
    "ForLoop",
    "DoWhileLoop",
    "BreakStatement",
    "ContinueStatement",
    "ReturnStatement",
    "ExitStatement",
    # Case statements
    "CaseExpression",
    "CaseStatement",
    # Goto
    "Label",
    "GotoStatement",
    # Exception handling
    "ExceptionType",
    "CatchBlock",
    "FinallyBlock",
    "ThrowStatement",
    "TryCatchStatement",
    # Events and functions
    "Event",
    "EventTrigger",
    "Function",
    "FunctionDefinition",
    "ProcedureDefinition",
    "Parameter",
    # Types
    "CustomType",
    "Type",
    # I/O
    "FileOperation",
    # Array operations
    "ArrayDeclaration",
    "ArrayAccess",
    "ArrayAssignment",
    "ArraySlice",
    "ArrayOperation",
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
