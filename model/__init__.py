"""PowerBuilder model package.

This package contains all model classes for representing PowerBuilder code.

TODO: Missing Features
    - Security model integration - Missing
    - Cross-module references - Missing
"""

from __future__ import annotations

# AST nodes
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
from .ast.controlflow import ControlFlow
from .ast.node_kind import NodeKind
from .ast.nodes import (
    Argument,
    BinaryExpression,
    CustomType,
    Event,
    EventTrigger,
    Expression,
    Function,
    Literal,
    Parameter,
    SQLCursor,
    SQLQuery,
    SQLTransaction,
    Statement,
    Type,
    UnaryExpression,
    Variable,
    VariableDeclaration,
)

# Attribute handling
from .attribute.attribute import Attribute, AttributeAccess

# DataWindow components
from .datawindow.datawindow import (
    Column,
    ComputeExpression,
    DataWindow,
    DisplayObject,
    Line,
    Rectangle,
    Table,
    Text,
)

# Library and behavioral
from .library.library import (
    Behavioral,
    BehavioralAlias,
    BehavioralLibrary,
    BehavioralOption,
    Export,
    Import,
    Library,
)

# Advanced DataWindow components
from .pb_datawindow import (
    ColumnType,
    DataWindowType,
    PBColumn,
    PBColumnNameOption,
    PBColumnTypeOption,
    PBComputeExpression,
    PBCrosstabDataWindow,
    PBDataWindow,
    PBDisplayObject,
    PBGraphDataWindow,
    PBNestedDataWindow,
    PBTable,
)

# Advanced Transaction handling
from .pb_transaction import (
    PBDistributedTransaction,
    PBSavepoint,
    PBSavepointOperation,
    PBStatementType,
    PBTransaction,
    PBTransactionCoordinator,
    PBTransactionError,
    PBTransactionErrorHandler,
    PBTransactionObject,
    PBTransactionState,
    PBTransactionStatement,
)

# Source code
from .source.source import (
    FileFooter,
    FileHeader,
    SourceComment,
    SourceDirective,
    SourceFile,
    SourcePosition,
    SourceRange,
    SourceSection,
)
from .system.events import (
    PBSystemEvent,
    PBSystemEventType,
    get_all_system_events,
    get_system_event,
    get_system_events_by_type,
)

# System components
from .system.functions import (
    PBBuiltInFunction,
    PBFunctionCategory,
    PBParameter,
    PBSystemFunction,
    get_all_system_functions,
    get_system_function,
    get_system_functions_by_category,
)
from .system.globals import (
    PBGlobalScope,
    PBGlobalVariable,
    get_all_global_variables,
    get_global_variable,
    get_global_variables_by_scope,
)

# Transaction handling
from .transaction.transaction import (
    Commit,
    Connect,
    Disconnect,
    Rollback,
    Savepoint,
    Transaction,
    TransactionState,
)

# UI elements
from .ui.ui_elements import (
    Control,
    DataWindowControl,
    EditMaskControl,
    ListViewControl,
    Menu,
    MenuItem,
    RichTextControl,
    TreeViewControl,
    UIElement,
    UserObject,
    Window,
)

# Common utilities - from model/utils/common.py
from .utils.common import (
    # String operations
    camel_to_snake,
    # Collection operations
    chunk_list,
    # File operations
    ensure_directory,
    filter_dict,
    find_duplicates,
    format_timestamp,
    get_file_extension,
    merge_dicts,
    normalize_path,
    pluralize,
    read_file_safe,
    # Conversion utilities
    safe_cast,
    safe_json_loads,
    snake_to_camel,
    to_bool,
    truncate,
)

# Configuration utilities
from .utils.config import Config, load_config, validate_config

# Error handling - consolidated from model/utils/errors.py
from .utils.errors import (
    ConfigurationError,
    DecompilationError,
    DecompileError,
    Error,
    ExtractError,
    ExtractionError,
    GenerateError,
    GenerationError,
    ModelError,
    ParseError,
    ParsingError,
    PowerBuilderError,
    PowerBuilderToolError,
    SimeFinchError,
    TransformError,
    TypeValidationError,
    ValidationError,
    handle_error,
)

# Logging utilities
from .utils.logging import configure_logging, get_logger

# Type system - consolidated from model/utils/type_system.py
from .utils.type_system import (
    create_type_from_info,
    format_type_info,
    normalize_type_name,
    validate_simple_type,
    validate_type_compatibility,
    validate_value_type,
)

# Base classes
# Legacy type functions - kept for backward compatibility
from .utils.utils import PBNode, normalize_type, validate_type

