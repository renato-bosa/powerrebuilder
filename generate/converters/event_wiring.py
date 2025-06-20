"""Event wiring system for connecting PowerBuilder events to Flutter callbacks.

This module handles the mapping and wiring of PowerBuilder events to Flutter
widget callbacks, ensuring proper event handling in the generated Flutter code.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

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
    additional_properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_properties is None:
            self.additional_properties = {}


class EventWiringSystem:
    """System for wiring PowerBuilder events to Flutter callbacks."""
    
    def __init__(self, event_converter=None):
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
                "rbuttondown": "onSecondaryTap"
            },
            "picturebutton": {
                "clicked": "onPressed",
                "doubleclicked": "onDoubleTap",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange"
            },
            "singlelineedit": {
                "modified": "onChanged",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange",
                "key": "onSubmitted"
            },
            "multilineedit": {
                "modified": "onChanged",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange"
            },
            "checkbox": {
                "clicked": "onChanged",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange"
            },
            "radiobutton": {
                "clicked": "onChanged",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange"
            },
            "dropdownlistbox": {
                "selectionchanged": "onChanged",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange"
            },
            "listbox": {
                "selectionchanged": "onTap",
                "doubleclicked": "onDoubleTap",
                "getfocus": "onFocusChange",
                "losefocus": "onFocusChange"
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
                "updateend": "onSaveEnd"
            },
            "treeview": {
                "selectionchanged": "onSelectionChanged",
                "expanding": "onExpanding",
                "collapsing": "onCollapsing",
                "beginlabeledit": "onBeginEdit",
                "endlabeledit": "onEndEdit",
                "deleteitem": "onDeleteItem",
                "doubleclicked": "onNodeDoubleTap"
            },
            "tab": {
                "selectionchanged": "onTabChanged",
                "selectionchanging": "onTabChanging"
            },
            "window": {
                "open": "initState",
                "close": "dispose",
                "closequery": "onCloseQuery",
                "activate": "onResume",
                "deactivate": "onPause",
                "resize": "onResize",
                "key": "onKey"
            },
            "picture": {
                "clicked": "onTap",
                "doubleclicked": "onDoubleTap",
                "rbuttondown": "onSecondaryTap"
            },
            "statictext": {
                "clicked": "onTap",
                "doubleclicked": "onDoubleTap"
            },
            "groupbox": {
                "clicked": "onTap"
            },
            "htrackbar": {
                "valuechanged": "onChanged",
                "pageup": "onChangeStart",
                "pagedown": "onChangeEnd"
            },
            "vtrackbar": {
                "valuechanged": "onChanged",
                "pageup": "onChangeStart",
                "pagedown": "onChangeEnd"
            },
            "spin": {
                "valuechanged": "onChanged"
            },
            "datepicker": {
                "valuechanged": "onDateChanged",
                "dropdown": "onTap"
            },
            "monthcalendar": {
                "datechanged": "onDaySelected",
                "clicked": "onDaySelected"
            }
        }
        
        # Controls that need GestureDetector wrapper for certain events
        self.gesture_detector_events = {
            "clicked": ["statictext", "picture", "groupbox", "rectangle", "oval", "line"],
            "doubleclicked": ["statictext", "picture", "groupbox"],
            "rbuttondown": ["picture", "statictext", "commandbutton"]
        }
        
        # Controls that need FocusNode for focus events
        self.focus_node_controls = [
            "singlelineedit", "multilineedit", "editmask", 
            "dropdownlistbox", "listbox", "checkbox", "radiobutton",
            "commandbutton", "picturebutton", "treeview"
        ]
    
    def wire_events(self, window_model: dict) -> Dict[str, Any]:
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
        control_lookup = {
            control.get("name", ""): control 
            for control in controls
        }
        
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
                        control, event_type, event, window_model
                    )
                    if wiring:
                        wirings.append(wiring)
                        
                        # Track additional requirements
                        if wiring.needs_focus_node and control_name not in focus_nodes_needed:
                            focus_nodes_needed.append(control_name)
                        
                        if wiring.needs_gesture_detector and control_name not in gesture_detectors_needed:
                            gesture_detectors_needed.append(control_name)
                        
                        # Add event handler method
                        handler_method = self._create_event_handler_method(wiring, event)
                        if handler_method:
                            event_handlers.append(handler_method)
            else:
                # Window-level event
                if event_type:
                    wiring = self._create_window_event_wiring(event_type, event)
                    if wiring:
                        wirings.append(wiring)
                        
                        # Add event handler method if not lifecycle
                        if event_type not in ["open", "close", "constructor", "destructor"]:
                            handler_method = self._create_event_handler_method(wiring, event)
                            if handler_method:
                                event_handlers.append(handler_method)
        
        # Also check for events embedded in control definitions
        for control in controls:
            control_events = control.get("events", [])
            for event in control_events:
                event_type = event.get("name", "").lower()
                wiring = self._create_event_wiring(
                    control, event_type, event, window_model
                )
                if wiring:
                    wirings.append(wiring)
                    
                    if wiring.needs_focus_node and control["name"] not in focus_nodes_needed:
                        focus_nodes_needed.append(control["name"])
                    
                    if wiring.needs_gesture_detector and control["name"] not in gesture_detectors_needed:
                        gesture_detectors_needed.append(control["name"])
                    
                    handler_method = self._create_event_handler_method(wiring, event)
                    if handler_method:
                        event_handlers.append(handler_method)
        
        return {
            "wirings": wirings,
            "focus_nodes": focus_nodes_needed,
            "gesture_detectors": gesture_detectors_needed,
            "event_handlers": event_handlers,
            "state_variables": self._extract_state_for_events(wirings, controls)
        }
    
    def _parse_event_name(self, event_name: str) -> Tuple[Optional[str], Optional[str]]:
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
            prefixes = ["cb", "pb", "sle", "mle", "rb", "cb", "ddlb", "lb", "dw", "tv", "tab"]
            for i, part in enumerate(parts):
                if part.lower() in prefixes:
                    # Found control prefix
                    control_parts = parts[:i+2]  # Include prefix and name
                    event_parts = parts[i+2:]
                    if event_parts:
                        return "_".join(control_parts), "_".join(event_parts).lower()
        
        # Assume it's a window-level event
        return None, event_name.lower()
    
    def _create_event_wiring(self, control: dict, event_type: str, 
                           event: dict, window_model: dict) -> Optional[EventWiring]:
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
            logger.warning(f"No Flutter callback mapping for {control_type}.{event_type}")
            return None
        
        # Generate handler method name
        handler_name = f"_{self._to_camel_case(control_name)}{self._to_pascal_case(event_type)}"
        
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
            additional_properties=additional_props
        )
    
    def _create_window_event_wiring(self, event_type: str, event: dict) -> Optional[EventWiring]:
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
            callback_signature=callback_signature
        )
    
    def _get_flutter_callback(self, control_type: str, event_type: str) -> Optional[str]:
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
            ("datawindow", "itemchanged"): "Function(int row, String column, dynamic value)",
            ("datawindow", "itemerror"): "int Function(int row, String column, dynamic value, String error)",
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
            ("monthcalendar", "datechanged"): "Function(DateTime selectedDay, DateTime focusedDay)"
        }
        
        # Check for specific signature
        signature_key = (control_type.lower(), event_type.lower())
        if signature_key in signatures:
            return signatures[signature_key]
        
        # Default signatures by event type
        if "changed" in event_type:
            return "ValueChanged<dynamic>"
        elif "clicked" in event_type or "tap" in event_type:
            return "VoidCallback"
        elif "focus" in event_type:
            return "ValueChanged<bool>"
        else:
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
    
    def _get_additional_properties(self, control_type: str, event_type: str) -> Dict[str, Any]:
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
    
    def _create_event_handler_method(self, wiring: EventWiring, event: dict) -> Dict[str, Any]:
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
                self._get_return_type_from_signature(wiring.callback_signature)
            )
        else:
            # Basic conversion
            dart_body = [f"// TODO: Implement {wiring.event_name} handler"]
            if event.get("body"):
                dart_body.append(f"// Original PowerBuilder code:")
                for line in event.get("body", []):
                    dart_body.append(f"// {line}")
        
        # Extract parameters from signature
        params = self._extract_params_from_signature(wiring.callback_signature)
        
        # Determine if async
        is_async = "Future" in wiring.callback_signature or any("await" in line for line in dart_body)
        
        return {
            "name": wiring.handler_name,
            "return_type": self._get_return_type_from_signature(wiring.callback_signature),
            "params": params,
            "is_async": is_async,
            "body": "\n    ".join(dart_body),
            "is_event_handler": True,
            "wiring": wiring
        }
    
    def _extract_state_for_events(self, wirings: List[EventWiring], controls: List[dict]) -> List[dict]:
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
            state_vars.append({
                "name": f"_{self._to_camel_case(control_name)}HasFocus",
                "type": "bool",
                "initial": "false",
                "description": f"Focus state for {control_name}"
            })
        
        # Add value state for controls that need it
        for control in controls:
            control_type = control.get("type", "").lower()
            control_name = control.get("name", "")
            
            if control_type in ["htrackbar", "vtrackbar", "slider"]:
                state_vars.append({
                    "name": f"_{self._to_camel_case(control_name)}Value",
                    "type": "double",
                    "initial": "0.0",
                    "description": f"Current value for {control_name}"
                })
            elif control_type == "checkbox":
                state_vars.append({
                    "name": f"_{self._to_camel_case(control_name)}Checked",
                    "type": "bool?",
                    "initial": "false",
                    "description": f"Checked state for {control_name}"
                })
            elif control_type == "radiobutton":
                # Group radio buttons
                group = control.get("group", "default")
                state_vars.append({
                    "name": f"_selected{self._to_pascal_case(group)}Radio",
                    "type": "String?",
                    "initial": "null",
                    "description": f"Selected radio button in {group} group"
                })
        
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
        elif "Future<" in signature:
            return "Future<void>"
        elif "bool Function" in signature:
            return "bool"
        elif "int Function" in signature:
            return "int"
        elif signature == "VoidCallback":
            return "void"
        else:
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
        elif signature == "ValueChanged<String>":
            return "String value"
        elif signature == "ValueChanged<String?>":
            return "String? value"
        elif signature == "ValueChanged<bool>":
            return "bool value"
        elif signature == "ValueChanged<bool?>":
            return "bool? value"
        elif signature == "ValueChanged<int>":
            return "int value"
        elif signature == "ValueChanged<double>":
            return "double value"
        elif signature == "ValueChanged<DateTime?>":
            return "DateTime? value"
        elif signature == "ValueChanged<dynamic>":
            return "dynamic value"
        elif "Function(" in signature:
            # Extract parameters from function signature
            import re
            match = re.search(r'Function\((.*?)\)', signature)
            if match:
                return match.group(1)
        elif signature == "bool Function(KeyEvent event)":
            return "KeyEvent event"
        elif signature == "Function(Size size)":
            return "Size size"
        
        return ""
    
    def generate_control_with_events(self, control: dict, wirings: List[EventWiring]) -> str:
        """Generate Flutter widget code with event handlers wired up.
        
        Args:
            control: Control dictionary
            wirings: List of EventWiring objects for this control
            
        Returns:
            Flutter widget code with events
        """
        control_type = control.get("type", "").lower()
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
            else:
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
    
    def _build_widget_code(self, widget_type: str, properties: dict, control: dict) -> str:
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
                if key != "controller" and key != "decoration":
                    prop_strings.append(f"{key}: {value}")
            
            return f"TextField(\n        {',\n        '.join(prop_strings)},\n      )"
        
        elif widget_type == "Checkbox":
            value_name = f"_{self._to_camel_case(control_name)}Checked"
            return f"""Checkbox(
        value: {value_name},
        onChanged: {properties.get('onChanged', '_handleCheckboxChange')},
        tristate: {properties.get('tristate', flutter_props.get('tristate', 'false'))},
      )"""
        
        elif widget_type == "ElevatedButton":
            button_text = flutter_props.get('_buttonText', control.get('text', 'Button'))
            return f"""ElevatedButton(
        onPressed: {properties.get('onPressed', 'null')},
        child: Text('{button_text}'),
      )"""
        
        elif widget_type == "IconButton":
            icon_data = flutter_props.get('_iconData', 'Icons.help')
            tooltip = flutter_props.get('tooltip', control.get('text', ''))
            return f"""IconButton(
        icon: Icon({icon_data}),
        onPressed: {properties.get('onPressed', 'null')},
        tooltip: '{tooltip}',
      )"""
        
        elif widget_type == "Text":
            text_data = flutter_props.get('data', control.get('text', control_name))
            style = flutter_props.get('style')
            if style:
                return f"Text('{text_data}', style: {style})"
            else:
                return f"Text('{text_data}')"
        
        elif widget_type == "DropdownButton":
            items = flutter_props.get('_items', '[]')
            value = flutter_props.get('value', 'null')
            return f"""DropdownButton<String>(
        value: {value},
        items: {items},
        onChanged: {properties.get('onChanged', '(value) {}')},
      )"""
        
        else:
            # Generic widget
            # Merge flutter_properties with event properties
            all_props = {}
            all_props.update(flutter_props)
            all_props.update(properties)
            
            if all_props:
                prop_strings = []
                for key, value in all_props.items():
                    if not key.startswith('_'):  # Skip internal properties
                        prop_strings.append(f"{key}: {value}")
                
                if prop_strings:
                    return f"{widget_type}(\n        {',\n        '.join(prop_strings)},\n      )"
            
            return f"{widget_type}()"
    
    def _wrap_in_gesture_detector(self, child_code: str, gesture_props: dict) -> str:
        """Wrap widget in GestureDetector."""
        prop_strings = [f"{key}: {value}" for key, value in gesture_props.items()]
        
        return f"""GestureDetector(
        {',\n        '.join(prop_strings)},
        child: {child_code},
      )"""
    
    def _wrap_in_focus(self, child_code: str, control_name: str, 
                      focus_wirings: List[EventWiring]) -> str:
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
    
    def _to_camel_case(self, name: str) -> str:
        """Convert name to camelCase."""
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)