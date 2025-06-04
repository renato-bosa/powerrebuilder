"""PowerBuilder behavioral model stubs.

This module provides stub classes for behavioral nodes that are referenced
in tests and other modules but not yet fully implemented.
"""

from dataclasses import dataclass
from typing import Any

from .utils.base import PBNode


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


@dataclass
class PBBehavioralAliasNode(PBNode):
    """Behavioral alias node."""

    alias: str = ""


@dataclass
class PBBehavioralLibraryNode(PBNode):
    """Behavioral library node."""

    library_file: str = ""


@dataclass
class PBBehavioralOptionNode(PBNode):
    """Behavioral option node."""

    behavioral_option: str = ""


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
    signature: Any = None

    def __post_init__(self):
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

    @property
    def is_behavioral(self) -> bool:
        return True

    @property
    def is_global(self) -> bool:
        return self.access_modifier == "global"

    @property
    def is_private(self) -> bool:
        return self.access_modifier == "private"

    @property
    def cyclomatic_complexity(self) -> int:
        return getattr(self, "_complexity", 1)

    def add_parameter(self, param: Any) -> None:
        param.behavioral = self
        self.parameters.append(param)

    def add_return(self, ret: Any) -> None:
        ret.behavioral = self
        self.returns.append(ret)

    def add_variable(self, var: Any) -> None:
        var.behavioral = self
        self.variables.append(var)

    def add_access(self, access: Any) -> None:
        self.accesses.append(access)

    def add_invocation(self, invocation: Any) -> None:
        self.invocations.append(invocation)

    def get_accessed_attributes(self) -> list[Any]:
        return self.accesses

    def get_outgoing_invocations(self) -> list[Any]:
        return [inv for inv in self.invocations if getattr(inv, "source", None) == self]

    def get_incoming_invocations(self) -> list[Any]:
        return [inv for inv in self.invocations if getattr(inv, "target", None) == self]

    def increase_complexity(self) -> None:
        if not hasattr(self, "_complexity"):
            self._complexity = 1
        self._complexity += 1

    def is_predefined_method(self) -> bool:
        predefined = {"sort", "move", "copy", "find", "replace", "trim"}
        return self.name.lower() in predefined


@dataclass
class AccessModifier:
    """Access modifier enumeration."""

    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    GLOBAL = "global"


@dataclass
class BehavioralOption(PBNode):
    """Behavioral option."""

    option_type: str = ""
    value: str = ""


@dataclass
class PBBehavioralAlias(PBNode):
    """Behavioral alias."""

    name: str = ""
    alias: str = ""


@dataclass
class PBBehaviorSignature(PBNode):
    """Behavior signature."""

    name: str = ""
    behavioral: Any = None
    return_type: Any = None


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
        result = (
            f"{self.name}: {self.variable_type.name if self.variable_type else 'any'}"
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
