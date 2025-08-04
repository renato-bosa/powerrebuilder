"""Event processing service for code generation."""

import logging
import re
from typing import Any

from src.interfaces import IEventProcessor

logger = logging.getLogger(__name__)


class EventProcessor(IEventProcessor):
    """Processes events for code generation."""

    def __init__(self) -> None:
        """Initialize the event processor."""
        self._event_mapping = {
            # Window events
            "open": "on_open",
            "close": "on_close",
            "activate": "on_activate",
            "deactivate": "on_deactivate",
            "resize": "on_resize",
            "key": "on_key_press",
            "timer": "on_timer",
            # Control events
            "clicked": "on_click",
            "doubleclicked": "on_double_click",
            "rightclicked": "on_right_click",
            "getfocus": "on_focus",
            "losefocus": "on_blur",
            "modified": "on_change",
            "selectionchanged": "on_selection_change",
            "itemchanged": "on_item_change",
            # DataWindow events
            "itemerror": "on_item_error",
            "itemfocuschanged": "on_item_focus_change",
            "rowfocuschanged": "on_row_focus_change",
            "rowfocuschanging": "on_row_focus_changing",
            "retrievestart": "on_retrieve_start",
            "retrieveend": "on_retrieve_end",
            "updatestart": "on_update_start",
            "updateend": "on_update_end",
            # Drag & Drop events
            "dragdrop": "on_drag_drop",
            "dragenter": "on_drag_enter",
            "dragleave": "on_drag_leave",
            "dragwithin": "on_drag_within",
            "beginrdrag": "on_begin_right_drag",
            "beginldrag": "on_begin_left_drag",
            # Other events
            "constructor": "on_create",
            "destructor": "on_destroy",
            "error": "on_error",
            "fileexists": "on_file_exists",
            "printpage": "on_print_page",
        }

        self._system_events = {
            "clicked",
            "doubleclicked",
            "rightclicked",
            "getfocus",
            "losefocus",
            "modified",
            "constructor",
            "destructor",
            "open",
            "close",
            "activate",
            "deactivate",
            "timer",
        }

    def process_events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process event definitions.

        Args:
            events: List of event definitions

        Returns:
            Processed events with handlers and metadata
        """
        processed = []

        for event in events:
            processed_event = self._process_single_event(event)
            if processed_event:
                processed.append(processed_event)

        # Sort events by priority
        processed.sort(key=self._get_event_priority)

        return processed

    def extract_event_handlers(self, ast: dict[str, Any]) -> dict[str, list[str]]:
        """Extract event handlers from AST.

        Args:
            ast: Abstract syntax tree

        Returns:
            Dictionary mapping control names to their event handlers
        """
        handlers = {}

        # Process controls with events
        if "controls" in ast:
            for control in ast["controls"]:
                control_name = control.get("name", "")
                if control_name and "events" in control:
                    handlers[control_name] = self._extract_control_handlers(control)

        # Process window-level events
        if "events" in ast:
            window_handlers = []
            for event in ast["events"]:
                if isinstance(event, dict):
                    event_name = event.get("name", "")
                    if event_name:
                        window_handlers.append(event_name)

            if window_handlers:
                handlers["window"] = window_handlers

        # Process functions that might be event handlers
        if "functions" in ast:
            self._extract_implicit_handlers(ast["functions"], handlers)

        return handlers

    def wire_events(
        self, controls: list[dict[str, Any]], event_handlers: dict[str, list[str]]
    ) -> dict[str, Any]:
        """Wire events to controls.

        Args:
            controls: List of controls
            event_handlers: Event handlers by control name

        Returns:
            Event wiring configuration
        """
        wiring = {"connections": [], "subscriptions": {}, "event_bus": []}

        # Wire control events
        for control in controls:
            control_name = control.get("name", "")
            control_type = control.get("type", "")

            if control_name in event_handlers:
                for handler in event_handlers[control_name]:
                    connection = self._create_event_connection(
                        control_name, control_type, handler
                    )
                    if connection:
                        wiring["connections"].append(connection)

                # Wire default events based on control type
                default_handlers = self._get_default_handlers(control_type)
                for event_name, handler_name in default_handlers.items():
                    if handler_name not in event_handlers.get(control_name, []):
                        connection = {
                            "source": control_name,
                            "event": event_name,
                            "handler": handler_name,
                            "type": "default",
                        }
                        wiring["connections"].append(connection)

        # Create event subscriptions
        self._create_subscriptions(wiring["connections"], wiring["subscriptions"])

        # Identify event bus candidates
        wiring["event_bus"] = self._identify_event_bus_candidates(wiring["connections"])

        return wiring

    # Private helper methods

    def _process_single_event(self, event: dict[str, Any]) -> dict[str, Any] | None:
        """Process a single event definition."""
        if not isinstance(event, dict):
            return None

        event_name = event.get("name", "")
        if not event_name:
            return None

        # Map PowerBuilder event name to modern name
        modern_name = self._event_mapping.get(event_name.lower(), event_name)

        processed = {
            "name": event_name,
            "modern_name": modern_name,
            "handler": f"{modern_name}_handler",
            "is_system": event_name.lower() in self._system_events,
            "parameters": [],
            "return_type": event.get("return_type", "void"),
            "body": event.get("body", []),
        }

        # Extract parameters
        if "parameters" in event:
            processed["parameters"] = self._process_event_parameters(
                event["parameters"]
            )
        elif "arguments" in event:
            processed["parameters"] = self._process_event_parameters(event["arguments"])

        # Analyze event body
        processed["metadata"] = self._analyze_event_body(processed["body"])

        # Determine event category
        processed["category"] = self._categorize_event(event_name)

        return processed

    def _process_event_parameters(self, params: Any) -> list[dict[str, Any]]:
        """Process event parameters."""
        if not params:
            return []

        processed = []

        # Handle different parameter formats
        if isinstance(params, list):
            for param in params:
                if isinstance(param, dict):
                    processed.append(
                        {
                            "name": param.get("name", ""),
                            "type": param.get("type", "any"),
                            "is_reference": param.get("is_reference", False),
                            "is_readonly": param.get("is_readonly", False),
                        }
                    )
        elif isinstance(params, dict):
            # Single parameter
            processed.append(
                {
                    "name": params.get("name", ""),
                    "type": params.get("type", "any"),
                    "is_reference": params.get("is_reference", False),
                    "is_readonly": params.get("is_readonly", False),
                }
            )

        return processed

    def _analyze_event_body(self, body: list[Any]) -> dict[str, Any]:
        """Analyze event body for metadata."""
        metadata = {
            "calls_parent": False,
            "has_error_handling": False,
            "modifies_state": False,
            "performs_io": False,
            "triggers_events": False,
            "accesses_database": False,
            "shows_messages": False,
        }

        if not body:
            return metadata

        # Convert body to string for analysis
        body_str = str(body).lower()

        # Check for parent calls
        if "call super" in body_str or "parent." in body_str:
            metadata["calls_parent"] = True

        # Check for error handling
        if "try" in body_str or "catch" in body_str or "messagebox" in body_str:
            metadata["has_error_handling"] = True

        # Check for state modifications
        if "this." in body_str or "set" in body_str or "=" in body_str:
            metadata["modifies_state"] = True

        # Check for I/O operations
        if "file" in body_str or "read" in body_str or "write" in body_str:
            metadata["performs_io"] = True

        # Check for event triggering
        if "triggerevent" in body_str or "postevent" in body_str:
            metadata["triggers_events"] = True

        # Check for database access
        if (
            "select" in body_str
            or "insert" in body_str
            or "update" in body_str
            or "delete" in body_str
        ):
            metadata["accesses_database"] = True

        # Check for message display
        if "messagebox" in body_str or "message" in body_str:
            metadata["shows_messages"] = True

        return metadata

    def _categorize_event(self, event_name: str) -> str:
        """Categorize event by type."""
        name_lower = event_name.lower()

        # Lifecycle events
        if name_lower in [
            "constructor",
            "destructor",
            "open",
            "close",
            "create",
            "destroy",
        ]:
            return "lifecycle"

        # User interaction events
        if name_lower in [
            "clicked",
            "doubleclicked",
            "rightclicked",
            "key",
            "modified",
        ]:
            return "user_interaction"

        # Focus events
        if "focus" in name_lower:
            return "focus"

        # Data events
        if any(
            term in name_lower for term in ["retrieve", "update", "item", "row", "data"]
        ):
            return "data"

        # Drag & Drop events
        if "drag" in name_lower or "drop" in name_lower:
            return "drag_drop"

        # Window events
        if name_lower in ["activate", "deactivate", "resize", "move"]:
            return "window"

        # System events
        if name_lower in ["timer", "idle", "systemkey"]:
            return "system"

        return "custom"

    def _get_event_priority(self, event: dict[str, Any]) -> tuple[int, str]:
        """Get event priority for sorting."""
        category_priority = {
            "lifecycle": 1,
            "data": 2,
            "user_interaction": 3,
            "focus": 4,
            "window": 5,
            "drag_drop": 6,
            "system": 7,
            "custom": 8,
        }

        priority = category_priority.get(event["category"], 99)
        return (priority, event["name"])

    def _extract_control_handlers(self, control: dict[str, Any]) -> list[str]:
        """Extract event handlers from a control."""
        handlers = []

        if "events" in control:
            for event in control["events"]:
                if isinstance(event, dict):
                    handler_name = event.get("handler", event.get("name", ""))
                    if handler_name:
                        handlers.append(handler_name)
                elif isinstance(event, str):
                    handlers.append(event)

        return handlers

    def _extract_implicit_handlers(
        self, functions: list[dict[str, Any]], handlers: dict[str, list[str]]
    ) -> None:
        """Extract implicit event handlers from functions."""
        # Common event handler patterns
        event_patterns = [
            (r"(\w+)_clicked$", "clicked"),
            (r"(\w+)_doubleclicked$", "doubleclicked"),
            (r"(\w+)_modified$", "modified"),
            (r"(\w+)_getfocus$", "getfocus"),
            (r"(\w+)_losefocus$", "losefocus"),
            (r"(\w+)_itemchanged$", "itemchanged"),
            (r"(\w+)_constructor$", "constructor"),
            (r"(\w+)_destructor$", "destructor"),
        ]

        for func in functions:
            func_name = func.get("name", "")
            if not func_name:
                continue

            # Check against patterns
            for pattern, _event_type in event_patterns:
                match = re.match(pattern, func_name)
                if match:
                    control_name = match.group(1)
                    if control_name not in handlers:
                        handlers[control_name] = []
                    if func_name not in handlers[control_name]:
                        handlers[control_name].append(func_name)
                    break

    def _create_event_connection(
        self, control_name: str, control_type: str, handler: str
    ) -> dict[str, Any] | None:
        """Create an event connection."""
        # Extract event type from handler name
        event_type = self._extract_event_from_handler(handler)
        if not event_type:
            return None

        return {
            "source": control_name,
            "source_type": control_type,
            "event": event_type,
            "handler": handler,
            "type": "explicit",
            "binding": "direct",
        }

    def _extract_event_from_handler(self, handler_name: str) -> str | None:
        """Extract event type from handler name."""
        # Common patterns
        patterns = [
            (r"on_(\w+)$", lambda m: m.group(1)),
            (r"handle_(\w+)$", lambda m: m.group(1)),
            (r"(\w+)_handler$", lambda m: m.group(1)),
            (r"(\w+)_clicked$", lambda m: "clicked"),
            (r"(\w+)_modified$", lambda m: "modified"),
            (r"(\w+)_changed$", lambda m: "changed"),
        ]

        for pattern, extractor in patterns:
            match = re.search(pattern, handler_name.lower())
            if match:
                return extractor(match)

        # Check if handler name is an event name
        if handler_name.lower() in self._event_mapping:
            return handler_name.lower()

        return None

    def _get_default_handlers(self, control_type: str) -> dict[str, str]:
        """Get default event handlers for a control type."""
        defaults = {
            "commandbutton": {"clicked": "on_click"},
            "checkbox": {"clicked": "on_check_change"},
            "radiobutton": {"clicked": "on_selection_change"},
            "singlelineedit": {
                "modified": "on_text_change",
                "getfocus": "on_focus",
                "losefocus": "on_blur",
            },
            "multilineedit": {
                "modified": "on_text_change",
                "getfocus": "on_focus",
                "losefocus": "on_blur",
            },
            "dropdownlistbox": {
                "selectionchanged": "on_selection_change",
                "modified": "on_value_change",
            },
            "listbox": {
                "selectionchanged": "on_selection_change",
                "doubleclicked": "on_item_double_click",
            },
            "datawindow": {
                "clicked": "on_cell_click",
                "doubleclicked": "on_cell_double_click",
                "itemchanged": "on_item_change",
                "rowfocuschanged": "on_row_change",
            },
            "tab": {"selectionchanged": "on_tab_change"},
            "treeview": {
                "selectionchanged": "on_node_select",
                "doubleclicked": "on_node_double_click",
            },
            "picture": {"clicked": "on_image_click"},
        }

        return defaults.get(control_type.lower(), {})

    def _create_subscriptions(
        self, connections: list[dict[str, Any]], subscriptions: dict[str, set[str]]
    ) -> None:
        """Create event subscriptions from connections."""
        for connection in connections:
            event_key = f"{connection['source']}.{connection['event']}"

            if event_key not in subscriptions:
                subscriptions[event_key] = set()

            subscriptions[event_key].add(connection["handler"])

    def _identify_event_bus_candidates(
        self, connections: list[dict[str, Any]]
    ) -> list[str]:
        """Identify events that should use event bus."""
        # Count event occurrences
        event_counts = {}
        for connection in connections:
            event_type = connection["event"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Events that appear multiple times are candidates
        candidates = []
        for event_type, count in event_counts.items():
            if count > 2:  # Threshold for event bus
                candidates.append(event_type)

        # Always include these in event bus
        always_bus = ["data_changed", "state_changed", "error_occurred"]
        for event in always_bus:
            if event not in candidates:
                candidates.append(event)

        return candidates
