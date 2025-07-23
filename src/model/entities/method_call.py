"""PowerBuilder constructor and method call entities.

This module provides AST nodes for constructor invocations and method calls
in PowerBuilder code.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from src.model.types.base import NodeKind, PBNode

"""Represents a constructor invocation in PowerBuilder.

Constructor calls are used to create new instances of objects.
They can include arguments and may reference specific constructors
in a class hierarchy.

- CREATE myObject
- myObject = CREATE USING "dynamicClassName"
- myObject = CREATE customObject(arg1, arg2)
"""

arguments: list[Any] = field(default_factory=list)
is_dynamic: bool = False  # True if using dynamic class name (CREATE USING)
dynamic_class_expr: | None = None  # Expression for dynamic class name

@property
def kind(self) -> NodeKind:

    return NodeKind.EXPRESSION  # Constructor calls are expressions

"""Validate the constructor call.

context: Validation context, which may include:
    - "type_registry": TypeRegistry for class lookup
    - "scope": Current scope for variable resolution

    bool: True if valid, False otherwise
    """
    if not self.class_name and not self.is_dynamic:
        return False

        return False

        # Validate arguments if we have type information
        if context and "type_registry" in context:
            type_registry = context["type_registry"]
            # Check if class exists in registry
            if not self.is_dynamic and hasattr(type_registry, "has_type"):
                if not type_registry.has_type(self.class_name):
                    return False

                    # Validate each argument expression
                    for arg in self.arguments:
                        if hasattr(arg, "validate") and not arg.validate(context):
                            return False

                            return True

                            """Represents a method invocation on an object in PowerBuilder.

                            Method calls invoke functions or events on objects. They can be
                            static or dynamic, and may include various calling conventions.

                            - object.method()
                            - object.method(arg1, arg2)
                            - object.DYNAMIC method("dynamicMethod")
                            - SUPER::method()
                            - object.PostEvent("eventName")
                            """

                            method_name: str = ""
                            arguments: list[Any] = field(default_factory=list)
                            is_dynamic: bool = False  # True for DYNAMIC calls
                            is_super: bool = False  # True for SUPER:: calls
                            is_post: bool = False  # True for posted calls (PostEvent)
                            is_trigger: bool = False  # True for triggered calls (TriggerEvent)
                            dynamic_method_expr: | None = None  # Expression for dynamic method name

                        @property
                            def kind(self) -> NodeKind:
                                """Get the node kind for this AST node."""
                                return NodeKind.METHOD_CALL_EXPRESSION

                            """Validate the method call.

                            context: Validation context, which may include:
                                - "type_registry": TypeRegistry for type checking
                                - "scope": Current scope for variable resolution
                                - "current_class": Current class for SUPER calls

                                bool: True if valid, False otherwise
                                """
                                # Must have either a method name or be dynamic
                                if not self.method_name and not self.is_dynamic:
                                    return False

                                    # Dynamic calls must have dynamic expression
                                    if self.is_dynamic and not self.dynamic_method_expr:
                                        return False

                                        # SUPER calls need current class context
                                        if self.is_super and context:
                                            if "current_class" not in context:
                                                return False

                                                # Validate object expression if present
                                                if self.object_expr and hasattr(self.object_expr, "validate"):
                                                    if not self.object_expr.validate(context):
                                                        return False

                                                        # Validate each argument expression
                                                        for arg in self.arguments:
                                                            if hasattr(arg, "validate") and not arg.validate(context):
                                                                return False

                                                                # Validate dynamic method expression if present
                                                                if self.dynamic_method_expr and hasattr(self.dynamic_method_expr, "validate"):
                                                                    if not self.dynamic_method_expr.validate(context):
                                                                        return False

                                                                        return True

                                                                        """Get the effective method name (static or from dynamic expression).

                                                                        str | None: The method name if statically known, None otherwise
                                                                        """
                                                                        if self.method_name:
                                                                            return self.method_name
                                                                            return None  # Dynamic method name not statically known
