"""Abstract visitor for PowerBuilder AST nodes.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Visitor/PWBASTAbstractVisitor.class.st
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar

from src.model.ast import CustomType as PBCustomTypeNode
from src.model.ast import Type as PBBasicTypeNode

# These imports are commented out as the modules don't exist yet
# from ....model.base.pb_file import PBCommonFileNode
# Import actual existing classes from the codebase
from src.model.constructs.pb_access import PBAccessNode

# The following imports are commented out as the modules/classes don't exist yet
from src.model.types.base import PBNode

# Stub classes for nodes that don't exist yet but are referenced in the visitor
# These should be implemented as needed or the visitor methods should be removed


# Stub classes for missing behavioral nodes
@dataclass
class PBAccessModifierDefinerNode(PBNode):
    """Stub for access modifier definer node."""

    access_modifier: Any = None


class PBAccessModifierNode(PBNode):
    """Stub for access modifier node."""

    access_modifier: str = ""


class PBBehavioralAliasNode(PBNode):
    """Stub for behavioral alias node."""

    alias: Any = None


class PBBehavioralLibraryNode(PBNode):
    """Stub for behavioral library node."""

    library_file: Any = None


class PBBehavioralOptionNode(PBNode):
    """Stub for behavioral option node."""

    option: Any = None


class PBCommonFileNode(PBNode):
    """Stub for common file node."""

    file_content: Any = None


class PBAccessOrTypeNode(PBNode):
    """Stub for access or type node."""

    access_or_type: Any = None


class PBArrayDesignationNode(PBNode):
    """Stub for array designation node."""

    array_designation: str = ""


class PBAssignationNode(PBNode):
    """Stub for assignation node."""

    expression: Any = None


class PBAssignationStatementNode(PBNode):
    """Stub for assignation statement node."""

    access_or_type: Any = None
    expression_action: Any = None
    assignation: Any = None


class PBBooleanValueNode(PBNode):
    """Stub for boolean value node."""

    boolean_value: str = ""


class PBCallStatementNode(PBNode):
    """Stub for call statement node."""

    variable: Any = None
    identifier: Any = None
    event_type: Any = None


class PBCaseElseNode(PBNode):
    """Stub for case else node."""

    statements: Any = None
    statement: Any = None


class PBCaseNode(PBNode):
    """Stub for case node."""

    case: Any = None


class PBChooseCaseNode(PBNode):
    """Stub for choose case node."""

    expression: Any = None
    cases: list = None
    case_else: Any = None


class PBConditionNode(PBNode):
    """Stub for condition node."""

    expression: Any = None


class PBConstantNode(PBNode):
    """Stub for constant node."""

    constant: str = ""


class PBContinueStatementNode(PBNode):
    """Stub for continue statement node."""

    continue_statement: str = ""


class PBCreateInstructionNode(PBNode):
    """Stub for create instruction node."""

    variable: Any = None


class PBCreateUsingInstructionNode(PBNode):
    """Stub for create using instruction node."""

    expression: Any = None


class PBCustomCallStatementNode(PBNode):
    """Stub for custom call statement node."""

    identifier: Any = None


class PBDescriptorNode(PBNode):
    """Stub for descriptor node."""

    expression: Any = None


class PBDestroyStatementNode(PBNode):
    """Stub for destroy statement node."""

    expression: Any = None


class PBDoLoopUntilNode(PBNode):
    """Stub for do loop until node."""

    statements: Any = None
    expression: Any = None


class PBDoLoopWhileNode(PBNode):
    """Stub for do loop while node."""

    statements: Any = None
    expression: Any = None


class PBDoUntilLoopNode(PBNode):
    """Stub for do until loop node."""

    expression: Any = None
    statements: Any = None


class PBDoWhileLoopNode(PBNode):
    """Stub for do while loop node."""

    expression: Any = None
    statements: Any = None


class PBDynamicMethodInvocationNode(PBNode):
    """Stub for dynamic method invocation node."""

    unchecked_identifier: Any = None
    function_arguments: Any = None


class PBElseIfNode(PBNode):
    """Stub for else if node."""

    expression: Any = None
    statements: Any = None


class PBElseNode(PBNode):
    """Stub for else node."""

    statements: Any = None


class PBElseOnLineNode(PBNode):
    """Stub for else on line node."""

    statement: Any = None


class PBEndForwardNode(PBNode):
    """Stub for end forward node."""

    end_forward: str = ""


class PBExitStatementNode(PBNode):
    """Stub for exit statement node."""

    exit_statement: str = ""


class PBExportNode(PBNode):
    """Stub for export node."""

    format_type: Any = None
    parameters: Any = None


class PBExpressionActionNode(PBNode):
    """Stub for expression action node."""

    action: Any = None
    expression_action: Any = None


class PBExpressionListNode(PBNode):
    """Stub for expression list node."""

    expressions: list = None


class PBExpressionNode(PBNode):
    """Stub for expression node."""

    expression: Any = None
    expression_action: Any = None


class PBExpressionOperatorNode(PBNode):
    """Stub for expression operator node."""

    expression_operator: str = ""


# Additional stub classes for missing array nodes
@dataclass
class PBArrayNode(PBNode):
    """Stub for array node."""

    expressions: list = None


class PBArrayPositionNode(PBNode):
    """Stub for array position node."""

    expressions: list = None


class PBArrayWithSizeNode(PBNode):
    """Stub for array with size node."""

    expressions: list = None


# Stub classes for missing SQL nodes
@dataclass
class PBCloseSqlCursorNode(PBNode):
    """Stub for close SQL cursor node."""

    cursor_name: Any = None


class PBDeclareCursorNode(PBNode):
    """Stub for declare cursor node."""

    cursor_name: Any = None
    sql_query: Any = None


class PBDeclareProcedureNode(PBNode):
    """Stub for declare procedure node."""

    procedure_name: Any = None
    parameters: Any = None


class PBExecuteProcedureNode(PBNode):
    """Stub for execute procedure node."""

    procedure_name: Any = None
    arguments: Any = None


# Stub classes for missing function argument nodes
@dataclass
class PBArgumentNode(PBNode):
    """Stub for argument node."""

    argument_option: Any = None
    type: Any = None
    identifier: Any = None
    array_with_size: Any = None


class PBArgumentOptionNode(PBNode):
    """Stub for argument option node."""

    argument_option: str = ""


class PBArgumentsNode(PBNode):
    """Stub for arguments node."""

    arguments: list = None


class PBDefaultVariableNode(PBNode):
    """Stub for default variable node."""

    default_value: Any = None


# Stub classes for missing event nodes
@dataclass
class PBEventAttributeNode(PBNode):
    """Stub for event attribute node."""

    attribute: Any = None


class PBEventDeclarationNode(PBNode):
    """Stub for event declaration node."""

    event_name: Any = None
    event_type: Any = None


class PBEventInvocationNode(PBNode):
    """Stub for event invocation node."""

    event_name: Any = None
    arguments: Any = None


class PBEventLongNode(PBNode):
    """Stub for event long node."""

    event_long: str = ""


class PBEventNameNode(PBNode):
    """Stub for event name node."""

    event_name: str = ""


class PBEventReferenceNameNode(PBNode):
    """Stub for event reference name node."""

    reference_name: str = ""


class PBEventTriggeringOrPostingNode(PBNode):
    """Stub for event triggering or posting node."""

    event_action: Any = None


class PBEventTypeNode(PBNode):
    """Stub for event type node."""

    event_type: str = ""


class PBEventWordNode(PBNode):
    """Stub for event word node."""

    event_word: str = ""


# Stub classes for missing datawindow nodes
@dataclass
class PBColumnDefinitionNode(PBNode):
    """Stub for column definition node."""

    column_name: Any = None
    column_type: Any = None


class PBColumnNameOptionNode(PBNode):
    """Stub for column name option node."""

    column_name_option: str = ""


class PBColumnNode(PBNode):
    """Stub for column node."""

    column_data: Any = None


class PBColumnTypeOptionNode(PBNode):
    """Stub for column type option node."""

    column_type_option: str = ""


class PBDataWindowFileNode(PBNode):
    """Stub for data window file node."""

    file_content: Any = None


class PBDataWindowNode(PBNode):
    """Stub for data window node."""

    datawindow_content: Any = None


T = TypeVar("T")


class PowerBuilderASTVisitor(ABC):
    """Abstract base class for PowerBuilder AST visitors.

    Features:
    - Generic visit method for any node type
    - Visit collection of nodes
    - Type-specific visit methods for each AST node type
    """

    def visit(self, node: Any | None) -> Any:
        """Visit a node.

        Args:
            node: Node to visit

        Returns:
            Result of visiting the node
        """
        if node is None:
            return None
        return node.accept_visitor(self)

    def visit_all(self, nodes: list[Any] | None) -> None:
        """Visit a collection of nodes.

        Args:
            nodes: List of nodes to visit
        """
        if nodes is not None:
            for node in nodes:
                self.visit(node)

    @abstractmethod
    def visit_access(self, node: PBAccessNode) -> None:
        """Visit an access node."""
        self.visit(node.accessed)
        self.visit(node.array_position)

    @abstractmethod
    def visit_access_modifier(self, node: PBAccessModifierNode) -> str:
        """Visit an access modifier node."""
        return node.access_modifier

    @abstractmethod
    def visit_access_modifier_definer(self, node: PBAccessModifierDefinerNode) -> None:
        """Visit an access modifier definer node."""
        self.visit(node.access_modifier)

    @abstractmethod
    def visit_access_or_type(self, node: PBAccessOrTypeNode) -> None:
        """Visit an access or type node."""
        self.visit(node.access_or_type)

    @abstractmethod
    def visit_argument(self, node: PBArgumentNode) -> None:
        """Visit an argument node."""
        self.visit(node.argument_option)
        self.visit(node.type)
        self.visit(node.identifier)
        self.visit(node.array_with_size)

    @abstractmethod
    def visit_argument_option(self, node: PBArgumentOptionNode) -> str:
        """Visit an argument option node."""
        return node.argument_option

    @abstractmethod
    def visit_arguments(self, node: PBArgumentsNode) -> None:
        """Visit an arguments node."""
        self.visit_all(node.arguments)

    @abstractmethod
    def visit_array(self, node: PBArrayNode) -> None:
        """Visit an array node."""
        self.visit_all(node.expressions)

    @abstractmethod
    def visit_array_designation(self, node: PBArrayDesignationNode) -> str:
        """Visit an array designation node."""
        return node.array_designation

    @abstractmethod
    def visit_array_position(self, node: PBArrayPositionNode) -> None:
        """Visit an array position node."""
        self.visit_all(node.expressions)

    @abstractmethod
    def visit_array_with_size(self, node: PBArrayWithSizeNode) -> None:
        """Visit an array with size node."""
        self.visit_all(node.expressions)

    @abstractmethod
    def visit_assignation(self, node: PBAssignationNode) -> None:
        """Visit an assignation node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_assignation_statement(self, node: PBAssignationStatementNode) -> None:
        """Visit an assignation statement node."""
        self.visit(node.access_or_type)
        self.visit(node.expression_action)
        self.visit(node.assignation)

    @abstractmethod
    def visit_basic_type(self, node: PBBasicTypeNode) -> str:
        """Visit a basic type node."""
        return node.basic_type

    @abstractmethod
    def visit_behavioral_alias(self, node: PBBehavioralAliasNode) -> None:
        """Visit a behavioral alias node."""
        self.visit(node.alias)

    @abstractmethod
    def visit_behavioral_library(self, node: PBBehavioralLibraryNode) -> None:
        """Visit a behavioral library node."""
        self.visit(node.library_file)

    @abstractmethod
    def visit_behavioral_option(self, node: PBBehavioralOptionNode) -> None:
        """Visit a behavioral option node."""
        self.visit(node.behavioral_option)

    @abstractmethod
    def visit_boolean_value(self, node: PBBooleanValueNode) -> str:
        """Visit a boolean value node."""
        return node.boolean_value

    @abstractmethod
    def visit_call_statement(self, node: PBCallStatementNode) -> None:
        """Visit a call statement node."""
        self.visit(node.variable)
        self.visit(node.identifier)
        self.visit(node.event_type)

    @abstractmethod
    def visit_case(self, node: PBCaseNode) -> None:
        """Visit a case node."""
        self.visit(node.case)

    @abstractmethod
    def visit_case_else(self, node: PBCaseElseNode) -> None:
        """Visit a case else node."""
        self.visit(node.statements)
        self.visit(node.statement)

    @abstractmethod
    def visit_choose_case(self, node: PBChooseCaseNode) -> None:
        """Visit a choose case node."""
        self.visit(node.expression)
        self.visit_all(node.cases)
        self.visit(node.case_else)

    @abstractmethod
    def visit_close_sql_cursor(self, node: PBCloseSqlCursorNode) -> None:
        """Visit a close SQL cursor node."""
        self.visit(node.identifier)

    @abstractmethod
    def visit_column(self, node: PBColumnNode) -> None:
        """Visit a column node."""
        self.visit(node.column_definition)

    @abstractmethod
    def visit_column_definition(self, node: PBColumnDefinitionNode) -> None:
        """Visit a column definition node."""
        self.visit(node.options)

    @abstractmethod
    def visit_column_name_option(self, node: PBColumnNameOptionNode) -> None:
        """Visit a column name option node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_column_type_option(self, node: PBColumnTypeOptionNode) -> None:
        """Visit a column type option node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_common_file(self, node: PBCommonFileNode) -> None:
        """Visit a common file node."""
        self.visit_all(node.file_statements)

    @abstractmethod
    def visit_condition(self, node: PBConditionNode) -> None:
        """Visit a condition node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_constant(self, node: PBConstantNode) -> str:
        """Visit a constant node."""
        return node.constant

    @abstractmethod
    def visit_continue_statement(self, node: PBContinueStatementNode) -> str:
        """Visit a continue statement node."""
        return node.continue_statement

    @abstractmethod
    def visit_create_instruction(self, node: PBCreateInstructionNode) -> None:
        """Visit a create instruction node."""
        self.visit(node.variable)

    @abstractmethod
    def visit_create_using_instruction(
        self,
        node: PBCreateUsingInstructionNode,
    ) -> None:
        """Visit a create using instruction node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_custom_call_statement(self, node: PBCustomCallStatementNode) -> None:
        """Visit a custom call statement node."""
        self.visit(node.identifier)

    @abstractmethod
    def visit_custom_type(self, node: PBCustomTypeNode) -> None:
        """Visit a custom type node."""
        self.visit(node.identifier)

    @abstractmethod
    def visit_data_window(self, node: PBDataWindowNode) -> None:
        """Visit a data window node."""
        self.visit(node.parameters)

    @abstractmethod
    def visit_data_window_file(self, node: PBDataWindowFileNode) -> None:
        """Visit a data window file node."""
        self.visit_all(node.file_statements)

    @abstractmethod
    def visit_declare_cursor(self, node: PBDeclareCursorNode) -> None:
        """Visit a declare cursor node."""
        self.visit(node.identifier)
        self.visit(node.target)

    @abstractmethod
    def visit_declare_procedure(self, node: PBDeclareProcedureNode) -> None:
        """Visit a declare procedure node."""
        self.visit(node.procedure_name)

    @abstractmethod
    def visit_default_variable(self, node: PBDefaultVariableNode) -> str:
        """Visit a default variable node."""
        return node.default_variable

    @abstractmethod
    def visit_descriptor(self, node: PBDescriptorNode) -> None:
        """Visit a descriptor node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_destroy_statement(self, node: PBDestroyStatementNode) -> None:
        """Visit a destroy statement node."""
        self.visit(node.expression)

    @abstractmethod
    def visit_do_loop_until(self, node: PBDoLoopUntilNode) -> None:
        """Visit a do loop until node."""
        self.visit(node.statements)
        self.visit(node.expression)

    @abstractmethod
    def visit_do_loop_while(self, node: PBDoLoopWhileNode) -> None:
        """Visit a do loop while node."""
        self.visit(node.statements)
        self.visit(node.expression)

    @abstractmethod
    def visit_do_until_loop(self, node: PBDoUntilLoopNode) -> None:
        """Visit a do until loop node."""
        self.visit(node.expression)
        self.visit(node.statements)

    @abstractmethod
    def visit_do_while_loop(self, node: PBDoWhileLoopNode) -> None:
        """Visit a do while loop node."""
        self.visit(node.expression)
        self.visit(node.statements)

    @abstractmethod
    def visit_dynamic_method_invocation(
        self,
        node: PBDynamicMethodInvocationNode,
    ) -> None:
        """Visit a dynamic method invocation node."""
        self.visit(node.unchecked_identifier)
        self.visit(node.function_arguments)

    @abstractmethod
    def visit_else(self, node: PBElseNode) -> None:
        """Visit an else node."""
        self.visit(node.statements)

    @abstractmethod
    def visit_else_if(self, node: PBElseIfNode) -> None:
        """Visit an else if node."""
        self.visit(node.expression)
        self.visit(node.statements)

    @abstractmethod
    def visit_else_on_line(self, node: PBElseOnLineNode) -> None:
        """Visit an else on line node."""
        self.visit(node.statement)

    @abstractmethod
    def visit_end_forward(self, node: PBEndForwardNode) -> str:
        """Visit an end forward node."""
        return node.end_forward

    @abstractmethod
    def visit_event_attribute(self, node: PBEventAttributeNode) -> None:
        """Visit an event attribute node."""
        self.visit(node.return_type)
        self.visit(node.event_name)
        self.visit(node.attribute)

    @abstractmethod
    def visit_event_declaration(self, node: PBEventDeclarationNode) -> None:
        """Visit an event declaration node."""
        self.visit(node.return_type)
        self.visit(node.event_reference_name)
        self.visit(node.custom_call_statement)
        self.visit(node.statements)

    @abstractmethod
    def visit_event_invocation(self, node: PBEventInvocationNode) -> None:
        """Visit an event invocation node."""
        self.visit(node.identifier)
        self.visit(node.function_arguments)

    @abstractmethod
    def visit_event_long(self, node: PBEventLongNode) -> None:
        """Visit an event long node."""
        self.visit(node.function_argument)

    @abstractmethod
    def visit_event_name(self, node: PBEventNameNode) -> None:
        """Visit an event name node."""
        self.visit(node.event_name)

    @abstractmethod
    def visit_event_reference_name(self, node: PBEventReferenceNameNode) -> None:
        """Visit an event reference name node."""
        self.visit(node.object_class)
        self.visit(node.event_name)
        self.visit(node.arguments)

    @abstractmethod
    def visit_event_triggering_or_posting(
        self,
        node: PBEventTriggeringOrPostingNode,
    ) -> None:
        """Visit an event triggering or posting node."""
        self.visit_all(node.identifiers)
        self.visit_all(node.array_positions)
        self.visit(node.event_name)
        self.visit(node.event_word)
        self.visit(node.event_long)

    @abstractmethod
    def visit_event_type(self, node: PBEventTypeNode) -> None:
        """Visit an event type node."""
        self.visit(node.event_type)

    @abstractmethod
    def visit_event_word(self, node: PBEventWordNode) -> None:
        """Visit an event word node."""
        self.visit(node.function_argument)

    @abstractmethod
    def visit_execute_procedure(self, node: PBExecuteProcedureNode) -> None:
        """Visit an execute procedure node."""
        self.visit(node.procedure_name)
        self.visit(node.using_clause)

    @abstractmethod
    def visit_exit_statement(self, node: PBExitStatementNode) -> str:
        """Visit an exit statement node."""
        return node.exit_statement

    @abstractmethod
    def visit_export(self, node: PBExportNode) -> None:
        """Visit an export node."""
        self.visit(node.format_type)
        self.visit(node.parameters)

    @abstractmethod
    def visit_expression(self, node: PBExpressionNode) -> None:
        """Visit an expression node."""
        self.visit(node.expression)
        self.visit(node.expression_action)

    @abstractmethod
    def visit_expression_action(self, node: PBExpressionActionNode) -> None:
        """Visit an expression action node."""
        self.visit(node.action)
        self.visit(node.expression_action)

    @abstractmethod
    def visit_expression_list(self, node: PBExpressionListNode) -> None:
        """Visit an expression list node."""
        self.visit_all(node.expressions)

    @abstractmethod
    def visit_expression_operator(self, node: PBExpressionOperatorNode) -> str:
        """Visit an expression operator node."""
        return node.expression_operator
