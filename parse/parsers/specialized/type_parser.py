"""Enhanced type parser for PowerBuilder custom types and enums.

This module provides parsing capabilities for PowerBuilder custom types,
including enumerated types, structures, and user-defined types.
"""

import logging

from lark import Token, Tree

from model.expressions import (Variable)
from src.model.ast.nodes.declarations import CustomType, TypeCategory

logger = logging.getLogger(__name__)


class EnumeratedType(CustomType):
    """Represents an enumerated type with values."""

    def __init__(self, name: str, values: dict[str, int], parent_type: str | None = None) -> None:


        """Initialize enumerated type.

        Args:
            name: Type name
            values: Dictionary of enum value names to their numeric values
            parent_type: Parent type if inherited
        """
        super().__init__(name, TypeCategory.CUSTOM, parent_type)
        self.values = values
        self.is_enumerated = True

    def get_value(self, name: str) -> int | None:




        """Get numeric value for enum name."""
        return self.values.get(name)

    def is_valid_value(self, name: str) -> bool:




        """Check if a name is a valid enum value."""
        return name in self.values


class StructureType(CustomType):
    """Represents a structure type with fields."""

    def __init__(self, name: str, fields: list[Variable], parent_type: str | None = None) -> None:


        """Initialize structure type.

        Args:
            name: Type name
            fields: List of field variables
            parent_type: Parent type if inherited
        """
        super().__init__(name, TypeCategory.CUSTOM, parent_type)
        self.fields = fields
        self.field_map = {field.name: field for field in fields}

    def get_field(self, name: str) -> Variable | None:




        """Get field by name."""
        return self.field_map.get(name)

    def has_field(self, name: str) -> bool:




        """Check if structure has a field."""
        return name in self.field_map


