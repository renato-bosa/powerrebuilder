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
from .entities.pb_function import PBFunction
from .entities.pb_event import PBEvent
from .entities.pb_variable import PBVariable
from .entities.pb_argument import PBArgumentNode as PBArgument
from .entities.pb_expression import PBExpression

# Constructs
from .constructs.pb_array import PBArray
# Note: PBSQL class needs to be implemented or use existing SQL node classes
from .constructs.pb_access import PBAccess
from .constructs.pb_attribute_access import PBAttributeAccess
from .constructs.global_vars import GlobalVariables
from .constructs.pcode import FunctionBlock

# AST nodes
from .ast.node_kind import NodeKind
from .ast.nodes import (
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
)
from .ast.functions import (
    Function,
    Parameter,
)
from .ast.control import (
    IfStatement,
    WhileLoop as WhileStatement,
    ForLoop as ForStatement,
    # DoWhileStatement,  # Not found in control.py
    # DoUntilStatement,  # Not found in control.py  
    CaseStatement as ChooseCase,
    CaseItem as CaseBlock,
)
from .ast.functions import (
    FunctionCall,
    FunctionDefinition as FunctionDeclaration,
)
from .ast.control import (
    ReturnStatement,
)
from .ast.arrays import (
    ArrayAccess,
    ArrayDeclaration,
    # ArrayInitializer,  # Not in arrays.py
)
from .ast.types import (
    BasicType as PrimitiveType,
    # StructType,  # Not in types.py
    # EnumType,  # Not in types.py
)
# Note: PrintStatement and ReadStatement not in io.py
from .ast.controlflow import ControlFlow
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
from .pb_datawindow.column import PBDataWindowColumn
from .pb_datawindow.table import PBDataWindowTable

# Transaction components
# Note: Using PBTransaction from pb_transaction instead
from .pb_transaction.transaction import PBTransaction
from .pb_transaction.distributed import DistributedTransaction
from .pb_transaction.error_handling import TransactionErrorHandler
from .pb_transaction.savepoint import Savepoint
from .pb_transaction.statement import TransactionStatement as PBTransactionStatement
from .pb_transaction.transaction_stubs import TransactionBlock, TransactionStatement

# UI components
from .ui.ui_elements import (
    UIElement,
    Window,
    Menu,
    Control,
    Button,
    TextBox,
    Label,
    DataWindowControl as UIDataWindowControl,
    TreeView,
    ListView,
    TabControl,
    GroupBox,
    CheckBox,
    RadioButton,
    ComboBox,
    ListBox,
    PictureBox,
    CommandButton,
    StaticText,
    EditMask,
    MultiLineEdit,
    RichTextEdit,
    DropDownListBox,
    DropDownPictureListBox,
    Graph,
    HProgressBar,
    VProgressBar,
    HScrollBar,
    VScrollBar,
    HTrackBar,
    VTrackBar,
    Picture,
    PictureButton,
    StaticHyperLink,
    Animation,
    DatePicker,
    MonthCalendar,
    InkEdit,
    InkPicture,
)

# System definitions
from .system.events import SystemEvent, EventType
from .system.functions import SystemFunction, FunctionCategory
from .system.globals import SystemGlobal

# Library management
from .library.library import Library, LibraryObject

# Source management
from .source.source import SourceFile, SourceLocation

# Attribute handling
from .attribute.attribute import Attribute, AttributeAccess

# Analysis tools
from .analysis.analysis import (
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
from .utils.common import (
    SourceAnchor,
    SourceRange,
    Position,
)
from .utils.errors import (
    ModelError,
    ValidationError,
    ParseError,
    GenerateError,
)
# Note: TypeChecker and TypeInference need to be implemented
from .ast.types import TypeRegistry
from .utils.validation import Validator
from .utils.validators import (
    NameValidator,
    TypeValidator,
    ExpressionValidator,
)
from .utils.scope import Scope, ScopeManager
from .utils.logging import get_logger

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
    'TransactionBlock',
    'TransactionStatement',
    'PBTransaction',
    'DistributedTransaction',
    'TransactionErrorHandler',
    'Savepoint',
    'PBTransactionStatement',
    # UI
    'UIElement',
    'Window',
    'Menu',
    'Control',
    'Button',
    'TextBox',
    'Label',
    'UIDataWindowControl',
    'TreeView',
    'ListView',
    'TabControl',
    'GroupBox',
    'CheckBox',
    'RadioButton',
    'ComboBox',
    'ListBox',
    'PictureBox',
    'CommandButton',
    'StaticText',
    'EditMask',
    'MultiLineEdit',
    'RichTextEdit',
    'DropDownListBox',
    'DropDownPictureListBox',
    'Graph',
    'HProgressBar',
    'VProgressBar',
    'HScrollBar',
    'VScrollBar',
    'HTrackBar',
    'VTrackBar',
    'Picture',
    'PictureButton',
    'StaticHyperLink',
    'Animation',
    'DatePicker',
    'MonthCalendar',
    'InkEdit',
    'InkPicture',
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
    'SourceAnchor',
    'SourceRange',
    'Position',
    'ModelError',
    'ValidationError',
    'ParseError',
    'GenerateError',
    # 'TypeChecker',  # Need to implement
    # 'TypeInference',  # Need to implement
    # 'TypeSystem',  # Need to implement
    'TypeRegistry',
    'Validator',
    'NameValidator',
    'TypeValidator',
    'ExpressionValidator',
    'Scope',
    'ScopeManager',
    'get_logger',
]