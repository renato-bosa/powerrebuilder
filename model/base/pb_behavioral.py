"""PowerBuilder behavioral model.

This module provides classes for behavioral nodes including aliases, libraries,
and behavioral options used in PowerBuilder.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..utils.base import PBNode


@dataclass
class PBBehavioralNode(PBNode):
    """Base class for behavioral nodes."""

    name: str = ""


@dataclass
class PBAccessModifierDefinerNode(PBNode):
    """Access modifier definer node."""

    access_modifier: str = "public"


@dataclass
class PBAccessModifierNode(PBNode):
    """Access modifier node."""

    access_modifier: str = "public"


class BehavioralOptionType(Enum):
    """Behavioral option types."""

    FORWARD = "forward"
    RPCFUNC = "rpcfunc"
    DYNAMIC = "dynamic"
    INDIRECT = "indirect"
    STATIC = "static"
    SYSTEM = "system"  # For system libraries


@dataclass
class PBBehavioralAliasNode(PBNode):
    """Behavioral alias node.

    Represents alias declarations like 'Alias For "alias_name"'.
    """

    name: str = ""  # The alias identifier
    alias_name: str = ""  # The target name being aliased
    target: Any | None = None  # Reference to the behavioral being aliased
    # For backward compatibility with existing tests
    alias: str = ""  

    def __post_init__(self) -> None:
        """  post init  .
        """


        # Handle backward compatibility
        if self.alias and not self.alias_name:
            self.alias_name = self.alias
        if not self.name and self.alias_name:
            # If only alias_name is provided, use it as name too
            self.name = self.alias_name
        # Only raise error if both are missing
        if not self.name and not self.alias_name and not self.alias:
            # Don't raise error for empty initialization
            pass

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            TODO: Add return description
        """


        return f"alias {self.alias_name or self.alias or ""}"


@dataclass
class PBBehavioralLibraryNode(PBNode):
    """Behavioral library node.

    Represents library declarations like 'Library "library.pbl"'.
    """

    name: str = ""  # Library identifier
    library_path: str = ""  # Path to the library file
    is_system: bool = False  # True for system libraries
    # For backward compatibility with existing tests
    library_file: str = ""

    def __post_init__(self) -> None:
        """  post init  .
        """


        # Handle backward compatibility
        if self.library_file and not self.library_path:
            self.library_path = self.library_file
        if not self.library_path and not self.library_file:
            # Don't raise error for empty initialization
            pass

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            TODO: Add return description
        """


        prefix = "system library" if self.is_system else "library"
        path = self.library_path or self.library_file or ""
        return f"{prefix} {path}"


@dataclass
class PBBehavioralOptionNode(PBNode):
    """Behavioral option node.

    Represents behavioral options like FORWARD, RPCFUNC, DYNAMIC, etc.
    """

    option_type: BehavioralOptionType = None
    value: str | None = None  # Optional value for the option

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.option_type is None:
            # For backward compatibility, parse behavioral_option if it exists
            if hasattr(self, "behavioral_option") and self.behavioral_option:
                try:
                    self.option_type = BehavioralOptionType(self.behavioral_option.lower())
                except ValueError:
                    # If not a valid enum value, use FORWARD as default
                    self.option_type = BehavioralOptionType.FORWARD
                delattr(self, "behavioral_option")
            else:
                raise ValueError("PBBehavioralOptionNode requires option_type")

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            TODO: Add return description
        """


        if self.value:
            return f"{self.option_type.value} {self.value}"
        return self.option_type.value


