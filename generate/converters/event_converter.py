"""PowerBuilder event to Flutter callback converter.

Converts PowerBuilder events and their handlers to appropriate
Flutter callbacks and event handling patterns.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .type_converter import TypeConverter
from .expression_converter import ExpressionConverter

logger = logging.getLogger(__name__)


@dataclass
class FlutterCallback:
    """Represents a Flutter callback definition."""
    name: str
    parameters: List[str]
    return_type: str
    body: List[str]
    is_async: bool = False


class EventConverter:
    """Converts PowerBuilder events to Flutter callbacks."""
    
    def __init__(self, type_converter: Optional[TypeConverter] = None,
                 expression_converter: Optional[ExpressionConverter] = None):
        """Initialize the event converter.
        
        Args:
            type_converter: Type converter instance
            expression_converter: Expression converter instance
        """
        self.type_converter = type_converter or TypeConverter()
        self.expression_converter = expression_converter or ExpressionConverter(self.type_converter)
        
        # PowerBuilder event to Flutter callback mappings
        self.event_map = {
            # Window events
            "open": {
                "flutter_method": "initState",
                "callback": False,
                "lifecycle": True
            },
            "close": {
                "flutter_method": "dispose", 
                "callback": False,
                "lifecycle": True
            },
            "activate": {
                "flutter_method": "onResume",
                "callback": True,
                "widget": "LifecycleObserver"
            },
            "deactivate": {
                "flutter_method": "onPause",
                "callback": True,
                "widget": "LifecycleObserver"
            },
            "resize": {
                "flutter_method": "onResize",
                "callback": True,
                "widget": "LayoutBuilder"
            },
            
            # Control events
            "clicked": {
                "flutter_method": "onPressed",
                "callback": True,
                "signature": "VoidCallback"
            },
            "doubleclicked": {
                "flutter_method": "onDoubleTap",
                "callback": True,
                "widget": "GestureDetector"
            },
            "rightclicked": {
                "flutter_method": "onSecondaryTap",
                "callback": True,
                "widget": "GestureDetector"
            },
            "getfocus": {
                "flutter_method": "onFocusChange",
                "callback": True,
                "signature": "ValueChanged<bool>",
                "condition": "hasFocus == true"
            },
            "losefocus": {
                "flutter_method": "onFocusChange",
                "callback": True,
                "signature": "ValueChanged<bool>",
                "condition": "hasFocus == false"
            },
            "modified": {
                "flutter_method": "onChanged",
                "callback": True,
                "signature": "ValueChanged<String>"
            },
            "itemchanged": {
                "flutter_method": "onChanged",
                "callback": True,
                "signature": "ValueChanged<T>"
            },
            "selectionchanged": {
                "flutter_method": "onSelectionChanged",
                "callback": True,
                "signature": "ValueChanged<T>"
            },
            
            # DataWindow events
            "itemchanged": {
                "flutter_method": "onCellEdit",
                "callback": True,
                "signature": "Function(int, String, dynamic)"
            },
            "itemerror": {
                "flutter_method": "onValidationError",
                "callback": True,
                "signature": "Function(int, String, dynamic, String)"
            },
            "rowfocuschanged": {
                "flutter_method": "onRowSelected",
                "callback": True,
                "signature": "ValueChanged<int>"
            },
            "retrievestart": {
                "flutter_method": "onLoadStart",
                "callback": True,
                "signature": "VoidCallback"
            },
            "retrieveend": {
                "flutter_method": "onLoadEnd",
                "callback": True,
                "signature": "ValueChanged<int>"
            },
            "updatestart": {
                "flutter_method": "onSaveStart",
                "callback": True,
                "signature": "Future<bool> Function()"
            },
            "updateend": {
                "flutter_method": "onSaveEnd",
                "callback": True,
                "signature": "ValueChanged<bool>"
            }
        }
    
    def convert_event(self, event_name: str, parameters: List[Any], body: List[str]) -> Any:
        """Convert a PowerBuilder event to Flutter callback.
        
        Args:
            event_name: Name of the PowerBuilder event
            parameters: Event parameters
            body: Event body statements
            
        Returns:
            Method object representing the Flutter callback
        """
        event_lower = event_name.lower()
        
        # Get mapping for this event
        mapping = self.event_map.get(event_lower, {})
        
        if mapping.get("lifecycle"):
            # Lifecycle method - special handling
            return self._create_lifecycle_method(event_name, mapping, body)
        elif mapping.get("callback"):
            # Regular callback
            return self._create_callback_method(event_name, mapping, parameters, body)
        else:
            # Unknown event - create generic handler
            return self._create_generic_handler(event_name, parameters, body)
    
    def _create_lifecycle_method(self, event_name: str, mapping: Dict, body: List[str]) -> Any:
        """Create a lifecycle method."""
        from .ast_converter import Method
        
        flutter_method = mapping["flutter_method"]
        
        # Convert body statements
        dart_body = self._convert_event_body(body, event_name)
        
        # Add super call for lifecycle methods
        if flutter_method == "initState":
            dart_body.insert(0, "super.initState();")
        elif flutter_method == "dispose":
            dart_body.append("super.dispose();")
        
        return Method(
            name=flutter_method,
            return_type="void",
            dart_return_type="void",
            parameters=[],
            body=dart_body,
            is_event=True,
            access_modifier="protected"
        )
    
    def _create_callback_method(self, event_name: str, mapping: Dict, 
                               parameters: List[Any], body: List[str]) -> Any:
        """Create a callback method."""
        from .ast_converter import Method, Variable
        
        flutter_method = mapping["flutter_method"]
        signature = mapping.get("signature", "VoidCallback")
        
        # Determine parameters based on signature
        dart_params = self._get_callback_parameters(signature)
        
        # Convert body statements
        dart_body = self._convert_event_body(body, event_name)
        
        # Determine if async
        is_async = "Future" in signature or self._needs_async(dart_body)
        
        # Determine return type
        return_type = self._get_callback_return_type(signature)
        
        # Create method name
        method_name = f"_{self._to_camel_case(event_name)}Handler"
        
        return Method(
            name=method_name,
            return_type=return_type,
            dart_return_type=return_type,
            parameters=dart_params,
            body=dart_body,
            is_event=True,
            is_async=is_async,
            access_modifier="private"
        )
    
    def _create_generic_handler(self, event_name: str, parameters: List[Any], 
                               body: List[str]) -> Any:
        """Create a generic event handler."""
        from .ast_converter import Method
        
        # Convert parameters
        dart_params = []
        for param in parameters:
            if hasattr(param, 'dart_type'):
                dart_params.append(param)
        
        # Convert body
        dart_body = self._convert_event_body(body, event_name)
        
        # Check if async
        is_async = self._needs_async(dart_body)
        
        method_name = f"_{self._to_camel_case(event_name)}Handler"
        
        return Method(
            name=method_name,
            return_type="void",
            dart_return_type="void",
            parameters=dart_params,
            body=dart_body,
            is_event=True,
            is_async=is_async,
            access_modifier="private"
        )
    
    def _get_callback_parameters(self, signature: str) -> List[Any]:
        """Get parameters for a callback based on signature."""
        from .ast_converter import Variable
        
        params = []
        
        if signature == "VoidCallback":
            # No parameters
            pass
        elif signature == "ValueChanged<String>":
            params.append(Variable(
                name="value",
                type="string",
                dart_type="String"
            ))
        elif signature == "ValueChanged<bool>":
            params.append(Variable(
                name="value", 
                type="boolean",
                dart_type="bool"
            ))
        elif signature == "ValueChanged<int>":
            params.append(Variable(
                name="value",
                type="integer", 
                dart_type="int"
            ))
        elif signature == "ValueChanged<T>":
            params.append(Variable(
                name="value",
                type="any",
                dart_type="dynamic"
            ))
        elif signature == "Function(int, String, dynamic)":
            params.extend([
                Variable(name="rowIndex", type="integer", dart_type="int"),
                Variable(name="columnName", type="string", dart_type="String"),
                Variable(name="value", type="any", dart_type="dynamic")
            ])
        
        return params
    
    def _get_callback_return_type(self, signature: str) -> str:
        """Get return type for a callback signature."""
        if "Future<bool>" in signature:
            return "Future<bool>"
        elif "Future" in signature:
            return "Future<void>"
        else:
            return "void"
    
    def _convert_event_body(self, body: List[str], event_name: str) -> List[str]:
        """Convert event body statements to Dart."""
        dart_body = []
        
        for statement in body:
            # This would use the expression converter
            # For now, just add a comment
            dart_body.append(f"// TODO: Convert PowerBuilder statement: {statement}")
        
        # Add common patterns
        if event_name.lower() == "clicked":
            if not dart_body:
                dart_body.append("// Handle button click")
        elif event_name.lower() == "modified":
            if not dart_body:
                dart_body.append("// Handle value change")
                dart_body.append("setState(() {});")
        
        return dart_body
    
    def _needs_async(self, body: List[str]) -> bool:
        """Check if method needs to be async."""
        async_keywords = ["await", "Future", "async", "then"]
        body_text = " ".join(body)
        return any(keyword in body_text for keyword in async_keywords)
    
    def _to_camel_case(self, name: str) -> str:
        """Convert name to camelCase."""
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
    
    def get_event_widget_wrapper(self, event_name: str) -> Optional[str]:
        """Get the widget wrapper needed for an event.
        
        Args:
            event_name: PowerBuilder event name
            
        Returns:
            Flutter widget name if wrapper is needed
        """
        mapping = self.event_map.get(event_name.lower(), {})
        return mapping.get("widget")
    
    def get_event_registration(self, event_name: str, handler_name: str) -> str:
        """Get the event registration code.
        
        Args:
            event_name: PowerBuilder event name
            handler_name: Generated handler method name
            
        Returns:
            Flutter event registration code
        """
        mapping = self.event_map.get(event_name.lower(), {})
        flutter_method = mapping.get("flutter_method", event_name)
        
        # Generate registration based on event type
        if event_name.lower() == "clicked":
            return f"{flutter_method}: {handler_name}"
        elif event_name.lower() in ["modified", "itemchanged"]:
            return f"{flutter_method}: (value) => {handler_name}(value)"
        else:
            return f"{flutter_method}: {handler_name}"