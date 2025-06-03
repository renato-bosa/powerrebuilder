"""PowerBuilder expression model stubs."""

from dataclasses import dataclass
from typing import Any

from .utils.base import PBNode


@dataclass
class PBAccessOrTypeNode(PBNode):
    """Access or type node."""

    access_or_type: Any = None


@dataclass
class PBArrayDesignationNode(PBNode):
    """Array designation node."""

    array_designation: str = ""


@dataclass
class PBAssignationNode(PBNode):
    """Assignation node."""

    expression: Any = None


@dataclass
class PBAssignationStatementNode(PBNode):
    """Assignation statement node."""

    access_or_type: Any = None
    expression_action: Any = None
    assignation: Any = None


@dataclass
class PBBooleanValueNode(PBNode):
    """Boolean value node."""

    boolean_value: str = "false"


@dataclass
class PBCallStatementNode(PBNode):
    """Call statement node."""

    variable: Any = None
    identifier: Any = None
    event_type: Any = None


@dataclass
class PBCaseElseNode(PBNode):
    """Case else node."""

    statements: Any = None
    statement: Any = None


@dataclass
class PBCaseNode(PBNode):
    """Case node."""

    case: Any = None


@dataclass
class PBChooseCaseNode(PBNode):
    """Choose case node."""

    expression: Any = None
    cases: list[Any] = None
    case_else: Any = None


@dataclass
class PBConditionNode(PBNode):
    """Condition node."""

    expression: Any = None


@dataclass
class PBConstantNode(PBNode):
    """Constant node."""

    constant: str = ""


@dataclass
class PBContinueStatementNode(PBNode):
    """Continue statement node."""

    continue_statement: str = "continue"


@dataclass
class PBCreateInstructionNode(PBNode):
    """Create instruction node."""

    variable: Any = None


@dataclass
class PBCreateUsingInstructionNode(PBNode):
    """Create using instruction node."""

    expression: Any = None


@dataclass
class PBCustomCallStatementNode(PBNode):
    """Custom call statement node."""

    identifier: Any = None


@dataclass
class PBDescriptorNode(PBNode):
    """Descriptor node."""

    expression: Any = None


@dataclass
class PBDestroyStatementNode(PBNode):
    """Destroy statement node."""

    expression: Any = None


@dataclass
class PBDoLoopUntilNode(PBNode):
    """Do loop until node."""

    statements: Any = None
    expression: Any = None


@dataclass
class PBDoLoopWhileNode(PBNode):
    """Do loop while node."""

    statements: Any = None
    expression: Any = None


@dataclass
class PBDoUntilLoopNode(PBNode):
    """Do until loop node."""

    expression: Any = None
    statements: Any = None


@dataclass
class PBDoWhileLoopNode(PBNode):
    """Do while loop node."""

    expression: Any = None
    statements: Any = None


@dataclass
class PBDynamicMethodInvocationNode(PBNode):
    """Dynamic method invocation node."""

    unchecked_identifier: Any = None
    function_arguments: Any = None


@dataclass
class PBElseIfNode(PBNode):
    """Else if node."""

    expression: Any = None
    statements: Any = None


@dataclass
class PBElseNode(PBNode):
    """Else node."""

    statements: Any = None


@dataclass
class PBElseOnLineNode(PBNode):
    """Else on line node."""

    statement: Any = None


@dataclass
class PBEndForwardNode(PBNode):
    """End forward node."""

    end_forward: str = "end forward"


@dataclass
class PBExitStatementNode(PBNode):
    """Exit statement node."""

    exit_statement: str = "exit"


@dataclass
class PBExportNode(PBNode):
    """Export node."""

    format_type: Any = None
    parameters: Any = None


@dataclass
class PBExpressionActionNode(PBNode):
    """Expression action node."""

    action: Any = None
    expression_action: Any = None


@dataclass
class PBExpressionListNode(PBNode):
    """Expression list node."""

    expressions: list[Any] = None


@dataclass
class PBExpressionNode(PBNode):
    """Expression node."""

    expression: Any = None
    expression_action: Any = None


@dataclass
class PBExpressionOperatorNode(PBNode):
    """Expression operator node."""

    expression_operator: str = ""
