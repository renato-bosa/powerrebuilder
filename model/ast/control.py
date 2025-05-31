"""Control structure AST nodes for PowerBuilder and Pseudocode.

This module contains AST nodes for representing control structures in both PowerBuilder
and pseudocode, including conditionals, loops, and case statements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..utils.base import PBNode


@dataclass
class Expression(PBNode):
    """Base class for expressions."""

    pass


@dataclass
class Statement(PBNode):
    """Base class for statements."""

    pass


@dataclass
class Block(Statement):
    """Block of statements."""

    statements: list[Statement] = field(default_factory=list)

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate all statements in this block.

        Args:
            context: Validation context

        Returns:
            bool: True if all statements are valid, False otherwise
        """
        context = context or {}
        validator = context.get("validator")

        if validator:
            return validator.validate_block(self, context.get("expected_type"))

        # If no validator provided, validate each statement individually
        return all(stmt.validate(context) for stmt in self.statements)


@dataclass
class Condition(Expression):
    """Condition expression."""

    left: Expression
    operator: str
    right: Expression

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate condition expression.

        Args:
            context: Validation context

        Returns:
            bool: True if condition is valid, False otherwise
        """
        context = context or {}

        # Validate both sides of the condition
        if not self.left.validate(context) or not self.right.validate(context):
            return False

        # TODO: Check that operator is valid for the types of left and right

        return True


@dataclass
class BooleanOperation(Expression):
    """Boolean operation (AND, OR, NOT)."""

    operator: str
    operands: list[Expression]

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate boolean operation.

        Args:
            context: Validation context

        Returns:
            bool: True if operation is valid, False otherwise
        """
        context = context or {}

        # Check that each operand is valid
        return all(operand.validate(context) for operand in self.operands)


@dataclass
class IfStatement(Statement):
    """IF statement with optional ELSE."""

    condition: Expression
    then_block: Block
    else_block: Block | None = None

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate IF statement.

        Args:
            context: Validation context

        Returns:
            bool: True if statement is valid, False otherwise
        """
        context = context or {}

        # Validate condition
        if not self.condition.validate(context):
            return False

        # Validate then block
        if not self.then_block.validate(context):
            return False

        # Validate else block if it exists
        return not (self.else_block and not self.else_block.validate(context))


@dataclass
class WhileLoop(Statement):
    """WHILE loop."""

    condition: Expression
    body: Block

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate WHILE loop.

        Args:
            context: Validation context

        Returns:
            bool: True if loop is valid, False otherwise
        """
        context = context or {}

        # Validate condition
        if not self.condition.validate(context):
            return False

        # Validate body
        return self.body.validate(context)


@dataclass
class RepeatUntilLoop(Statement):
    """REPEAT-UNTIL loop."""

    body: Block
    condition: Expression

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate REPEAT-UNTIL loop.

        Args:
            context: Validation context

        Returns:
            bool: True if loop is valid, False otherwise
        """
        context = context or {}

        # Validate body
        if not self.body.validate(context):
            return False

        # Validate condition
        return self.condition.validate(context)


@dataclass
class ForLoop(Statement):
    """FOR loop with optional STEP."""

    variable: str
    start: Expression
    end: Expression
    step: Expression | None = None
    body: Block = field(default_factory=Block)

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate FOR loop.

        Args:
            context: Validation context

        Returns:
            bool: True if loop is valid, False otherwise
        """
        context = context or {}

        # Validate start, end, and step expressions
        if not self.start.validate(context) or not self.end.validate(context):
            return False

        if self.step and not self.step.validate(context):
            return False

        # Validate body
        return self.body.validate(context)


@dataclass
class CaseItem(PBNode):
    """Single case in a CASE statement."""

    value: Expression
    statement: Statement

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate case item.

        Args:
            context: Validation context

        Returns:
            bool: True if case item is valid, False otherwise
        """
        context = context or {}

        # Validate value
        if not self.value.validate(context):
            return False

        # Validate statement
        return self.statement.validate(context)


@dataclass
class CaseStatement(Statement):
    """CASE statement with optional OTHERWISE."""

    expression: Expression
    cases: list[CaseItem]
    otherwise: Statement | None = None

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate CASE statement.

        Args:
            context: Validation context

        Returns:
            bool: True if statement is valid, False otherwise
        """
        context = context or {}

        # Validate expression
        if not self.expression.validate(context):
            return False

        # Validate case items
        for case in self.cases:
            if not case.validate(context):
                return False

        # Validate otherwise clause if it exists
        return not (self.otherwise and not self.otherwise.validate(context))


@dataclass
class BreakStatement(Statement):
    """BREAK statement for loops."""

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate BREAK statement.

        Args:
            context: Validation context

        Returns:
            bool: True if statement is valid (inside a loop), False otherwise
        """
        context = context or {}
        validator = context.get("validator")

        if validator:
            return validator.validate_break(self)

        # Without validator context, we can't check if inside a loop
        return True


@dataclass
class ContinueStatement(Statement):
    """CONTINUE statement for loops."""

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate CONTINUE statement.

        Args:
            context: Validation context

        Returns:
            bool: True if statement is valid (inside a loop), False otherwise
        """
        context = context or {}
        validator = context.get("validator")

        if validator:
            return validator.validate_continue(self)

        # Without validator context, we can't check if inside a loop
        return True


@dataclass
class ReturnStatement(Statement):
    """RETURN statement with optional value."""

    value: Expression | None = None

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate RETURN statement.

        Args:
            context: Validation context, which may include:
                - 'expected_type': The expected return type
                - 'type_registry': TypeRegistry for type checking

        Returns:
            bool: True if statement is valid, False otherwise
        """
        context = context or {}
        expected_type = context.get("expected_type")
        context.get("type_registry")

        # Check if value matches expected type
        if not self.value and expected_type:
            return False
        if self.value and not expected_type:
            return False

        # Validate the value if it exists
        if self.value and not self.value.validate(context):
            return False

        # TODO: Implement type checking for return value

        return True


@dataclass
class LabelStatement(Statement):
    """Label for GOTO statements."""

    name: str

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate label statement.

        Args:
            context: Validation context

        Returns:
            bool: True if label is valid, False otherwise
        """
        context = context or {}
        validator = context.get("validator")

        if validator:
            validator.register_label(self)

        return True


@dataclass
class GotoStatement(Statement):
    """GOTO statement."""

    label: str

    def validate(self, context: dict[str, Any] = None) -> bool:
        """Validate GOTO statement.

        Args:
            context: Validation context

        Returns:
            bool: True if statement is valid (target label exists), False otherwise
        """
        context = context or {}
        validator = context.get("validator")

        if validator:
            return validator.validate_goto(self)

        # Without validator context, we can't check if label exists
        return True
