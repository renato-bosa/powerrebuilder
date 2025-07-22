"""Type resolution system for PowerBuilder custom types and enums.

This module provides comprehensive type resolution, validation, and
management for custom types, enums, and structures defined in PowerBuilder code.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from ...model.ast import ASTNode, CustomType, Literal, TypeCategory


class ResolutionPhase:
    """Type resolution phases."""

    DECLARATION = "declaration"
    REFERENCE = "reference"
    VALIDATION = "validation"


@dataclass
class TypeDependency:
    """Represents a dependency between types."""

    dependent_type: str
    dependency: str
    dependency_kind: str  # 'parent', 'field', 'enum_value'
    location: str | None = None


@dataclass
class ResolutionContext:
    """Context for type resolution."""

    current_namespace: list[str] = field(default_factory=list)
    type_registry: dict[str, CustomType] = field(default_factory=dict)
    unresolved_references: set[str] = field(default_factory=set)
    dependencies: list[TypeDependency] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_type(self, name: str, custom_type: CustomType) -> None:
        """Add a type to the registry."""
        full_name = self.get_full_name(name)
        self.type_registry[full_name] = custom_type

    def get_type(self, name: str) -> CustomType | None:
        """Get a type from the registry."""
        full_name = self.get_full_name(name)
        return self.type_registry.get(full_name)

    def get_full_name(self, name: str) -> str:
        """Get fully qualified name."""
        if "." in name:
            return name
        if self.current_namespace:
            return ".".join([*self.current_namespace, name])
        return name


logger = logging.getLogger(__name__)


class TypeResolver:
    """Resolves and validates custom types, enums, and structures.

    - Type declaration collection
    - Reference resolution
    - Inheritance validation
    - Enum value computation
    - Circular dependency detection
    """

    def __init__(self) -> None:
        self.context = ResolutionContext()

    def resolve_types(self, ast: ASTNode) -> ResolutionContext:
        """Main entry point for type resolution.

        Performs multi-phase resolution:
        1. Collect all type declarations
        2. Resolve type references
        3. Validate types
        """
        logger.info("Starting type resolution")

        # Phase 1: Collect declarations
        self._collect_declarations(ast)

        # Phase 2: Resolve references
        self._resolve_references()

        # Phase 3: Validate types
        self._validate_types()

        # Phase 4: Compute enum values
        self._compute_enum_values()

        logger.info(
            "Type resolution complete. Found %s types", len(self.context.type_registry)
        )
        return self.context

    def _collect_declarations(self, node: Any) -> None:
        """Collect all type declarations."""
        # Handle CustomType and its subclasses
        if isinstance(node, CustomType):
            self._process_custom_type(node)
            return

        # Handle tree nodes from Lark parser
        if hasattr(node, "data") and hasattr(node, "children"):
            # Check if this is a type declaration node
            if node.data == "type_declaration":
                self._process_type_declaration_node(node)

            # Recursively process children
            for child in node.children:
                self._collect_declarations(child)

        # Handle AST nodes with get_children method
        elif hasattr(node, "get_children"):
            for child in node.get_children():
                self._collect_declarations(child)

    def _process_custom_type(self, custom_type: CustomType) -> None:
        """Process a CustomType object that was already created by the transformer."""
        logger.debug("Processing custom type: %s", custom_type.name)

        # Handle parent type dependencies
        if hasattr(custom_type, "parent_type") and custom_type.parent_type:
            self.context.dependencies.append(
                TypeDependency(
                    dependent_type=custom_type.name,
                    dependency=custom_type.parent_type,
                    dependency_kind="parent",
                ),
            )

        # Process EnumeratedType - check for 'values' attribute
        if hasattr(custom_type, "values") and hasattr(custom_type, "get_value"):
            # EnumeratedType already has values populated
            for name, value in custom_type.values.items():
                custom_type.fields[name] = {
                    "type": "integer",
                    "value": value,
                    "ordinal": list(custom_type.values.keys()).index(name),
                }

        # Process StructureType - check for 'fields' attribute
        elif hasattr(custom_type, "fields") and hasattr(custom_type, "get_field"):
            # StructureType already has fields populated
            for field in custom_type.fields:
                field_type = str(field.type) if hasattr(field, "type") else "any"
                custom_type.fields[field.name] = {
                    "type": field_type,
                    "array_bounds": field.array_bounds
                    if hasattr(field, "array_bounds")
                    else None,
                }

                # Track dependencies on custom types
                if self._is_custom_type(field_type):
                    self.context.dependencies.append(
                        TypeDependency(
                            dependent_type=custom_type.name,
                            dependency=field_type,
                            dependency_kind="field",
                        ),
                    )

        self.context.add_type(custom_type.name, custom_type)

    def _process_type_declaration_node(self, _node: Any) -> None:
        """Process a type declaration node from the parser tree."""
        logger.debug("Processing type declaration node from parser")
        # This handles raw parser nodes before transformation
        # The transformer should handle creating the actual type objects
        # No processing needed here - delegation to transformer is intentional

    def _resolve_field_type(self, type_node: Any) -> str:
        """Resolve field type to string representation."""
        if isinstance(type_node, str):
            return type_node
        if hasattr(type_node, "name"):
            return type_node.name
        return str(type_node)

    def _is_custom_type(self, type_name: str) -> bool:
        """Check if a type is a custom type."""
        # Basic types that are not custom
        basic_types = {
            "integer",
            "long",
            "string",
            "boolean",
            "real",
            "double",
            "decimal",
            "date",
            "time",
            "datetime",
            "blob",
            "any",
        }
        return type_name.lower() not in basic_types

    def _resolve_references(self) -> None:
        """Resolve all type references."""
        logger.debug("Resolving type references")

        # Build dependency graph
        dep_graph = self._build_dependency_graph()

        # Topological sort to resolve in order
        sorted_types = self._topological_sort(dep_graph)

        # Resolve each type
        for type_name in sorted_types:
            self._resolve_type_references(type_name)

    def _build_dependency_graph(self) -> dict[str, set[str]]:
        """Build dependency graph from dependencies."""
        graph = {}

        for dep in self.context.dependencies:
            if dep.dependent_type not in graph:
                graph[dep.dependent_type] = set()
            graph[dep.dependent_type].add(dep.dependency)

        return graph

    def _topological_sort(self, graph: dict[str, set[str]]) -> list[str]:
        """Perform topological sort on dependency graph."""
        # Add all types to graph
        all_types = set(self.context.type_registry.keys())
        for type_name in all_types:
            if type_name not in graph:
                graph[type_name] = set()

        # Kahn's algorithm
        in_degree = dict.fromkeys(all_types, 0)
        for node in graph:
            for dep in graph[node]:
                if dep in in_degree:
                    in_degree[dep] += 1

        queue = [node for node in all_types if in_degree[node] == 0]
        sorted_list = []

        while queue:
            node = queue.pop(0)
            sorted_list.append(node)

            for dep in graph.get(node, set()):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)

        # Check for cycles
        if len(sorted_list) != len(all_types):
            self.context.errors.append(
                "Circular dependency detected in type definitions"
            )

        return sorted_list

    def _resolve_type_references(self, type_name: str) -> None:
        """Resolve references for a specific type."""
        custom_type = self.context.get_type(type_name)
        if not custom_type:
            return

        # Resolve parent type
        if custom_type.parent_type:
            parent = self.context.get_type(custom_type.parent_type)
            if parent:
                # Inherit fields from parent
                for field_name, field_info in parent.fields.items():
                    if field_name not in custom_type.fields:
                        custom_type.fields[field_name] = field_info.copy()
            else:
                self.context.unresolved_references.add(custom_type.parent_type)

    def _validate_types(self) -> None:
        """Validate all types."""
        logger.debug("Validating types")

        for type_name, custom_type in self.context.type_registry.items():
            self._validate_type(type_name, custom_type)

    def _validate_type(self, type_name: str, custom_type: CustomType) -> None:
        """Validate a single type."""
        # Check for unresolved parent
        if (
            custom_type.parent_type
            and custom_type.parent_type in self.context.unresolved_references
        ):
            self.context.errors.append(
                f"Type '{type_name}' references undefined parent type '{custom_type.parent_type}'",
            )

        # Validate enum values
        if custom_type.category == TypeCategory.ENUM:
            self._validate_enum(type_name, custom_type)

        # Validate structure fields
        elif custom_type.category == TypeCategory.STRUCTURE:
            self._validate_structure(type_name, custom_type)

    def _validate_enum(self, type_name: str, enum_type: CustomType) -> None:
        """Validate enum type."""
        # Check for duplicate values
        values = set()
        for field_info in enum_type.fields.values():
            if "value" in field_info and field_info["value"] is not None:
                if field_info["value"] in values:
                    self.context.errors.append(
                        f"Enum '{type_name}' has duplicate value {field_info['value']}",
                    )
                values.add(field_info["value"])

    def _validate_structure(self, type_name: str, struct_type: CustomType) -> None:
        """Validate structure type."""
        # Check field types
        for field_name, field_info in struct_type.fields.items():
            field_type = field_info.get("type")
            if field_type and self._is_custom_type(field_type):
                if not self.context.get_type(field_type):
                    self.context.errors.append(
                        f"Structure '{type_name}' field '{field_name}' references undefined type '{field_type}'",
                    )

    def _compute_enum_values(self) -> None:
        """Compute enum values for enums without explicit values."""
        logger.debug("Computing enum values")

        for custom_type in self.context.type_registry.values():
            if custom_type.category == TypeCategory.ENUM:
                self._compute_enum_type_values(custom_type)

    def _compute_enum_type_values(self, enum_type: CustomType) -> None:
        """Compute values for a single enum type."""
        last_value = -1

        for field_name in sorted(
            enum_type.fields.keys(), key=lambda x: enum_type.fields[x].get("ordinal", 0)
        ):
            field_info = enum_type.fields[field_name]

            if field_info.get("value") is None:
                # Assign next sequential value
                field_info["value"] = last_value + 1
            else:
                # Parse and evaluate expression if needed
                field_info["value"] = self._evaluate_enum_expression(
                    field_info["value"]
                )

            last_value = field_info["value"]

    def _evaluate_enum_expression(self, expr: Any) -> int:
        """Evaluate enum value expression."""
        if isinstance(expr, int):
            return expr
        if isinstance(expr, str) and expr.isdigit():
            return int(expr)
        if isinstance(expr, Literal) and hasattr(expr, "value"):
            return int(expr.value)

        # Support for complex expressions using expression evaluator
        try:
            # Create context with any defined enum values
            from ...model.expressions.evaluator import (
                EvaluationContext,
                ExpressionEvaluator,
            )

            context = EvaluationContext()
            # Add any enum values that have been resolved
            if hasattr(self, "_resolved_enum_values"):
                context.variables.update(self._resolved_enum_values)

            # If expr is already an Expression object, evaluate it
            if hasattr(expr, "__class__") and "Expression" in expr.__class__.__name__:
                evaluator = ExpressionEvaluator(context)
                result = evaluator.evaluate(expr)
                if isinstance(result, int | float):
                    return int(result)

        except Exception as e:
            logger.debug("Failed to evaluate complex expression: %s", e)

        logger.warning("Unable to evaluate enum expression: %s, defaulting to 0", expr)
        return 0
