"""AST module for PowerBuilder model."""

from __future__ import annotations

# Base nodes
from .nodes.base import Expression, Statement
from src.model.types.base import PBNode
from .node_kind import NodeKind

# Type imports
from .nodes.declarations import Type, TypeCategory, Field

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

# Import literals
from .literals import (
    Literal, StringLiteral, IntegerLiteral, RealLiteral,
    NullLiteral, BooleanLiteral, Identifier,
    BinaryExpression, UnaryExpression, Function
)

# Import from functions module
from .functions import *

# Import from io module  
from .io import *

# Import PowerBuilder types
from .pb_types import *

# Additional classes for compatibility
class ArrayAccess(Expression):
    def __init__(self, array=None, index=None):
        self.array = array
        self.index = index

class ASTAssignment(Statement):
    def __init__(self, target=None, value=None):
        self.target = target
        self.value = value

class BasicType:
    def __init__(self, name="string"):
        self.name = name

class Block(Statement):
    def __init__(self, statements=None):
        self.statements = statements or []

class CaseStatement(Statement):
    def __init__(self, expression=None, cases=None):
        self.expression = expression
        self.cases = cases or []

class CustomType:
    def __init__(self, name="object"):
        self.name = name

class Event(Statement):
    def __init__(self, name="", parameters=None):
        self.name = name
        self.parameters = parameters or []

class ForLoop(Statement):
    def __init__(self, init=None, condition=None, update=None, body=None):
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body

class FunctionDefinition(Statement):
    def __init__(self, name="", parameters=None, body=None):
        self.name = name
        self.parameters = parameters or []
        self.body = body

class IfStatement(Statement):
    def __init__(self, condition=None, then_stmt=None, else_stmt=None):
        self.condition = condition
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

class Parameter:
    def __init__(self, name="", type_name="string"):
        self.name = name
        self.type_name = type_name

class ReturnStatement(Statement):
    def __init__(self, value=None):
        self.value = value

class Signature:
    def __init__(self, name="", parameters=None, return_type=None):
        self.name = name
        self.parameters = parameters or []
        self.return_type = return_type

class Variable(Expression):
    def __init__(self, name="", type_name="string"):
        self.name = name
        self.type_name = type_name

class WhileLoop(Statement):
    def __init__(self, condition=None, body=None):
        self.condition = condition
        self.body = body

__all__ = [
    # Base classes
    "Expression", "Statement", "PBNode", "NodeKind",
    # Types
    "Type", "TypeCategory", "Field",
    # Literals
    "Literal", "StringLiteral", "IntegerLiteral", "RealLiteral",
    "NullLiteral", "BooleanLiteral", "Identifier",
    "BinaryExpression", "UnaryExpression", "Function",
    # Additional AST nodes
    "ArrayAccess", "ASTAssignment", "BasicType", "Block", "CaseStatement",
    "CustomType", "Event", "ForLoop", "FunctionDefinition", "IfStatement",
    "Parameter", "ReturnStatement", "Signature", "Variable", "WhileLoop",
    # SQL
    "SelectStatement", "InsertStatement", "UpdateStatement", "DeleteStatement",
    "ResultColumn", "FromClause", "TableReference", "JoinClause", "WhereClause",
    "OrderByClause", "OrderingTerm", "LimitClause", "SubqueryExpression",
    "Assignment", "ColumnReference", "GroupByClause", "HavingClause",
    "WithClause", "WithExpression", "SetOperationStatement", "SqlStatement",
    "SqlParameter", "ColonParameter", "QuestionMarkParameter",
    "SQLQuery", "SQLCursor", "SQLTransaction", "SQLCommit", "SQLRollback",
    "SQLPrepare", "SQLVariable", "SQLFromClause",
]
