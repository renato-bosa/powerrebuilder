"""Entity creator visitor for PowerBuilder AST.

This module provides a visitor that creates entities from AST nodes.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from model.ast.nodes import (
    Event,
    Expression,
    Function,
    Parameter,
    Type,
    Variable,
)
from model.ast.sql import (
    SQLQuery,
)
from model.constructs.pb_access import PBAccessNode
from model.entities.pb_argument import PBArgumentNode, PBArgumentsNode
from model.constructs.pb_array import PBArrayWithSizeNode
from model.entities.pb_event import (
    PBEventDeclarationNode,
    PBEventInvocationNode,
    PBEventReferenceNameNode,
    PBEventTriggeringOrPostingNode,
    PBEventTypeNode,
)
from model.entities.pb_expression import (
    PBAccessOrTypeNode,
    PBAssignationStatementNode,
    PBAttributeAccessNode,
    PBDynamicMethodInvocationNode,
    PBExpressionActionNode,
    PBExpressionNode,
    PBExpressionTermNode,
    PBExpressionWithSignNode,
    PBFunctionArgumentsNode,
    PBFunctionDeclarationNode,
    PBFunctionDefinitionNode,
    PBFunctionInvocationNode,
    PBFunctionSignatureNode,
    PBIdentifierNode,
)
from model.base.pb_file import PBFileNode
from model.base.pb_type import PBBasicTypeNode, PBCustomTypeNode
from model.entities.pb_variable import PBGlobalVariableDeclarationNode
from model.utils.errors import ParsingError

from .abstract_visitor import PowerBuilderASTVisitor


@dataclass
class ResolvableIdentifier:
    """Identifier that can be resolved later."""

    identifier: str
    expected_kind: type | list[type]
    node: Any
    found_action: callable | None = None
    not_found_action: callable | None = None
    previous: Optional["ResolvableIdentifier"] = None


@dataclass
class EntityCreatorState:
    """State for entity creator visitor."""

    current_library: Any | None = None
    type_declaration_type: dict[str, Any] = field(default_factory=dict)
    expression_is_left_hand_side: bool = False
    current_entity: Any | None = None


class PowerBuilderEntityCreatorVisitor(PowerBuilderASTVisitor):
    """Visitor for creating entities from AST nodes.

    Features:
    - Creates entities during AST traversal
    - Tracks resolvable identifiers
    - Handles attribute access chains
    """

    def __init__(self) -> None:
        """Initialize visitor."""
        self.state = EntityCreatorState()
        self.resolvable_identifiers: set[ResolvableIdentifier] = set()
        self.current_scope = "public"

    def attribute_access_name(self, node: Expression) -> str:
        """Get the full name of an attribute access chain.

        Args:
            node: Expression action node

        Returns:
            Full attribute access name
        """
        try:
            return node.to_string()
        except AttributeError:
            return str(node)

    def create_attribute_access(self, node: Expression) -> None:
        """Create an attribute access entity.

        Args:
            node: Expression action node
        """
        try:
            self.attribute_access_name(node)
            identifier = self.create_resolvable_identifier(node)
            self.resolve(identifier)
        except (AttributeError, ParsingError):
            # Log warning but continue
            pass

    def create_resolvable_identifier(self, node: Any) -> ResolvableIdentifier:
        """Create a resolvable identifier.

        Args:
            node: AST node

        Returns:
            Resolvable identifier
        """
        try:
            name = node.name if hasattr(node, "name") else str(node)
            return ResolvableIdentifier(name, node)
        except AttributeError as e:
            raise ParsingError(f"Failed to create identifier: {e}") from e

    def resolve(self, identifier: ResolvableIdentifier) -> None:
        """Add identifier to resolution set.

        Args:
            identifier: Resolvable identifier
        """
        self.resolvable_identifiers.add(identifier)

    def visit_access(self, node: PBAccessNode) -> None:
        """Visit an access node."""
        self.visit(node.array_position)

        if self.state.current_entity.__class__.__name__ in {
            "DataWindow",
            "GraphicComponent",
        }:
            self.visit(node.accessed)
            return

        write_access = self.state.expression_is_left_hand_side
        identifier = self.visit(node.accessed)

        def found_action(identifier, current_entity) -> None:
            if not identifier.entity.__class__.__name__.startswith("MajorObject"):
                self.create_access(current_entity, identifier, write_access)

        def not_found_action(identifier, current_entity):
            return current_entity.create_stub_value_holder(
                identifier.representation_string
            )

        identifier.found_action = found_action
        identifier.not_found_action = not_found_action
        self.resolve(identifier)

    def visit_access_or_type(self, node: PBAccessOrTypeNode) -> Any:
        """Visit an access or type node."""
        return self.visit(node.access_or_type)

    def visit_argument(self, node: PBArgumentNode) -> Any:
        """Visit an argument node."""
        self.visit(node.argument_option)
        self.visit(node.type)
        self.visit(node.array_with_size)
        return self.visit(node.identifier)

    def visit_arguments(self, node: PBArgumentsNode) -> list[Any] | None:
        """Visit an arguments node."""
        if node.arguments is None:
            return None
        return self.visit_all(node.arguments)

    def visit_array_with_size(self, node: PBArrayWithSizeNode) -> list[Any]:
        """Visit an array with size node."""
        return self.visit_all(node.expressions)

    def visit_assignation_statement(self, node: PBAssignationStatementNode) -> None:
        """Visit an assignation statement node."""
        access_or_type = self.visit(node.access_or_type)
        self.state.expression_is_left_hand_side = True
        variable = self.visit(node.expression_action)
        if variable and hasattr(variable, "is_resolvable") and variable.is_resolvable:
            variable.previous = access_or_type
        self.state.expression_is_left_hand_side = False
        self.visit(node.assignation)

    def visit_attribute_access(self, node: PBAttributeAccessNode) -> Any:
        """Visit an attribute access node."""
        self.visit(node.array_information)
        return self.visit(node.unchecked_identifier)

    def visit_basic_type(self, node: PBBasicTypeNode) -> Any:
        """Visit a basic type node."""
        return self.ensure_famix_entity("BasicType", node.basic_type)

    def visit_custom_type(self, node: PBCustomTypeNode) -> Any:
        """Visit a custom type node."""
        type_to_resolve = self.create_resolvable_identifier(node)

        def found_action(identifier, current_entity) -> None:
            self.preprocessed_file = current_entity.source_anchor.file_reference
            reference = self.create_reference(identifier.node)
            reference.source = current_entity
            reference.target = identifier.entity

        def not_found_action(identifier, current_entity):
            return self.ensure_famix_entity("CustomType", self.visit(node.identifier))

        type_to_resolve.found_action = found_action
        type_to_resolve.not_found_action = not_found_action
        return self.resolve(type_to_resolve)

    def visit_dynamic_method_invocation(
        self, node: PBDynamicMethodInvocationNode
    ) -> None:
        """Visit a dynamic method invocation node."""
        argument_asts = node.function_arguments
        invocation = self.create_resolvable_identifier(node)

        def found_action(identifier, current_entity) -> None:
            self.preprocessed_file = current_entity.source_anchor.file_reference
            invocation = self.create_invocation(identifier.node)
            invocation.sender = current_entity
            invocation.candidates = identifier.candidates

            if argument_asts and argument_asts.function_arguments:
                for arg_ast in argument_asts.function_arguments:
                    argument = self.create_argument(arg_ast)
                    argument.invocation = invocation

        def not_found_action(identifier):
            return [self.create_stub("Function", identifier)]

        invocation.found_action = found_action
        invocation.not_found_action = not_found_action
        self.resolve(invocation)

    def visit_event_declaration(self, node: PBEventDeclarationNode) -> None:
        """Visit an event declaration node."""
        event = self.create_entity("Event", node)
        with self.use_current_entity(event):
            self.visit(node.event_reference_name)
            self.visit(node.custom_call_statement)
            self.visit(node.statements)

    def visit_event_invocation(self, node: PBEventInvocationNode) -> None:
        """Visit an event invocation node."""
        argument_asts = node.function_arguments
        invocation = self.create_resolvable_identifier(node)

        def found_action(identifier, current_entity) -> None:
            self.preprocessed_file = current_entity.source_anchor.file_reference
            invocation = self.create_invocation(identifier.node)
            invocation.sender = current_entity
            invocation.candidates = identifier.candidates

            if argument_asts and argument_asts.function_arguments:
                for arg_ast in argument_asts.function_arguments:
                    argument = self.create_argument(arg_ast)
                    argument.invocation = invocation

        def not_found_action(identifier):
            return [self.create_stub("Event", identifier)]

        invocation.found_action = found_action
        invocation.not_found_action = not_found_action
        self.resolve(invocation)

    def visit_event_reference_name(self, node: PBEventReferenceNameNode) -> None:
        """Visit an event reference name node."""
        self.visit(node.object_class)
        self.state.current_entity.name = self.visit(node.event_name)
        self.visit(node.arguments)

    def visit_event_triggering_or_posting(
        self, node: PBEventTriggeringOrPostingNode
    ) -> None:
        """Visit an event triggering or posting node."""
        try:
            event_name = node.event_name.to_string()
        except:
            return

        custom_identifier = PBIdentifierNode(
            identifier=event_name.replace('"', "").replace("!", ""),
            start_position=node.start_position,
            stop_position=node.stop_position,
        )

        event_invocation = PBEventInvocationNode(
            identifier=custom_identifier,
            start_position=node.start_position,
            stop_position=node.stop_position,
        )

        self.visit_event_invocation(event_invocation)

    def visit_event_type(self, node: PBEventTypeNode) -> Any:
        """Visit an event type node."""
        return self.visit(node.event_type)

    def visit_expression(self, node: PBExpressionNode) -> Any:
        """Visit an expression node."""
        self.visit(node.expression_action)
        return self.visit(node.expression)

    def visit_expression_action(self, node: PBExpressionActionNode) -> Any:
        """Visit an expression action node."""
        if node.is_attribute_access:
            return self.create_attribute_access(node)

        if node.expression_action is None:
            return self.visit(node.action)

        self.visit(node.action)
        return self.visit(node.expression_action)

    def visit_expression_term(self, node: PBExpressionTermNode) -> Any:
        """Visit an expression term node."""
        return self.visit(node.expression_term)

    def visit_expression_with_sign(self, node: PBExpressionWithSignNode) -> Any:
        """Visit an expression with sign node."""
        self.visit(node.expression_sign)
        return self.visit(node.expression)

    def visit_file(self, node: PBFileNode) -> None:
        """Visit a file node."""
        major_entity = self.create_entity(
            self.major_entity_class_for_extension(node.file_extension),
            node,
        )
        major_entity.name = node.file_name
        major_entity.library = self.state.current_library

        with self.use_current_entity(major_entity):
            super().visit_file(node)

    def visit_function_arguments(self, node: PBFunctionArgumentsNode) -> Any:
        """Visit a function arguments node."""
        super().visit_function_arguments(node)
        return len(node.function_arguments or [])

    def visit_function_declaration(self, node: PBFunctionDeclarationNode) -> None:
        """Visit a function declaration node."""
        with self.use_current_entity(None):
            super().visit_function_declaration(node)

    def visit_function_definition(self, node: PBFunctionDefinitionNode) -> Any:
        """Visit a function definition node."""
        function = self.create_entity("Function", node)
        with self.use_current_entity(function):
            super().visit_function_definition(node)
        return self.state.current_entity

    def visit_function_invocation(self, node: PBFunctionInvocationNode) -> None:
        """Visit a function invocation node."""
        argument_asts = node.function_arguments
        invocation = self.create_resolvable_identifier(node)

        def found_action(identifier, current_entity) -> None:
            self.preprocessed_file = current_entity.source_anchor.file_reference
            invocation = self.create_invocation(identifier.node)
            invocation.sender = current_entity
            invocation.candidates = identifier.candidates

            if argument_asts and argument_asts.function_arguments:
                for arg_ast in argument_asts.function_arguments:
                    argument = self.create_argument(arg_ast)
                    argument.invocation = invocation

        def not_found_action(identifier):
            return [self.create_stub("SubRoutine", identifier)]

        invocation.found_action = found_action
        invocation.not_found_action = not_found_action
        self.resolve(invocation)
        self.visit(node.default_variable)

    def visit_function_signature(self, node: PBFunctionSignatureNode) -> None:
        """Visit a function signature node."""
        if self.state.current_entity is None:
            return None

        arguments = node.arguments.arguments
        if arguments:
            self.create_parameters(arguments)

        signature = self.create_entity("BehaviorSignature", node)
        signature.name = self.state.current_entity.name
        signature.behavioral = self.state.current_entity
        signature.source_anchor.end_pos += 1  # Include semicolon

        return_type_holder = self.visit(node.type)
        if (
            hasattr(return_type_holder, "is_resolvable")
            and return_type_holder.is_resolvable
        ):
            return_type_holder.add_typed_variable(self.state.current_entity)

        self.state.current_entity.return_type = return_type_holder
        self.state.current_entity.name = self.visit(node.identifier)
        self.state.current_entity.access_modifier = self.visit(node.access_modifier)

        return signature

    def visit_global_variable_declaration(
        self, node: PBGlobalVariableDeclarationNode
    ) -> None:
        """Visit a global variable declaration node."""
        self.visit(node.type)
        self.state.current_entity.create_value_holder(
            self.visit(node.variable).representation_string,
            "GlobalVariable",
        )

    def visit_event(self, node: Event) -> None:
        """Visit an event node."""
        try:
            identifier = self.create_resolvable_identifier(node)
            self.resolve(identifier)
        except AttributeError:
            pass

    def visit_function(self, node: Function) -> None:
        """Visit a function node."""
        try:
            identifier = self.create_resolvable_identifier(node)
            self.resolve(identifier)
        except AttributeError:
            pass

    def visit_variable(self, node: Variable) -> None:
        """Visit a variable node."""
        try:
            identifier = self.create_resolvable_identifier(node)
            self.resolve(identifier)
        except AttributeError:
            pass

    def visit_type(self, node: Type) -> None:
        """Visit a type node."""
        try:
            identifier = self.create_resolvable_identifier(node)
            self.resolve(identifier)
        except AttributeError:
            pass

    def visit_parameter(self, node: Parameter) -> None:
        """Visit a parameter node."""
        try:
            identifier = self.create_resolvable_identifier(node)
            self.resolve(identifier)
        except AttributeError:
            pass

    def visit_sql_query(self, node: SQLQuery) -> None:
        """Visit a SQL query node."""
        try:
            # Extract table names from query
            tables = self._extract_tables(node.query)
            for table in tables:
                identifier = ResolvableIdentifier(table, node)
                self.resolve(identifier)
        except AttributeError:
            pass

    def _extract_tables(self, query: str) -> list[str]:
        """Extract table names from SQL query.

        Args:
            query: SQL query string

        Returns:
            List of table names
        """
        # Simple implementation - could be improved with SQL parser
        words = query.split()
        tables = []
        for i, word in enumerate(words):
            if word.lower() == "from" and i + 1 < len(words):
                tables.append(words[i + 1].strip(",.;"))
        return tables
