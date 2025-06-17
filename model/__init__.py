"""PowerBuilder model package.

This package contains all model classes for representing PowerBuilder code.

Organization:
- base/: Base classes and core types (PBEntity, PBBehavioralEntity, etc.)
- entities/: Concrete entity types (functions, events, variables, etc.)
- constructs/: Language constructs (arrays, SQL, access modifiers, etc.)
- specialized/: Specialized subsystems
  - ast/: Abstract Syntax Tree nodes
  - pb_datawindow/: DataWindow-specific models
  - pb_transaction/: Transaction-specific models
  - ui/: UI element models
  - system/: System-level definitions
- utils/: Utility classes and type system
- analysis/: Code analysis tools

TODO: Missing Features
    - Security model integration - COMPLETED (SecurityAnalyzer added)
    - Cross-module references - COMPLETED (CrossModuleReferenceResolver added)
"""

from __future__ import annotations

# Analysis tools
from .analysis import (
    AnalysisReport,
    AnalysisResult,
    CallGraph,
    CodeMetrics,
    DependencyAnalysis,
    DependencyGraph,
    SecurityAnalysis,
    UIFlowGraph,
)
from .security_analyzer import SecurityAnalyzer, analyze_security
from .cross_module_resolver import (
    CrossModuleReferenceResolver,
    ModuleInfo,
    SymbolReference,
    CrossModuleContext,
    analyze_cross_module_references
)

# Optimization tools
from .optimization import ExpressionOptimizer

# Note: PrintStatement and ReadStatement not in io.py
from .ast.ast_nodes import (
    # Argument,  # Removed duplicate, use PBArgument instead
    BinaryExpression,
    ControlFlow,
    Event,
    EventTrigger,
    Expression,
    IfStatement,
    Literal,
    ReturnStatement,
    Statement,
    UnaryExpression,
    Variable,
    VariableDeclaration,
)
from .ast.ast_nodes import (
    CaseExpression as CaseBlock,
)
from .ast.ast_nodes import (
    # DoUntilStatement,  # Not implemented yet
    CaseStatement as ChooseCase,
)
from .ast.ast_nodes import (
    DoWhileLoop as DoWhileStatement,
)
from .ast.ast_nodes import (
    ForLoop as ForStatement,
)
from .ast.ast_nodes import (
    WhileLoop as WhileStatement,
)
from .ast.functions import (
    Function,
    FunctionCall,
    Parameter,
)
from .ast.functions import (
    FunctionDefinition as FunctionDeclaration,
)

# AST nodes
from .ast.node_kind import NodeKind
from .ast.sql import (
    DeleteStatement,
    InsertStatement,
    SelectStatement,
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
    UpdateStatement,
)

# Note: TypeChecker and TypeInference need to be implemented
from .ast.types import (
    ArrayAccess,
    ArrayDeclaration,
    # ArrayInitializer,  # Not implemented
    CustomType,
    Type,
    TypeRegistry,
)
from .ast.types import (
    BasicType as PrimitiveType,
    # StructType,  # Not in types.py
    # EnumType,  # Not in types.py
)

# Attribute handling
from .attribute import Attribute, AttributeAccess
from .base.pb_behavioral import PBBehavioralNode as PBBehavioralEntity
from .base.pb_behavioral_library import PBBehavioralLibrary

# Base classes
from .base.pb_entity import PBSourcedEntity as PBEntity
from .base.pb_file import PBCommonFileNode as PBFile
from .constructs.global_vars import GlobalVariables

# Note: PBSQL class needs to be implemented or use existing SQL node classes
from .constructs.pb_access import PBAccess

# Constructs
from .constructs.pb_array import PBArray
from .constructs.pb_attribute_access import PBAttributeAccess
from .constructs.pcode import FunctionBlock
from .entities.expressions import PBExpression
from .entities.function_entities import PBArgumentNode as PBArgument
from .entities.function_entities import PBFunction, PBVariable

# Entities
from .entities.pb_application import PBApplication
from .entities.pb_event import PBEvent

# Library management
from .library import Library, LibraryObject
from .pb_datawindow.column import PBColumn as PBDataWindowColumn

# DataWindow components
# Note: Using PBDataWindow from pb_datawindow instead
from .pb_datawindow.datawindow import PBDataWindow
from .pb_datawindow.table import PBTable as PBDataWindowTable
from .pb_transaction.distributed import (
    PBDistributedTransaction as DistributedTransaction,
)
from .pb_transaction.error_handling import (
    PBTransactionErrorHandler as TransactionErrorHandler,
)
from .pb_transaction.savepoint import PBSavepoint as Savepoint
from .pb_transaction.statement import PBTransactionStatement

# Transaction components
# Note: Using PBTransaction from pb_transaction instead
from .pb_transaction.transaction import PBTransaction

# Source management
from .source import SourceFile, SourceRange
from .source import SourcePosition as Position
from .source import SourcePosition as SourceLocation

# System definitions
from .system.events import PBSystemEvent as SystemEvent
from .system.events import PBSystemEventType as EventType
from .system.functions import PBFunctionCategory as FunctionCategory
from .system.functions import PBSystemFunction as SystemFunction
from .system.globals import PBGlobalVariable as SystemGlobal

