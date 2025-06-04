# extract/pbd_core/pcode_ir.py
"""Defines basic structures for a P-code Intermediate Representation (IR).
This IR will be the target for lifting raw p-code into structured code.
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import Union


# --- Base IR Node --- #
@dataclass
class IrNode(ABC):
    """Abstract base class for all IR nodes."""
    # Could add common attributes like line numbers, source mapping, etc. later
    pass

# --- Expressions --- #
# Expressions produce a value.


@dataclass
class Expression(IrNode):
    """Base class for all expressions."""
    pass


@dataclass
class Constant(Expression):
    """Represents a constant value (integer, string, boolean, null)."""
    value: int | str | bool | None
    # type_hint: Optional[str] = None # e.g., "integer", "string"


@dataclass
class VariableRef(Expression):
    """Represents a reference to a variable."""
    name: str
    # scope: Optional[str] = None # e.g., "local", "instance", "global"


@dataclass
class BinaryOperation(Expression):
    """Represents a binary operation (e.g., +, -, *, /, AND, OR, ==, <)."""
    left: Expression
    operator: str  # e.g., "+", "==", "AND"
    right: Expression


@dataclass
class UnaryOperation(Expression):
    """Represents a unary operation (e.g., -, NOT)."""
    operator: str  # e.g., "-", "NOT"
    operand: Expression


@dataclass
class FunctionCall(Expression):
    """Represents a function call."""
    function_name: VariableRef | str  # Can be a direct name or a var holding a func ref
    arguments: list[Expression] = field(default_factory=list)
    # is_method_call: bool = False
    # object_instance: Optional[Expression] = None # For method calls like obj.Method()


@dataclass
class ArrayAccess(Expression):
    """Represents accessing an element of an array or list."""
    base: Expression  # The array variable
    indices: list[Expression] = field(default_factory=list)

# --- Statements --- #
# Statements perform an action but do not produce a value (though some might contain expressions).


@dataclass
class Statement(IrNode):
    """Base class for all statements."""
    pass


@dataclass
class AssignmentStatement(Statement):
    """Represents an assignment (e.g., x = y + 1)."""
    target: VariableRef | ArrayAccess  # LHS of the assignment
    source: Expression  # RHS of the assignment


@dataclass
class ExpressionStatement(Statement):
    """A statement that consists of a single expression (e.g., a function call)."""
    expression: Expression


@dataclass
class IfStatement(Statement):
    """Represents an if-then-else structure."""
    condition: Expression
    then_block: list[Statement] = field(default_factory=list)
    else_block: list[Statement] | None = field(default_factory=list)  # For else or elseif chains


@dataclass
class WhileLoop(Statement):
    """Represents a while loop."""
    condition: Expression
    body: list[Statement] = field(default_factory=list)


@dataclass
class ForLoop(Statement):  # Placeholder, PB FOR loops might be more complex
    """Represents a for loop (conceptual)."""
    initializer: Statement | None = None
    condition: Expression | None = None
    incrementor: Statement | None = None
    body: list[Statement] = field(default_factory=list)


@dataclass
class DoLoopUntil(Statement):
    """Represents a DO ... LOOP UNTIL condition loop."""
    condition: Expression
    body: list[Statement] = field(default_factory=list)


@dataclass
class DoLoopWhile(Statement):
    """Represents a DO ... LOOP WHILE condition loop."""
    condition: Expression
    body: list[Statement] = field(default_factory=list)


@dataclass
class ChooseCaseStatement(Statement):  # PowerBuilder CHOOSE CASE
    """Represents a CHOOSE CASE structure."""
    test_expression: Expression | None = None  # The expression after CHOOSE CASE
    cases: list["CaseBlock"] = field(default_factory=list)
    case_else: list[Statement] | None = field(default_factory=list)


@dataclass
class CaseBlock(IrNode):  # Part of ChooseCaseStatement
    """Represents a single CASE block in a CHOOSE CASE statement."""
    conditions: list[Union[Expression, "CaseRange"]]  # e.g., CASE 1, CASE 2 TO 5, CASE IS > 10
    body: list[Statement] = field(default_factory=list)


@dataclass
class CaseRange(IrNode):  # Part of CaseBlock
    """Represents a range in a CASE statement (e.g., 1 TO 5)."""
    lower_bound: Expression
    upper_bound: Expression


@dataclass
class ReturnStatement(Statement):
    """Represents a return statement."""
    value: Expression | None = None


@dataclass
class BreakStatement(Statement):
    """Represents a break statement (exiting a loop)."""
    pass


@dataclass
class ContinueStatement(Statement):
    """Represents a continue statement (skipping to next loop iteration)."""
    pass


@dataclass
class TryCatchStatement(Statement):
    """Represents a TRY...CATCH...FINALLY structure."""
    try_block: list[Statement] = field(default_factory=list)
    catch_blocks: list["CatchBlock"] = field(default_factory=list)
    finally_block: list[Statement] | None = field(default_factory=list)


@dataclass
class CatchBlock(IrNode):
    """Represents a CATCH block in a TRY...CATCH statement."""
    exception_type: str | None = None  # e.g., "dwruntimeerror", "oleexception"
    exception_variable: VariableRef | None = None
    body: list[Statement] = field(default_factory=list)


@dataclass
class ThrowStatement(Statement):
    """Represents a THROW statement."""
    expression: Expression  # The exception object being thrown


@dataclass
class LabelStatement(Statement):
    """Represents a GOTO label."""
    name: str


@dataclass
class GotoStatement(Statement):
    """Represents a GOTO statement."""
    label_name: str

# --- Top-Level Structure --- #


@dataclass
class Script(IrNode):
    """Represents a complete script or function body."""
    name: str  # e.g., function name, event name
    parameters: list[VariableRef] = field(default_factory=list)
    local_declarations: list[VariableRef] = field(default_factory=list)  # Simplified for now
    body: list[Statement] = field(default_factory=list)
    # return_type: Optional[str] = None

# Example of how one might use these:
# func_body = Script(
#     name="of_calculate_total",
#     parameters=[VariableRef(name="price"), VariableRef(name="quantity")],
#     body=[
#         AssignmentStatement(
#             target=VariableRef(name="total"),
#             source=BinaryOperation(
#                 left=VariableRef(name="price"),
#                 operator="*",
#                 right=VariableRef(name="quantity")
#             )
#         ),
#         ReturnStatement(value=VariableRef(name="total"))
#     ]
# )
