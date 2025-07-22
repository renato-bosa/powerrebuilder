"""Event wiring system for connecting PowerBuilder events to Flutter callbacks.

This module handles the mapping and wiring of PowerBuilder events to Flutter
widget callbacks, ensuring proper event handling in the generated Flutter code.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EventWiring:
    """Represents a wiring between a control and its event handler."""

    control_name: str
    control_type: str
    event_name: str
    handler_name: str
    flutter_callback: str
    callback_signature: str
    needs_gesture_detector: bool = False
    needs_focus_node: bool = False
    additional_properties: dict[str, Any] = field(default_factory=dict)


class EventWiringSystem:
    """System for wiring PowerBuilder events to Flutter callbacks."""

    def __init__(self, event_converter=None) -> None:
        """Initialize the event wiring system.

        Args:
            event_converter: Optional EventConverter instance for advanced conversions
        """
        self.event_converter = event_converter

        # PowerBuilder event to Flutter callback mappings by control type
        self.control_event_mappings = {
            "commandbutton": {
                "clicked": "onPressed",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange",
                "rbuttondown": "onSecondaryTap",
            },
            "picturebutton": {
                "clicked": "onPressed",
                "doubleclicked": "onDoubleTap",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange",
            },
            "singlelineedit": {
                "modified": "onChanged",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange",
                "key": "onSubmitted",
            },
            "multilineedit": {
                "modified": "onChanged",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange",
            },
            "checkbox": {
                "clicked": "onChanged",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange",
            },
            "radiobutton": {
                "clicked": "onChanged",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange",
            },
            "dropdownlistbox": {
                "selectionchanged": "onChanged",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange",
            },
            "listbox": {
                "selectionchanged": "onTap",
                "doubleclicked": "onDoubleTap",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange",
            },
            "datawindow": {
                "itemchanged": "onCellEdit",
                "itemerror": "onValidationError",
                "rowfocuschanged": "onRowSelected",
                "rowfocuschanging": "onRowSelecting",
                "clicked": "onCellClicked",
                "doubleclicked": "onCellDoubleClicked",
                "buttonclicked": "onButtonClicked",
                "retrievestart": "onLoadStart",
                "retrieveend": "onLoadEnd",
                "updatestart": "onSaveStart",
                "updateend": "onSaveEnd",
            },
            "treeview": {
                "selectionchanged": "onSelectionChanged",
                "expanding": "onExpanding",
                "collapsing": "onCollapsing",
                "beginlabeledit": "onBeginEdit",
                "endlabeledit": "onEndEdit",
                "deleteitem": "onDeleteItem",
                "doubleclicked": "onNodeDoubleTap",
            },
            "tab": {
                "selectionchanged": "onTabChanged",
                "selectionchanging": "onTabChanging",
            },
            "window": {
                "open": "initState",
                "close": "dispose",
                "closequery": "onCloseQuery",
                "activate": "onResume",
                "deactivate": "onPause",
                "resize": "onResize",
                "key": "onKey",
            },
            "picture": {
                "clicked": "onTap",
                "doubleclicked": "onDoubleTap",
                "rbuttondown": "onSecondaryTap",
            },
            "statictext": {
                "clicked": "onTap",
                "doubleclicked": "onDoubleTap",
            },
            "groupbox": {
                "clicked": "onTap",
            },
            "htrackbar": {
                "valuechanged": "onChanged",
                "pageup": "onChangeStart",
                "pagedown": "onChangeEnd",
            },
            "vtrackbar": {
                "valuechanged": "onChanged",
                "pageup": "onChangeStart",
                "pagedown": "onChangeEnd",
            },
            "spin": {
                "valuechanged": "onChanged",
            },
            "datepicker": {
                "valuechanged": "onDateChanged",
                "dropdown": "onTap",
            },
            "monthcalendar": {
                "datechanged": "onDaySelected",
                "clicked": "onDaySelected",
            },
        }

        # Controls that need GestureDetector wrapper for certain events
        self.gesture_detector_events = {
            "clicked": [
                "statictext",
                "picture",
                "groupbox",
                "rectangle",
                "oval",
                "line",
            ],
            "doubleclicked": ["statictext", "picture", "groupbox"],
            "rbuttondown": ["picture", "statictext", "commandbutton"],
        }

        # Controls that need FocusNode for focus events
        self.focus_node_controls = [
            "singlelineedit",
            "multilineedit",
            "editmask",
            "dropdownlistbox",
            "listbox",
            "checkbox",
            "radiobutton",
            "commandbutton",
            "picturebutton",
            "treeview",
        ]

    def wire_events(self, window_model: dict) -> dict[str, Any]:
        """Wire all events from a window model to their controls.

        Args:
            window_model: Window model containing controls and events

        Returns:
            Dictionary with event wirings and additional state needed
        """
        wirings = []
        focus_nodes_needed = []
        gesture_detectors_needed = []
        event_handlers = []

        # Extract events from window model
        events = window_model.get("events", [])
        controls = window_model.get("controls", [])

        # Create control lookup
        control_lookup = {control.get("name", ""): control for control in controls}

        # Process each event
        for event in events:
            event_name = event.get("name", "")

            # Parse event name to extract control and event type
            control_name, event_type = self._parse_event_name(event_name)

            if control_name and event_type:
                # Find the control
                control = control_lookup.get(control_name)
                if control:
                    # Create wiring
                    wiring = self._create_event_wiring(
                        control,
                        event_type,
                        event,
                        window_model,
                    )
                    if wiring:
                        wirings.append(wiring)

                        # Track additional requirements
                        if (
                            wiring.needs_focus_node
                            and control_name not in focus_nodes_needed
                        ):
                            focus_nodes_needed.append(control_name)

                        if (
                            wiring.needs_gesture_detector
                            and control_name not in gesture_detectors_needed
                        ):
                            gesture_detectors_needed.append(control_name)

                        # Add event handler method
                        handler_method = self._create_event_handler_method(
                            wiring, event
                        )
                        if handler_method:
                            event_handlers.append(handler_method)
            # Window-level event
            elif event_type:
                wiring = self._create_window_event_wiring(event_type, event)
                if wiring:
                    wirings.append(wiring)

                    # Add event handler method if not lifecycle
                    if event_type not in [
                        "open",
                        "close",
                        "constructor",
                        "destructor",
                    ]:
                        handler_method = self._create_event_handler_method(
                            wiring, event
                        )
                        if handler_method:
                            event_handlers.append(handler_method)

        # Also check for events embedded in control definitions
        for control in controls:
            control_events = control.get("events", [])
            for event in control_events:
                event_type = event.get("name", "").lower()
                wiring = self._create_event_wiring(
                    control,
                    event_type,
                    event,
                    window_model,
                )
                if wiring:
                    wirings.append(wiring)

                    if (
                        wiring.needs_focus_node
                        and control["name"] not in focus_nodes_needed
                    ):
                        focus_nodes_needed.append(control["name"])

                    if (
                        wiring.needs_gesture_detector
                        and control["name"] not in gesture_detectors_needed
                    ):
                        gesture_detectors_needed.append(control["name"])

                    handler_method = self._create_event_handler_method(wiring, event)
                    if handler_method:
                        event_handlers.append(handler_method)

        return {
            "wirings": wirings,
            "focus_nodes": focus_nodes_needed,
            "gesture_detectors": gesture_detectors_needed,
            "event_handlers": event_handlers,
            "state_variables": self._extract_state_for_events(wirings, controls),
        }

    def _parse_event_name(self, event_name: str) -> tuple[str | None, str | None]:
        """Parse event name to extract control name and event type.

        Args:
            event_name: PowerBuilder event name (e.g., "cb_ok::clicked" or "clicked")

        Returns:
            Tuple of (control_name, event_type) or (None, event_type) for window events
        """
        # Handle scope resolution operator
        if "::" in event_name:
            parts = event_name.split("::")
            if len(parts) == 2:
                return parts[0], parts[1].lower()

        # Handle underscore notation (e.g., "cb_ok_clicked")
        parts = event_name.split("_")
        if len(parts) >= 2:
            # Try to identify control prefix
            prefixes = [
                "cb",
                "pb",
                "sle",
                "mle",
                "rb",
                "cb",
                "ddlb",
                "lb",
                "dw",
                "tv",
                "tab",
            ]
            for i, part in enumerate(parts):
                if part.lower() in prefixes:
                    # Found control prefix
                    control_parts = parts[: i + 2]  # Include prefix and name
                    event_parts = parts[i + 2 :]
                    if event_parts:
                        return "_".join(control_parts), "_".join(event_parts).lower()

        # Assume it's a window-level event
        return None, event_name.lower()

    def _create_event_wiring(
        self, control: dict, event_type: str, _event: dict, _window_model: dict
    ) -> EventWiring | None:
        """Create event wiring for a control event.

        Args:
            control: Control dictionary
            event_type: Type of event (e.g., "clicked")
            event: Event dictionary with body and parameters
            window_model: Window model for context

        Returns:
            EventWiring object or None
        """
        control_type = control.get("type", "").lower()
        control_name = control.get("name", "")

        # Get Flutter callback name for this event
        flutter_callback = self._get_flutter_callback(control_type, event_type)
        if not flutter_callback:
            logger.warning(
                f"No Flutter callback mapping for {control_type}.{event_type}"
            )
            return None

        # Generate handler method name
        handler_name = (
            f"_{self._to_camel_case(control_name)}{self._to_pascal_case(event_type)}"
        )

        # Determine callback signature
        callback_signature = self._get_callback_signature(control_type, event_type)

        # Check if needs GestureDetector
        needs_gesture = self._needs_gesture_detector(control_type, event_type)

        # Check if needs FocusNode
        needs_focus = self._needs_focus_node(control_type, event_type)

        # Get additional properties for specific event types
        additional_props = self._get_additional_properties(control_type, event_type)

        return EventWiring(
            control_name=control_name,
            control_type=control_type,
            event_name=event_type,
            handler_name=handler_name,
            flutter_callback=flutter_callback,
            callback_signature=callback_signature,
            needs_gesture_detector=needs_gesture,
            needs_focus_node=needs_focus,
            additional_properties=additional_props,
        )

    def _create_window_event_wiring(
        self, event_type: str, _event: Any
    ) -> EventWiring | None:
        """Create event wiring for window-level events.

        Args:
            event_type: Type of event (e.g., "closequery")
            event: Event dictionary

        Returns:
            EventWiring object or None
        """
        # Get Flutter callback/method for window event
        flutter_callback = self._get_flutter_callback("window", event_type)
        if not flutter_callback:
            return None

        # Special handling for lifecycle events
        if event_type in ["open", "constructor"]:
            flutter_callback = "initState"
        elif event_type in ["close", "destructor"]:
            flutter_callback = "dispose"

        handler_name = f"_{self._to_camel_case(event_type)}"
        callback_signature = self._get_callback_signature("window", event_type)

        return EventWiring(
            control_name="window",
            control_type="window",
            event_name=event_type,
            handler_name=handler_name,
            flutter_callback=flutter_callback,
            callback_signature=callback_signature,
        )

    def _get_flutter_callback(self, control_type: str, event_type: str) -> str | None:
        """Get Flutter callback name for a PowerBuilder event.

        Args:
            control_type: Type of control
            event_type: Type of event

        Returns:
            Flutter callback name or None
        """
        control_mappings = self.control_event_mappings.get(control_type.lower(), {})
        return control_mappings.get(event_type.lower())

    def _get_callback_signature(self, control_type: str, event_type: str) -> str:
        """Get Flutter callback signature for an event.

        Args:
            control_type: Type of control
            event_type: Type of event

        Returns:
            Dart callback signature
        """
        # Define common callback signatures
        signatures = {
            ("commandbutton", "clicked"): "VoidCallback",
            ("picturebutton", "clicked"): "VoidCallback",
            ("singlelineedit", "modified"): "ValueChanged<String>",
            ("multilineedit", "modified"): "ValueChanged<String>",
            ("checkbox", "clicked"): "ValueChanged<bool?>",
            ("radiobutton", "clicked"): "ValueChanged<dynamic>",
            ("dropdownlistbox", "selectionchanged"): "ValueChanged<String?>",
            ("listbox", "selectionchanged"): "ValueChanged<int>",
            (
                "datawindow",
                "itemchanged",
            ): "Function(int row, String column, dynamic value)",
            (
                "datawindow",
                "itemerror",
            ): "int Function(int row, String column, dynamic value, String error)",
            ("datawindow", "rowfocuschanged"): "ValueChanged<int>",
            ("datawindow", "buttonclicked"): "Function(int row, String buttonName)",
            ("treeview", "selectionchanged"): "ValueChanged<TreeNode>",
            ("tab", "selectionchanged"): "ValueChanged<int>",
            ("window", "closequery"): "Future<bool> Function()",
            ("window", "key"): "bool Function(KeyEvent event)",
            ("window", "resize"): "Function(Size size)",
            ("htrackbar", "valuechanged"): "ValueChanged<double>",
            ("vtrackbar", "valuechanged"): "ValueChanged<double>",
            ("datepicker", "valuechanged"): "ValueChanged<DateTime?>",
            (
                "monthcalendar",
                "datechanged",
            ): "Function(DateTime selectedDay, DateTime focusedDay)",
        }

        # Check for specific signature
        signature_key = (control_type.lower(), event_type.lower())
        if signature_key in signatures:
            return signatures[signature_key]

        # Default signatures by event type
        if "changed" in event_type:
            return "ValueChanged<dynamic>"
        if "clicked" in event_type or "tap" in event_type:
            return "VoidCallback"
        if "focus" in event_type:
            return "ValueChanged<bool>"
        return "VoidCallback"

    def _needs_gesture_detector(self, control_type: str, event_type: str) -> bool:
        """Check if control needs GestureDetector for this event.

        Args:
            control_type: Type of control
            event_type: Type of event

        Returns:
            True if GestureDetector is needed
        """
        event_controls = self.gesture_detector_events.get(event_type.lower(), [])
        return control_type.lower() in event_controls

    def _needs_focus_node(self, control_type: str, event_type: str) -> bool:
        """Check if control needs FocusNode for this event.

        Args:
            control_type: Type of control
            event_type: Type of event

        Returns:
            True if FocusNode is needed
        """
        if event_type.lower() in ["getfocus", "losefocus"]:
            return control_type.lower() in self.focus_node_controls
        return False

    def _get_additional_properties(
        self, control_type: str, event_type: str
    ) -> dict[str, Any]:
        """Get additional properties needed for specific event types.

        Args:
            control_type: Type of control
            event_type: Type of event

        Returns:
            Dictionary of additional properties
        """
        props = {}

        # DataWindow events might need additional context
        if control_type.lower() == "datawindow":
            if event_type in ["itemchanged", "itemerror"]:
                props["needs_row_context"] = True
            if event_type in ["buttonclicked"]:
                props["button_mapping"] = True

        # Tab events need index
        if control_type.lower() == "tab" and event_type == "selectionchanged":
            props["needs_index"] = True

        # Focus events need focus state
        if event_type.lower() in ["getfocus", "losefocus"]:
            props["track_focus_state"] = True

        return props

    def _create_event_handler_method(
        self, wiring: EventWiring, event: dict
    ) -> dict[str, Any]:
        """Create event handler method for the wiring.

        Args:
            wiring: EventWiring object
            event: Original event dictionary with body

        Returns:
            Dictionary representing the handler method
        """
        # Use event converter if available
        if self.event_converter:
            # Convert event body to Dart
            dart_body = self.event_converter._convert_event_body(
                event.get("body", []),
                wiring.event_name,
                self._get_return_type_from_signature(wiring.callback_signature),
            )
        else:
            # Generate event handler body directly
            dart_body = self._generate_event_handler_body(
                wiring.event_name,
                event.get("body", []),
                wiring.callback_signature,
                wiring.control_type,
            )

        # Extract parameters from signature
        params = self._extract_params_from_signature(wiring.callback_signature)

        # Determine if async
        is_async = "Future" in wiring.callback_signature or any(
            "await" in line for line in dart_body
        )

        return {
            "name": wiring.handler_name,
            "return_type": self._get_return_type_from_signature(
                wiring.callback_signature
            ),
            "params": params,
            "is_async": is_async,
            "body": "\n    ".join(dart_body),
            "is_event_handler": True,
            "wiring": wiring,
        }

    def _extract_state_for_events(
        self, wirings: list[EventWiring], controls: list[dict]
    ) -> list[dict]:
        """Extract state variables needed for event handling.

        Args:
            wirings: List of event wirings
            controls: List of controls

        Returns:
            List of state variable definitions
        """
        state_vars = []

        # Add focus state for controls that track focus
        focus_controls = set()
        for wiring in wirings:
            if wiring.additional_properties.get("track_focus_state"):
                focus_controls.add(wiring.control_name)

        for control_name in focus_controls:
            state_vars.append(
                {
                    "name": f"_{self._to_camel_case(control_name)}HasFocus",
                    "type": "bool",
                    "initial": "false",
                    "description": f"Focus state for {control_name}",
                }
            )

        # Add value state for controls that need it
        for control in controls:
            control_type = control.get("type", "").lower()
            control_name = control.get("name", "")

            if control_type in ["htrackbar", "vtrackbar", "slider"]:
                state_vars.append(
                    {
                        "name": f"_{self._to_camel_case(control_name)}Value",
                        "type": "double",
                        "initial": "0.0",
                        "description": f"Current value for {control_name}",
                    }
                )
            elif control_type == "checkbox":
                state_vars.append(
                    {
                        "name": f"_{self._to_camel_case(control_name)}Checked",
                        "type": "bool?",
                        "initial": "false",
                        "description": f"Checked state for {control_name}",
                    }
                )
            elif control_type == "radiobutton":
                # Group radio buttons
                group = control.get("group", "default")
                state_vars.append(
                    {
                        "name": f"_selected{self._to_pascal_case(group)}Radio",
                        "type": "String?",
                        "initial": "null",
                        "description": f"Selected radio button in {group} group",
                    }
                )

        # Remove duplicates
        unique_vars = []
        seen_names = set()
        for var in state_vars:
            if var["name"] not in seen_names:
                seen_names.add(var["name"])
                unique_vars.append(var)

        return unique_vars

    def _get_return_type_from_signature(self, signature: str) -> str:
        """Extract return type from callback signature.

        Args:
            signature: Dart callback signature

        Returns:
            Return type string
        """
        if "Future<bool>" in signature:
            return "Future<bool>"
        if "Future<" in signature:
            return "Future<void>"
        if "bool Function" in signature:
            return "bool"
        if "int Function" in signature:
            return "int"
        if signature == "VoidCallback":
            return "void"
        return "void"

    def _extract_params_from_signature(self, signature: str) -> str:
        """Extract parameter string from callback signature.

        Args:
            signature: Dart callback signature

        Returns:
            Parameter string for method signature
        """
        if signature == "VoidCallback":
            return ""
        if signature == "ValueChanged<String>":
            return "String value"
        if signature == "ValueChanged<String?>":
            return "String? value"
        if signature == "ValueChanged<bool>":
            return "bool value"
        if signature == "ValueChanged<bool?>":
            return "bool? value"
        if signature == "ValueChanged<int>":
            return "int value"
        if signature == "ValueChanged<double>":
            return "double value"
        if signature == "ValueChanged<DateTime?>":
            return "DateTime? value"
        if signature == "ValueChanged<dynamic>":
            return "dynamic value"
        if "Function(" in signature:
            # Extract parameters from function signature
            import re

            match = re.search(r"Function\((.*?)\)", signature)
            if match:
                return match.group(1)
        elif signature == "bool Function(KeyEvent event)":
            return "KeyEvent event"
        elif signature == "Function(Size size)":
            return "Size size"

        return ""

    def generate_control_with_events(
        self, control: dict, wirings: list[EventWiring]
    ) -> str:
        """Generate Flutter widget code with event handlers wired up.

        Args:
            control: Control dictionary
            wirings: List of EventWiring objects for this control

        Returns:
            Flutter widget code with events
        """
        control.get("type", "").lower()
        control_name = control.get("name", "")
        flutter_widget = control.get("flutter_widget", {})

        # Find wirings for this control
        control_wirings = [w for w in wirings if w.control_name == control_name]

        if not control_wirings:
            # No events, return basic widget
            return self._generate_basic_widget(control)

        # Generate widget with event handlers
        widget_type = flutter_widget.get("widget", "Container")
        dart_name = flutter_widget.get("dart_name", self._to_camel_case(control_name))

        # Build property map including event handlers
        properties = {}

        # Add regular properties
        for key, value in flutter_widget.get("flutter_properties", {}).items():
            properties[key] = value

        # Add event handlers
        for wiring in control_wirings:
            if wiring.needs_gesture_detector:
                # Will wrap in GestureDetector
                continue
            # Direct property
            properties[wiring.flutter_callback] = wiring.handler_name

        # Generate widget code
        widget_code = self._build_widget_code(widget_type, properties, control)

        # Wrap in GestureDetector if needed
        gesture_wirings = [w for w in control_wirings if w.needs_gesture_detector]
        if gesture_wirings:
            gesture_props = {}
            for wiring in gesture_wirings:
                gesture_props[wiring.flutter_callback] = wiring.handler_name

            widget_code = self._wrap_in_gesture_detector(widget_code, gesture_props)

        # Wrap in Focus widget if needed
        focus_wirings = [w for w in control_wirings if w.needs_focus_node]
        if focus_wirings:
            widget_code = self._wrap_in_focus(widget_code, dart_name, focus_wirings)

        return widget_code

    def _generate_basic_widget(self, control: dict) -> str:
        """Generate basic widget without events."""
        flutter_widget = control.get("flutter_widget", {})
        widget_type = flutter_widget.get("widget", "Container")
        properties = flutter_widget.get("flutter_properties", {})

        return self._build_widget_code(widget_type, properties, control)

    def _build_widget_code(
        self, widget_type: str, properties: dict, control: dict
    ) -> str:
        """Build Flutter widget code from type and properties."""
        control_name = control.get("name", "unknown")

        # Get flutter_widget properties if available
        flutter_widget = control.get("flutter_widget", {})
        flutter_props = flutter_widget.get("flutter_properties", {})

        # Special handling for different widget types
        if widget_type == "TextField":
            controller_name = f"_{self._to_camel_case(control_name)}Controller"
            prop_strings = [f"controller: {controller_name}"]

            # Add decoration if available
            if flutter_widget.get("decoration"):
                prop_strings.append(f"decoration: {flutter_widget['decoration']}")

            # Add other properties
            for key, value in properties.items():
                if key not in {"controller", "decoration"}:
                    prop_strings.append(f"{key}: {value}")

            return f"TextField(\n        {',\n        '.join(prop_strings)},\n      )"

        if widget_type == "Checkbox":
            value_name = f"_{self._to_camel_case(control_name)}Checked"
            return f"""Checkbox(
        value: {value_name},
        onChanged: {properties.get("onChanged", "_handleCheckboxChange")},
        tristate: {properties.get("tristate", flutter_props.get("tristate", "false"))},
      )"""

        if widget_type == "ElevatedButton":
            button_text = flutter_props.get(
                "_buttonText", control.get("text", "Button")
            )
            return f"""ElevatedButton(
        onPressed: {properties.get("onPressed", "null")},
        child: Text('{button_text}'),
      )"""

        if widget_type == "IconButton":
            icon_data = flutter_props.get("_iconData", "Icons.help")
            tooltip = flutter_props.get("tooltip", control.get("text", ""))
            return f"""IconButton(
        icon: Icon({icon_data}),
        onPressed: {properties.get("onPressed", "null")},
        tooltip: '{tooltip}',
      )"""

        if widget_type == "Text":
            text_data = flutter_props.get("data", control.get("text", control_name))
            style = flutter_props.get("style")
            if style:
                return f"Text('{text_data}', style: {style})"
            return f"Text('{text_data}')"

        if widget_type == "DropdownButton":
            items = flutter_props.get("_items", "[]")
            value = flutter_props.get("value", "null")
            return f"""DropdownButton<String>(
        value: {value},
        items: {items},
        onChanged: {properties.get("onChanged", "(value) {}")},
      )"""

        # Generic widget
        # Merge flutter_properties with event properties
        all_props = {}
        all_props.update(flutter_props)
        all_props.update(properties)

        if all_props:
            prop_strings = []
            for key, value in all_props.items():
                if not key.startswith("_"):  # Skip internal properties
                    prop_strings.append(f"{key}: {value}")

            if prop_strings:
                return f"{widget_type}(\n        {',\n        '.join(prop_strings)},\n      )"

        return f"{widget_type}()"

    def _wrap_in_gesture_detector(self, child_code: str, gesture_props: dict) -> str:
        """Wrap widget in GestureDetector."""
        prop_strings = [f"{key}: {value}" for key, value in gesture_props.items()]

        return f"""GestureDetector(
        {",\n        ".join(prop_strings)},
        child: {child_code},
      )"""

    def _wrap_in_focus(
        self, child_code: str, control_name: str, focus_wirings: list[EventWiring]
    ) -> str:
        """Wrap widget in Focus widget for focus events."""
        focus_node = f"_{control_name}FocusNode"

        # Build onFocusChange handler
        on_focus_change = f"""(hasFocus) {{
          setState(() {{
            _{control_name}HasFocus = hasFocus;
          }});
          if (hasFocus) {{
            {focus_wirings[0].handler_name}(true);
          }} else {{
            {focus_wirings[0].handler_name}(false);
          }}
        }}"""

        return f"""Focus(
        focusNode: {focus_node},
        onFocusChange: {on_focus_change},
        child: {child_code},
      )"""

    def _generate_event_handler_body(
        self,
        event_name: str,
        body: list[str],
        callback_signature: str,
        control_type: str,
    ) -> list[str]:
        """Generate event handler body for different event types.

        Args:
            event_name: Name of the event
            body: Original PowerBuilder event body
            callback_signature: Flutter callback signature
            control_type: Type of control

        Returns:
            List of Dart code lines for the event handler body
        """
        dart_body = []
        event_lower = event_name.lower()

        # Handle specific event types
        if event_lower == "clicked":
            dart_body.extend(self._generate_clicked_handler(control_type, body))
        elif event_lower == "modified" or event_lower == "onchanged":
            dart_body.extend(self._generate_modified_handler(control_type, body))
        elif event_lower == "getfocus" or event_lower == "losefocus":
            dart_body.extend(
                self._generate_focus_handler(event_lower, control_type, body)
            )
        elif event_lower == "selectionchanged":
            dart_body.extend(
                self._generate_selection_changed_handler(control_type, body)
            )
        elif event_lower == "itemchanged":
            dart_body.extend(self._generate_item_changed_handler(control_type, body))
        elif event_lower == "itemerror":
            dart_body.extend(self._generate_item_error_handler(body))
        elif event_lower == "rowfocuschanged":
            dart_body.extend(self._generate_row_focus_changed_handler(body))
        elif event_lower == "closequery":
            dart_body.extend(self._generate_close_query_handler(body))
        elif event_lower == "key":
            dart_body.extend(self._generate_key_handler(body))
        elif event_lower == "resize":
            dart_body.extend(self._generate_resize_handler(body))
        elif event_lower in ["doubleclicked", "rbuttondown"]:
            dart_body.extend(
                self._generate_gesture_handler(event_lower, control_type, body)
            )
        elif event_lower in [
            "retrievestart",
            "retrieveend",
            "updatestart",
            "updateend",
        ]:
            dart_body.extend(
                self._generate_datawindow_operation_handler(event_lower, body)
            )
        else:
            # Generic handler
            dart_body.extend(
                self._generate_generic_handler(event_name, body, callback_signature)
            )

        # Add original PowerBuilder code as comments if body exists
        if body and not dart_body:
            dart_body.append(f"// TODO: Implement {event_name} handler")
            dart_body.append("// Original PowerBuilder code:")
            for line in body:
                dart_body.append(f"// {line}")

        return dart_body

    def _generate_clicked_handler(
        self, control_type: str, body: list[str]
    ) -> list[str]:
        """Generate handler for clicked events."""
        lines = []

        if control_type.lower() == "commandbutton":
            lines.append("// Handle button click")
            if body:
                # Analyze body for common patterns
                if any("messagebox" in line.lower() for line in body):
                    lines.append("await showDialog(")
                    lines.append("  context: context,")
                    lines.append("  builder: (context) => AlertDialog(")
                    lines.append("    title: const Text('Information'),")
                    lines.append("    content: const Text('Button clicked'),")
                    lines.append("    actions: [")
                    lines.append("      TextButton(")
                    lines.append(
                        "        onPressed: () => Navigator.of(context).pop(),"
                    )
                    lines.append("        child: const Text('OK'),")
                    lines.append("      ),")
                    lines.append("    ],")
                    lines.append("  ),")
                    lines.append(");")
                elif any("close" in line.lower() for line in body):
                    lines.append("Navigator.of(context).pop();")
                elif any("open" in line.lower() for line in body):
                    lines.append("// Navigate to another screen")
                    lines.append("Navigator.of(context).push(")
                    lines.append("  MaterialPageRoute(")
                    lines.append("    builder: (context) => NextScreen(),")
                    lines.append("  ),")
                    lines.append(");")
                else:
                    lines.append("// Add button click logic here")
            else:
                lines.append("// Add button click logic here")
        elif control_type.lower() == "checkbox":
            lines.append("setState(() {")
            lines.append("  // Toggle checkbox state")
            lines.append("  _isChecked = !_isChecked;")
            lines.append("});")
        elif control_type.lower() == "radiobutton":
            lines.append("setState(() {")
            lines.append("  // Update selected radio button")
            lines.append("  _selectedValue = value;")
            lines.append("});")
        else:
            lines.append("// Handle click event")

        return lines

    def _generate_modified_handler(
        self, control_type: str, body: list[str]
    ) -> list[str]:
        """Generate handler for modified/changed events."""
        lines = []

        if control_type.lower() in ["singlelineedit", "multilineedit"]:
            lines.append("setState(() {")
            lines.append("  // Update text value")
            lines.append("  _textValue = value;")
            lines.append("});")

            # Check for validation in body
            if body and any(
                "validation" in line.lower() or "check" in line.lower() for line in body
            ):
                lines.append("")
                lines.append("// Validate input")
                lines.append("if (!_isValidInput(value)) {")
                lines.append("  // Show error")
                lines.append("  ScaffoldMessenger.of(context).showSnackBar(")
                lines.append("    const SnackBar(content: Text('Invalid input')),")
                lines.append("  );")
                lines.append("}")
        elif control_type.lower() in ["dropdownlistbox", "combobox"]:
            lines.append("setState(() {")
            lines.append("  // Update selected value")
            lines.append("  _selectedItem = value;")
            lines.append("});")

            # Check for dependent updates
            if body and any("update" in line.lower() for line in body):
                lines.append("")
                lines.append("// Update dependent controls")
                lines.append("_updateDependentData(value);")
        else:
            lines.append("// Handle value change")
            lines.append("setState(() {});")

        return lines

    def _generate_focus_handler(
        self, event_name: str, control_type: str, body: list[str]
    ) -> list[str]:
        """Generate handler for focus events."""
        lines = []

        if event_name == "getfocus":
            lines.append("// Handle focus gained")
            lines.append("setState(() {")
            lines.append("  _hasFocus = true;")
            lines.append("});")

            if control_type.lower() in ["singlelineedit", "multilineedit"]:
                lines.append("")
                lines.append("// Select all text on focus")
                lines.append("_textController.selection = TextSelection(")
                lines.append("  baseOffset: 0,")
                lines.append("  extentOffset: _textController.text.length,")
                lines.append(");")
        else:  # losefocus
            lines.append("// Handle focus lost")
            lines.append("setState(() {")
            lines.append("  _hasFocus = false;")
            lines.append("});")

            # Check for validation on focus lost
            if body and any("valid" in line.lower() for line in body):
                lines.append("")
                lines.append("// Validate on focus lost")
                lines.append("if (!_validateField()) {")
                lines.append("  // Return focus if validation fails")
                lines.append("  FocusScope.of(context).requestFocus(_focusNode);")
                lines.append("}")

        return lines

    def _generate_selection_changed_handler(
        self, control_type: str, body: list[str]
    ) -> list[str]:
        """Generate handler for selection changed events."""
        lines = []

        if control_type.lower() == "listbox":
            lines.append("// Handle list selection change")
            lines.append("setState(() {")
            lines.append("  _selectedIndex = value;")
            lines.append("});")
            lines.append("")
            lines.append("// Process selection")
            lines.append("if (value >= 0 && value < _items.length) {")
            lines.append("  _processSelectedItem(_items[value]);")
            lines.append("}")
        elif control_type.lower() == "tab":
            lines.append("// Handle tab selection change")
            lines.append("setState(() {")
            lines.append("  _selectedTab = value;")
            lines.append("});")
            lines.append("")
            lines.append("// Load tab content if needed")
            lines.append("_loadTabContent(value);")
        elif control_type.lower() == "treeview":
            lines.append("// Handle tree selection change")
            lines.append("setState(() {")
            lines.append("  _selectedNode = value;")
            lines.append("});")
            lines.append("")
            lines.append("// Process selected node")
            lines.append("_processTreeNode(value);")
        else:
            lines.append("// Handle selection change")
            lines.append("setState(() {});")

        return lines

    def _generate_item_changed_handler(
        self, control_type: str, body: list[str]
    ) -> list[str]:
        """Generate handler for DataWindow item changed events."""
        lines = []

        lines.append("// Handle DataWindow cell edit")
        lines.append(
            "debugPrint('Item changed at row: $row, column: $column, value: $value');"
        )
        lines.append("")
        lines.append("// Validate the new value")
        lines.append("if (!_validateCellValue(column, value)) {")
        lines.append("  // Reject the change")
        lines.append("  return;")
        lines.append("}")
        lines.append("")
        lines.append("// Update the data model")
        lines.append("setState(() {")
        lines.append("  _dataRows[row][column] = value;")
        lines.append("  _isModified = true;")
        lines.append("});")
        lines.append("")
        lines.append("// Check for calculated fields")
        lines.append("if (_hasCalculatedFields(column)) {")
        lines.append("  _updateCalculatedFields(row);")
        lines.append("}")

        return lines

    def _generate_item_error_handler(self, body: list[str]) -> list[str]:
        """Generate handler for DataWindow item error events."""
        lines = []

        lines.append("// Handle DataWindow validation error")
        lines.append("debugPrint('Validation error at row: $row, column: $column');")
        lines.append("debugPrint('Value: $value, Error: $error');")
        lines.append("")
        lines.append("// Show error message")
        lines.append("ScaffoldMessenger.of(context).showSnackBar(")
        lines.append("  SnackBar(")
        lines.append("    content: Text(error),")
        lines.append("    backgroundColor: Colors.red,")
        lines.append("  ),")
        lines.append(");")
        lines.append("")
        lines.append("// Return action to take")
        lines.append("// 0 = Reject and show message")
        lines.append("// 1 = Accept value anyway")
        lines.append("// 2 = Reject but allow focus change")
        lines.append("return 0;")

        return lines

    def _generate_row_focus_changed_handler(self, body: list[str]) -> list[str]:
        """Generate handler for DataWindow row focus changed events."""
        lines = []

        lines.append("// Handle row selection change")
        lines.append("debugPrint('Row focus changed to: $value');")
        lines.append("")
        lines.append("setState(() {")
        lines.append("  _currentRow = value;")
        lines.append("});")
        lines.append("")
        lines.append("// Load row details if needed")
        lines.append("if (value >= 0 && value < _dataRows.length) {")
        lines.append("  _loadRowDetails(_dataRows[value]);")
        lines.append("}")

        return lines

    def _generate_close_query_handler(self, body: list[str]) -> list[str]:
        """Generate handler for window close query events."""
        lines = []

        lines.append("// Check if window can be closed")
        lines.append("if (_hasUnsavedChanges) {")
        lines.append("  // Show confirmation dialog")
        lines.append("  final bool? shouldClose = await showDialog<bool>(")
        lines.append("    context: context,")
        lines.append("    builder: (context) => AlertDialog(")
        lines.append("      title: const Text('Unsaved Changes'),")
        lines.append(
            "      content: const Text('You have unsaved changes. Do you want to close anyway?'),"
        )
        lines.append("      actions: [")
        lines.append("        TextButton(")
        lines.append("          onPressed: () => Navigator.of(context).pop(false),")
        lines.append("          child: const Text('Cancel'),")
        lines.append("        ),")
        lines.append("        TextButton(")
        lines.append("          onPressed: () => Navigator.of(context).pop(true),")
        lines.append("          child: const Text('Close'),")
        lines.append("        ),")
        lines.append("      ],")
        lines.append("    ),")
        lines.append("  );")
        lines.append("  ")
        lines.append("  return shouldClose ?? false;")
        lines.append("}")
        lines.append("")
        lines.append("// Allow close")
        lines.append("return true;")

        return lines

    def _generate_key_handler(self, body: list[str]) -> list[str]:
        """Generate handler for key events."""
        lines = []

        lines.append("// Handle key press")
        lines.append("if (event is KeyDownEvent) {")
        lines.append("  // Check for specific keys")
        lines.append("  if (event.logicalKey == LogicalKeyboardKey.escape) {")
        lines.append("    // Handle ESC key")
        lines.append("    Navigator.of(context).pop();")
        lines.append("    return true;")
        lines.append("  } else if (event.logicalKey == LogicalKeyboardKey.enter) {")
        lines.append("    // Handle Enter key")
        lines.append("    _submitForm();")
        lines.append("    return true;")
        lines.append("  } else if (event.logicalKey == LogicalKeyboardKey.f1) {")
        lines.append("    // Handle F1 for help")
        lines.append("    _showHelp();")
        lines.append("    return true;")
        lines.append("  }")
        lines.append("}")
        lines.append("")
        lines.append("// Key not handled")
        lines.append("return false;")

        return lines

    def _generate_resize_handler(self, body: list[str]) -> list[str]:
        """Generate handler for resize events."""
        lines = []

        lines.append("// Handle window resize")
        lines.append("debugPrint('Window resized to: ${size.width} x ${size.height}');")
        lines.append("")
        lines.append("setState(() {")
        lines.append("  _windowSize = size;")
        lines.append("});")
        lines.append("")
        lines.append("// Adjust layout if needed")
        lines.append("if (size.width < 600) {")
        lines.append("  // Switch to mobile layout")
        lines.append("  _layoutMode = LayoutMode.mobile;")
        lines.append("} else if (size.width < 1200) {")
        lines.append("  // Tablet layout")
        lines.append("  _layoutMode = LayoutMode.tablet;")
        lines.append("} else {")
        lines.append("  // Desktop layout")
        lines.append("  _layoutMode = LayoutMode.desktop;")
        lines.append("}")

        return lines

    def _generate_gesture_handler(
        self, event_name: str, control_type: str, body: list[str]
    ) -> list[str]:
        """Generate handler for gesture events."""
        lines = []

        if event_name == "doubleclicked":
            lines.append("// Handle double tap")
            if control_type.lower() == "listbox":
                lines.append("// Open item details on double tap")
                lines.append("if (_selectedIndex >= 0) {")
                lines.append("  _openItemDetails(_items[_selectedIndex]);")
                lines.append("}")
            else:
                lines.append("// Perform double tap action")
                lines.append("_handleDoubleTap();")
        elif event_name == "rbuttondown":
            lines.append("// Handle right click / secondary tap")
            lines.append("// Show context menu")
            lines.append("_showContextMenu(context);")

        return lines

    def _generate_datawindow_operation_handler(
        self, event_name: str, body: list[str]
    ) -> list[str]:
        """Generate handler for DataWindow operation events."""
        lines = []

        if event_name == "retrievestart":
            lines.append("// Data retrieval started")
            lines.append("setState(() {")
            lines.append("  _isLoading = true;")
            lines.append("  _loadingMessage = 'Loading data...';")
            lines.append("});")
        elif event_name == "retrieveend":
            lines.append("// Data retrieval completed")
            lines.append("setState(() {")
            lines.append("  _isLoading = false;")
            lines.append("  _rowCount = value; // Number of rows retrieved")
            lines.append("});")
            lines.append("")
            lines.append("// Show result message")
            lines.append("if (value == 0) {")
            lines.append("  ScaffoldMessenger.of(context).showSnackBar(")
            lines.append("    const SnackBar(content: Text('No data found')),")
            lines.append("  );")
            lines.append("} else {")
            lines.append("  ScaffoldMessenger.of(context).showSnackBar(")
            lines.append("    SnackBar(content: Text('$value rows retrieved')),")
            lines.append("  );")
            lines.append("}")
        elif event_name == "updatestart":
            lines.append("// Update operation starting")
            lines.append("setState(() {")
            lines.append("  _isSaving = true;")
            lines.append("});")
            lines.append("")
            lines.append("// Validate before saving")
            lines.append("if (!_validateAllData()) {")
            lines.append("  setState(() {")
            lines.append("    _isSaving = false;")
            lines.append("  });")
            lines.append("  return false; // Cancel update")
            lines.append("}")
            lines.append("")
            lines.append("return true; // Allow update")
        elif event_name == "updateend":
            lines.append("// Update operation completed")
            lines.append("setState(() {")
            lines.append("  _isSaving = false;")
            lines.append("  _isModified = false;")
            lines.append("});")
            lines.append("")
            lines.append("// Show result")
            lines.append("if (value) {")
            lines.append("  ScaffoldMessenger.of(context).showSnackBar(")
            lines.append("    const SnackBar(")
            lines.append("      content: Text('Data saved successfully'),")
            lines.append("      backgroundColor: Colors.green,")
            lines.append("    ),")
            lines.append("  );")
            lines.append("} else {")
            lines.append("  ScaffoldMessenger.of(context).showSnackBar(")
            lines.append("    const SnackBar(")
            lines.append("      content: Text('Save operation failed'),")
            lines.append("      backgroundColor: Colors.red,")
            lines.append("    ),")
            lines.append("  );")
            lines.append("}")

        return lines

    def _generate_generic_handler(
        self, event_name: str, body: list[str], signature: str
    ) -> list[str]:
        """Generate generic event handler."""
        lines = []

        lines.append(f"// Handle {event_name} event")

        # Add parameter usage based on signature
        if "ValueChanged<" in signature:
            lines.append("debugPrint('Value changed to: $value');")
            lines.append("setState(() {")
            lines.append("  // Update state with new value")
            lines.append("});")
        elif "Function(" in signature and signature != "VoidCallback":
            lines.append("// Process event parameters")
            lines.append("debugPrint('Event triggered with parameters');")

        # Add common patterns
        if body:
            has_state_change = any(
                "set" in line.lower() or "update" in line.lower() for line in body
            )
            has_navigation = any(
                "open" in line.lower() or "close" in line.lower() for line in body
            )

            if has_state_change:
                lines.append("")
                lines.append("// Update component state")
                lines.append("setState(() {")
                lines.append("  // TODO: Update state based on event")
                lines.append("});")

            if has_navigation:
                lines.append("")
                lines.append("// Handle navigation")
                lines.append("// TODO: Implement navigation logic")

        # Add return statement if needed
        return_type = self._get_return_type_from_signature(signature)
        if return_type and return_type != "void":
            lines.append("")
            if return_type == "bool":
                lines.append("return true; // TODO: Implement return logic")
            elif return_type == "int":
                lines.append("return 0; // TODO: Implement return logic")
            elif return_type.startswith("Future"):
                lines.append("return Future.value(); // TODO: Implement async return")
            else:
                lines.append(f"return null; // TODO: Return {return_type}")

        return lines

    def _to_camel_case(self, name: str) -> str:
        """Convert name to camelCase."""
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)