# TransactionBlock and TransactionStatement imports removed - file does not exist
# UI components
from .ui import (
    Control,
    DataWindowControl,
    EditMaskControl,
    ListViewControl,
    Menu,
    MenuItem,
    RichTextControl,
    # Note: Specific control types like Button, TextBox, etc. are represented
    # using the generic Control class with appropriate type attributes
    TreeViewControl,
    TreeViewItem,
    UIElement,
    UserObject,
    Window,
)

# Utility classes
from .utils.base import PBNode
from .utils.errors import (
    GenerateError,
    ModelError,
    ParseError,
    ValidationError,
)

# Note: PBType and DataType classes need to be implemented
from .utils.errors import ModelError as ModelException
from .utils.scope import Scope
from .utils.validators import ASTValidator as Validator

__all__ = [
    # Analysis
    "AnalysisReport",
    "AnalysisResult",
    "analyze_security",
    "analyze_cross_module_references",
    "ArrayAccess",
    "ArrayDeclaration",
    # Attribute
    "Attribute",
    "AttributeAccess",
    # 'Argument',  # Use PBArgument instead
    "BinaryExpression",
    "CallGraph",
    "CaseBlock",
    # 'DoWhileStatement',  # Not in control.py
    # 'DoUntilStatement',  # Not in control.py
    "ChooseCase",
    "CodeMetrics",
    "Control",
    # 'StructType',  # Not in types.py
    # 'EnumType',  # Not in types.py
    # 'PrintStatement',  # Not in io.py
    # 'ReadStatement',  # Not in io.py
    "ControlFlow",
    "CrossModuleContext",
    "CrossModuleReferenceResolver",
    "CustomType",
    "DataWindowControl",
    "DeleteStatement",
    "DependencyAnalysis",
    "DependencyGraph",
    "DistributedTransaction",
    "EditMaskControl",
    "Event",
    "EventTrigger",
    "EventType",
    "Expression",
    "ExpressionOptimizer",
    "ForStatement",
    "Function",
    "FunctionBlock",  # Renamed from PCode
    "FunctionCall",
    "FunctionCategory",
    "FunctionDeclaration",
    "GenerateError",
    "GlobalVariables",
    "IfStatement",
    "InsertStatement",
    # Library
    "Library",
    "LibraryObject",
    "ListViewControl",
    "Literal",
    "Menu",
    "MenuItem",
    "ModelError",
    "ModuleInfo",
    # 'PBType',  # Need to implement
    # 'DataType',  # Need to implement
    # 'AccessModifier',  # Need to implement
    "ModelException",
    # AST
    "NodeKind",
    # 'PBSQL',  # Need to implement
    "PBAccess",
    # Entities
    "PBApplication",
    "PBArgument",
    # Constructs
    "PBArray",
    "PBAttributeAccess",
    "PBBehavioralEntity",
    "PBBehavioralLibrary",
    # DataWindow
    "PBDataWindow",
    "PBDataWindowColumn",
    "PBDataWindowTable",
    # Base
    "PBEntity",
    "PBEvent",
    "PBExpression",
    "PBFile",
    "PBFunction",
    # Utils
    "PBNode",  # Base node class
    # Transaction
    # 'TransactionBlock',  # File does not exist
    # 'TransactionStatement',  # File does not exist
    "PBTransaction",
    "PBTransactionStatement",
    "PBVariable",
    "Parameter",
    "ParseError",
    "Position",  # SourcePosition aliased as Position
    # 'ArrayInitializer',  # Not in arrays.py
    "PrimitiveType",
    "ReturnStatement",
    "RichTextControl",
    "SQLCommit",
    "SQLCursor",
    "SQLFromClause",
    "SQLPrepare",
    "SQLQuery",
    "SQLRollback",
    "SQLTransaction",
    "SQLVariable",
    "Savepoint",
    # 'NameValidator',  # Does not exist
    # 'TypeValidator',  # Does not exist
    # 'ExpressionValidator',  # Does not exist
    "Scope",
    "SecurityAnalysis",
    "SecurityAnalyzer",
    "SelectStatement",
    # Source
    "SourceFile",
    "SourceLocation",
    # 'SourceAnchor',  # Does not exist
    "SourceRange",  # From source.source
    "SqlParameter",
    "SqlStatement",
    "Statement",
    "SymbolReference",
    # System
    "SystemEvent",
    "SystemFunction",
    "SystemGlobal",
    "TransactionErrorHandler",
    "TreeViewControl",
    "TreeViewItem",
    "Type",
    # 'TypeChecker',  # Need to implement
    # 'TypeInference',  # Need to implement
    # 'TypeSystem',  # Need to implement
    "TypeRegistry",
    # UI
    "UIElement",
    "UIFlowGraph",
    "UnaryExpression",
    "UpdateStatement",
    "UserObject",
    "ValidationError",
    "Validator",  # ASTValidator aliased as Validator
    "Variable",
    "VariableDeclaration",
    "WhileStatement",
    "Window",
    # 'ScopeManager',  # Does not exist
]
