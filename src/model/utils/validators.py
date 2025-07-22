"""Validator classes for AST nodes.

This module provides a consolidated validator for AST nodes, including scope management,
control flow validation, and type checking.
"""

from __future__ import annotations
import logging
from typing import Any, TYPE_CHECKING, Optional
from dataclasses import dataclass, field

from src.model.symbols.scope import Scope
from src.model.ast.nodes.declarations import Type, TypeRegistry
from src.model.ast.nodes.base import Statement, Expression
from src.model.ast.functions import FunctionDefinition, ProcedureDefinition
from src.model.types.errors import ParseErrorCollector, ValidationErrorRecord
from src.model.utils.type_checker import TypeChecker, CheckLevel
from src.model.ast.pb_types import PBTypeRegistry
from src.model.types.inference import TypeInferenceEngine

if TYPE_CHECKING:
    from src.model.ast import ASTNode

logger = logging.getLogger(__name__)


@dataclass
class ValidationContext:
    """Context for validation operations."""
    
    current_scope: Scope
    current_function: Optional[FunctionDefinition] = None
    current_loop: Optional[Statement] = None
    in_case_statement: bool = False
    type_registry: TypeRegistry = field(default_factory=TypeRegistry)
    pb_type_registry: PBTypeRegistry = field(default_factory=PBTypeRegistry)
    errors: ParseErrorCollector = field(default_factory=ParseErrorCollector)
    
    def enter_scope(self) -> Scope:
        """Enter a new scope."""
        self.current_scope = Scope(parent=self.current_scope)
        return self.current_scope
    
    def exit_scope(self) -> None:
        """Exit current scope."""
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
    
    def enter_function(self, func: FunctionDefinition) -> None:
        """Enter function context."""
        self.current_function = func
        self.enter_scope()
        
        # Add function parameters to scope
        for param in func.signature.parameters:
            self.current_scope.declare_variable(param.name, param.type)
    
    def exit_function(self) -> None:
        """Exit function context."""
        self.current_function = None
        self.exit_scope()
    
    def enter_loop(self, loop: Statement) -> None:
        """Enter loop context."""
        self.current_loop = loop
    
    def exit_loop(self) -> None:
        """Exit loop context."""
        self.current_loop = None


