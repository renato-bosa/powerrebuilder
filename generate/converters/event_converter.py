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
            "closequery": {
                "flutter_method": "onCloseQuery",
                "callback": True,
                "signature": "Future<bool> Function()",
                "return_type": "bool",
                "return_mapping": {
                    0: "true",   # Allow close
                    1: "false"   # Prevent close
                }
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
            "key": {
                "flutter_method": "onKey",
                "callback": True,
                "signature": "bool Function(KeyEvent)",
                "return_type": "bool",
                "return_mapping": {
                    0: "false",  # Key not processed
                    1: "true"    # Key processed
                }
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
            "itemchanging": {
                "flutter_method": "onChanging",
                "callback": True,
                "signature": "bool Function(dynamic, dynamic)",
                "return_type": "bool",
                "return_mapping": {
                    0: "true",   # Accept change
                    1: "false"   # Reject change
                }
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
                "signature": "int Function(int, String, dynamic, String)",
                "return_type": "int",
                "return_mapping": {
                    0: "ValidationAction.reject.index",
                    1: "ValidationAction.accept.index",
                    2: "ValidationAction.rejectAllowFocusChange.index",
                    3: "ValidationAction.rejectNoMessage.index"
                }
            },
            "rowfocuschanged": {
                "flutter_method": "onRowSelected",
                "callback": True,
                "signature": "ValueChanged<int>"
            },
            "rowfocuschanging": {
                "flutter_method": "onRowSelecting",
                "callback": True,
                "signature": "bool Function(int, int)",
                "return_type": "bool",
                "return_mapping": {
                    0: "true",   # Allow row change
                    1: "false"   # Prevent row change
                }
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
                "signature": "Future<bool> Function()",
                "return_type": "bool",
                "return_mapping": {
                    0: "true",   # Allow update
                    1: "false"   # Prevent update
                }
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
        
        # Get return type and mapping from configuration
        return_type = mapping.get("return_type")
        return_mapping = mapping.get("return_mapping", {})
        
        # Convert body statements with return type info
        dart_body = self._convert_event_body(body, event_name, return_type, return_mapping)
        
        # Determine if async
        is_async = "Future" in signature or self._needs_async(dart_body)
        
        # Determine return type from signature or mapping
        if return_type:
            dart_return_type = "Future<bool>" if is_async and return_type == "bool" else return_type
        else:
            dart_return_type = self._get_callback_return_type(signature)
        
        # Create method name
        method_name = f"_{self._to_camel_case(event_name)}Handler"
        
        return Method(
            name=method_name,
            return_type=dart_return_type,
            dart_return_type=dart_return_type,
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
        
        # Try to infer return type from body
        inferred_return_type = self._infer_return_type(body)
        
        # Convert body
        dart_body = self._convert_event_body(body, event_name, inferred_return_type)
        
        # Check if async
        is_async = self._needs_async(dart_body)
        
        # Determine dart return type
        if inferred_return_type:
            dart_return_type = f"Future<{inferred_return_type}>" if is_async else inferred_return_type
        else:
            dart_return_type = "Future<void>" if is_async else "void"
        
        method_name = f"_{self._to_camel_case(event_name)}Handler"
        
        return Method(
            name=method_name,
            return_type=dart_return_type,
            dart_return_type=dart_return_type,
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
        elif signature == "int Function(int, String, dynamic, String)":
            params.extend([
                Variable(name="rowIndex", type="integer", dart_type="int"),
                Variable(name="columnName", type="string", dart_type="String"),
                Variable(name="value", type="any", dart_type="dynamic"),
                Variable(name="errorMessage", type="string", dart_type="String")
            ])
        elif signature == "bool Function(KeyEvent)":
            params.append(Variable(
                name="event",
                type="KeyEvent",
                dart_type="KeyEvent"
            ))
        elif signature == "bool Function(dynamic, dynamic)":
            params.extend([
                Variable(name="oldValue", type="any", dart_type="dynamic"),
                Variable(name="newValue", type="any", dart_type="dynamic")
            ])
        elif signature == "bool Function(int, int)":
            params.extend([
                Variable(name="currentRow", type="integer", dart_type="int"),
                Variable(name="newRow", type="integer", dart_type="int")
            ])
        elif signature == "Future<bool> Function()":
            # No parameters for async bool functions
            pass
        
        return params
    
    def _get_callback_return_type(self, signature: str) -> str:
        """Get return type for a callback signature."""
        if "Future<bool>" in signature:
            return "Future<bool>"
        elif "Future<int>" in signature:
            return "Future<int>"
        elif "Future" in signature:
            return "Future<void>"
        elif "bool Function" in signature:
            return "bool"
        elif "int Function" in signature:
            return "int"
        else:
            return "void"
    
    def _convert_event_body(self, body: List[str], event_name: str, 
                          return_type: Optional[str] = None, 
                          return_mapping: Optional[Dict[int, str]] = None) -> List[str]:
        """Convert event body statements to Dart.
        
        Args:
            body: PowerBuilder event body statements
            event_name: Name of the event
            return_type: Expected return type for the event
            return_mapping: Mapping of PowerBuilder return values to Dart values
        """
        dart_body = []
        has_return = False
        
        for statement in body:
            # Check for return statements
            if statement.strip().startswith("return") and return_mapping:
                # Extract return value
                return_match = self._extract_return_value(statement)
                if return_match is not None and return_match in return_mapping:
                    dart_body.append(f"return {return_mapping[return_match]};")
                    has_return = True
                elif return_match is not None:
                    # Direct return value without mapping
                    dart_body.append(f"return {return_match};")
                    has_return = True
                else:
                    dart_body.append(f"// TODO: Convert return statement: {statement}")
            else:
                # This would use the expression converter
                # For now, just add a comment
                dart_body.append(f"// TODO: Convert PowerBuilder statement: {statement}")
        
        # Add default return if needed
        if not has_return and return_type:
            if return_type == "bool":
                if event_name.lower() in ["closequery", "itemchanging", "rowfocuschanging"]:
                    dart_body.append("return true; // Default: allow action")
                else:
                    dart_body.append("return false; // Default return")
            elif return_type == "int":
                dart_body.append("return 0; // Default return")
        
        # Add common patterns for events without return types
        if not return_type:
            if event_name.lower() == "clicked":
                if not dart_body:
                    dart_body.append("// Handle button click")
            elif event_name.lower() == "modified":
                if not dart_body:
                    dart_body.append("// Handle value change")
                    dart_body.append("setState(() {});")
        
        return dart_body
    
    def _extract_return_value(self, statement: str) -> Optional[int]:
        """Extract numeric return value from a return statement."""
        import re
        
        # Match "return <number>" pattern
        match = re.search(r'return\s+(-?\d+)', statement.strip())
        if match:
            return int(match.group(1))
        return None
    
    def _infer_return_type(self, body: List[str]) -> Optional[str]:
        """Infer return type from event body statements."""
        for statement in body:
            stripped = statement.strip()
            if stripped.startswith("return"):
                # Check for numeric returns
                if self._extract_return_value(statement) is not None:
                    return "int"
                # Check for boolean returns
                elif "true" in stripped.lower() or "false" in stripped.lower():
                    return "bool"
                # Check for string returns
                elif '"' in stripped or "'" in stripped:
                    return "String"
        return None
    
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
        signature = mapping.get("signature", "")
        
        # Generate registration based on event type and signature
        if "ValueChanged" in signature:
            return f"{flutter_method}: (value) => {handler_name}(value)"
        elif "Function(" in signature and signature != "VoidCallback":
            # Extract parameter names from signature
            if event_name.lower() == "itemerror":
                return f"{flutter_method}: (row, col, val, err) => {handler_name}(row, col, val, err)"
            elif event_name.lower() == "itemchanging":
                return f"{flutter_method}: (oldVal, newVal) => {handler_name}(oldVal, newVal)"
            elif event_name.lower() == "rowfocuschanging":
                return f"{flutter_method}: (current, next) => {handler_name}(current, next)"
            else:
                return f"{flutter_method}: {handler_name}"
        else:
            return f"{flutter_method}: {handler_name}"
    
    def get_event_enums(self) -> List[str]:
        """Get any enums needed for event handling.
        
        Returns:
            List of enum definitions
        """
        enums = []
        
        # Add ValidationAction enum for itemerror event
        validation_enum = """
/// Action to take on validation error
enum ValidationAction {
  reject,                      // 0: Reject value and show message
  accept,                      // 1: Accept value
  rejectAllowFocusChange,      // 2: Reject but allow focus change
  rejectNoMessage,             // 3: Reject without showing message
}
"""
        enums.append(validation_enum.strip())
        
        return enums