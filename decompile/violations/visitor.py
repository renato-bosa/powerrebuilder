"""Violation detection and runner for PowerBuilder AST.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Violation/PWBViolationDetectVisitor.class.st and related classes.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from model.pb_behavioral import PBBehavioralNode
from model.pb_expression import (
    PBFunctionDefinitionNode,
    PBFunctionSignatureNode,
    PBNumberNode,
    PBSubroutineDefinitionNode,
    PBSubroutineSignatureNode,
)
from model.pb_library import PBLibraryNode
from parse.parse_coordinator import PowerBuilderBaseParser
from parse.visitors.abstract_visitor import PowerBuilderASTVisitor


# --- QueryLimitRuleViolation ---
@dataclass
class QueryLimitRuleViolation:
    """Violation for SQL queries without LIMIT clause.
    Features:
    - Tracks file and position information
    - Links to behavioral element and library
    - Provides access to violation details.
    """
    file: Path | None = None
    start_position: int | None = None
    stop_position: int | None = None
    library: PBLibraryNode | None = None
    behavior: PBBehavioralNode | None = None

    @property
    def behavior_name(self) -> str:
        return self.behavior.name if self.behavior else ''

    @property
    def object_name(self) -> str:
        return self.file.stem if self.file else ''

    @property
    def relative_line(self) -> int:
        if not self.file or not self.behavior:
            return 0
        with open(self.file, encoding='utf-8') as f:
            contents = f.read()
        violation_line = contents.count('\n', 0, self.start_position) + 1
        behavior_line = contents.count('\n', 0, self.behavior.source_anchor.start_pos) + 1
        return violation_line - behavior_line

    @property
    def value(self) -> str:
        if not self.file or not self.start_position or not self.stop_position:
            return ''
        with open(self.file, encoding='utf-8') as f:
            contents = f.read()
            return contents[self.start_position:self.stop_position]


# --- ViolationRunner ---
class ViolationRunner:
    """Runner for PowerBuilder code quality checks."""
    def __init__(self) -> None:
        self.visitor = PowerBuilderViolationDetectVisitor()
        self.processed_files: set[Path] = set()

    def run_on_file(self, file_path: Path) -> list[QueryLimitRuleViolation]:
        if file_path in self.processed_files:
            return []
        self.processed_files.add(file_path)
        try:
            ast = PowerBuilderBaseParser.parse_file(file_path)
            self.visitor.preprocessed_file(file_path)
            self.visitor.visit(ast)
            return self.visitor.violations
        except Exception as e:
            raise ValueError(f"Error processing file {file_path}: {str(e)}") from e

    def run_on_directory(self, dir_path: Path, extension: str | None = None) -> list[QueryLimitRuleViolation]:
        violations = []
        if extension:
            files = dir_path.glob(f"**/*.{extension}")
        else:
            files = dir_path.glob("**/*")
        for file in files:
            if file.is_file():
                try:
                    violations.extend(self.run_on_file(file))
                except ValueError:
                    continue
        return violations

    def clear(self) -> None:
        self.processed_files.clear()
        self.visitor = PowerBuilderViolationDetectVisitor()


# --- ViolationDetectState and PowerBuilderViolationDetectVisitor ---
@dataclass
class ViolationDetectState:
    """State for violation detect visitor."""
    violations: list[QueryLimitRuleViolation] = field(default_factory=list)
    limit: str = '9999'
    preprocessing_map: dict[str, int] = field(default_factory=dict)
    file: Path | None = None
    current_library: PBLibraryNode | None = None
    current_behavior: PBBehavioralNode | None = None


class PowerBuilderViolationDetectVisitor(PowerBuilderASTVisitor):
    """Visitor for detecting violations in PowerBuilder AST.

    Features:
    - Detects SQL queries without LIMIT clause
    - Tracks file and position information
    - Handles preprocessing offsets
    """

    def __init__(self) -> None:
        """Initialize visitor."""
        self.state = ViolationDetectState()

    def add_violation(self, violation: QueryLimitRuleViolation) -> None:
        """Add a violation.

        Args:
            violation: Violation to add
        """
        self.state.violations.append(violation)

    @property
    def violations(self) -> list[QueryLimitRuleViolation]:
        """Get detected violations.

        Returns:
            List of violations
        """
        return self.state.violations

    def preprocessed_file(self, file: Path) -> None:
        """Set preprocessed file path.

        Args:
            file: Original file path
        """
        self.state.file = file.parent / 'cleaned' / file.name

    def unpreprocessed_file(self) -> Path:
        """Get original file path.

        Returns:
            Original file path
        """
        if not self.state.file:
            return Path()
        return Path(str(self.state.file).replace('/cleaned/', '/'))

    def unpreprocessed_position(self, position: int) -> int:
        """Get original file position.

        Args:
            position: Position in preprocessed file

        Returns:
            Position in original file
        """
        if not self.state.file:
            return position

        return self.state.preprocessing_map.get(str(self.state.file), 0) + position

    def visit_function_definition(self, node: PBFunctionDefinitionNode) -> None:
        """Visit a function definition node."""
        function_name = self.visit(node.function_signature)
        self.state.current_behavior = PBBehavioralNode(
            name=function_name,
            source_anchor=None,  # TODO: Create source anchor
        )
        self.visit(node.statements)

    def visit_function_signature(self, node: PBFunctionSignatureNode) -> str:
        """Visit a function signature node."""
        return self.visit(node.identifier)

    def visit_number(self, node: PBNumberNode) -> None:
        """Visit a number node."""
        if node.number.startswith(self.state.limit):
            self.add_violation(QueryLimitRuleViolation(
                file=self.unpreprocessed_file(),
                start_position=self.unpreprocessed_position(node.start_position),
                stop_position=self.unpreprocessed_position(node.stop_position),
                library=self.state.current_library,
                behavior=self.state.current_behavior,
            ))

    def visit_subroutine_definition(self, node: PBSubroutineDefinitionNode) -> None:
        """Visit a subroutine definition node."""
        subroutine_name = self.visit(node.subroutine_signature)
        self.state.current_behavior = PBBehavioralNode(
            name=subroutine_name,
            source_anchor=None,  # TODO: Create source anchor
        )
        self.visit(node.statements)

    def visit_subroutine_signature(self, node: PBSubroutineSignatureNode) -> str:
        """Visit a subroutine signature node."""
        return self.visit(node.identifier)

    # Required abstract methods from base class
    def visit_access(self, node: Any) -> None:
        """Visit an access node."""
        pass

    def visit_access_modifier(self, node: Any) -> str:
        """Visit an access modifier node."""
        return ""

    def visit_access_modifier_definer(self, node: Any) -> None:
        """Visit an access modifier definer node."""
        pass

    def visit_access_or_type(self, node: Any) -> None:
        """Visit an access or type node."""
        pass

    def visit_argument(self, node: Any) -> None:
        """Visit an argument node."""
        pass

    def visit_argument_option(self, node: Any) -> str:
        """Visit an argument option node."""
        return ""

    def visit_arguments(self, node: Any) -> None:
        """Visit an arguments node."""
        pass

    def visit_array(self, node: Any) -> None:
        """Visit an array node."""
        pass

    def visit_array_designation(self, node: Any) -> str:
        """Visit an array designation node."""
        return ""

    def visit_array_position(self, node: Any) -> None:
        """Visit an array position node."""
        pass

    def visit_array_with_size(self, node: Any) -> None:
        """Visit an array with size node."""
        pass

    def visit_assignation(self, node: Any) -> None:
        """Visit an assignation node."""
        pass

    def visit_assignation_statement(self, node: Any) -> None:
        """Visit an assignation statement node."""
        pass

    def visit_basic_type(self, node: Any) -> str:
        """Visit a basic type node."""
        return ""

    def visit_behavioral_alias(self, node: Any) -> None:
        """Visit a behavioral alias node."""
        pass

    def visit_behavioral_library(self, node: Any) -> None:
        """Visit a behavioral library node."""
        pass

    def visit_behavioral_option(self, node: Any) -> None:
        """Visit a behavioral option node."""
        pass

    def visit_boolean_value(self, node: Any) -> str:
        """Visit a boolean value node."""
        return ""

    def visit_call_statement(self, node: Any) -> None:
        """Visit a call statement node."""
        pass

    def visit_case(self, node: Any) -> None:
        """Visit a case node."""
        pass

    def visit_case_else(self, node: Any) -> None:
        """Visit a case else node."""
        pass

    def visit_choose_case(self, node: Any) -> None:
        """Visit a choose case node."""
        pass

    def visit_close_sql_cursor(self, node: Any) -> None:
        """Visit a close SQL cursor node."""
        pass

    def visit_column(self, node: Any) -> None:
        """Visit a column node."""
        pass

    def visit_column_definition(self, node: Any) -> None:
        """Visit a column definition node."""
        pass

    def visit_column_name_option(self, node: Any) -> None:
        """Visit a column name option node."""
        pass

    def visit_column_type_option(self, node: Any) -> None:
        """Visit a column type option node."""
        pass

    def visit_common_file(self, node: Any) -> None:
        """Visit a common file node."""
        pass

    def visit_condition(self, node: Any) -> None:
        """Visit a condition node."""
        pass

    def visit_constant(self, node: Any) -> str:
        """Visit a constant node."""
        return ""

    def visit_continue_statement(self, node: Any) -> str:
        """Visit a continue statement node."""
        return ""

    def visit_create_instruction(self, node: Any) -> None:
        """Visit a create instruction node."""
        pass

    def visit_create_using_instruction(self, node: Any) -> None:
        """Visit a create using instruction node."""
        pass

    def visit_custom_call_statement(self, node: Any) -> None:
        """Visit a custom call statement node."""
        pass

    def visit_custom_type(self, node: Any) -> None:
        """Visit a custom type node."""
        pass

    def visit_data_window(self, node: Any) -> None:
        """Visit a data window node."""
        pass

    def visit_data_window_file(self, node: Any) -> None:
        """Visit a data window file node."""
        pass

    def visit_declare_cursor(self, node: Any) -> None:
        """Visit a declare cursor node."""
        pass

    def visit_declare_procedure(self, node: Any) -> None:
        """Visit a declare procedure node."""
        pass

    def visit_default_variable(self, node: Any) -> str:
        """Visit a default variable node."""
        return ""

    def visit_descriptor(self, node: Any) -> None:
        """Visit a descriptor node."""
        pass

    def visit_destroy_statement(self, node: Any) -> None:
        """Visit a destroy statement node."""
        pass

    def visit_do_loop_until(self, node: Any) -> None:
        """Visit a do loop until node."""
        pass

    def visit_do_loop_while(self, node: Any) -> None:
        """Visit a do loop while node."""
        pass

    def visit_do_until_loop(self, node: Any) -> None:
        """Visit a do until loop node."""
        pass

    def visit_do_while_loop(self, node: Any) -> None:
        """Visit a do while loop node."""
        pass

    def visit_dynamic_method_invocation(self, node: Any) -> None:
        """Visit a dynamic method invocation node."""
        pass

    def visit_else(self, node: Any) -> None:
        """Visit an else node."""
        pass

    def visit_else_if(self, node: Any) -> None:
        """Visit an else if node."""
        pass

    def visit_else_on_line(self, node: Any) -> None:
        """Visit an else on line node."""
        pass

    def visit_end_forward(self, node: Any) -> str:
        """Visit an end forward node."""
        return ""

    def visit_event_attribute(self, node: Any) -> None:
        """Visit an event attribute node."""
        pass

    def visit_event_declaration(self, node: Any) -> None:
        """Visit an event declaration node."""
        pass

    def visit_event_invocation(self, node: Any) -> None:
        """Visit an event invocation node."""
        pass

    def visit_event_long(self, node: Any) -> None:
        """Visit an event long node."""
        pass

    def visit_event_name(self, node: Any) -> None:
        """Visit an event name node."""
        pass

    def visit_event_reference_name(self, node: Any) -> None:
        """Visit an event reference name node."""
        pass

    def visit_event_triggering_or_posting(self, node: Any) -> None:
        """Visit an event triggering or posting node."""
        pass

    def visit_event_type(self, node: Any) -> None:
        """Visit an event type node."""
        pass

    def visit_event_word(self, node: Any) -> None:
        """Visit an event word node."""
        pass

    def visit_execute_procedure(self, node: Any) -> None:
        """Visit an execute procedure node."""
        pass

    def visit_exit_statement(self, node: Any) -> str:
        """Visit an exit statement node."""
        return ""

    def visit_export(self, node: Any) -> None:
        """Visit an export node."""
        pass

    def visit_expression(self, node: Any) -> None:
        """Visit an expression node."""
        pass

    def visit_expression_action(self, node: Any) -> None:
        """Visit an expression action node."""
        pass

    def visit_expression_list(self, node: Any) -> None:
        """Visit an expression list node."""
        pass

    def visit_expression_operator(self, node: Any) -> str:
        """Visit an expression operator node."""
        return ""