# Additional behavioral classes for tests
@dataclass
class PBBehavioral(PBNode):
    """PowerBuilder behavioral base class."""

    name: str = ""
    access_modifier: str = "public"
    parameters: list[Any] = None
    variables: list[Any] = None
    returns: list[Any] = None
    invocations: list[Any] = None
    accesses: list[Any] = None
    # Store signature in private field
    _signature: Any = field(default=None, init=False)
    # Behavioral-specific attributes
    aliases: dict[str, PBBehavioralAliasNode] = field(default_factory=dict)
    library: PBBehavioralLibraryNode | None = None
    options: list[BehavioralOptionType] = field(default_factory=list)

    @property
    def signature(self) -> Any:


        """Getter for signature that ensures bidirectional link."""
        return self._signature

    @signature.setter
    def signature(self, value) -> None:


        """Setter for signature that ensures bidirectional link."""
        self._signature = value
        if value is not None and hasattr(value, "behavioral"):
            value.behavioral = self

    def __post_init__(self) -> None:
        """  post init  .
        """


        if self.parameters is None:
            self.parameters = []
        if self.variables is None:
            self.variables = []
        if self.returns is None:
            self.returns = []
        if self.invocations is None:
            self.invocations = []
        if self.accesses is None:
            self.accesses = []
        # Initialize empty collections for behavioral attributes
        if not hasattr(self, "aliases"):
            self.aliases = {}
        if not hasattr(self, "options"):
            self.options = []

    @property
    def is_behavioral(self) -> bool:
        """Check if behavioral.

        Returns:
            TODO: Add return description
        """

        return True

    @property
    def is_global(self) -> bool:
        """Check if global.

        Returns:
            TODO: Add return description
        """

        return self.access_modifier == "global"

    @property
    def is_private(self) -> bool:
        """Check if private.

        Returns:
            TODO: Add return description
        """

        return self.access_modifier == "private"

    @property
    def cyclomatic_complexity(self) -> int:
        """Cyclomatic complexity.

        Returns:
            TODO: Add return description
        """

        return getattr(self, "_complexity", 1)

    def add_parameter(self, param: Any) -> None:
        """Add parameter.

        Args:
            param: TODO: Add description
        """


        param.behavioral = self
        self.parameters.append(param)
        # Also add to signature if it exists
        if self._signature and hasattr(self._signature, "parameters"):
            self._signature.parameters.append(param)

    def add_return(self, ret: Any) -> None:
        """Add return.

        Args:
            ret: TODO: Add description
        """


        ret.behavioral = self
        self.returns.append(ret)

    def add_variable(self, var: Any) -> None:
        """Add variable.

        Args:
            var: TODO: Add description
        """


        var.behavioral = self
        self.variables.append(var)

    def add_access(self, access: Any) -> None:
        """Add access.

        Args:
            access: TODO: Add description
        """


        self.accesses.append(access)

    def add_invocation(self, invocation: Any) -> None:
        """Add invocation.

        Args:
            invocation: TODO: Add description
        """


        self.invocations.append(invocation)

    def get_accessed_attributes(self) -> list[Any]:
        """Get accessed attributes.

        Returns:
            TODO: Add return description
        """


        return self.accesses

    def get_outgoing_invocations(self) -> list[Any]:
        """Get outgoing invocations.

        Returns:
            TODO: Add return description
        """


        return [inv for inv in self.invocations if getattr(inv, "source", None) == self]

    def get_incoming_invocations(self) -> list[Any]:
        """Get incoming invocations.

        Returns:
            TODO: Add return description
        """


        return [inv for inv in self.invocations if getattr(inv, "target", None) == self]

    def increase_complexity(self) -> None:
        """Increase complexity.
        """


        if not hasattr(self, "_complexity"):
            self._complexity = 1
        self._complexity += 1

    def is_predefined_method(self) -> bool:
        """Check if predefined method.

        Returns:
            TODO: Add return description
        """


        predefined = {"sort", "move", "copy", "find", "replace", "trim"}
        return self.name.lower() in predefined

    # Alias management methods
    def add_alias(self, alias_node: Any) -> None:


        """Add an alias to this behavioral."""
        # Set target reference
        if hasattr(alias_node, "target"):
            alias_node.target = self
        # Store by alias_name for get_alias lookup
        if hasattr(alias_node, "alias_name") and alias_node.alias_name:
            self.aliases[alias_node.alias_name] = alias_node
        elif hasattr(alias_node, "name") and alias_node.name:
            # Fallback to name if alias_name not available
            self.aliases[alias_node.name] = alias_node

    def get_aliases(self) -> list[Any]:




        """Get all aliases for this behavioral."""
        return list(self.aliases.values())

    def get_alias(self, name: str) -> Any | None:




        """Get a specific alias by name."""
        return self.aliases.get(name)

    # Library management methods
    def set_library(self, library_node: PBBehavioralLibraryNode) -> None:


        """Set the library for this behavioral."""
        self.library = library_node

    def get_library(self) -> PBBehavioralLibraryNode | None:




        """Get the library for this behavioral."""
        return self.library

    @property
    def is_system_library(self) -> bool:


        """Check if this behavioral is from a system library."""
        return self.library is not None and self.library.is_system

    # Option management methods
    def add_option(self, option: BehavioralOptionType) -> None:


        """Add a behavioral option."""
        if option not in self.options:
            self.options.append(option)

    def remove_option(self, option: BehavioralOptionType) -> None:




        """Remove a behavioral option."""
        if option in self.options:
            self.options.remove(option)

    def has_option(self, option: BehavioralOptionType) -> bool:




        """Check if this behavioral has a specific option."""
        return option in self.options

    # Property methods for common options
    @property
    def is_forward(self) -> bool:


        """Check if this is a forward declaration."""
        return BehavioralOptionType.FORWARD in self.options

    @property
    def is_rpcfunc(self) -> bool:


        """Check if this is an RPC function."""
        return BehavioralOptionType.RPCFUNC in self.options

    @property
    def is_dynamic(self) -> bool:


        """Check if this is a dynamic behavioral."""
        return BehavioralOptionType.DYNAMIC in self.options

    @property
    def is_indirect(self) -> bool:


        """Check if this is an indirect behavioral."""
        return BehavioralOptionType.INDIRECT in self.options

    @property
    def is_static(self) -> bool:


        """Check if this is a static behavioral."""
        return BehavioralOptionType.STATIC in self.options

    def to_string(self) -> str:




        """Get string representation of this behavioral."""
        parts = [self.access_modifier]

        # Add options (forward, static, etc.)
        for option in self.options:
            parts.append(option.value)

        # Add library info if present
        if self.library:
            if hasattr(self.library, "is_system") and self.library.is_system:
                parts.append("system")
            parts.append("library")
            if hasattr(self.library, "library_path"):
                parts.append(str(self.library.library_path))
            elif hasattr(self.library, "library_file"):
                parts.append(str(self.library.library_file))

        # Add name
        parts.append(self.name)

        # Add parameters - with space if parameters exist, no space if empty
        if self.parameters:
            param_strs = [p.to_string() if hasattr(p, "to_string") else str(p) for p in self.parameters]
            parts.append(f"({", ".join(param_strs)})")
        else:
            # For empty params, append directly to name without space
            parts[-1] = parts[-1] + "()"

        # Add aliases if present
        if self.aliases:
            alias_strs = []
            for alias in self.aliases.values():
                alias_strs.append(str(alias))
            parts.append(f"[{", ".join(alias_strs)}]")

        # Add return type
        if self.signature and hasattr(self.signature, "return_type") and self.signature.return_type:
            parts.append(f"returns {self.signature.return_type.name}")

        return " ".join(parts)

    def get_reachable_entities(self) -> list[Any]:




        """Get all entities reachable from this behavioral."""
        entities = []
        # Add self (this function) as reachable
        entities.append(self)
        # Add invoked behaviors
        for inv in self.get_outgoing_invocations():
            if hasattr(inv, "target") and inv.target:
                entities.append(inv.target)
        # Add accessed attributes
        entities.extend(self.get_accessed_attributes())
        # Add parameter and variable types
        for param in self.parameters:
            if hasattr(param, "parameter_type") and param.parameter_type:
                entities.append(param.parameter_type)
        for var in self.variables:
            if hasattr(var, "variable_type") and var.variable_type:
                entities.append(var.variable_type)
        return entities


