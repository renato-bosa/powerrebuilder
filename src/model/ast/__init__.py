from __future__ import annotations

# Additional node imports
from .additional_nodes import (
    AttributeNode,
    BetweenExpression,
    CallStatement,
    # Metadata nodes
    CommentNode,
    CompoundAssignment,
    # Statement nodes
    CreateStatement,
    DeclareProcedureStatement,
    DescribeStatement,
    DescriptorNode,
    DestroyStatement,
    # PowerBuilder-specific nodes
    DynamicMethodInvocation,
    # Declaration nodes
    EnumerationDeclaration,
    EnumerationValue,
    ExecuteImmediateStatement,
    ExecuteProcedureStatement,
    ExistsExpression,
    ExportStatement,
    FetchCursorStatement,
    ForwardDeclarationEnd,
    GlobalVariableDeclaration,
    ImportStatement,
    # Expression nodes
    InExpression,
    LibraryReference,
    LikeExpression,
    OleAutomationNode,
    # SQL nodes
    OpenCursorStatement,
    ProcedureParameter,
    SharedVariableDeclaration,
)
from .nodes.base import (
    Assignment as ASTAssignment,
)

# Node imports from consolidated ast_nodes.py
from .nodes.base import (
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
    Identifier,
    IfStatement,
    IntegerLiteral,
    # Goto
    Label,
    # Literals
    Literal,
    NullLiteral,
    RealLiteral,
    RepeatUntilLoop,
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
from .nodes.base import (
    CaseExpression as CaseItem,  # Alias for test compatibility
)
from .nodes.base import (
    Label as LabelStatement,  # Alias for test compatibility
)
from .functions import (
    Function,
    FunctionCall,
    FunctionDefinition,
    Parameter,
    ProcedureCall,
    ProcedureDefinition,
    Signature,
)
from .io import (
    CloseFile,
    FileManager,
    FileMode,
    FileOperation,
    OpenFile,
    ReadFile,
    WriteFile,
)
from .node_kind import NodeKind

# PowerBuilder type imports
from .pb_types import (
    DataType,
    PBArrayType,
    PBBasicType,
    PBBasicTypeNode,
    PBCustomType,
    PBCustomTypeNode,
    PBDataWindowType,
    PBFormatType,
    PBParametrizedType,
    PBSourcedEntity,
    PBType,
    PBTypeNode,
    PBTypeRegistry,
)

# SQL Node imports
from .nodes.sql import (
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
from .nodes.declarations import (
    ArrayAccess,
    ArrayAssignment,
    ArrayDeclaration,
    ArrayOperation,
    ArraySlice,
    ArrayType,
    BasicType,
    CustomType,
    Field,
    Structure,
    Type,
    TypeBounds,
    TypeCategory,
    TypeRegistry,
)

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