# Validation utilities - consolidated from model/utils/validation.py
from .utils.validation import (
    validate_access,
    validate_enum,
    validate_event,
    validate_name,
    validate_range,
    validate_required_fields,
    validate_unique,
)

__all__ = [
    # Base class
    "PBNode",
    "NodeKind",
    # AST nodes
    "Expression",
    "Statement",
    "Event",
    "EventTrigger",
    "Literal",
    "BinaryExpression",
    "UnaryExpression",
    "Function",
    "Parameter",
    "Argument",
    "Type",
    "CustomType",
    "Variable",
    "VariableDeclaration",
    "SQLQuery",
    "SQLCursor",
    "SQLTransaction",
    "ControlFlow",
    # Attribute handling
    "Attribute",
    "AttributeAccess",
    # DataWindow components
    "DataWindow",
    "Table",
    "Column",
    "ComputeExpression",
    "DisplayObject",
    "Text",
    "Line",
    "Rectangle",
    # Advanced DataWindow components
    "DataWindowType",
    "ColumnType",
    "PBDataWindow",
    "PBTable",
    "PBColumn",
    "PBColumnNameOption",
    "PBColumnTypeOption",
    "PBComputeExpression",
    "PBDisplayObject",
    "PBNestedDataWindow",
    "PBCrosstabDataWindow",
    "PBGraphDataWindow",
    # Transaction handling
    "Transaction",
    "TransactionState",
    "Connect",
    "Disconnect",
    "Commit",
    "Rollback",
    "Savepoint",
    # Advanced Transaction handling
    "PBTransaction",
    "PBTransactionState",
    "PBTransactionObject",
    "PBTransactionStatement",
    "PBDistributedTransaction",
    "PBTransactionCoordinator",
    "PBSavepoint",
    "PBSavepointOperation",
    "PBStatementType",
    "PBTransactionError",
    "PBTransactionErrorHandler",
    # Library and behavioral
    "Library",
    "Export",
    "Import",
    "Behavioral",
    "BehavioralOption",
    "BehavioralLibrary",
    "BehavioralAlias",
    # UI elements
    "UIElement",
    "Window",
    "Control",
    "Menu",
    "MenuItem",
    "UserObject",
    "DataWindowControl",
    "TreeViewControl",
    "EditMaskControl",
    "ListViewControl",
    "RichTextControl",
    # Source code
    "SourceFile",
    "SourcePosition",
    "SourceRange",
    "SourceComment",
    "SourceDirective",
    "SourceSection",
    "FileHeader",
    "FileFooter",
    # Error classes
    "SimeFinchError",
    "Error",
    "PowerBuilderError",
    "ParseError",
    "ValidationError",
    "TransformError",
    "TypeValidationError",
    "PowerBuilderToolError",
    "ExtractionError",
    "ParsingError",
    "DecompileError",
    "DecompilationError",
    "ExtractError",
    "GenerateError",
    "GenerationError",
    "ConfigurationError",
    "ModelError",
    "handle_error",
    # Type system
    "normalize_type_name",
    "normalize_type",
    "validate_simple_type",
    "validate_type",
    "validate_type_compatibility",
    "validate_value_type",
    "create_type_from_info",
    "format_type_info",
    # Validation
    "validate_access",
    "validate_event",
    "validate_enum",
    "validate_name",
    "validate_range",
    "validate_required_fields",
    "validate_unique",
    # File operations
    "ensure_directory",
    "normalize_path",
    "get_file_extension",
    "read_file_safe",
    # String operations
    "camel_to_snake",
    "snake_to_camel",
    "pluralize",
    "truncate",
    "format_timestamp",
    # Collection operations
    "merge_dicts",
    "filter_dict",
    "chunk_list",
    "find_duplicates",
    # Conversion utilities
    "to_bool",
    "safe_json_loads",
    "safe_cast",
    # Configuration
    "Config",
    "load_config",
    "validate_config",
    # Logging
    "configure_logging",
    "get_logger",
    # Analysis tools
    "CodeMetrics",
    "DependencyAnalysis",
    "SecurityAnalysis",
    "CallGraph",
    "DependencyGraph",
    "UIFlowGraph",
    "AnalysisResult",
    "AnalysisReport",
    # System components
    "PBBuiltInFunction",
    "PBSystemFunction",
    "PBParameter",
    "PBFunctionCategory",
    "get_system_function",
    "get_system_functions_by_category",
    "get_all_system_functions",
    "PBSystemEvent",
    "PBSystemEventType",
    "get_system_event",
    "get_system_events_by_type",
    "get_all_system_events",
    "PBGlobalVariable",
    "PBGlobalScope",
    "get_global_variable",
    "get_global_variables_by_scope",
    "get_all_global_variables",
]
