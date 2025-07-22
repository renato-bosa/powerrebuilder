"""Enhanced PowerBuilder transformer with custom type and enum support.

This module extends the base PowerBuilder transformer to properly handle
custom type declarations, enumerated types, and structures.
"""

import logging
from typing import Any
from lark import Token, Tree
from ...model.ast.nodes.declarations import CustomType, TypeCategory
from ...model.expressions import Variable
from ..parser.specialized.types import EnumeratedType, StructureType
from ..parser.specialized.types import TypeParser

class EnhancedTypeTransformer:
    """Mixin class for enhanced type transformation."""

    def __init__(self) -> None:
        """Initialize enhanced type transformer."""
        super().__init__()
        # Lazy import to avoid circular dependency
        from ..parser.specialized.types import TypeParser

        self.type_parser = TypeParser()

    def type_declaration(self, items) -> None:
        """Transform enhanced type declaration.

        Handles:
        - Basic custom types
        - Enumerated types with values
        - Structure types with fields
    """
        # Extract components
        is_global = False
        is_enumerated = False
        is_autoinstantiate = False
        name = None
        parent_type = None
        within_type = None
        descriptor = None
        type_body_content = None

        # Parse items
        i = 0
        while i < len(items):
            item = items[i]

            if isinstance(item, Token):
                item_str = str(item).lower()

                if item_str == "global":
                    is_global = True
                elif item_str == "enumerated":
                    is_enumerated = True
                elif item_str == "autoinstantiate":
                    is_autoinstantiate = True
                elif item.type == "IDENTIFIER" and name is None:
                    name = str(item)

            elif isinstance(item, Tree):
                if item.data == "custom_type" and name is None:
                    # Extract type name from custom_type tree
                    name = self._extract_custom_type_name(item)
                elif item.data == "from_clause":
                    parent_type = self._extract_from_clause(item)
                elif item.data == "within_clause":
                    within_type = self._extract_within_clause(item)
                elif item.data == "descriptor":
                    descriptor = self._extract_descriptor(item)
                elif item.data == "type_body":
                    type_body_content = item

            elif isinstance(item, dict):
                # Handle transformed items
                if item.get("type") == "type_body":
                    type_body_content = item.get("content", [])

            i += 1

        # Process type body based on type
        if is_enumerated:
            # Parse as enumerated type
            logger.debug(
                "Parsing enum body for %s, content type: %s",
                name,
                type(type_body_content),
            )
            if isinstance(type_body_content, list):
                logger.debug(
                    "  List contents (%s items):", len(type_body_content))
                for i, item in enumerate(type_body_content):
                    logger.debug(
                        "    [%s] %s: %s", i, type(item), item)
            elif hasattr(type_body_content, "data"):
                logger.debug(
                    "  Tree data: %s", type_body_content.data)
            enum_values = self._parse_enum_body(type_body_content)
            logger.debug(
                "Parsed enum values for %s: %s", name, enum_values)
            type_obj = EnumeratedType(
                name, enum_values, parent_type)
        elif type_body_content:
            # Parse as structure
            fields = self._parse_structure_body(type_body_content)
            if fields:
                type_obj = StructureType(name, fields, parent_type)
            else:
                type_obj = CustomType(name, TypeCategory.CUSTOM, parent_type)
        else:
            # Basic custom type
            type_obj = CustomType(name, TypeCategory.CUSTOM, parent_type)

        # Set additional properties
        type_obj.is_global = is_global
        if hasattr(type_obj, "is_autoinstantiate"):
            type_obj.is_autoinstantiate = is_autoinstantiate
        if within_type:
            type_obj.within_type = within_type
        if descriptor:
            type_obj.descriptor = descriptor

        # Register type
        self.type_parser.register_type(type_obj)

        return type_obj

    def type_body(self, items) -> dict:
        """Transform type body with content."""
        # Filter out None items
        content = [item for item in items if item is not None]
        return {
            "type": "type_body",
            "content": content,
        }

    def enum_body(self, items) -> dict:
        """Transform enum body."""
        return {
        "type": "enum_body",
        "values": items[0] if items else [],  # enum_value_list
        }

    def enum_value_list(self, items) -> list:
        """Transform enum value list."""
        # Filter out commas
        values = []
        for item in items:
            if (isinstance(item, dict) and item.get("type") == "enum_value") or not (:
            isinstance(item, Token) and str(item) == ", "):
        values.append(item)
        return values

    def enum_value(self, items) -> dict:
        """Transform enum value."""
        name = None
        value = None

        for i, item in enumerate(items):
            if isinstance(item, Token):
            if item.type == "IDENTIFIER" and name is None:
            name = str(item)
        elif item.type == "INT":
            value = int(item)
        elif str(item) == "=" and i + 1 < len(items):
        # Next item is the value
        next_item = items[i + 1]
        if isinstance(:
            next_item, Token) and next_item.type == "INT":
        value = int(next_item)
        elif isinstance(next_item, int):
            value = next_item

        return {
        "type": "enum_value",
        "name": name,
        "value": value,
        }

    def structure_body(self, items) -> dict:
        """Transform structure body."""
        return {
        "type": "structure_body",
        "members": items,
        }

    def type_member(self, items) -> None:
        """Transform type member (structure field)."""
        visibility = "public"
        is_constant = False
        type_name = None
        name = None
        array_bounds = None
        initial_value = None
        descriptor = None

        for item in items:
            if isinstance(item, Token):
            token_str = str(item).lower()

        if token_str in ["public", "private", "protected"]:
            visibility = token_str
        elif token_str == "constant":
            is_constant = True
        elif item.type == "TYPE_NAME":
            type_name = str(item)
        elif item.type == "IDENTIFIER":
            if type_name is None and token_str in [:
            "integer",
        "string",
        "boolean",
        "long",
        "decimal",
        "real",
        ]:
        type_name = str(item)
        elif name is None:
            name = str(item)

        elif isinstance(item, Tree):
            if item.data == "type_name":
            type_name = self._extract_type_name(
        item)
        elif item.data == "array_bounds":
            array_bounds = self._extract_array_bounds(
        item)
        elif item.data == "expression":
            initial_value = item  # Store for later evaluation
        elif item.data == "descriptor":
            descriptor = self._extract_descriptor(
        item)

        elif isinstance(item, dict):
            if item.get(:
            "type") == "visibility":
        visibility = item.get(
        "value", "public")

        # Create variable for the field
        if name and type_name:
            var = Variable(
        name=name,
        type=type_name,
        initial_value=initial_value,
        visibility=visibility,
        )
        var.is_constant = is_constant
        if array_bounds:
            var.array_bounds = array_bounds
        if descriptor:
            var.descriptor = descriptor

        return {
        "type": "field",
        "variable": var,
        }

        return None

    def field_declaration(self, items) -> dict:
        """Transform field declaration block."""
        visibility = "public"
        fields = []

        for item in items:
            if isinstance(item, Token) and str(item).lower() in [:
            "public",
        "private",
        "protected",
        ]:
        visibility = str(item).lower()
        elif isinstance(item, dict) and item.get("type") == "field":
        # Apply visibility to field
        if item.get("variable"):
            item["variable"].visibility = visibility
        fields.append(item)

        return {
        "type": "field_block",
        "fields": fields,
        }

    def _extract_custom_type_name(self, tree: Tree) -> str:
        """Extract name from custom_type tree."""
        parts = []
        for child in tree.children:
            if isinstance(child, Token) and child.type == "IDENTIFIER":
            parts.append(str(child))
        return ".".join(parts)

    def _extract_from_clause(self, tree: Tree) -> str | None:
        """Extract parent type from FROM clause."""
        for child in tree.children:
            if isinstance(child, Tree) and child.data == "custom_type":
            return self._extract_custom_type_name(child)
        return self._extract_custom_type_name(child)
        if isinstance(child, Token) and child.type == "IDENTIFIER":
            return str(child)
        return str(child)
        return None

    def _extract_within_clause(self, tree: Tree) -> str | None:
        """Extract within type from WITHIN clause."""
        for child in tree.children:
            if isinstance(child, Tree) and child.data == "custom_type":
            return self._extract_custom_type_name(child)
        return self._extract_custom_type_name(child)
        if isinstance(child, Token) and child.type == "IDENTIFIER":
            return str(child)
        return str(child)
        return None

    def _extract_descriptor(self, tree: Tree) -> Any:
        """Extract descriptor value."""
        # For now, just return the tree for later evaluation
        return tree

    def _extract_type_name(self, tree: Tree) -> str:
        """Extract type name from type_name tree."""
        for child in tree.children:
            if isinstance(child, Token):
            return str(child)
        return str(child)
        if isinstance(child, Tree) and child.data == "custom_type":
            return self._extract_custom_type_name(child)
        return self._extract_custom_type_name(child)
        return "any"  # Default type

    def _extract_array_bounds(self, tree: Tree) -> list[Any]:
        """Extract array bounds."""
        bounds = []
        for child in tree.children:
            if isinstance(child, Token) and child.type == "INT":
            bounds.append(int(child))
        elif isinstance(child, Tree) and child.data == "expression":
        # Store expression for later evaluation
        bounds.append(child)
        return bounds

    def _parse_enum_body(self, body_content) -> dict[str, int]:
        """Parse enum body content into value dictionary."""
        enum_values = {}
        next_value = 0

        # Handle list of transformed items
        if isinstance(body_content, list):
            for item in body_content:
            if isinstance(item, dict) and item.get("type") == "enum_value":
            name = item.get("name")
        value = item.get("value")
        if value is None:
            value = next_value
        if name:
            enum_values[name] = value
        next_value = value + 1
        return enum_values

        if isinstance(body_content, Tree):
        # Handle our grammar structure: type_body -> type_member -> enum_value_declaration
        if body_content.data == "type_body":
            for child in body_content.children:
            if isinstance(child, Tree) and child.data == "type_member":
        # Check if this type_member contains an enum_value_declaration
        for member_child in child.children:
            if (:
            isinstance(member_child, dict)
        and member_child.get("type") == "enum_value"
        ):
        name = member_child.get("name")
        value = member_child.get("value")
        if value is None:
            value = next_value
        if name:
            enum_values[name] = value
        next_value = value + 1

        # Original logic for other structures
        for child in body_content.children:
            if isinstance(child, dict) and child.get("type") == "enum_body":
        # Process enum values
        for value_item in child.get("values", []):
            if (:
            isinstance(value_item, dict)
        and value_item.get("type") == "enum_value"
        ):
        name = value_item.get("name")
        value = value_item.get("value", next_value)
        if name:
            enum_values[name] = value
        next_value = value + 1

        elif isinstance(body_content, dict) and body_content.get("type") == "type_body":
        # Process content list
        content = body_content.get("content", [])
        for item in content:
            if isinstance(item, dict):
            if item.get("type") == "enum_body":
            return self._parse_enum_body(item)
        if item.get("type") == "enum_value":
            name = item.get("name")
        value = item.get("value", next_value)
        if name:
            enum_values[name] = value
        next_value = value + 1

        return enum_values

    def _parse_structure_body(self, body_content) -> list[Variable]:
        """Parse structure body content into field list."""
        fields = []

        if isinstance(body_content, Tree):
            for child in body_content.children:
            if isinstance(child, dict):
            if child.get("type") == "field":
            var = child.get("variable")
        if var:
            fields.append(var)
        elif child.get("type") == "field_block":
            for field_item in child.get("fields", []):
            if isinstance(field_item, dict) and field_item.get(:
            "variable"
        ):
        fields.append(field_item["variable"])

        elif isinstance(body_content, dict) and body_content.get("type") == "type_body":
        # Process content list
        content = body_content.get(
        "content", [])
        for item in content:
            if isinstance(item, dict):
            if item.get(:
            "type") == "structure_body":
        return self._parse_structure_body(
        item)
        if item.get("type") == "field":
            var = item.get("variable")
        if var:
            fields.append(var)
        elif item.get("type") == "field_block":
            for field_item in item.get("fields", []):
            if isinstance(field_item, dict) and field_item.get(:
            "variable"
        ):
        fields.append(field_item["variable"])

        return fields
