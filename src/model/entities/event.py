"""PowerBuilder event model stubs."""

from dataclasses import dataclass
from typing import Any

from src.model.types.base import PBNode


class PBEventAttributeNode(PBNode):
    """Event attribute node."""

    return_type: Any = None
    event_name: Any = None
    attribute: Any = None


    class PBEventDeclarationNode(PBNode):
        """Event declaration node."""

        return_type: Any = None
        event_name: Any = None  # Add event_name for compatibility
        event_reference_name: Any = None
        custom_call_statement: Any = None
        statements: Any = None

        def __post_init__(self):
            """Sync event_name and event_reference_name."""
            if self.event_name and not self.event_reference_name:
                self.event_reference_name = self.event_name
            elif self.event_reference_name and not self.event_name:
                self.event_name = self.event_reference_name


                class PBEventInvocationNode(PBNode):
                    """Event invocation node."""

                    identifier: Any = None
                    function_arguments: Any = None


                    class PBEventLongNode(PBNode):
                        """Event long node."""

                        function_argument: Any = None


                        class PBEventNameNode(PBNode):
                            """Event name node."""

                            event_name: Any = None


                            class PBEventReferenceNameNode(PBNode):
                                """Event reference name node."""

                                object_class: Any = None
                                event_name: Any = None
                                arguments: Any = None


                                class PBEventTriggeringOrPostingNode(PBNode):
                                    """Event triggering or posting node."""

                                    identifiers: list[Any] = None
                                    array_positions: list[Any] = None
                                    event_name: Any = None
                                    event_word: Any = None
                                    event_long: Any = None


                                    class PBEventTypeNode(PBNode):
                                        """Event type node."""

                                        event_type: Any = None


                                        class PBEventWordNode(PBNode):
                                            """Event word node."""

                                            function_argument: Any = None


                                            class PBEvent(PBNode):
                                                """PowerBuilder event stub class."""

                                                name: str = ""