class TypeParser:
    """Parser for PowerBuilder custom types and enums."""

    def __init__(self) -> None:




        """Initialize type parser."""
        self.types: dict[str, CustomType | EnumeratedType | StructureType] = {}

    def parse_type_declaration(self, tree: Tree) -> CustomType | EnumeratedType | StructureType:




        """Parse a type declaration tree.

        Args:
            tree: Lark parse tree for type declaration

        Returns:
            Parsed type object
        """
        # Extract basic information
        name = None
        parent_type = None
        is_global = False
        is_enumerated = False
        fields = []
        enum_values = {}

        # Parse tree structure
        for child in tree.children:
            if isinstance(child, Token):
                if child.type == "IDENTIFIER" and name is None:
                    name = str(child)
                elif child.value.lower() == "global":
                    is_global = True
                elif child.value.lower() == "enumerated":
                    is_enumerated = True

            elif isinstance(child, Tree):
                if child.data == "from_clause":
                    parent_type = self._extract_parent_type(child)
                elif child.data == "type_body":
                    if is_enumerated:
                        enum_values = self._parse_enum_body(child)
                    else:
                        fields = self._parse_structure_body(child)

        # Create appropriate type object
        if is_enumerated:
            type_obj = EnumeratedType(name, enum_values, parent_type)
        elif fields:
            type_obj = StructureType(name, fields, parent_type)
        else:
            type_obj = CustomType(name, TypeCategory.CUSTOM, parent_type)

        type_obj.is_global = is_global

        # Store in registry
        self.types[name] = type_obj

        return type_obj

    def _extract_parent_type(self, tree: Tree) -> str | None:




        """Extract parent type from FROM clause.

        Args:
            tree: FROM clause tree

        Returns:
            Parent type name
        """
        for child in tree.children:
            if isinstance(child, Token) and child.type == "IDENTIFIER":
                return str(child)
            elif isinstance(child, Tree) and child.data == "custom_type":
                # Handle qualified names (e.g., namespace.typename)
                parts = []
                for token in child.children:
                    if isinstance(token, Token) and token.type == "IDENTIFIER":
                        parts.append(str(token))
                return ".".join(parts)
        return None

    def _parse_enum_body(self, tree: Tree) -> dict[str, int]:




        """Parse enumerated type body.

        Args:
            tree: Type body tree

        Returns:
            Dictionary of enum values
        """
        enum_values = {}
        next_value = 0

        # Track enum values for expression evaluation
        self._current_enum_values = {}

        for child in tree.children:
            if isinstance(child, Tree) and child.data == "enum_value":
                name, value = self._parse_enum_value(child, next_value)
                if name:
                    enum_values[name] = value
                    self._current_enum_values[name] = value
                    next_value = value + 1

        # Clear the temporary tracking
        self._current_enum_values = None

        return enum_values

    def _parse_enum_value(self, tree: Tree, default_value: int) -> tuple[str | None, int]:




        """Parse a single enum value.

        Args:
            tree: Enum value tree
            default_value: Default numeric value if not specified

        Returns:
            Tuple of (name, value)
        """
        name = None
        value = default_value

        for i, child in enumerate(tree.children):
            if isinstance(child, Token) and child.type == "IDENTIFIER":
                name = str(child)
            elif isinstance(child, Token) and child.value == "=":
                # Next child should be the value
                if i + 1 < len(tree.children):
                    next_child = tree.children[i + 1]
                    if isinstance(next_child, Token) and next_child.type == "INT":
                        value = int(next_child)
                    elif isinstance(next_child, Tree) and next_child.data == "expression":
                        # Evaluate constant expression
                        try:
                            from model.expressions.evaluator import (
                                EvaluationContext,
                                ExpressionEvaluator,
                            )
                            from parse.ast_to_model import ASTToModelTransformer

                            # Transform the parse tree to model expression
                            transformer = ASTToModelTransformer()
                            expr = transformer.transform_expression(next_child)

                            # Create context with enum values seen so far
                            context = EvaluationContext()
                            if hasattr(self, "_current_enum_values"):
                                context.variables.update(self._current_enum_values)

                            # Evaluate the expression
                            evaluator = ExpressionEvaluator(context)
                            value = evaluator.evaluate(expr)

                            if isinstance(value, (int, float)):
                                value = int(value)
                            else:
                                logger.warning(f"Enum expression evaluated to non-numeric value: {value}")
                                value = None
                        except Exception as e:
                            logger.warning(f"Failed to evaluate enum expression: {e}")
                            value = None

        return name, value

    def _parse_structure_body(self, tree: Tree) -> list[Variable]:




        """Parse structure type body.

        Args:
            tree: Type body tree

        Returns:
            List of field variables
        """
        fields = []

        for child in tree.children:
            if isinstance(child, Tree) and child.data in ["type_member", "field_declaration"]:
                field = self._parse_field(child)
                if field:
                    fields.append(field)

        return fields

    def _parse_field(self, tree: Tree) -> Variable | None:




        """Parse a structure field.

        Args:
            tree: Field declaration tree

        Returns:
            Variable object for the field
        """
        name = None
        type_name = None
        initial_value = None
        visibility = "public"  # Default visibility

        for child in tree.children:
            if isinstance(child, Token):
                if child.type == "IDENTIFIER":
                    if type_name is None and child.value.lower() in ["integer", "string", "boolean", "long", "decimal", "real", "date", "time", "datetime"]:
                        type_name = str(child)
                    elif name is None:
                        name = str(child)
                elif child.type == "TYPE_NAME":
                    type_name = str(child)
                elif child.value.lower() in ["public", "private", "protected"]:
                    visibility = str(child).lower()

            elif isinstance(child, Tree):
                if child.data == "expression":
                    # Parse initial value expression
                    try:
                        from model.expressions.evaluator import (
                            EvaluationContext,
                            ExpressionEvaluator,
                        )
                        from parse.ast_to_model import ASTToModelTransformer

                        # Transform the parse tree to model expression
                        transformer = ASTToModelTransformer()
                        expr = transformer.transform_expression(child)

                        # Create context for evaluation
                        context = EvaluationContext()

                        # Evaluate the expression
                        evaluator = ExpressionEvaluator(context)
                        initial_value = evaluator.evaluate(expr)

                        # Convert to appropriate type if needed
                        if initial_value is not None:
                            logger.debug(f"Successfully evaluated initial value expression: {initial_value}")
                    except Exception as e:
                        logger.warning(f"Failed to evaluate initial value expression: {e}")
                        initial_value = None
                elif child.data == "visibility_modifier":
                    for token in child.children:
                        if isinstance(token, Token):
                            visibility = str(token).lower()
                            break

        if name and type_name:
            return Variable(
                name=name, type=type_name, initial_value=initial_value, visibility=visibility,
            )

        return None

    def get_type(self, name: str) -> CustomType | EnumeratedType | StructureType | None:




        """Get a registered type by name.

        Args:
            name: Type name

        Returns:
            Type object or None if not found
        """
        return self.types.get(name)

    def register_type(self, type_obj: CustomType | EnumeratedType | StructureType) -> None:




        """Register a type in the parser.

        Args:
            type_obj: Type object to register
        """
        self.types[type_obj.name] = type_obj
