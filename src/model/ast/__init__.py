from __future__ import annotations

# Additional node imports

# Node imports from consolidated ast_nodes.py
from .node_kind import NodeKind

# Type imports
from .nodes.declarations import Type, TypeCategory, Field

# PowerBuilder type imports

# SQL Node imports
from .nodes.sql import (
    SelectStatement, InsertStatement, UpdateStatement, DeleteStatement,
    ResultColumn, FromClause, TableReference, JoinClause, WhereClause,
    OrderByClause, OrderingTerm, LimitClause, SubqueryExpression,
    Assignment, ColumnReference, GroupByClause, HavingClause,
    WithClause, WithExpression, SetOperationStatement, SqlStatement,
    SqlParameter, ColonParameter, QuestionMarkParameter,
    SQLQuery, SQLCursor, SQLTransaction, SQLCommit, SQLRollback,
    SQLPrepare, SQLVariable, SQLFromClause
)

# Base nodes
from .nodes.base import (
    Expression, Statement
)

# Import literals from literals module
from .literals import (
    Literal, StringLiteral, IntegerLiteral, RealLiteral,
    NullLiteral, BooleanLiteral, Identifier,
    BinaryExpression, UnaryExpression, Function
)

# Additional imports that tests might need
from .additional_nodes import *
from .functions import *
from .io import *
from .pb_types import *

# Aliases for backward compatibility
BasicType = PBBasicTypeNode
CustomType = PBCustomTypeNode

__all__ = [
    "ASTAssignment",
    # Base nodes
    "ASTNode",
    "Identifier",
    "CaseItem",
    "LabelStatement",
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
    "CloseFile",
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
    # Structure
    "Field",
    # I/O
    "FileManager",
    "FileMode",
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
    "OpenFile",
    "OrderByClause",
    "OrderingTerm",
    "Parameter",
    "ProcedureCall",
    "ProcedureDefinition",
    "QuestionMarkParameter",
    "ReadFile",
    "RealLiteral",
    "RepeatUntilLoop",
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
    "Signature",
    "SqlParameter",
    "SqlStatement",
    "Statement",
    "StringLiteral",
    "Structure",
    "SubqueryExpression",
    "TableReference",
    "ThrowStatement",
    "TryCatchStatement",
    "Type",
    "TypeBounds",
    # Type system
    "TypeCategory",
    "TypeRegistry",
    # PowerBuilder types
    "PBType",
    "PBBasicType",
    "PBCustomType",
    "PBArrayType",
    "PBDataWindowType",
    "PBTypeNode",
    "PBBasicTypeNode",
    "PBCustomTypeNode",
    "PBTypeRegistry",
    "DataType",
    "PBSourcedEntity",
    "UnaryExpression",
    "UpdateStatement",
    # Variables and expressions
    "Variable",
    "VariableDeclaration",
    "WhereClause",
    "WhileLoop",
    "WithClause",
    "WithExpression",
    "WriteFile",
    # Parameterized and Format types
    "PBParametrizedType",
    "PBFormatType",
    # Additional nodes from additional_nodes.py
    # Declaration nodes
    "EnumerationDeclaration",
    "EnumerationValue",
    "GlobalVariableDeclaration",
    "SharedVariableDeclaration",
    "ForwardDeclarationEnd",
    # Statement nodes
    "CreateStatement",
    "DestroyStatement",
    "CallStatement",
    "CompoundAssignment",
    # SQL nodes
    "OpenCursorStatement",
    "FetchCursorStatement",
    "ExecuteImmediateStatement",
    "DeclareProcedureStatement",
    "ExecuteProcedureStatement",
    "ProcedureParameter",
    # Expression nodes
    "InExpression",
    "LikeExpression",
    "ExistsExpression",
    "BetweenExpression",
    # PowerBuilder-specific nodes
    "DynamicMethodInvocation",
    "ExportStatement",
    "ImportStatement",
    "DescriptorNode",
    "OleAutomationNode",
    "DescribeStatement",
    # Metadata nodes
    "CommentNode",
    "AttributeNode",
    "LibraryReference",
]
