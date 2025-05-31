"""Validator classes for AST nodes.

This module provides a consolidated validator for AST nodes, including scope management,
control flow validation, and type checking.
"""
from __future__ import annotations

from ..ast.control import (
    Block,
    BreakStatement,
    CaseStatement,
    ContinueStatement,
    ForLoop,
    GotoStatement,
    LabelStatement,
    RepeatUntilLoop,
    WhileLoop,
)
from ..ast.functions import (
    FunctionCall,
    FunctionDefinition,
    ProcedureCall,
    ProcedureDefinition,
)
from ..ast.types import Type, TypeRegistry
from .scope import Scope


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
        for _case in stmt.cases:
            # TODO: Implement value uniqueness and type checking
            pass
        return True

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
            "validator": self,
            "type_registry": self.type_registry,
            "expected_type": func.signature.return_type,
        }

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
        self, block: Block, expected_type: Type | None = None,
    ) -> bool:
        """Validate a block of statements."""
        context = {
            "validator": self,
            "type_registry": self.type_registry,
            "expected_type": expected_type,
        }

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
