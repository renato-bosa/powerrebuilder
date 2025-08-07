"""AST module for PowerBuilder model with lazy loading to reduce import overhead."""

from __future__ import annotations
from typing import Any, TYPE_CHECKING
import sys
import importlib
from types import ModuleType

# Cache for lazy-loaded imports
_ast_cache: dict[str, Any] = {}

# Import types for type checking but not at runtime to avoid circular imports
if TYPE_CHECKING:
    from .nodes.base import Expression, Statement, Identifier
    from .nodes.declarations import Type, TypeCategory, Field
    from .nodes.literals import *
    from .nodes.expressions import *
    from .nodes.variables import *
    from .nodes.sql import *
    from src.model.types.base import PBNode
    from .node_kind import NodeKind

def __getattr__(name: str) -> Any:
    """Lazy import AST components on first access.
    
    Args:
        name: The attribute name to import
        
    Returns:
        The imported type, module, or object
        
    Raises:
        AttributeError: If the attribute cannot be found
    """
    if name in _ast_cache:
        return _ast_cache[name]
    
    # Define lazy loading mappings
    lazy_imports: dict[str, tuple[str, str]] = {
        # Base nodes
        "Expression": (".nodes.base", "Expression"),
        "Statement": (".nodes.base", "Statement"),
        "PBNode": ("src.model.types.base", "PBNode"),
        "NodeKind": (".node_kind", "NodeKind"),
        
        # Type imports
        "Type": (".nodes.declarations", "Type"),
        "TypeCategory": (".nodes.declarations", "TypeCategory"),
        "Field": (".nodes.declarations", "Field"),
        "ArrayType": (".nodes.declarations", "ArrayType"),
        
        # SQL Node imports
        "SelectStatement": (".nodes.sql", "SelectStatement"),
        "InsertStatement": (".nodes.sql", "InsertStatement"),
        "UpdateStatement": (".nodes.sql", "UpdateStatement"),
        "DeleteStatement": (".nodes.sql", "DeleteStatement"),
        "ResultColumn": (".nodes.sql", "ResultColumn"),
        "FromClause": (".nodes.sql", "FromClause"),
        "TableReference": (".nodes.sql", "TableReference"),
        "JoinClause": (".nodes.sql", "JoinClause"),
        "WhereClause": (".nodes.sql", "WhereClause"),
        "OrderByClause": (".nodes.sql", "OrderByClause"),
        "OrderingTerm": (".nodes.sql", "OrderingTerm"),
        "LimitClause": (".nodes.sql", "LimitClause"),
        "SubqueryExpression": (".nodes.sql", "SubqueryExpression"),
        "Assignment": (".nodes.sql", "Assignment"),
        "ColumnReference": (".nodes.sql", "ColumnReference"),
        "GroupByClause": (".nodes.sql", "GroupByClause"),
        "HavingClause": (".nodes.sql", "HavingClause"),
        "WithClause": (".nodes.sql", "WithClause"),
        "WithExpression": (".nodes.sql", "WithExpression"),
        "SetOperationStatement": (".nodes.sql", "SetOperationStatement"),
        "SqlStatement": (".nodes.sql", "SqlStatement"),
        "SqlParameter": (".nodes.sql", "SqlParameter"),
        "ColonParameter": (".nodes.sql", "ColonParameter"),
        "QuestionMarkParameter": (".nodes.sql", "QuestionMarkParameter"),
        "SQLQuery": (".nodes.sql", "SQLQuery"),
        "SQLCursor": (".nodes.sql", "SQLCursor"),
        "SQLTransaction": (".nodes.sql", "SQLTransaction"),
        "SQLCommit": (".nodes.sql", "SQLCommit"),
        "SQLRollback": (".nodes.sql", "SQLRollback"),
        "SQLPrepare": (".nodes.sql", "SQLPrepare"),
        "SQLVariable": (".nodes.sql", "SQLVariable"),
        "SQLFromClause": (".nodes.sql", "SQLFromClause"),
        
        # Literals
        "Literal": (".literals", "Literal"),
        "StringLiteral": (".literals", "StringLiteral"),
        "NumberLiteral": (".literals", "NumberLiteral"),
        "IntegerLiteral": (".literals", "IntegerLiteral"),
        "RealLiteral": (".literals", "RealLiteral"),
        "NullLiteral": (".literals", "NullLiteral"),
        "BooleanLiteral": (".literals", "BooleanLiteral"),
        "DateLiteral": (".literals", "DateLiteral"),
        "TimeLiteral": (".literals", "TimeLiteral"),
        "DateTimeLiteral": (".literals", "DateTimeLiteral"),
        "DecimalLiteral": (".literals", "DecimalLiteral"),
        "Identifier": (".nodes.base", "Identifier"),
        "BinaryExpression": (".literals", "BinaryExpression"),
        "UnaryExpression": (".literals", "UnaryExpression"),
        "Function": (".literals", "Function"),
        
        # Expressions
        "BinaryOperator": (".nodes.expressions", "BinaryOperator"),
        "UnaryOperator": (".nodes.expressions", "UnaryOperator"),
        "TernaryExpression": (".nodes.expressions", "TernaryExpression"),
        "ConcatenationOperator": (".nodes.expressions", "ConcatenationOperator"),
        "PowerOperator": (".nodes.expressions", "PowerOperator"),
        "FunctionCall": (".nodes.expressions", "FunctionCall"),
        "MemberAccess": (".nodes.expressions", "MemberAccess"),
        
        # Variables
        "Variable": (".nodes.variables", "Variable"),
        "Parameter": (".nodes.variables", "Parameter"),
        "LocalVariable": (".nodes.variables", "LocalVariable"),
        "InstanceVariable": (".nodes.variables", "InstanceVariable"),
        "GlobalVariable": (".nodes.variables", "GlobalVariable"),
        "SharedVariable": (".nodes.variables", "SharedVariable"),
    }
    
    # Handle star imports from functions, io, pb_types modules
    star_imports: dict[str, list[str]] = {
        ".functions": [".functions"],
        ".io": [".io"],
        ".pb_types": [".pb_types"],
    }
    
    if name in lazy_imports:
        module_name, attr_name = lazy_imports[name]
        try:
            if module_name.startswith('.'):
                # Relative import
                full_module = f"src.model.ast{module_name}"
                if module_name.startswith("src."):
                    full_module = module_name
                module = importlib.import_module(full_module)
                _ast_cache[name] = getattr(module, attr_name)
            else:
                # Absolute import
                module = importlib.import_module(module_name)
                _ast_cache[name] = getattr(module, attr_name)
            return _ast_cache[name]
        except (ImportError, AttributeError):
            pass  # Continue to check star imports
    
    # Check star imports
    for star_module in star_imports:
        try:
            full_module = f"src.model.ast{star_module}"
            module = importlib.import_module(full_module)
            if hasattr(module, name):
                _ast_cache[name] = getattr(module, name)
                return _ast_cache[name]
        except (ImportError, AttributeError):
            continue
    
    # Check inline classes
    if name in _get_inline_classes():
        _ast_cache[name] = _get_inline_classes()[name]
        return _ast_cache[name]
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def _get_inline_classes() -> dict[str, type]:
    """Get inline class definitions.
    
    Returns:
        Dictionary mapping class names to class types
    """
    if 'inline_classes' in _ast_cache:
        return _ast_cache['inline_classes']
    
    # Lazy load Expression for inheritance
    try:
        from .nodes.base import Expression, Statement
    except ImportError:
        # Fallback classes
        class Expression:
            pass
        class Statement:
            pass
    
    # Define inline classes
    class ArrayAccess(Expression):
        def __init__(self, array: Any = None, index: Any = None) -> None:
            self.array = array
            self.index = index

    class ASTAssignment(Statement):
        def __init__(self, target: Any = None, value: Any = None) -> None:
            self.target = target
            self.value = value

    class BasicType:
        def __init__(self, name: str = "string") -> None:
            self.name = name

    class Block(Statement):
        def __init__(self, statements: list[Any] | None = None) -> None:
            self.statements = statements or []

    class CaseStatement(Statement):
        def __init__(self, expression: Any = None, cases: list[Any] | None = None) -> None:
            self.expression = expression
            self.cases = cases or []

    class CustomType:
        def __init__(self, name: str = "object") -> None:
            self.name = name

    class Event(Statement):
        def __init__(self, name: str = "", parameters: list[Any] | None = None) -> None:
            self.name = name
            self.parameters = parameters or []

    class ForLoop(Statement):
        def __init__(self, init: Any = None, condition: Any = None, update: Any = None, body: Any = None) -> None:
            self.init = init
            self.condition = condition
            self.update = update
            self.body = body

    class FunctionDefinition(Statement):
        def __init__(self, name: str = "", parameters: list[Any] | None = None, body: Any = None) -> None:
            self.name = name
            self.parameters = parameters or []
            self.body = body

    class IfStatement(Statement):
        def __init__(self, condition: Any = None, then_stmt: Any = None, else_stmt: Any = None) -> None:
            self.condition = condition
            self.then_stmt = then_stmt
            self.else_stmt = else_stmt

    class Parameter:
        def __init__(self, name: str = "", type_name: str = "string") -> None:
            self.name = name
            self.type_name = type_name

    class ReturnStatement(Statement):
        def __init__(self, value: Any = None) -> None:
            self.value = value

    class Signature:
        def __init__(self, name: str = "", parameters: list[Any] | None = None, return_type: Any = None) -> None:
            self.name = name
            self.parameters = parameters or []
            self.return_type = return_type

    class Variable(Expression):
        def __init__(self, name: str = "", type_name: str = "string") -> None:
            self.name = name
            self.type_name = type_name

    class WhileLoop(Statement):
        def __init__(self, condition: Any = None, body: Any = None) -> None:
            self.condition = condition
            self.body = body
    
    inline_classes: dict[str, type] = {
        "ArrayAccess": ArrayAccess,
        "ASTAssignment": ASTAssignment,
        "BasicType": BasicType,
        "Block": Block,
        "CaseStatement": CaseStatement,
        "CustomType": CustomType,
        "Event": Event,
        "ForLoop": ForLoop,
        "FunctionDefinition": FunctionDefinition,
        "IfStatement": IfStatement,
        "Parameter": Parameter,
        "ReturnStatement": ReturnStatement,
        "Signature": Signature,
        "Variable": Variable,
        "WhileLoop": WhileLoop,
    }
    
    _ast_cache['inline_classes'] = inline_classes
    return inline_classes

# Make inline classes available at module level for __all__ compatibility
def _populate_module_namespace() -> None:
    """Populate module namespace with inline classes."""
    current_module = sys.modules[__name__]
    inline_classes = _get_inline_classes()
    for name, cls in inline_classes.items():
        setattr(current_module, name, cls)

# Populate on import
_populate_module_namespace()

# Remove __all__ to eliminate pyright errors with lazy loading
# All exports are handled through __getattr__ mechanism
