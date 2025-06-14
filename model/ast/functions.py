"""Function and procedure AST nodes for PowerBuilder and Pseudocode.

This module contains AST nodes for representing functions and procedures in both PowerBuilder
and pseudocode, including parameter handling, type checking, and scope management.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from model.utils.base import PBNode

from .ast_nodes import Block, Expression, Statement

if TYPE_CHECKING:
    from .types import Type

logger = logging.getLogger(__name__)


@dataclass
class Parameter(PBNode):
    """Function or procedure parameter."""

    name: str = ""
    type: Type | None = None
    default_value: Expression | None = None
    is_ref: bool = False
    is_readonly: bool = False

    def validate(self, context: dict[str, Any] | None = None) -> bool:
        """Validate parameter.

        Args:
            context: Validation context, which may include:
                - 'value': The value to validate against this parameter
                - 'type_registry': TypeRegistry for type checking

        Returns:
            bool: True if valid, False otherwise
        """
        context = context or {}
        value = context.get("value")
        type_registry = context.get("type_registry")

        if not value:
            return bool(self.default_value)

        # If type registry is provided, perform type checking
        if type_registry and self.type:
            # In a real implementation, we would use the type registry to check type compatibility
            pass

        return True

    @property
    def default(self) -> Expression | None:
        """Alias for default_value to maintain compatibility with code generator.

        Returns:
            Optional[Expression]: The default value for this parameter
        """
        return self.default_value


@dataclass
class Function(PBNode):
    """Function definition used in code generation.

    This is a simplified version of FunctionDefinition used primarily for tests and code generation.
    """

    name: str = ""
    parameters: list[Parameter] = field(default_factory=list)
    return_type: Type | None = None
    body: list[Any] = field(default_factory=list)
    docstring: str | None = None


@dataclass
class Signature(PBNode):
    """Function or procedure signature."""

    name: str = ""
    parameters: list[Parameter] = field(default_factory=list)
    return_type: Type | None = None
    is_public: bool = True
    is_static: bool = False

    def validate(self, context: dict[str, Any] | None = None) -> bool:
        """Validate function signature.

        Args:
            context: Validation context, which may include:
                - 'args': List of arguments to validate
                - 'type_registry': TypeRegistry for type checking

        Returns:
            bool: True if valid, False otherwise
        """
        context = context or {}
        args = context.get("args", [])
        type_registry = context.get("type_registry")

        if len(args) > len(self.parameters):
            return False

        # Validate each provided argument against corresponding parameter
        for param, arg in zip(self.parameters, args, strict=False):
            param_context = {"value": arg, "type_registry": type_registry}
            if not param.validate(param_context):
                return False

        # Check remaining parameters have defaults
        return all(param.default_value for param in self.parameters[len(args) :])


@dataclass
class FunctionDefinition(Statement):
    """Function definition with body."""

    signature: Signature | None = None
    body: Block | None = None
    local_variables: dict[str, Type] = field(default_factory=dict)

    def validate(self, context: dict[str, Any] | None = None) -> bool:
        """Validate function definition.

        Args:
            context: Validation context, which may include:
                - 'type_registry': TypeRegistry for type checking
                - 'validator': The ASTValidator for context-aware validation

        Returns:
            bool: True if valid, False otherwise
        """
        context = context or {}
        context.get("type_registry")
        validator = context.get("validator")

        # If we have a validator, use it to perform thorough validation
        if validator:
            return validator.validate_function(self)

        # Otherwise do basic validation
        # Validate return type checking
        if hasattr(self.body, "statements"):
            return_stmts = self._find_return_statements(self.body)

            for ret_stmt in return_stmts:
                if not self._validate_return_statement(ret_stmt, context):
                    return False

        return True

    def _find_return_statements(self, block) -> list:
        """Find all return statements in a block."""
        returns = []

        if hasattr(block, "statements"):
            for stmt in block.statements:
                if hasattr(stmt, "node_kind") and stmt.node_kind == "RETURN":
                    returns.append(stmt)
                # Recursively check nested blocks
                elif hasattr(stmt, "then_block"):
                    returns.extend(self._find_return_statements(stmt.then_block))
                elif hasattr(stmt, "else_block"):
                    returns.extend(self._find_return_statements(stmt.else_block))
                elif hasattr(stmt, "body"):
                    returns.extend(self._find_return_statements(stmt.body))

        return returns

    def _validate_return_statement(self, ret_stmt, context: dict) -> bool:
        """Validate a single return statement against function signature."""
        expected_type = self.signature.return_type

        # If function returns void, return statement should have no value
        if expected_type is None or expected_type.name == "void":
            if hasattr(ret_stmt, "value") and ret_stmt.value is not None:
                # Returning a value from void function
                logger.warning(
                    f"Function {self.signature.name} returns void but has return statement with value"
                )
                return False
            return True

        # If function has return type, check if return has a value
        if not hasattr(ret_stmt, "value") or ret_stmt.value is None:
            logger.warning(
                f"Function {self.signature.name} expects return type {expected_type.name} but return has no value"
            )
            return False

        # Type checking would go here if we have type information
        # For now, just ensure there's a return value when expected
        return True


@dataclass
class ProcedureDefinition(Statement):
    """Procedure definition with body."""

    signature: Signature | None = None
    body: Block | None = None
    local_variables: dict[str, Type] = field(default_factory=dict)

    def validate(self, context: dict[str, Any] | None = None) -> bool:
        """Validate procedure definition.

        Args:
            context: Validation context, which may include:
                - 'type_registry': TypeRegistry for type checking
                - 'validator': The ASTValidator for context-aware validation

        Returns:
            bool: True if valid, False otherwise
        """
        context = context or {}
        context.get("type_registry")
        validator = context.get("validator")

        # If we have a validator, use it to perform thorough validation
        if validator:
            return validator.validate_procedure(self)

        return True


@dataclass
class FunctionCall(Expression):
    """Function call expression."""

    function_name: str = ""
    arguments: list[Expression] = field(default_factory=list)

    def validate(self, context: dict[str, Any] | None = None) -> bool:
        """Validate function call.

        Args:
            context: Validation context, which may include:
                - 'function': The function being called
                - 'type_registry': TypeRegistry for type checking
                - 'validator': The ASTValidator for context-aware validation

        Returns:
            bool: True if valid, False otherwise
        """
        context = context or {}
        function = context.get("function")
        type_registry = context.get("type_registry")
        validator = context.get("validator")

        # If we have a validator, use it
        if validator:
            return validator.validate_function_call(self)

        # Otherwise validate directly if function is provided
        if function and hasattr(function, "signature"):
            sig_context = {"args": self.arguments, "type_registry": type_registry}
            return function.signature.validate(sig_context)

        return True


@dataclass
class ProcedureCall(Statement):
    """Procedure call statement."""

    procedure_name: str = ""
    arguments: list[Expression] = field(default_factory=list)

    def validate(self, context: dict[str, Any] | None = None) -> bool:
        """Validate procedure call.

        Args:
            context: Validation context, which may include:
                - 'procedure': The procedure being called
                - 'type_registry': TypeRegistry for type checking
                - 'validator': The ASTValidator for context-aware validation

        Returns:
            bool: True if valid, False otherwise
        """
        context = context or {}
        procedure = context.get("procedure")
        type_registry = context.get("type_registry")
        validator = context.get("validator")

        # If we have a validator, use it
        if validator:
            return validator.validate_procedure_call(self)

        # Otherwise validate directly if procedure is provided
        if procedure and hasattr(procedure, "signature"):
            sig_context = {"args": self.arguments, "type_registry": type_registry}
            return procedure.signature.validate(sig_context)

        return True


# Note: ScopeValidator has been moved to model.utils.validators and renamed to ASTValidator
