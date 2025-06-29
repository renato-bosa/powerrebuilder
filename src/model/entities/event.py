"""PowerBuilder event model stubs."""

from dataclasses import dataclass
from typing import Any

from model.utils.base import PBNode


@dataclass
class PBEventAttributeNode(PBNode):
    """Event attribute node."""

    return_type: Any = None
    event_name: Any = None
    attribute: Any = None


@dataclass
class PBEventDeclarationNode(PBNode):
    """Event declaration node."""

    return_type: Any = None
    event_reference_name: Any = None
    custom_call_statement: Any = None
    statements: Any = None


@dataclass
class PBEventInvocationNode(PBNode):
    """Event invocation node."""

    identifier: Any = None
    function_arguments: Any = None


@dataclass
class PBEventLongNode(PBNode):
    """Event long node."""

    function_argument: Any = None


@dataclass
class PBEventNameNode(PBNode):
    """Event name node."""

    event_name: Any = None


@dataclass
class PBEventReferenceNameNode(PBNode):
    """Event reference name node."""

    object_class: Any = None
    event_name: Any = None
    arguments: Any = None


@dataclass
class PBEventTriggeringOrPostingNode(PBNode):
    """Event triggering or posting node."""

    identifiers: list[Any] = None
    array_positions: list[Any] = None
    event_name: Any = None
    event_word: Any = None
    event_long: Any = None


@dataclass
class PBEventTypeNode(PBNode):
    """Event type node."""

    event_type: Any = None


@dataclass
class PBEventWordNode(PBNode):
    """Event word node."""

    function_argument: Any = None


@dataclass
class PBEvent(PBNode):
    """PowerBuilder event stub class."""

    name: str = ""