class AccessModifier:
    """Access modifier enumeration."""

    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    GLOBAL = "global"


class BehavioralOption:
    """Behavioral option enumeration."""

    FORWARD = BehavioralOptionType.FORWARD
    RPCFUNC = BehavioralOptionType.RPCFUNC
    DYNAMIC = BehavioralOptionType.DYNAMIC
    INDIRECT = BehavioralOptionType.INDIRECT
    STATIC = BehavioralOptionType.STATIC
    SYSTEM = BehavioralOptionType.SYSTEM


@dataclass
class PBBehavioralAlias(PBNode):
    """Behavioral alias."""

    name: str = ""
    alias_name: str = ""
    target: Any | None = None

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            TODO: Add return description
        """


        return f"alias {self.alias_name}"


@dataclass
class PBBehaviorSignature(PBNode):
    """Behavior signature."""

    name: str = ""
    behavioral: Any = None
    return_type: Any = None
    parameters: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        """  post init  .
        """


        # Initialize empty list if not provided
        if self.parameters is None:
            self.parameters = []

    def __str__(self) -> str:




        """Get string representation of signature."""
        parts = []
        if self.return_type:
            parts.append(f"returns {self.return_type.name}")
        if self.parameters:
            param_strs = []
            for p in self.parameters:
                if hasattr(p, "to_string"):
                    param_strs.append(p.to_string())
                elif hasattr(p, "name") and hasattr(p, "parameter_type"):
                    param_strs.append(f"{p.name}: {p.parameter_type.name}")
                else:
                    param_strs.append(str(p))
            parts.append(f"({", ".join(param_strs)})")
        return " ".join(parts)


@dataclass
class PBFunctionReturn(PBNode):
    """Function return."""

    behavioral: Any = None
    value: Any = None


@dataclass
class PBInvocation(PBNode):
    """Invocation."""

    name: str = ""
    source: Any = None
    target: Any = None


@dataclass
class PBParameter(PBNode):
    """Parameter."""

    name: str = ""
    parameter_type: Any = None
    behavioral: Any = None

    def to_string(self) -> str:
        """To string.

        Returns:
            TODO: Add return description
        """


        if self.parameter_type:
            return f"{self.name}: {self.parameter_type.name}"
        return self.name


@dataclass
class PBVariable(PBNode):
    """Variable."""

    name: str = ""
    behavioral: Any = None
    variable_type: Any = None
    initial_value: Any = None

    def to_string(self) -> str:
        """To string.

        Returns:
            TODO: Add return description
        """


        result = (
            f"{self.name}: {self.variable_type.name if self.variable_type else "any"}"
        )
        if self.initial_value is not None:
            result += f" = {self.initial_value}"
        return result


# Test-specific classes
@dataclass
class PBEvent(PBNode):
    """Event stub for tests."""

    name: str = ""


@dataclass
class PBTrigger(PBNode):
    """Trigger stub for tests."""

    name: str = ""


@dataclass
class PBFunction(PBNode):
    """Function stub for tests."""

    name: str = ""


@dataclass
class PBProcedure(PBNode):
    """Procedure stub for tests."""

    name: str = ""


# Export all classes
__all__ = [
    "BehavioralOptionType", "PBBehavioralNode", "PBAccessModifierDefinerNode", "PBAccessModifierNode", "PBBehavioralAliasNode", "PBBehavioralLibraryNode", "PBBehavioralOptionNode", "PBBehavioral", "AccessModifier", "BehavioralOption", "PBBehavioralAlias", "PBBehaviorSignature", "PBFunctionReturn", "PBInvocation", "PBParameter", "PBVariable", "PBEvent", "PBTrigger", "PBFunction", "PBProcedure", ]
