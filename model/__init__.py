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
    - Security model integration - Missing
    - Cross-module references - Missing
"""

from __future__ import annotations

# Base classes
from .base.pb_entity import PBSourcedEntity as PBEntity
from .base.pb_behavioral import PBBehavioralNode as PBBehavioralEntity
from .base.pb_behavioral_library import PBBehavioralLibrary
from .base.pb_file import PBCommonFileNode as PBFile
# Note: PBType and DataType classes need to be implemented
from .utils.errors import ModelError as ModelException

# Entities
from .entities.pb_application import PBApplication
from .entities.function_entities import PBFunction, PBVariable, PBArgumentNode as PBArgument
from .entities.pb_event import PBEvent
from .entities.expressions import PBExpression

# Constructs
from .constructs.pb_array import PBArray
# Note: PBSQL class needs to be implemented or use existing SQL node classes
from .constructs.pb_access import PBAccess
from .constructs.pb_attribute_access import PBAttributeAccess
from .constructs.global_vars import GlobalVariables
from .constructs.pcode import FunctionBlock

# AST nodes
from .ast.node_kind import NodeKind
from .ast.ast_nodes import (
    # Argument,  # Removed duplicate, use PBArgument instead
    BinaryExpression,
    Event,
    EventTrigger,
    Expression,
    Literal,
    Statement,
    UnaryExpression,
    Variable,
    VariableDeclaration,
)
from .ast.types import (
    CustomType,
    Type,
    BasicType as PrimitiveType,
    # StructType,  # Not in types.py
    # EnumType,  # Not in types.py
)
from .ast.functions import (
    Function,
    Parameter,
    FunctionCall,
    FunctionDefinition as FunctionDeclaration,
)
from .ast.ast_nodes import (
    IfStatement,
    WhileLoop as WhileStatement,
    ForLoop as ForStatement,
    DoWhileLoop as DoWhileStatement,
    # DoUntilStatement,  # Not implemented yet
    CaseStatement as ChooseCase,
    CaseExpression as CaseBlock,
    ReturnStatement,
)
from .ast.types import (
    ArrayAccess,
    ArrayDeclaration,
    # ArrayInitializer,  # Not implemented
)
# Note: PrintStatement and ReadStatement not in io.py
from .ast.ast_nodes import ControlFlow
from .ast.sql import (
    SQLQuery,
    SQLCursor,
    SQLTransaction,
    SQLCommit,
    SQLRollback,
    SQLPrepare,
    SQLVariable,
    SQLFromClause,
    SqlParameter,
    SqlStatement,
    SelectStatement,
    InsertStatement,
    UpdateStatement,
    DeleteStatement,
)

# DataWindow components
# Note: Using PBDataWindow from pb_datawindow instead
from .pb_datawindow.datawindow import PBDataWindow
from .pb_datawindow.column import PBColumn as PBDataWindowColumn
from .pb_datawindow.table import PBTable as PBDataWindowTable

# Transaction components
# Note: Using PBTransaction from pb_transaction instead
from .pb_transaction.transaction import PBTransaction
from .pb_transaction.distributed import PBDistributedTransaction as DistributedTransaction
from .pb_transaction.error_handling import PBTransactionErrorHandler as TransactionErrorHandler
from .pb_transaction.savepoint import PBSavepoint as Savepoint
from .pb_transaction.statement import PBTransactionStatement
# TransactionBlock and TransactionStatement imports removed - file does not exist

# UI components
from .ui import (
    UIElement,
    Window,
    Menu,
    MenuItem,
    Control,
    UserObject,
    DataWindowControl,
    TreeViewItem,
    TreeViewControl,
    EditMaskControl,
    ListViewControl,
    RichTextControl,
    # Note: Specific control types like Button, TextBox, etc. are represented
    # using the generic Control class with appropriate type attributes
)

# System definitions
from .system.events import PBSystemEvent as SystemEvent, PBSystemEventType as EventType
from .system.functions import PBSystemFunction as SystemFunction, PBFunctionCategory as FunctionCategory
from .system.globals import PBGlobalVariable as SystemGlobal

# Library management
from .library import Library, LibraryObject

# Source management
from .source import SourceFile, SourcePosition as SourceLocation

# Attribute handling
from .attribute import Attribute, AttributeAccess

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

# Utility classes
from .utils.base import PBNode
from .source import SourcePosition as Position, SourceRange
from .utils.errors import (
    ModelError,
    ValidationError,
    ParseError,
    GenerateError,
)
# Note: TypeChecker and TypeInference need to be implemented
from .ast.types import TypeRegistry
from .utils.validators import ASTValidator as Validator
from .utils.scope import Scope

__all__ = [
    # Base
    'PBEntity',
    'PBBehavioralEntity',
    'PBBehavioralLibrary',
    'PBFile',
    # 'PBType',  # Need to implement
    # 'DataType',  # Need to implement
    # 'AccessModifier',  # Need to implement
    'ModelException',
    # Entities
    'PBApplication',
    'PBFunction',
    'PBEvent',
    'PBVariable',
    'PBArgument',
    'PBExpression',
    # Constructs
    'PBArray',
    # 'PBSQL',  # Need to implement
    'PBAccess',
    'PBAttributeAccess',
    'GlobalVariables',
    'FunctionBlock',  # Renamed from PCode
    # AST
    'NodeKind',
    # 'Argument',  # Use PBArgument instead
    'BinaryExpression',
    'CustomType',
    'Event',
    'EventTrigger',
    'Expression',
    'Function',
    'Literal',
    'Parameter',
    'SQLCursor',
    'SQLQuery',
    'SQLTransaction',
    'SQLCommit',
    'SQLRollback',
    'SQLPrepare',
    'SQLVariable',
    'SQLFromClause',
    'SqlParameter',
    'SqlStatement',
    'SelectStatement',
    'InsertStatement',
    'UpdateStatement',
    'DeleteStatement',
    'Statement',
    'Type',
    'UnaryExpression',
    'Variable',
    'VariableDeclaration',
    'IfStatement',
    'WhileStatement',
    'ForStatement',
    # 'DoWhileStatement',  # Not in control.py
    # 'DoUntilStatement',  # Not in control.py
    'ChooseCase',
    'CaseBlock',
    'FunctionCall',
    'FunctionDeclaration',
    'ReturnStatement',
    'ArrayAccess',
    'ArrayDeclaration',
    # 'ArrayInitializer',  # Not in arrays.py
    'PrimitiveType',
    # 'StructType',  # Not in types.py
    # 'EnumType',  # Not in types.py
    # 'PrintStatement',  # Not in io.py
    # 'ReadStatement',  # Not in io.py
    'ControlFlow',
    # DataWindow
    'PBDataWindow',
    'PBDataWindowColumn',
    'PBDataWindowTable',
    # Transaction
    # 'TransactionBlock',  # File does not exist
    # 'TransactionStatement',  # File does not exist
    'PBTransaction',
    'DistributedTransaction',
    'TransactionErrorHandler',
    'Savepoint',
    'PBTransactionStatement',
    # UI
    'UIElement',
    'Window',
    'Menu',
    'MenuItem',
    'Control',
    'UserObject',
    'DataWindowControl',
    'TreeViewItem',
    'TreeViewControl',
    'EditMaskControl',
    'ListViewControl',
    'RichTextControl',
    # System
    'SystemEvent',
    'EventType',
    'SystemFunction',
    'FunctionCategory',
    'SystemGlobal',
    # Library
    'Library',
    'LibraryObject',
    # Source
    'SourceFile',
    'SourceLocation',
    # Attribute
    'Attribute',
    'AttributeAccess',
    # Analysis
    'AnalysisReport',
    'AnalysisResult',
    'CallGraph',
    'CodeMetrics',
    'DependencyAnalysis',
    'DependencyGraph',
    'SecurityAnalysis',
    'UIFlowGraph',
    # Utils
    'PBNode',  # Base node class
    # 'SourceAnchor',  # Does not exist
    'SourceRange',  # From source.source
    'Position',  # SourcePosition aliased as Position
    'ModelError',
    'ValidationError',
    'ParseError',
    'GenerateError',
    # 'TypeChecker',  # Need to implement
    # 'TypeInference',  # Need to implement
    # 'TypeSystem',  # Need to implement
    'TypeRegistry',
    'Validator',  # ASTValidator aliased as Validator
    # 'NameValidator',  # Does not exist
    # 'TypeValidator',  # Does not exist
    # 'ExpressionValidator',  # Does not exist
    'Scope',
    # 'ScopeManager',  # Does not exist
]