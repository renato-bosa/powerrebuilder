"""Validator classes for AST nodes.

This module provides a consolidated validator for AST nodes, including scope management,
control flow validation, and type checking.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from model.ast.ast_nodes import (Block, BreakStatement, CaseStatement, ContinueStatement, ForLoop, GotoStatement, RepeatUntilLoop, WhileLoop)
from model.ast.ast_nodes import (Label as LabelStatement)

from .scope import Scope

if TYPE_CHECKING:
    from model.ast.functions import (
        FunctionCall,
        FunctionDefinition,
        ProcedureCall,
        ProcedureDefinition,
    )
    from model.ast.types import Type, TypeRegistry

logger = logging.getLogger(__name__)


class ASTValidator:
    """Consolidated validator for AST nodes, including scope and control flow."""

    def __init__(self, type_registry: TypeRegistry) -> None:


        self.type_registry = type_registry
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self.current_loop_depth = 0
        self.labels: dict[str, LabelStatement] = {}

    # Scope management methods
    def enter_scope(self) -> None:


        """Enter a new scope."""
        self.current_scope = Scope(self.current_scope)

    def exit_scope(self) -> None:




        """Exit current scope."""
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    # Control flow methods
    def enter_loop(self) -> None:


        """Enter a loop context."""
        self.current_loop_depth += 1

    def exit_loop(self) -> None:




        """Exit a loop context."""
        self.current_loop_depth -= 1

    def validate_break(self, stmt: BreakStatement) -> bool:




        """Validate BREAK statement is inside a loop."""
        return self.current_loop_depth > 0

    def validate_continue(self, stmt: ContinueStatement) -> bool:




        """Validate CONTINUE statement is inside a loop."""
        return self.current_loop_depth > 0

    def register_label(self, stmt: LabelStatement) -> None:




        """Register a label for GOTO validation."""
        self.labels[stmt.name] = stmt

    def validate_goto(self, stmt: GotoStatement) -> bool:




        """Validate GOTO target exists."""
        return stmt.label in self.labels

    def validate_case_values(self, stmt: CaseStatement) -> bool:




        """Validate case values are unique and of correct type."""
        # Collect all case values for uniqueness check
        seen_values = set()
        case_type = None

        # First, determine the type from the switch expression if possible
        if hasattr(stmt.expression, "type"):
            case_type = stmt.expression.type

        for case in stmt.cases:
            for value in case.values:
                # Extract literal value if it's a literal expression
                literal_val = None
                if hasattr(value, "value"):
                    literal_val = value.value
                elif hasattr(value, "expression"):
                    literal_val = value.expression
                else:
                    # For non-literal expressions, we can't check uniqueness
                    continue

                # Check for duplicate case values
                if literal_val in seen_values:
                    logger.warning("Duplicate case value: %s", literal_val)
                    return False
                seen_values.add(literal_val)

                # Type checking if we have type information
                if case_type and hasattr(value, "type"):
                    if not self._are_types_compatible(value.type, case_type):
                        logger.warning(
                            f"Case value type {value.type} incompatible with switch expression type {case_type}",
                        )
                        return False

        return True

    def _are_types_compatible(self, type1, type2) -> bool:




        """Check if two types are compatible for case statement."""
        if type1 == type2:
            return True

        # Handle string representations
        if isinstance(type1, str) and isinstance(type2, str):
            return type1.lower() == type2.lower()

        # Handle numeric compatibility
        numeric_types = {
            "integer", "long", "decimal", "double", "real", "int", "float", "number", }
        if (
            isinstance(type1, str)
            and type1.lower() in numeric_types
            and isinstance(type2, str)
            and type2.lower() in numeric_types
        ):
            return True

        # If we have Type objects with compatibility checking
        if hasattr(type1, "can_assign_from"):
            return type1.can_assign_from(type2)
        if hasattr(type2, "can_assign_from"):
            return type2.can_assign_from(type1)

        return False

    # Function and procedure validation
    def validate_function(self, func: FunctionDefinition) -> bool:


        """Validate function definition."""
        # Create new scope for function body
        self.enter_scope()

        # Register parameters in function scope
        for param in func.signature.parameters:
            self.current_scope.declare_variable(param.name, param.type)

        # Register local variables
        for name, type_ in func.local_variables.items():
            self.current_scope.declare_variable(name, type_)

        # Create context for validating the body
        context = {
            "validator": self, "type_registry": self.type_registry, "expected_type": func.signature.return_type, }

        # Validate function body
        valid = func.body.validate(context)

        # Exit function scope
        self.exit_scope()

        return valid

    def validate_procedure(self, proc: ProcedureDefinition) -> bool:




        """Validate procedure definition."""
        # Create new scope for procedure body
        self.enter_scope()

        # Register parameters in procedure scope
        for param in proc.signature.parameters:
            self.current_scope.declare_variable(param.name, param.type)

        # Register local variables
        for name, type_ in proc.local_variables.items():
            self.current_scope.declare_variable(name, type_)

        # Create context for validating the body
        context = {"validator": self, "type_registry": self.type_registry}

        # Validate procedure body
        valid = proc.body.validate(context)

        # Exit procedure scope
        self.exit_scope()

        return valid

    def validate_function_call(self, call: FunctionCall) -> bool:




        """Validate function call."""
        func = self.current_scope.get_function(call.function_name)
        if not func:
            return False

        # Create context for signature validation
        context = {"args": call.arguments, "type_registry": self.type_registry}

        return func.signature.validate(context)

    def validate_procedure_call(self, call: ProcedureCall) -> bool:




        """Validate procedure call."""
        proc = self.current_scope.get_procedure(call.procedure_name)
        if not proc:
            return False

        # Create context for signature validation
        context = {"args": call.arguments, "type_registry": self.type_registry}

        return proc.signature.validate(context)

    # General block validation
    def validate_block(
        self, block: Block, expected_type: Type | None = None, ) -> bool:


        """Validate a block of statements."""
        context = {
            "validator": self, "type_registry": self.type_registry, "expected_type": expected_type, }

        for stmt in block.statements:
            if isinstance(stmt, WhileLoop | ForLoop | RepeatUntilLoop):
                self.enter_loop()
                valid = stmt.validate(context)
                self.exit_loop()
                if not valid:
                    return False
            elif not stmt.validate(context):
                return False
        return True
