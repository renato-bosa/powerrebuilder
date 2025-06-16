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
            },
            
            # Additional PowerBuilder events
            "constructor": {
                "flutter_method": "initState",
                "callback": False,
                "lifecycle": True
            },
            "destructor": {
                "flutter_method": "dispose",
                "callback": False,
                "lifecycle": True
            },
            "dragdrop": {
                "flutter_method": "onDragEnd",
                "callback": True,
                "signature": "Function(DragEndDetails)",
                "widget": "Draggable"
            },
            "dragenter": {
                "flutter_method": "onDragEntered",
                "callback": True,
                "signature": "Function(dynamic)"
            },
            "dragleave": {
                "flutter_method": "onDragExited", 
                "callback": True,
                "signature": "VoidCallback"
            },
            "dragwithin": {
                "flutter_method": "onDragUpdate",
                "callback": True,
                "signature": "Function(DragUpdateDetails)"
            },
            "other": {
                "flutter_method": "onCustomEvent",
                "callback": True,
                "signature": "dynamic Function(dynamic)",
                "return_type": "dynamic"
            },
            "systemerror": {
                "flutter_method": "onError",
                "callback": True,
                "signature": "Function(Object, StackTrace)",
                "widget": "ErrorBoundary"
            },
            "timer": {
                "flutter_method": "onTimer",
                "callback": True,
                "signature": "VoidCallback",
                "widget": "Timer.periodic"
            },
            "help": {
                "flutter_method": "onHelp",
                "callback": True,
                "signature": "VoidCallback"
            },
            "hotlinkalarm": {
                "flutter_method": "onLinkActivated",
                "callback": True,
                "signature": "ValueChanged<String>"
            },
            
            # DataWindow specific events
            "buttonclicked": {
                "flutter_method": "onButtonClicked",
                "callback": True,
                "signature": "Function(int, String)",
                "return_type": "int",
                "return_mapping": {
                    0: "ButtonAction.proceed.index",
                    1: "ButtonAction.cancel.index"
                }
            },
            "buttonclicking": {
                "flutter_method": "onButtonClicking",
                "callback": True,
                "signature": "int Function(int, String)",
                "return_type": "int",
                "return_mapping": {
                    0: "ButtonAction.proceed.index",
                    1: "ButtonAction.cancel.index"
                }
            },
            "clicked": {
                "flutter_method": "onCellClicked",
                "callback": True,
                "signature": "Function(int, String)"
            },
            "doubleclicked": {
                "flutter_method": "onCellDoubleClicked",
                "callback": True,
                "signature": "Function(int, String)"
            },
            "error": {
                "flutter_method": "onDataError",
                "callback": True,
                "signature": "Function(int, String, dynamic)",
                "return_type": "int",
                "return_mapping": {
                    0: "ErrorAction.continue.index",
                    1: "ErrorAction.retry.index",
                    2: "ErrorAction.cancel.index"
                }
            },
            "retrieveerror": {
                "flutter_method": "onRetrieveError",
                "callback": True,
                "signature": "int Function(String, String)",
                "return_type": "int",
                "return_mapping": {
                    0: "0", # Continue
                    1: "1"  # Stop retrieval
                }
            },
            "sqlerror": {
                "flutter_method": "onSqlError",
                "callback": True,
                "signature": "int Function(String, int)",
                "return_type": "int",
                "return_mapping": {
                    0: "SqlErrorAction.continue.index",
                    1: "SqlErrorAction.stop.index",
                    2: "SqlErrorAction.retry.index"
                }
            },
            "validation": {
                "flutter_method": "onValidation",
                "callback": True,
                "signature": "bool Function(int, String, dynamic)",
                "return_type": "bool",
                "return_mapping": {
                    0: "false", # Validation failed
                    1: "true"   # Validation passed
                }
            },
            
            # Tree view events
            "begindrag": {
                "flutter_method": "onDragStart",
                "callback": True,
                "signature": "Function(TreeNode)",
                "widget": "Draggable"
            },
            "beginlabeledit": {
                "flutter_method": "onBeginEdit",
                "callback": True,
                "signature": "bool Function(TreeNode)",
                "return_type": "bool",
                "return_mapping": {
                    0: "true",  # Allow edit
                    1: "false"  # Cancel edit
                }
            },
            "endlabeledit": {
                "flutter_method": "onEndEdit",
                "callback": True,
                "signature": "bool Function(TreeNode, String)",
                "return_type": "bool",
                "return_mapping": {
                    0: "true",  # Accept changes
                    1: "false"  # Cancel changes
                }
            },
            "deleteitem": {
                "flutter_method": "onDeleteItem",
                "callback": True,
                "signature": "bool Function(TreeNode)",
                "return_type": "bool",
                "return_mapping": {
                    0: "true",  # Allow delete
                    1: "false"  # Cancel delete
                }
            },
            "expanding": {
                "flutter_method": "onExpanding",
                "callback": True,
                "signature": "bool Function(TreeNode)",
                "return_type": "bool",
                "return_mapping": {
                    0: "true",  # Allow expand
                    1: "false"  # Cancel expand
                }
            },
            "collapsing": {
                "flutter_method": "onCollapsing",
                "callback": True,
                "signature": "bool Function(TreeNode)",
                "return_type": "bool", 
                "return_mapping": {
                    0: "true",  # Allow collapse
                    1: "false"  # Cancel collapse
                }
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
            stripped = statement.strip()
            
            # Handle return statements
            if stripped.startswith("return"):
                converted_return = self._convert_return_statement(
                    stripped, return_type, return_mapping
                )
                if converted_return:
                    dart_body.append(converted_return)
                    has_return = True
                else:
                    dart_body.append(f"// TODO: Convert return statement: {statement}")
            
            # Handle assignment statements
            elif "=" in stripped and not any(op in stripped for op in ["==", "!=", "<=", ">=", "<>", "+=", "-=", "*=", "/="]):
                converted_assignment = self._convert_assignment_statement(stripped)
                dart_body.append(converted_assignment)
            
            # Handle if statements
            elif stripped.startswith("if ") or stripped.startswith("IF "):
                converted_if = self._convert_if_statement(stripped)
                dart_body.append(converted_if)
            
            # Handle method calls
            elif "(" in stripped and ")" in stripped:
                converted_call = self._convert_method_call(stripped)
                dart_body.append(converted_call)
            
            # Handle common PowerBuilder patterns
            elif stripped.lower().startswith("messagebox"):
                dart_body.append(self._convert_messagebox(stripped))
            elif stripped.lower().startswith("setfocus"):
                dart_body.append("// Request focus")
                dart_body.append("FocusScope.of(context).requestFocus(_focusNode);")
            elif stripped.lower().startswith("close"):
                dart_body.append("Navigator.of(context).pop();")
            elif stripped:
                # Use expression converter for other statements
                try:
                    converted = self.expression_converter.convert_expression(stripped)
                    dart_body.append(f"{converted};")
                except:
                    dart_body.append(f"// TODO: Convert PowerBuilder statement: {statement}")
        
        # Add default return if needed
        if not has_return and return_type:
            default_return = self._get_default_return(return_type, event_name)
            dart_body.append(default_return)
        
        # Add common patterns for events without return types
        if not return_type and not dart_body:
            if event_name.lower() == "clicked":
                dart_body.append("// Handle button click")
            elif event_name.lower() == "modified":
                dart_body.append("// Handle value change")
                dart_body.append("setState(() {");
                dart_body.append("  // Update state here")
                dart_body.append("});")
            elif event_name.lower() in ["getfocus", "losefocus"]:
                dart_body.append("// Handle focus change")
                dart_body.append("setState(() {});")
        
        return dart_body
    
    def _convert_return_statement(self, statement: str, return_type: Optional[str] = None,
                                 return_mapping: Optional[Dict[int, str]] = None) -> Optional[str]:
        """Convert a return statement to Dart.
        
        Args:
            statement: PowerBuilder return statement
            return_type: Expected return type
            return_mapping: Mapping of PowerBuilder return values to Dart values
            
        Returns:
            Converted Dart return statement or None
        """
        import re
        
        # Extract the return value/expression
        match = re.search(r'return\s+(.+?)(?:;|$)', statement, re.IGNORECASE)
        if not match:
            return "return;" if not return_type or return_type == "void" else None
        
        return_expr = match.group(1).strip()
        
        # Check for numeric return with mapping
        if return_mapping:
            try:
                numeric_value = int(return_expr)
                if numeric_value in return_mapping:
                    return f"return {return_mapping[numeric_value]};"
            except ValueError:
                pass
        
        # Handle boolean returns
        if return_type == "bool":
            if return_expr.lower() == "true":
                return "return true;"
            elif return_expr.lower() == "false":
                return "return false;"
            elif return_expr in ["1", "-1"]:
                return "return true;"
            elif return_expr == "0":
                return "return false;"
        
        # Handle object/structure returns
        if return_type and return_type not in ["void", "int", "bool", "String", "double"]:
            # Complex type - try to convert the expression
            try:
                converted_expr = self.expression_converter.convert_expression(return_expr)
                return f"return {converted_expr};"
            except:
                return f"return null; // TODO: Convert return expression: {return_expr}"
        
        # Try general expression conversion
        try:
            converted_expr = self.expression_converter.convert_expression(return_expr)
            return f"return {converted_expr};"
        except:
            return f"return {return_expr}; // TODO: Verify conversion"
    
    def _convert_assignment_statement(self, statement: str) -> str:
        """Convert an assignment statement to Dart."""
        try:
            # Split on first = sign
            parts = statement.split("=", 1)
            if len(parts) == 2:
                lhs = parts[0].strip()
                rhs = parts[1].strip()
                
                # Convert both sides
                converted_lhs = self.expression_converter.convert_expression(lhs)
                converted_rhs = self.expression_converter.convert_expression(rhs)
                
                # Check if we need setState for instance variables
                if lhs.startswith("this.") or (not "." in lhs and not lhs.startswith("_")):
                    return f"setState(() {{ {converted_lhs} = {converted_rhs}; }});"
                else:
                    return f"{converted_lhs} = {converted_rhs};"
        except:
            pass
        
        return f"// TODO: Convert assignment: {statement}"
    
    def _convert_if_statement(self, statement: str) -> str:
        """Convert an if statement to Dart."""
        import re
        
        # Extract condition
        match = re.search(r'if\s+(.+?)\s+then', statement, re.IGNORECASE)
        if match:
            condition = match.group(1)
            try:
                converted_condition = self.expression_converter.convert_expression(condition)
                return f"if ({converted_condition}) {{"
            except:
                return f"if (/* TODO: {condition} */) {{"
        
        return f"// TODO: Convert if statement: {statement}"
    
    def _convert_method_call(self, statement: str) -> str:
        """Convert a method call to Dart."""
        try:
            # Simple conversion attempt
            converted = self.expression_converter.convert_expression(statement)
            if not statement.strip().endswith(";"):
                converted += ";"
            return converted
        except:
            # Handle common PowerBuilder method patterns
            if "." in statement:
                parts = statement.split(".", 1)
                object_name = parts[0].strip()
                method_call = parts[1].strip()
                
                # Convert common object references
                if object_name.lower() == "this":
                    return f"{method_call};"
                elif object_name.lower() == "parent":
                    return f"widget.{method_call};"
                else:
                    return f"{self._to_camel_case(object_name)}.{method_call};"
            
            return f"{statement}; // TODO: Verify method call conversion"
    
    def _convert_messagebox(self, statement: str) -> str:
        """Convert MessageBox call to Flutter dialog."""
        import re
        
        # Extract MessageBox parameters
        match = re.search(r'messagebox\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', 
                         statement, re.IGNORECASE)
        if match:
            title = match.group(1)
            message = match.group(2)
            return f"""showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('{title}'),
        content: Text('{message}'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );"""
        
        return "// TODO: Convert MessageBox call"
    
    def _get_default_return(self, return_type: str, event_name: str) -> str:
        """Get appropriate default return statement."""
        event_lower = event_name.lower()
        
        if return_type == "bool":
            # Event-specific defaults
            if event_lower in ["closequery", "updatestart"]:
                return "return true; // Default: allow action"
            elif event_lower in ["itemchanging", "rowfocuschanging"]:
                return "return true; // Default: allow change"
            elif event_lower == "key":
                return "return false; // Default: key not handled"
            else:
                return "return false; // Default return"
        elif return_type == "int":
            if event_lower == "itemerror":
                return "return ValidationAction.reject.index; // Default: reject with message"
            else:
                return "return 0; // Default return"
        elif return_type == "String":
            return 'return ""; // Default return'
        elif return_type == "double":
            return "return 0.0; // Default return"
        elif return_type.startswith("Future"):
            inner_type = return_type[7:-1] if return_type.startswith("Future<") else "void"
            if inner_type == "bool":
                if event_lower in ["closequery", "updatestart"]:
                    return "return Future.value(true); // Default: allow action"
                else:
                    return "return Future.value(false); // Default return"
            elif inner_type == "int":
                return "return Future.value(0); // Default return"
            else:
                return "return Future.value(); // Default return"
        else:
            return "return null; // Default return"
    
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
        import re
        
        for statement in body:
            stripped = statement.strip()
            if stripped.startswith("return"):
                # Extract the return expression
                match = re.search(r'return\s+(.+?)(?:;|$)', stripped, re.IGNORECASE)
                if match:
                    return_expr = match.group(1).strip()
                    
                    # Check for null returns
                    if return_expr.lower() in ["null", "isnull"]:
                        return "dynamic"
                    
                    # Check for numeric returns
                    if self._extract_return_value(statement) is not None:
                        return "int"
                    
                    # Check for decimal/double returns
                    if re.match(r'^-?\d+\.\d+$', return_expr):
                        return "double"
                    
                    # Check for boolean returns
                    if return_expr.lower() in ["true", "false"]:
                        return "bool"
                    
                    # Check for string returns
                    if (return_expr.startswith('"') and return_expr.endswith('"')) or \
                       (return_expr.startswith("'") and return_expr.endswith("'")):
                        return "String"
                    
                    # Check for array returns
                    if "[" in return_expr and "]" in return_expr:
                        return "List<dynamic>"
                    
                    # Check for object creation
                    if "create" in return_expr.lower() or "new " in return_expr.lower():
                        # Try to extract the type name
                        type_match = re.search(r'(?:create|new)\s+(\w+)', return_expr, re.IGNORECASE)
                        if type_match:
                            type_name = self.type_converter.convert_type(type_match.group(1))
                            return type_name
                    
                    # Check for function/method calls that might return objects
                    if "(" in return_expr and ")" in return_expr:
                        # Common patterns
                        if "getrow" in return_expr.lower():
                            return "Map<String, dynamic>"
                        elif "getitem" in return_expr.lower():
                            return "dynamic"
                        elif "find" in return_expr.lower():
                            return "int"  # Usually returns row number
        
        # Check for async patterns in body
        if any("await" in stmt or "Future" in stmt for stmt in body):
            # Try to find the actual return type
            for stmt in body:
                if "return" in stmt and "Future" not in stmt:
                    base_type = self._infer_return_type([stmt])
                    if base_type:
                        return f"Future<{base_type}>"
            return "Future<void>"
        
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
        validation_enum = """/// Action to take on validation error
enum ValidationAction {
  reject,                      // 0: Reject value and show message
  accept,                      // 1: Accept value
  rejectAllowFocusChange,      // 2: Reject but allow focus change
  rejectNoMessage,             // 3: Reject without showing message
}"""
        enums.append(validation_enum)
        
        # Add ButtonAction enum for button events
        button_enum = """/// Action to take on button click
enum ButtonAction {
  proceed,                     // 0: Continue with action
  cancel,                      // 1: Cancel action
}"""
        enums.append(button_enum)
        
        # Add ErrorAction enum for error events
        error_enum = """/// Action to take on data error
enum ErrorAction {
  continue,                    // 0: Continue processing
  retry,                       // 1: Retry operation
  cancel,                      // 2: Cancel operation
}"""
        enums.append(error_enum)
        
        # Add SqlErrorAction enum for SQL error events
        sql_error_enum = """/// Action to take on SQL error
enum SqlErrorAction {
  continue,                    // 0: Continue processing
  stop,                        // 1: Stop processing
  retry,                       // 2: Retry SQL operation
}"""
        enums.append(sql_error_enum)
        
        return enums
    
    def get_complex_return_type_handlers(self) -> Dict[str, str]:
        """Get handlers for complex return types.
        
        Returns:
            Dictionary mapping event names to custom return type handlers
        """
        return {
            "other": """
  // Handle custom event with dynamic return
  dynamic handleOtherEvent(dynamic eventData) {
    // Process event data
    if (eventData is Map) {
      return {'processed': true, 'timestamp': DateTime.now()};
    } else if (eventData is List) {
      return eventData.map((item) => processItem(item)).toList();
    }
    return null;
  }""",
            
            "systemerror": """
  // Handle system error with proper error boundaries
  void handleSystemError(Object error, StackTrace stackTrace) {
    // Log error
    debugPrint('System error: $error');
    debugPrint('Stack trace: $stackTrace');
    
    // Report to error tracking service
    // ErrorReporting.reportError(error, stackTrace);
    
    // Show user-friendly error dialog
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('System Error'),
        content: Text('An unexpected error occurred: ${error.toString()}'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }""",
        }