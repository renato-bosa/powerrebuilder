from __future__ import annotations

from .ast_nodes import (
    Assignment as ASTAssignment,
)

# Node imports from consolidated ast_nodes.py
from .ast_nodes import (
    # Base classes
    ASTNode,
    # Operators
    BinaryExpression,
    Block,
    BooleanLiteral,
    BooleanOperation,
    BreakStatement,
    # Case statements
    CaseExpression,
    CaseStatement,
    CatchBlock,
    # Control flow
    Condition,
    ContinueStatement,
    # Code generation
    ControlFlow,
    DoWhileLoop,
    # Events
    Event,
    EventTrigger,
    # Exception handling
    ExceptionType,
    ExitStatement,
    Expression,
    FinallyBlock,
    ForLoop,
    GotoStatement,
    IfStatement,
    IntegerLiteral,
    # Goto
    Label,
    # Literals
    Literal,
    NullLiteral,
    RealLiteral,
    ReturnStatement,
    Statement,
    StringLiteral,
    ThrowStatement,
    TryCatchStatement,
    UnaryExpression,
    # Variables
    Variable,
    VariableDeclaration,
    WhileLoop,
)
from .functions import (
    Function,
    FunctionCall,
    FunctionDefinition,
    Parameter,
    ProcedureDefinition,
)
from .io import (
    FileOperation,
)
from .node_kind import NodeKind

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
    SetOperationStatement,
    SQLCommit,
    SQLCursor,
    SQLFromClause,
    SqlParameter,
    SQLPrepare,
    SQLQuery,
    SQLRollback,
    SqlStatement,
    SQLTransaction,
    SQLVariable,
    SubqueryExpression,
    TableReference,
    UpdateStatement,
    WhereClause,
    WithClause,
    WithExpression,
)
from .types import (
    ArrayAccess,
    ArrayAssignment,
    ArrayDeclaration,
    ArrayOperation,
    ArraySlice,
    ArrayType,
    BasicType,
    CustomType,
    Type,
    TypeBounds,
    TypeCategory,
    TypeRegistry,
)

__all__ = [
    "ASTAssignment",
    # Base nodes
    "ASTNode",
    "ArrayAccess",
    "ArrayAssignment",
    # Array operations
    "ArrayDeclaration",
    "ArrayOperation",
    "ArraySlice",
    "ArrayType",
    # SQL Nodes
    "Assignment",
    "BasicType",
    "BinaryExpression",
    "Block",
    "BooleanLiteral",
    "BooleanOperation",
    "BreakStatement",
    # Case statements
    "CaseExpression",
    "CaseStatement",
    "CatchBlock",
    "ColonParameter",
    "ColumnReference",
    # Control flow
    "Condition",
    "ContinueStatement",
    "ControlFlow",
    # Types
    "CustomType",
    "DeleteStatement",
    "DoWhileLoop",
    # Events and functions
    "Event",
    "EventTrigger",
    # Exception handling
    "ExceptionType",
    "ExitStatement",
    "Expression",
    # I/O
    "FileOperation",
    "FinallyBlock",
    "ForLoop",
    "FromClause",
    "Function",
    "FunctionDefinition",
    "GotoStatement",
    "GroupByClause",
    "HavingClause",
    "IfStatement",
    "InsertStatement",
    "IntegerLiteral",
    "JoinClause",
    # Goto
    "Label",
    "LimitClause",
    # Literals
    "Literal",
    "NodeKind",
    "NullLiteral",
    "OrderByClause",
    "OrderingTerm",
    "Parameter",
    "ProcedureDefinition",
    "QuestionMarkParameter",
    "RealLiteral",
    "ResultColumn",
    "ReturnStatement",
    "SQLCommit",
    "SQLCursor",
    "SQLFromClause",
    "SQLPrepare",
    "SQLQuery",
    "SQLRollback",
    "SQLTransaction",
    "SQLVariable",
    "SelectStatement",
    "SetOperationStatement",
    "SqlParameter",
    "SqlStatement",
    "Statement",
    "StringLiteral",
    "SubqueryExpression",
    "TableReference",
    "ThrowStatement",
    "TryCatchStatement",
    "Type",
    "TypeBounds",
    # Type system
    "TypeCategory",
    "TypeRegistry",
    "UnaryExpression",
    "UpdateStatement",
    # Variables and expressions
    "Variable",
    "VariableDeclaration",
    "WhereClause",
    "WhileLoop",
    "WithClause",
    "WithExpression",
]
