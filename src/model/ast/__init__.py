"""AST module for PowerBuilder model with lazy loading to reduce import overhead."""

from __future__ import annotations
from typing import Any

# Cache for lazy-loaded imports
_ast_cache: dict[str, Any] = {}

def __getattr__(name: str) -> Any:
    """Lazy import AST components on first access."""
    if name in _ast_cache:
        return _ast_cache[name]
    
    # Define lazy loading mappings
    lazy_imports = {
        # Base nodes
        "Expression": (".nodes.base", "Expression"),
        "Statement": (".nodes.base", "Statement"),
        "PBNode": ("src.model.types.base", "PBNode"),
        "NodeKind": (".node_kind", "NodeKind"),
        
        # Type imports
        "Type": (".nodes.declarations", "Type"),
        "TypeCategory": (".nodes.declarations", "TypeCategory"),
        "Field": (".nodes.declarations", "Field"),
        
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
        "IntegerLiteral": (".literals", "IntegerLiteral"),
        "RealLiteral": (".literals", "RealLiteral"),
        "NullLiteral": (".literals", "NullLiteral"),
        "BooleanLiteral": (".literals", "BooleanLiteral"),
        "Identifier": (".literals", "Identifier"),
        "BinaryExpression": (".literals", "BinaryExpression"),
        "UnaryExpression": (".literals", "UnaryExpression"),
        "Function": (".literals", "Function"),
    }
    
    # Handle star imports from functions, io, pb_types modules
    star_imports = {
        ".functions": [".functions"],
        ".io": [".io"],
        ".pb_types": [".pb_types"],
    }
    
    if name in lazy_imports:
        module_name, attr_name = lazy_imports[name]
        try:
            if module_name.startswith('.'):
                # Relative import
                import importlib
                full_module = f"src.model.ast{module_name}"
                if module_name.startswith("src."):
                    full_module = module_name
                module = importlib.import_module(full_module)
                _ast_cache[name] = getattr(module, attr_name)
            else:
                # Absolute import
                import importlib
                module = importlib.import_module(module_name)
                _ast_cache[name] = getattr(module, attr_name)
            return _ast_cache[name]
        except (ImportError, AttributeError) as e:
            pass  # Continue to check star imports
    
    # Check star imports
    for star_module in star_imports:
        try:
            import importlib
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

def _get_inline_classes():
    """Get inline class definitions."""
    if 'inline_classes' in _ast_cache:
        return _ast_cache['inline_classes']
    
    # Lazy load Expression for inheritance
    try:
        import importlib
        base_module = importlib.import_module("src.model.ast.nodes.base")
        Expression = base_module.Expression
        Statement = base_module.Statement
    except ImportError:
        # Fallback classes
        class Expression:
            pass
        class Statement:
            pass
    
    # Define inline classes
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
    
    inline_classes = {
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