class ASTValidator:
    """Comprehensive validator for PowerBuilder AST nodes.
    
    Performs:
    - Scope validation
    - Type checking
    - Control flow validation
    - Semantic checks
    """
    
    def __init__(self,
                 type_registry: Optional[TypeRegistry] = None,
                 pb_type_registry: Optional[PBTypeRegistry] = None,
                 check_level: CheckLevel = CheckLevel.MODERATE) -> None:
        """Initialize validator.
        
        Args:
            type_registry: Registry for custom types
            pb_type_registry: Registry for PowerBuilder types
            check_level: Type checking strictness
        """
        self.type_registry = type_registry or TypeRegistry()
        self.pb_type_registry = pb_type_registry or PBTypeRegistry()
        self.type_inference = TypeInferenceEngine()
        self.type_checker = TypeChecker(
            type_registry=self.pb_type_registry,
            type_inference=self.type_inference,
            check_level=check_level
        )
    
    def validate(self, node: 'ASTNode', context: Optional[ValidationContext] = None) -> ValidationContext:
        """Validate an AST node and its children.
        
        Args:
            node: AST node to validate
            context: Validation context (created if not provided)
            
        Returns:
            ValidationContext with any errors found
        """
        if context is None:
            context = ValidationContext(
                current_scope=Scope(),
                type_registry=self.type_registry,
                pb_type_registry=self.pb_type_registry
            )
        
        # Dispatch based on node type
        method_name = f"_validate_{node.__class__.__name__.lower()}"
        method = getattr(self, method_name, self._validate_generic)
        method(node, context)
        
        return context
    
    def _validate_generic(self, node: 'ASTNode', context: ValidationContext) -> None:
        """Generic validation for nodes without specific handlers."""
        # Validate children if node has them
        if hasattr(node, 'children'):
            for child in node.children:
                self.validate(child, context)
        
        # Check common attributes
        if hasattr(node, 'body') and isinstance(node.body, list):
            for stmt in node.body:
                self.validate(stmt, context)
    
    def _validate_block(self, block: Any, context: ValidationContext) -> None:
        """Validate a block statement."""
        context.enter_scope()
        
        for statement in block.statements:
            self.validate(statement, context)
        
        context.exit_scope()
    
    def _validate_assignment(self, assignment: Any, context: ValidationContext) -> None:
        """Validate assignment statement."""
        # Check if variable is declared
        var_type = context.current_scope.get_variable(assignment.variable)
        
        if not var_type:
            # Variable not declared - infer type from value
            result = self.type_checker.check_expression(
                assignment.value,
                scope=context.current_scope
            )
            
            if result.inferred_type:
                # Declare variable with inferred type
                context.current_scope.declare_variable(
                    assignment.variable,
                    Type(name=result.inferred_type.name)
                )
            else:
                context.errors.add_error(
                    f"Cannot infer type for undeclared variable '{assignment.variable}'",
                    error_code="VAR_001"
                )
        else:
            # Variable declared - check type compatibility
            result = self.type_checker.check_assignment(
                assignment,
                scope=context.current_scope
            )
            
            for error in result.errors:
                context.errors.add_validation_error(
                    error.message,
                    node_type="Assignment",
                    validation_rule="type_compatibility",
                    error_code=error.error_code
                )
            
            for warning in result.warnings:
                context.errors.add_warning(
                    warning.message,
                    error_code=warning.error_code
                )
    
    def _validate_functioncall(self, call: Any, context: ValidationContext) -> None:
        """Validate function call."""
        # Look up function definition
        func_def = context.current_scope.get_function(call.function_name)
        
        if not func_def:
            context.errors.add_error(
                f"Undefined function '{call.function_name}'",
                error_code="FUNC_003"
            )
            return
        
        # Type check arguments
        result = self.type_checker.check_function_call(
            call,
            func_def,
            scope=context.current_scope
        )
        
        for error in result.errors:
            context.errors.add_validation_error(
                error.message,
                node_type="FunctionCall",
                validation_rule="argument_types",
                error_code=error.error_code
            )
        
        for warning in result.warnings:
            context.errors.add_warning(
                warning.message,
                error_code=warning.error_code
            )
    
    def _validate_ifstatement(self, stmt: Any, context: ValidationContext) -> None:
        """Validate if statement."""
        # Check condition is boolean
        result = self.type_checker.check_expression(
            stmt.condition,
            expected_type=self.pb_type_registry.get("boolean"),
            scope=context.current_scope
        )
        
        if not result.valid:
            context.errors.add_validation_error(
                "If condition must be boolean type",
                node_type="IfStatement",
                validation_rule="condition_type",
                error_code="CTRL_001"
            )
        
        # Validate then branch
        self.validate(stmt.then_part, context)
        
        # Validate else branch if present
        if stmt.else_part:
            self.validate(stmt.else_part, context)
    
    def _validate_whilestatement(self, stmt: Any, context: ValidationContext) -> None:
        """Validate while statement."""
        # Check condition is boolean
        result = self.type_checker.check_expression(
            stmt.condition,
            expected_type=self.pb_type_registry.get("boolean"),
            scope=context.current_scope
        )
        
        if not result.valid:
            context.errors.add_validation_error(
                "While condition must be boolean type",
                node_type="WhileStatement",
                validation_rule="condition_type",
                error_code="CTRL_002"
            )
        
        # Enter loop context
        context.enter_loop(stmt)
        self.validate(stmt.body, context)
        context.exit_loop()
    
    def _validate_forstatement(self, stmt: Any, context: ValidationContext) -> None:
        """Validate for statement."""
        # Validate initialization
        if stmt.init:
            self.validate(stmt.init, context)
        
        # Check condition is boolean (if present)
        if stmt.condition:
            result = self.type_checker.check_expression(
                stmt.condition,
                expected_type=self.pb_type_registry.get("boolean"),
                scope=context.current_scope
            )
            
            if not result.valid:
                context.errors.add_validation_error(
                    "For condition must be boolean type",
                    node_type="ForStatement",
                    validation_rule="condition_type",
                    error_code="CTRL_003"
                )
        
        # Enter loop context
        context.enter_loop(stmt)
        
        # Validate update
        if stmt.update:
            self.validate(stmt.update, context)
        
        # Validate body
        self.validate(stmt.body, context)
        
        context.exit_loop()
    
    def _validate_returnstatement(self, stmt: Any, context: ValidationContext) -> None:
        """Validate return statement."""
        if not context.current_function:
            context.errors.add_error(
                "Return statement outside of function",
                error_code="CTRL_004"
            )
            return
        
        # Check return type matches function signature
        if stmt.value and context.current_function.signature.return_type:
            result = self.type_checker.check_expression(
                stmt.value,
                expected_type=context.current_function.signature.return_type,
                scope=context.current_scope
            )
            
            if not result.valid:
                context.errors.add_validation_error(
                    f"Return type mismatch in function '{context.current_function.signature.name}'",
                    node_type="ReturnStatement",
                    validation_rule="return_type",
                    error_code="FUNC_004"
                )
        elif stmt.value and not context.current_function.signature.return_type:
            context.errors.add_warning(
                "Function returns value but no return type declared",
                error_code="FUNC_005"
            )
        elif not stmt.value and context.current_function.signature.return_type:
            context.errors.add_error(
                "Function must return a value",
                error_code="FUNC_006"
            )
    
    def _validate_breakstatement(self, stmt: Any, context: ValidationContext) -> None:
        """Validate break statement."""
        if not context.current_loop and not context.in_case_statement:
            context.errors.add_error(
                "Break statement outside of loop or case",
                error_code="CTRL_005"
            )
    
    def _validate_continuestatement(self, stmt: Any, context: ValidationContext) -> None:
        """Validate continue statement."""
        if not context.current_loop:
            context.errors.add_error(
                "Continue statement outside of loop",
                error_code="CTRL_006"
            )
    
    def _validate_functiondefinition(self, func: FunctionDefinition, context: ValidationContext) -> None:
        """Validate function definition."""
        # Check if function already defined
        existing = context.current_scope.get_function(func.signature.name)
        if existing:
            context.errors.add_error(
                f"Function '{func.signature.name}' already defined",
                error_code="FUNC_007"
            )
        else:
            # Register function
            context.current_scope.declare_function(func)
        
        # Validate function body
        context.enter_function(func)
        
        if func.body:
            self.validate(func.body, context)
        
        # Check if function has return statements when needed
        if func.signature.return_type and not self._has_return_statement(func.body):
            context.errors.add_warning(
                f"Function '{func.signature.name}' may not return a value on all paths",
                error_code="FUNC_008"
            )
        
        context.exit_function()
    
    def _has_return_statement(self, node: Any) -> bool:
        """Check if node contains a return statement."""
        if isinstance(node, ReturnStatement):
            return True
        
        if hasattr(node, 'body'):
            if isinstance(node.body, list):
                return any(self._has_return_statement(stmt) for stmt in node.body)
            else:
                return self._has_return_statement(node.body)
        
        if hasattr(node, 'statements'):
            return any(self._has_return_statement(stmt) for stmt in node.statements)
        
        return False


# Convenience functions
def validate_ast(node: 'ASTNode',
                type_registry: Optional[TypeRegistry] = None,
                check_level: CheckLevel = CheckLevel.MODERATE) -> ParseErrorCollector:
    """Validate an AST and return errors.
    
    Args:
        node: AST node to validate
        type_registry: Type registry to use
        check_level: Type checking strictness
        
    Returns:
        ParseErrorCollector with any errors found
    """
    validator = ASTValidator(
        type_registry=type_registry,
        check_level=check_level
    )
    
    context = validator.validate(node)
    return context.errors


def validate_with_context(node: 'ASTNode',
                         context: ValidationContext,
                         check_level: CheckLevel = CheckLevel.MODERATE) -> None:
    """Validate an AST using existing context.
    
    Args:
        node: AST node to validate
        context: Existing validation context
        check_level: Type checking strictness
    """
    validator = ASTValidator(
        type_registry=context.type_registry,
        pb_type_registry=context.pb_type_registry,
        check_level=check_level
    )
    
    validator.validate(node, context)
