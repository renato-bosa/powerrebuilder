"""PowerBuilder event to Flutter callback converter.

Converts PowerBuilder events and their handlers to appropriate
Flutter callbacks and event handling patterns.
"""

import logging
from typing import Any
from dataclasses import dataclass

from .type_converter import TypeConverter
from .expression_converter import ExpressionConverter

logger = logging.getLogger(__name__)


@dataclass
class FlutterCallback:
    """Represents a Flutter callback definition."""
    name: str
    parameters: list[str]
    return_type: str
    body: list[str]
    is_async: bool = False


class EventConverter:
    """Converts PowerBuilder events to Flutter callbacks."""
    
    def __init__(self, type_converter: TypeConverter | None = None, expression_converter: ExpressionConverter | None = None) -> None:

    
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
                "flutter_method": "initState", "callback": False, "lifecycle": True
            }, "close": {
                "flutter_method": "dispose", "callback": False, "lifecycle": True
            }, "closequery": {
                "flutter_method": "onCloseQuery", "callback": True, "signature": "Future<bool> Function()", "return_type": "bool", "return_mapping": {
                    0: "true", # Allow close
                    1: "false"   # Prevent close
                }
            }, "activate": {
                "flutter_method": "onResume", "callback": True, "widget": "LifecycleObserver"
            }, "deactivate": {
                "flutter_method": "onPause", "callback": True, "widget": "LifecycleObserver"
            }, "resize": {
                "flutter_method": "onResize", "callback": True, "widget": "LayoutBuilder"
            }, "key": {
                "flutter_method": "onKey", "callback": True, "signature": "bool Function(KeyEvent)", "return_type": "bool", "return_mapping": {
                    0: "false", # Key not processed
                    1: "true"    # Key processed
                }
            }, # Control events
            "clicked": {
                "flutter_method": "onPressed", "callback": True, "signature": "VoidCallback"
            }, "doubleclicked": {
                "flutter_method": "onDoubleTap", "callback": True, "widget": "GestureDetector"
            }, "rightclicked": {
                "flutter_method": "onSecondaryTap", "callback": True, "widget": "GestureDetector"
            }, "getfocus": {
                "flutter_method": "onFocusChange", "callback": True, "signature": "ValueChanged<bool>", "condition": "hasFocus == true"
            }, "losefocus": {
                "flutter_method": "onFocusChange", "callback": True, "signature": "ValueChanged<bool>", "condition": "hasFocus == false"
            }, "modified": {
                "flutter_method": "onChanged", "callback": True, "signature": "ValueChanged<String>"
            }, "itemchanged": {
                "flutter_method": "onChanged", "callback": True, "signature": "ValueChanged<T>"
            }, "itemchanging": {
                "flutter_method": "onChanging", "callback": True, "signature": "bool Function(dynamic, dynamic)", "return_type": "bool", "return_mapping": {
                    0: "true", # Accept change
                    1: "false"   # Reject change
                }
            }, "selectionchanged": {
                "flutter_method": "onSelectionChanged", "callback": True, "signature": "ValueChanged<T>"
            }, # DataWindow events
            "itemchanged": {
                "flutter_method": "onCellEdit", "callback": True, "signature": "Function(int, String, dynamic)"
            }, "itemerror": {
                "flutter_method": "onValidationError", "callback": True, "signature": "int Function(int, String, dynamic, String)", "return_type": "int", "return_mapping": {
                    0: "ValidationAction.reject.index", 1: "ValidationAction.accept.index", 2: "ValidationAction.rejectAllowFocusChange.index", 3: "ValidationAction.rejectNoMessage.index"
                }
            }, "rowfocuschanged": {
                "flutter_method": "onRowSelected", "callback": True, "signature": "ValueChanged<int>"
            }, "rowfocuschanging": {
                "flutter_method": "onRowSelecting", "callback": True, "signature": "bool Function(int, int)", "return_type": "bool", "return_mapping": {
                    0: "true", # Allow row change
                    1: "false"   # Prevent row change
                }
            }, "retrievestart": {
                "flutter_method": "onLoadStart", "callback": True, "signature": "VoidCallback"
            }, "retrieveend": {
                "flutter_method": "onLoadEnd", "callback": True, "signature": "ValueChanged<int>"
            }, "updatestart": {
                "flutter_method": "onSaveStart", "callback": True, "signature": "Future<bool> Function()", "return_type": "bool", "return_mapping": {
                    0: "true", # Allow update
                    1: "false"   # Prevent update
                }
            }, "updateend": {
                "flutter_method": "onSaveEnd", "callback": True, "signature": "ValueChanged<bool>"
            }, # Additional PowerBuilder events
            "constructor": {
                "flutter_method": "initState", "callback": False, "lifecycle": True
            }, "destructor": {
                "flutter_method": "dispose", "callback": False, "lifecycle": True
            }, "dragdrop": {
                "flutter_method": "onDragEnd", "callback": True, "signature": "Function(DragEndDetails)", "widget": "Draggable"
            }, "dragenter": {
                "flutter_method": "onDragEntered", "callback": True, "signature": "Function(dynamic)"
            }, "dragleave": {
                "flutter_method": "onDragExited", "callback": True, "signature": "VoidCallback"
            }, "dragwithin": {
                "flutter_method": "onDragUpdate", "callback": True, "signature": "Function(DragUpdateDetails)"
            }, "other": {
                "flutter_method": "onCustomEvent", "callback": True, "signature": "dynamic Function(dynamic)", "return_type": "dynamic"
            }, "systemerror": {
                "flutter_method": "onError", "callback": True, "signature": "Function(Object, StackTrace)", "widget": "ErrorBoundary"
            }, "timer": {
                "flutter_method": "onTimer", "callback": True, "signature": "VoidCallback", "widget": "Timer.periodic"
            }, "help": {
                "flutter_method": "onHelp", "callback": True, "signature": "VoidCallback"
            }, "hotlinkalarm": {
                "flutter_method": "onLinkActivated", "callback": True, "signature": "ValueChanged<String>"
            }, # DataWindow specific events
            "buttonclicked": {
                "flutter_method": "onButtonClicked", "callback": True, "signature": "Function(int, String)", "return_type": "int", "return_mapping": {
                    0: "ButtonAction.proceed.index", 1: "ButtonAction.cancel.index"
                }
            }, "buttonclicking": {
                "flutter_method": "onButtonClicking", "callback": True, "signature": "int Function(int, String)", "return_type": "int", "return_mapping": {
                    0: "ButtonAction.proceed.index", 1: "ButtonAction.cancel.index"
                }
            }, "clicked": {
                "flutter_method": "onCellClicked", "callback": True, "signature": "Function(int, String)"
            }, "doubleclicked": {
                "flutter_method": "onCellDoubleClicked", "callback": True, "signature": "Function(int, String)"
            }, "error": {
                "flutter_method": "onDataError", "callback": True, "signature": "Function(int, String, dynamic)", "return_type": "int", "return_mapping": {
                    0: "ErrorAction.continue.index", 1: "ErrorAction.retry.index", 2: "ErrorAction.cancel.index"
                }
            }, "retrieveerror": {
                "flutter_method": "onRetrieveError", "callback": True, "signature": "int Function(String, String)", "return_type": "int", "return_mapping": {
                    0: "0", # Continue
                    1: "1"  # Stop retrieval
                }
            }, "sqlerror": {
                "flutter_method": "onSqlError", "callback": True, "signature": "int Function(String, int)", "return_type": "int", "return_mapping": {
                    0: "SqlErrorAction.continue.index", 1: "SqlErrorAction.stop.index", 2: "SqlErrorAction.retry.index"
                }
            }, "validation": {
                "flutter_method": "onValidation", "callback": True, "signature": "bool Function(int, String, dynamic)", "return_type": "bool", "return_mapping": {
                    0: "false", # Validation failed
                    1: "true"   # Validation passed
                }
            }, # Tree view events
            "begindrag": {
                "flutter_method": "onDragStart", "callback": True, "signature": "Function(TreeNode)", "widget": "Draggable"
            }, "beginlabeledit": {
                "flutter_method": "onBeginEdit", "callback": True, "signature": "bool Function(TreeNode)", "return_type": "bool", "return_mapping": {
                    0: "true", # Allow edit
                    1: "false"  # Cancel edit
                }
            }, "endlabeledit": {
                "flutter_method": "onEndEdit", "callback": True, "signature": "bool Function(TreeNode, String)", "return_type": "bool", "return_mapping": {
                    0: "true", # Accept changes
                    1: "false"  # Cancel changes
                }
            }, "deleteitem": {
                "flutter_method": "onDeleteItem", "callback": True, "signature": "bool Function(TreeNode)", "return_type": "bool", "return_mapping": {
                    0: "true", # Allow delete
                    1: "false"  # Cancel delete
                }
            }, "expanding": {
                "flutter_method": "onExpanding", "callback": True, "signature": "bool Function(TreeNode)", "return_type": "bool", "return_mapping": {
                    0: "true", # Allow expand
                    1: "false"  # Cancel expand
                }
            }, "collapsing": {
                "flutter_method": "onCollapsing", "callback": True, "signature": "bool Function(TreeNode)", "return_type": "bool", "return_mapping": {
                    0: "true", # Allow collapse
                    1: "false"  # Cancel collapse
                }
            }
        }
    
    def convert_event(self, event_name: str, parameters: list[Any], body: list[str], control_name: str | None = None) -> Any:

    
        
    
        """Convert a PowerBuilder event to Flutter callback.
        
        Args:
            event_name: Name of the PowerBuilder event
            parameters: Event parameters
            body: Event body statements
            control_name: Name of the control that owns this event
            
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
            return self._create_callback_method(event_name, mapping, parameters, body, control_name)
        else:
            # Unknown event - create generic handler
            return self._create_generic_handler(event_name, parameters, body, control_name)
    
    def _create_lifecycle_method(self, event_name: str, mapping: Dict, body: list[str]) -> Any:

    
        
    
        """Create a lifecycle method."""
        from .ast_converter import Method
        
        flutter_method = mapping["flutter_method"]
        
        # Convert body statements
        dart_body = self._convert_event_body(body, event_name)
        
        # Add super call for lifecycle methods
        if flutter_method == "initState":
            dart_body.insert(0, "super.initState()")
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
                               parameters: list[Any], body: list[str],
                               control_name: str | None = None) -> Any:

    
        
    
        """Create a callback method."""
        from .ast_converter import Method
        
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
        
        # Create method name that includes control name for uniqueness
        if control_name:
            method_name = f"_{self._to_camel_case(control_name)}{self._to_pascal_case(event_name)}Handler"
        else:
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
    
    def _create_generic_handler(self, event_name: str, parameters: list[Any], 
                               body: list[str], control_name: str | None = None) -> Any:

    
        
    
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
        
        # Create method name that includes control name for uniqueness
        if control_name:
            method_name = f"_{self._to_camel_case(control_name)}{self._to_pascal_case(event_name)}Handler"
        else:
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
    
    def _get_callback_parameters(self, signature: str) -> list[Any]:

    
        
    
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
    
    def _convert_event_body(self, body: list[str], event_name: str, 
                          return_type: str | None = None, 
                          return_mapping: dict[int, str | None] = None) -> list[str]:

    
        
    
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
                    # Try to handle the return statement anyway
                    basic_return = self._convert_basic_return(stripped, return_type)
                    dart_body.append(basic_return)
            
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
                except Exception as e:
                    logger.debug("Exception caught: %s", e)
                    # Try to provide more context about the statement
                    if '::' in stripped:
                        dart_body.append(f"// Scope resolution operator not supported: {statement}")
                    elif any(keyword in stripped.lower() for keyword in ['goto', 'halt', 'yield']):
                        dart_body.append(f"// Control flow keyword not supported: {statement}")
                    elif 'create' in stripped.lower():
                        dart_body.append(f"// Object creation: {statement}")
                    elif 'using' in stripped.lower():
                        dart_body.append(f"// Using statement: {statement}")
                    else:
                        dart_body.append(f"// PowerBuilder statement: {statement}")
        
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
    
    def _convert_return_statement(self, statement: str, return_type: str | None = None,
                                 return_mapping: dict[int, str | None] = None) -> str | None:

    
        
    
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
        
        # Check for complex expressions that need special handling
        if any(pattern in return_expr for pattern in ['.', '(', 'IIF', 'String(', 'Integer(', 'GetItem']):
            return self._convert_complex_return(statement, return_type)
        
        # Handle different return types
        if not return_expr:
            # Empty return for void or default return
            if return_type == "void":
                return "return;"
            elif return_type == "int":
                return "return 0;"
            elif return_type == "bool":
                return "return false;"
            elif return_type == "String":
                return "return '';"  
            elif return_type == "double":
                return "return 0.0;"
            else:
                return "return null;"
        
        # Handle object/structure returns
        if return_type and return_type not in ["void", "int", "bool", "String", "double"]:
            # Complex type - try to convert the expression
            try:
                # Apply type casting if needed
                if any(cast in return_expr for cast in ['Integer(', 'String(', 'Long(', 'Double(']):
                    return_expr = self._convert_type_cast(return_expr)
                    return f"return {return_expr};"
                else:
                    converted_expr = self.expression_converter.convert_expression(return_expr)
                    return f"return {converted_expr};"
            except Exception as e:
                logger.debug("Failed to convert complex return expression: %s", e)
                # Provide a better default based on the type
                if return_type.endswith("?"):
                    return "return null;"
                elif return_type.startswith("List<"):
                    return "return [];"
                elif return_type.startswith("Map<"):
                    return "return {};"
                elif return_type.startswith("Future<"):
                    inner_type = return_type[7:-1]  # Extract inner type
                    return f"return Future.value({self._get_default_value(inner_type)});"
                else:
                    return f"return null; // Unable to convert: {return_expr}"
        
        # Try general expression conversion
        try:
            # Check for type casting
            if any(cast in return_expr for cast in ['Integer(', 'String(', 'Long(', 'Double(']):
                converted_expr = self._convert_type_cast(return_expr)
            else:
                converted_expr = self.expression_converter.convert_expression(return_expr)
            
            # Ensure proper return mapping if available
            if return_mapping and converted_expr.isdigit():
                mapped_value = return_mapping.get(int(converted_expr), converted_expr)
                return f"return {mapped_value};"
            return f"return {converted_expr};"
        except Exception as e:
            logger.debug("Failed to convert return expression: %s", e)
            # Try complex return as last resort
            return self._convert_complex_return(statement, return_type)
    
    def _convert_basic_return(self, statement: str, return_type: str | None) -> str:

    
        
    
        """Convert a basic return statement when full conversion fails."""
        # Extract return value
        if statement.lower().startswith("return "):
            return_value = statement[7:].strip()
        else:
            return_value = ""
        
        if not return_value:
            return self._get_default_return(return_type, "")
        
        # Try simple conversions
        if return_value.lower() == "true":
            return "return true;"
        elif return_value.lower() == "false":
            return "return false;"
        elif return_value.lower() == "null":
            return "return null;"
        elif return_value.isdigit():
            return f"return {return_value};"
        else:
            # Attempt basic expression conversion
            try:
                converted = self.expression_converter.convert_expression(return_value)
                return f"return {converted};"
            except Exception as e:
                return self._get_default_return(return_type, return_value)
    
    def _get_default_return(self, return_type: str | None, original_expr: str) -> str:

    
        
    
        """Get a default return statement based on the return type."""
        if not return_type or return_type == "void":
            return "return;"
        elif return_type == "int":
            return "return 0; // Default for: " + original_expr if original_expr else "return 0;"
        elif return_type == "bool":
            return "return false; // Default for: " + original_expr if original_expr else "return false;"
        elif return_type == "String":
            return "return ''; // Default for: " + original_expr if original_expr else "return '';"
        elif return_type == "double":
            return "return 0.0; // Default for: " + original_expr if original_expr else "return 0.0;"
        elif return_type.endswith("?"):
            return "return null; // Nullable type default"
        elif return_type.startswith("List<"):
            return "return []; // Empty list default"
        elif return_type.startswith("Map<"):
            return "return {}; // Empty map default"
        elif return_type.startswith("Future<"):
            inner_type = return_type[7:-1] if return_type.endswith(">") else "dynamic"
            default_value = self._get_default_value(inner_type)
            return f"return Future.value({default_value}); // Future default"
        else:
            return f"return null; // Default for type: {return_type}"
    
    def _get_default_value(self, type_name: str) -> str:

    
        
    
        """Get the default value for a given type."""
        defaults = {
            "int": "0",
            "bool": "false",
            "String": "''",
            "double": "0.0",
            "void": "null",
            "dynamic": "null"
        }
        
        if type_name in defaults:
            return defaults[type_name]
        elif type_name.endswith("?"):
            return "null"
        elif type_name.startswith("List<"):
            return "[]"
        elif type_name.startswith("Map<"):
            return "{}"
        else:
            return "null"
    
    def _convert_assignment_statement(self, statement: str) -> str:

    
        
    
        """Convert an assignment statement to Dart."""
        import re
        
        # Handle compound assignment operators
        compound_ops = [('+=', '+'), ('-=', '-'), ('*=', '*'), ('/=', '/'), 
                       ('&=', '&'), ('|=', '|'), ('^=', '^'), ('++', ''), ('--', '')]
        
        # Check for complex assignment patterns (but avoid simple compound operators)
        complex_patterns = ['<<=', '>>=', 'GetItem', 'String(']
        special_bitwise = ['&=', '|=', '^=']
        if any(pattern in statement for pattern in special_bitwise):
            return self._convert_complex_assignment(statement)
        if any(pattern in statement for pattern in complex_patterns):
            return self._convert_complex_assignment(statement)
        
        # Check for increment/decrement
        if statement.strip().endswith('++'):
            var_name = statement.strip()[:-2].strip()
            try:
                converted_var = self.expression_converter.convert_expression(var_name)
                if self._needs_set_state(var_name):
                    return f"setState(() {{ {converted_var}++; }});"
                return f"{converted_var}++;"
            except Exception as e:
                logger.debug("Exception caught: %s", e)
        elif statement.strip().endswith('--'):
            var_name = statement.strip()[:-2].strip()
            try:
                converted_var = self.expression_converter.convert_expression(var_name)
                if self._needs_set_state(var_name):
                    return f"setState(() {{ {converted_var}--; }});"
                return f"{converted_var}--;"
            except Exception as e:
                logger.debug("Exception caught: %s", e)
        
        # Check for compound assignments
        for op, base_op in compound_ops[:
            7]:  # Skip ++ and --
            if op in statement:
                match = re.match(rf'^\s*(.+?)\s*\{op}\s*(.+)$', statement)
                if match:
                    lhs = match.group(1).strip()
                    rhs = match.group(2).strip()
                    try:
                        converted_lhs = self._convert_lhs(lhs)
                        converted_rhs = self.expression_converter.convert_expression(rhs)
                        
                        if base_op:  # Normal compound operator
                            expanded = f"{converted_lhs} = {converted_lhs} {base_op} {converted_rhs}"
                        else:  # Special case (shouldn't happen here)
                            expanded = f"{converted_lhs} = {converted_rhs}"
                        
                        if self._needs_set_state(lhs):
                            return f"setState(() {{ {expanded}; }});"
                        return f"{expanded};"
                    except Exception as e:
                        logger.debug("Failed to convert compound assignment: %s", e)
        
        # Handle simple assignment
        try:
            # Split on first = sign
            parts = statement.split("=", 1)
            if len(parts) == 2:
                lhs = parts[0].strip()
                rhs = parts[1].strip()
                
                # Handle array assignment with complex expressions
                if '[' in lhs:
                    return self._convert_array_assignment(lhs, rhs)
                
                # Handle property assignment
                if '.' in lhs:
                    try:
                        converted_lhs = self._convert_lhs(lhs)
                        # Check for type casting in RHS
                        if any(cast in rhs for cast in ['Integer(', 'String(', 'Long(', 'Double(']):
                            converted_rhs = self._convert_type_cast(rhs)
                        else:
                            converted_rhs = self.expression_converter.convert_expression(rhs)
                        
                        # Check if the object needs setState
                        object_name = lhs.split('.')[0]
                        if self._needs_set_state(object_name):
                            return f"setState(() {{ {converted_lhs} = {converted_rhs}; }});"
                        return f"{converted_lhs} = {converted_rhs};"
                    except Exception as e:
                        logger.debug("Exception caught: %s", e)
                
                # Standard assignment
                converted_lhs = self._convert_lhs(lhs)
                # Check for type casting in RHS
                if any(cast in rhs for cast in ['Integer(', 'String(', 'Long(', 'Double(']):
                    converted_rhs = self._convert_type_cast(rhs)
                else:
                    converted_rhs = self.expression_converter.convert_expression(rhs)
                
                if self._needs_set_state(lhs):
                    return f"setState(() {{ {converted_lhs} = {converted_rhs}; }});"
                return f"{converted_lhs} = {converted_rhs};"
        except Exception as e:
            logger.debug("Failed to convert assignment: %s", e)
        
        # Provide more specific feedback based on the error
        if '::' in statement:
            return f"// Assignment with scope resolution operator not supported: {statement}"
        elif ':=' in statement:
            # Convert Pascal-style assignment
            return statement.replace(':=', '=') + ";"
        else:
            return f"// Assignment not converted: {statement}"
    
    def _convert_array_assignment(self, lhs: str, rhs: str) -> str:

    
        
    
        """Convert array assignment with potentially complex indices."""
        import re
        
        # Use the array access converter
        try:
            converted_lhs = self._convert_array_access(lhs)
            
            # Convert RHS with type casting support
            if any(cast in rhs for cast in ['Integer(', 'String(', 'Long(', 'Double(']):
                converted_rhs = self._convert_type_cast(rhs)
            else:
                converted_rhs = self.expression_converter.convert_expression(rhs)
            
            # Extract the base variable name for setState check
            base_var = re.match(r'^(\w+)', lhs).group(1) if re.match(r'^(\w+)', lhs) else lhs
            
            if self._needs_set_state(base_var):
                return f"setState(() {{ {converted_lhs} = {converted_rhs}; }});"
            return f"{converted_lhs} = {converted_rhs};"
        except Exception as e:
            # Fallback to simple conversion
            # More specific fallback
            base_var = lhs.split('[')[0].strip()
            return f"// Array assignment: {self._to_camel_case(base_var)}[/* index */] = {rhs};"
    
    def _needs_set_state(self, variable_name: str) -> bool:

    
        
    
        """Check if a variable assignment needs setState."""
        # Instance variables need setState
        if variable_name.startswith("this."):
            return True
        
        # Check if it's a known local variable pattern
        local_patterns = ['temp', 'tmp', 'local', 'i', 'j', 'k', 'n', 'idx', 'index', 'count']
        lower_name = variable_name.lower()
        if any(pattern in lower_name for pattern in local_patterns):
            return False
        
        # If it's a simple identifier without dots, it's likely an instance variable
        if '.' not in variable_name and not variable_name.startswith('_'):
            return True
        
        return False
    
    def _convert_lhs(self, lhs: str) -> str:

    
        
    
        """Convert left-hand side of assignment."""
        # Handle special cases
        if lhs.lower() == "this":
            return "this"
        elif lhs.lower() == "parent":
            return "widget"
        
        # Try expression converter first
        try:
            return self.expression_converter.convert_expression(lhs)
        except Exception as e:
            # Fallback to simple conversion
            if '.' in lhs:
                parts = lhs.split('.', 1)
                object_name = self._to_camel_case(parts[0])
                property_name = self._to_camel_case(parts[1])
                return f"{object_name}.{property_name}"
            else:
                return self._to_camel_case(lhs)
    
    def _convert_if_statement(self, statement: str) -> str:

    
        
    
        """Convert an if statement to Dart."""
        import re
        
        # Handle different PowerBuilder if statement formats
        # Format 1: IF condition THEN
        match = re.search(r'if\s+(.+?)\s+then', statement, re.IGNORECASE)
        if match:
            condition = match.group(1).strip()
            try:
                # Handle complex conditions with nested parentheses
                converted_condition = self._convert_complex_condition(condition)
                return f"if ({converted_condition}) {{"
            except Exception as e:
                logger.debug("Failed to convert if condition: %s", e)
                # Try simpler conversion
                try:
                    converted = self.expression_converter.convert_expression(condition)
                    return f"if ({converted}) {{"
                except Exception as e:
                    # Provide partially converted condition
                    partial = condition.replace(' and ', ' && ').replace(' or ', ' || ')
                    partial = partial.replace(' not ', ' !')
                    return f"if (/* {partial} */) {{"
        
        # Format 2: Single line IF ... THEN ... END IF
        single_line_match = re.match(r'if\s+(.+?)\s+then\s+(.+?)(?:\s+else\s+(.+?))?\s+end\s*if', 
                                    statement, re.IGNORECASE)
        if single_line_match:
            condition = single_line_match.group(1).strip()
            then_part = single_line_match.group(2).strip()
            else_part = single_line_match.group(3)
            
            try:
                converted_condition = self._convert_complex_condition(condition)
                converted_then = self._convert_statement(then_part)
                
                if else_part:
                    converted_else = self._convert_statement(else_part.strip())
                    return f"({converted_condition}) ? {converted_then} : {converted_else};"
                else:
                    return f"if ({converted_condition}) {{ {converted_then} }}"
            except Exception as e:
                # Provide basic structure even if full conversion failed
                return f"if (/* {condition} */) {{ /* {then_part} */ }}"
        
        # Handle ELSEIF
        if statement.strip().lower().startswith('elseif'):
            match = re.search(r'elseif\s+(.+?)\s+then', statement, re.IGNORECASE)
            if match:
                condition = match.group(1).strip()
                try:
                    converted_condition = self._convert_complex_condition(condition)
                    return f"}} else if ({converted_condition}) {{"
                except Exception as e:
                    # Provide partially converted condition
                    partial = condition.replace(' and ', ' && ').replace(' or ', ' || ')
                    partial = partial.replace(' not ', ' !')
                    return f"}} else if (/* {partial} */) {{"
        
        # Handle ELSE
        if statement.strip().lower() == 'else':
            return "} else {"
        
        # Handle END IF
        if statement.strip().lower().replace(' ', '') == 'endif':
            return "}"
        
        # Provide more context about what couldn't be converted
        if 'if' in statement.lower():
            return f"// If statement pattern not recognized: {statement}"
        else:
            return f"// Control flow statement: {statement}"
    
    def _convert_complex_condition(self, condition: str) -> str:

    
        
    
        """Convert complex PowerBuilder conditions to Dart."""
        import re
        
        # Handle NULL checks
        condition = re.sub(r'\bISNULL\s*\(\s*(.+?)\s*\)', r'(\1 == null)', condition, flags=re.IGNORECASE)
        condition = re.sub(r'(.+?)\s+IS\s+NULL', r'(\1 == null)', condition, flags=re.IGNORECASE)
        condition = re.sub(r'(.+?)\s+IS\s+NOT\s+NULL', r'(\1 != null)', condition, flags=re.IGNORECASE)
        
        # Handle NOT operator
        condition = re.sub(r'\bNOT\s+', '!', condition, flags=re.IGNORECASE)
        
        # Handle AND/OR operators
        condition = re.sub(r'\s+AND\s+', ' && ', condition, flags=re.IGNORECASE)
        condition = re.sub(r'\s+OR\s+', ' || ', condition, flags=re.IGNORECASE)
        
        # Handle comparison operators
        condition = condition.replace('<>', '!=')
        condition = condition.replace('=', '==')
        # Fix double equals that might have been created
        condition = condition.replace('===', '==')
        condition = condition.replace('!==', '!=')
        condition = condition.replace('>==', '>=')
        condition = condition.replace('<==', '<=')
        
        # Now convert the expressions within the condition
        return self.expression_converter.convert_expression(condition)
    
    def _convert_method_call(self, statement: str) -> str:

    
        
    
        """Convert a method call to Dart."""
        import re
        
        try:
            # First attempt: Use expression converter
            converted = self.expression_converter.convert_expression(statement)
            if not converted.strip().endswith(";"):
                converted += ";"
            return converted
        except Exception as e:
            logger.debug("Expression converter failed for method call: %s", e)
        
        # Handle special PowerBuilder method calls
        statement = statement.strip()
        
        # Handle system functions
        system_functions = {
            'messagebox': self._convert_messagebox,
            'beep': lambda s: 'SystemSound.play(SystemSoundType.click);',
            'yield': lambda s: 'await Future.delayed(Duration.zero);',
            'sleep': lambda s: self._convert_sleep(s),
            'setnull': lambda s: self._convert_setnull(s),
            'isnull': lambda s: self._convert_isnull(s),
            'isvalid': lambda s: self._convert_isvalid(s),
            'destroy': lambda s: self._convert_destroy(s),
            'close': lambda s: self._convert_close(s),
            'open': lambda s: self._convert_open(s)
        }
        
        # Check for system functions
        lower_statement = statement.lower()
        for func_name, converter in system_functions.items():
            if lower_statement.startswith(func_name + '('):
                return converter(statement)
        
        # Handle object method calls
        if "." in statement:
            # Split into object and method parts
            match = re.match(r'^(.+?)\.(.+)$', statement)
            if match:
                object_part = match.group(1).strip()
                method_part = match.group(2).strip()
                
                # Convert object reference
                converted_object = self._convert_object_reference(object_part)
                
                # Handle method call with parameters
                method_match = re.match(r'^(\w+)\s*\((.*)\)$', method_part)
                if method_match:
                    method_name = self._to_camel_case(method_match.group(1))
                    params = method_match.group(2).strip()
                    
                    if params:
                        # Convert parameters
                        try:
                            converted_params = self._convert_method_parameters(params)
                            return f"{converted_object}.{method_name}({converted_params});"
                        except Exception as e:
                            return f"{converted_object}.{method_name}({params});"
                    else:
                        return f"{converted_object}.{method_name}();"
                else:
                    # Property access or method without parentheses
                    converted_method = self._to_camel_case(method_part)
                    return f"{converted_object}.{converted_method};"
        
        # Handle simple function calls
        match = re.match(r'^(\w+)\s*\((.*)\)$', statement)
        if match:
            func_name = self._to_camel_case(match.group(1))
            params = match.group(2).strip()
            
            if params:
                try:
                    converted_params = self._convert_method_parameters(params)
                    return f"{func_name}({converted_params});"
                except Exception as e:
                    return f"{func_name}({params});"
            else:
                return f"{func_name}();"
        
        # Last resort: add semicolon if missing
        if not statement.endswith(";"):
            return f"{statement};"
        
        return statement
    
    def _convert_object_reference(self, object_ref: str) -> str:

    
        
    
        """Convert PowerBuilder object reference to Dart."""
        lower_ref = object_ref.lower()
        
        # Special object references
        if lower_ref == "this":
            return "this"
        elif lower_ref == "parent":
            return "widget"
        elif lower_ref == "super":
            return "super"
        elif lower_ref == "me":
            return "this"
        
        # Try expression converter
        try:
            return self.expression_converter.convert_expression(object_ref)
        except Exception as e:
            # Fallback to camelCase conversion
            return self._to_camel_case(object_ref)
    
    def _convert_method_parameters(self, params: str) -> str:

    
        
    
        """Convert method parameters to Dart."""
        if not params:
            return ""
        
        # Split parameters by comma, respecting nested parentheses and quotes
        param_list = self._split_parameters(params)
        converted_params = []
        
        for param in param_list:
            param = param.strip()
            try:
                converted = self.expression_converter.convert_expression(param)
                converted_params.append(converted)
            except Exception as e:
                # Fallback for special cases
                if param.lower() == "true" or param.lower() == "false":
                    converted_params.append(param.lower())
                elif param.lower() == "null":
                    converted_params.append("null")
                else:
                    converted_params.append(param)
        
        return ", ".join(converted_params)
    
    def _split_parameters(self, params: str) -> list:

    
        
    
        """Split parameters by comma, respecting nested structures."""
        result = []
        current = []
        paren_depth = 0
        in_quotes = False
        quote_char = None
        
        for char in params:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == '(' and not in_quotes:
                paren_depth += 1
            elif char == ')' and not in_quotes:
                paren_depth -= 1
            elif char == ',' and paren_depth == 0 and not in_quotes:
                result.append(''.join(current))
                current = []
                continue
            
            current.append(char)
        
        if current:
            result.append(''.join(current))
        
        return result
    
    def _convert_sleep(self, statement: str) -> str:

    
        
    
        """Convert sleep function to Dart."""
        match = re.match(r'sleep\s*\(\s*(\d+)\s*\)', statement, re.IGNORECASE)
        if match:
            seconds = match.group(1)
            return f"await Future.delayed(Duration(seconds: {seconds}));"
        return "await Future.delayed(Duration(seconds: 1));"
    
    def _convert_setnull(self, statement: str) -> str:

    
        
    
        """Convert SetNull function to Dart."""
        import re
        # Try multiple patterns for SetNull
        patterns = [
            r'setnull\s*\(\s*(.+?)\s*\)',  # SetNull(var)
            r'(.+?)\s*=\s*setnull\s*\(\s*\)',  # var = SetNull()
            r'setnull\s+(.+?)(?:\s|$)',  # SetNull var (without parens)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, statement, re.IGNORECASE)
            if match:
                var_name = match.group(1).strip()
                # Handle array references
                if '[' in var_name and ']' in var_name:
                    var_name = self._convert_array_access(var_name)
                else:
                    var_name = self._to_camel_case(var_name)
                return f"{var_name} = null;"
        
        # Fallback: if the statement contains setnull, provide a generic conversion
        if 'setnull' in statement.lower():
            return "/* SetNull */ null;"
        return f"// SetNull not converted: {statement}"
    
    def _convert_isnull(self, statement: str) -> str:

    
        
    
        """Convert IsNull function to Dart."""
        import re
        # Try to find IsNull pattern, handling nested parentheses
        pattern = r'isnull\s*\(\s*([^)]+(?:\([^)]*\)[^)]*)*)\s*\)'
        match = re.search(pattern, statement, re.IGNORECASE)
        if match:
            var_expr = match.group(1).strip()
            try:
                var_name = self.expression_converter.convert_expression(var_expr)
                return f"({var_name} == null)"
            except Exception as e:
                # Fallback to simpler conversion
                if '[' in var_expr and ']' in var_expr:
                    var_name = self._convert_array_access(var_expr)
                else:
                    var_name = self._to_camel_case(var_expr)
                return f"({var_name} == null)"
        
        # Handle IsNull without parentheses
        if re.match(r'isnull\s+(\w+)', statement, re.IGNORECASE):
            match = re.match(r'isnull\s+(\w+)', statement, re.IGNORECASE)
            var_name = self._to_camel_case(match.group(1))
            return f"({var_name} == null)"
        
        # If we can identify it's an IsNull check, provide generic null check
        if 'isnull' in statement.lower():
            return "(/* expression */ == null)"
        return f"// IsNull not converted: {statement}"
    
    def _convert_isvalid(self, statement: str) -> str:

    
        
    
        """Convert IsValid function to Dart."""
        import re
        # Try to find IsValid pattern, handling nested parentheses
        pattern = r'isvalid\s*\(\s*([^)]+(?:\([^)]*\)[^)]*)*)\s*\)'
        match = re.search(pattern, statement, re.IGNORECASE)
        if match:
            var_expr = match.group(1).strip()
            try:
                var_name = self.expression_converter.convert_expression(var_expr)
                # For objects, check if not null and potentially disposed
                if any(x in var_expr.lower() for x in ['window', 'control', 'datawindow']):
                    return f"({var_name} != null && !{var_name}.isDisposed)"
                return f"({var_name} != null)"
            except Exception as e:
                # Fallback to simpler conversion
                var_name = self._to_camel_case(var_expr)
                return f"({var_name} != null)"
        
        # Handle IsValid without parentheses
        if re.match(r'isvalid\s+(\w+)', statement, re.IGNORECASE):
            match = re.match(r'isvalid\s+(\w+)', statement, re.IGNORECASE)
            var_name = self._to_camel_case(match.group(1))
            return f"({var_name} != null)"
        
        # If we can identify it's an IsValid check, provide generic null check
        if 'isvalid' in statement.lower():
            return "(/* object */ != null)"
        return f"// IsValid not converted: {statement}"
    
    def _convert_destroy(self, statement: str) -> str:

    
        
    
        """Convert Destroy function to Dart."""
        import re
        # Try multiple patterns for Destroy
        patterns = [
            r'destroy\s*\(\s*(.+?)\s*\)',  # Destroy(object)
            r'destroy\s+(.+?)(?:\s|$)',  # Destroy object (without parens)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, statement, re.IGNORECASE)
            if match:
                object_expr = match.group(1).strip()
                # Handle array elements
                if '[' in object_expr and ']' in object_expr:
                    object_name = self._convert_array_access(object_expr)
                    return f"{object_name}?.dispose(); {object_name} = null;"
                else:
                    object_name = self._to_camel_case(object_expr)
                    # For destroyed objects, also set to null
                    return f"{object_name}?.dispose(); {object_name} = null;"
        
        # If we can identify it's a destroy operation, provide generic dispose
        if 'destroy' in statement.lower():
            return "/* object */?.dispose();"
        return f"// Destroy not converted: {statement}"
    
    def _convert_close(self, statement: str) -> str:

    
        
    
        """Convert Close function to Dart."""
        match = re.match(r'close\s*\(\s*(.+?)\s*\)', statement, re.IGNORECASE)
        if match:
            window_name = match.group(1).strip()
            if window_name.lower() == "this":
                return "Navigator.of(context).pop();"
            else:
                return f"// Close window: {window_name}"
        return "Navigator.of(context).pop();"
    
    def _convert_open(self, statement: str) -> str:

    
        
    
        """Convert Open function to Dart."""
        import re
        # Try multiple patterns for Open
        patterns = [
            r'open\s*\(\s*([^,]+?)\s*\)',  # Open(window)
            r'open\s*\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)',  # Open(window, parent)
            r'open\s+(\w+)(?:\s|$)',  # Open window (without parens)
        ]
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, statement, re.IGNORECASE)
            if match:
                window_expr = match.group(1).strip()
                # Remove quotes if present
                window_expr = window_expr.strip('"\'')
                
                # Handle window variable references vs window class names
                if window_expr.startswith('w_'):
                    # It's a window class name
                    window_name = self._to_pascal_case(window_expr)
                else:
                    # It's a variable holding a window reference
                    window_name = self._to_camel_case(window_expr)
                
                # Handle parent window parameter
                if i == 1 and match.group(2):  # Open with parent
                    parent = self._to_camel_case(match.group(2).strip())
                    return f"Navigator.of(context).push(MaterialPageRoute(builder: (context) => {window_name}(parent: {parent})));"
                
                return f"Navigator.of(context).push(MaterialPageRoute(builder: (context) => {window_name}()));"
        
        # Handle OpenSheet and OpenWithParm variations
        if 'opensheet' in statement.lower():
            match = re.search(r'opensheet\s*\(\s*([^,]+)', statement, re.IGNORECASE)
            if match:
                window_name = self._to_pascal_case(match.group(1).strip().strip('"\''))
                return f"// OpenSheet: Navigator.of(context).push(MaterialPageRoute(builder: (context) => {window_name}()));"
        
        if 'openwithparm' in statement.lower():
            match = re.search(r'openwithparm\s*\(\s*([^,]+)\s*,\s*([^)]+)', statement, re.IGNORECASE)
            if match:
                window_name = self._to_pascal_case(match.group(1).strip().strip('"\''))
                param = self.expression_converter.convert_expression(match.group(2).strip())
                return f"Navigator.of(context).push(MaterialPageRoute(builder: (context) => {window_name}(parameter: {param})));"
        
        # Generic open fallback
        if 'open' in statement.lower():
            return "Navigator.of(context).push(MaterialPageRoute(builder: (context) => /* Window */()));"
        
        return f"// Open not converted: {statement}"
    
    def _convert_messagebox(self, statement: str) -> str:

    
        
    
        """Convert MessageBox call to Flutter dialog."""
        import re
        
        # Try to extract MessageBox parameters
        # Handle both single and double parameter versions
        double_param = re.search(r'messagebox\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']\s*\)', 
                               statement, re.IGNORECASE)
        single_param = re.search(r'messagebox\s*\(\s*["\']([^"\']+)["\']\s*\)', 
                               statement, re.IGNORECASE)
        
        title = "Information"
        message = "Message"
        
        if double_param:
            title = double_param.group(1)
            message = double_param.group(2)
        elif single_param:
            # Single parameter version - use default title
            message = single_param.group(1)
        else:
            # Check for variable or expression parameters
            var_match = re.search(r'messagebox\s*\(\s*([^,)]+)(?:\s*,\s*([^)]+))?\s*\)', 
                                statement, re.IGNORECASE)
            if var_match:
                # Has variable parameters - generate code that uses them
                param1 = var_match.group(1).strip()
                param2 = var_match.group(2).strip() if var_match.group(2) else None
                
                if param2:
                    return f"""showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text({param1}.toString()),
        content: Text({param2}.toString()),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );"""
                else:
                    return f"""showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Information'),
        content: Text({param1}.toString()),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );"""
        
        # Return with escaped strings for literal values
        title_escaped = title.replace("'", "\\'")
        message_escaped = message.replace("'", "\\'")
        
        return f"""showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('{title_escaped}'),
        content: Text('{message_escaped}'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('OK'),
          ),
        ],
      ),
    );"""
    
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
    
    def _extract_return_value(self, statement: str) -> int | None:

    
        
    
        """Extract numeric return value from a return statement."""
        import re
        
        # Match "return <number>" pattern
        match = re.search(r'return\s+(-?\d+)', statement.strip())
        if match:
            return int(match.group(1))
        return None
    
    def _infer_return_type(self, body: list[str]) -> str | None:

    
        
    
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
    
    def _needs_async(self, body: list[str]) -> bool:

    
        
    
        """Check if method needs to be async."""
        async_keywords = ["await", "Future", "async", "then"]
        body_text = " ".join(body)
        return any(keyword in body_text for keyword in async_keywords)
    
    def _to_camel_case(self, name: str) -> str:

    
        
    
        """Convert name to camelCase."""
        parts = name.split("_")
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
    
    def _to_pascal_case(self, name: str) -> str:

    
        
    
        """Convert name to PascalCase."""
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)
    
    def get_event_widget_wrapper(self, event_name: str) -> str | None:

    
        
    
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
    
    def get_event_enums(self) -> list[str]:

    
        
    
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
    
    def get_complex_return_type_handlers(self) -> dict[str, str]:

    
        
    
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
    
    def _convert_complex_return(self, statement: str, return_type: str | None = None) -> str:

    
        
    
        """Convert complex return statements with nested function calls.
        
        Handles cases like:
        - return GetDataWindow().GetItemNumber(GetCurrentRow(), "amount") * GetTaxRate()
        - return Parent.GetWindow().GetFrame().GetData()
        - return IIF(IsValid(dw_1), dw_1.GetItemString(1, "status"), "N/A")
        """
        import re
        
        # Extract return expression
        match = re.search(r'return\s+(.+?)(?:;|$)', statement, re.IGNORECASE)
        if not match:
            return self._get_default_return(return_type, "")
        
        expr = match.group(1).strip()
        
        # Handle IIF expressions (ternary)
        iif_pattern = r'IIF\s*\(\s*(.+?)\s*,\s*(.+?)\s*,\s*(.+?)\s*\)'
        expr = re.sub(iif_pattern, lambda m: f"({self._convert_complex_condition(m.group(1))}) ? {self.expression_converter.convert_expression(m.group(2))} : {self.expression_converter.convert_expression(m.group(3))}", expr, flags=re.IGNORECASE)
        
        # Handle method chaining
        if '.' in expr and '(' in expr:
            try:
                converted = self._convert_method_chain(expr)
                return f"return {converted};"
            except Exception as e:
                logger.debug("Exception caught: %s", e)
        
        # Try standard expression conversion
        try:
            converted = self.expression_converter.convert_expression(expr)
            return f"return {converted};"
        except Exception as e:
            # Provide more helpful fallback
            if 'this.' in expr:
                return f"return this./* {expr.replace('this.', '')} */;"
            elif any(op in expr for op in ['+', '-', '*', '/', '%']):
                return f"return /* {expr} */;"
            else:
                return f"return null; // Complex expression: {expr}"
    
    def _convert_method_chain(self, expr: str) -> str:

    
        
    
        """Convert method chaining expressions.
        
        Handles:
        - object.method1().method2().property
        - Parent.GetWindow().GetFrame()
        - dw_1.SetFilter("...").Filter()
        """
        # Split by dots but preserve method calls
        parts = []
        current = []
        paren_depth = 0
        in_quotes = False
        
        i = 0
        while i < len(expr):
            char = expr[i]
            
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
            elif char in ('"', "'") and in_quotes:
                in_quotes = False
            elif char == '(' and not in_quotes:
                paren_depth += 1
            elif char == ')' and not in_quotes:
                paren_depth -= 1
            elif char == '.' and paren_depth == 0 and not in_quotes:
                parts.append(''.join(current))
                current = []
                i += 1
                continue
            
            current.append(char)
            i += 1
        
        if current:
            parts.append(''.join(current))
        
        # Convert each part
        converted_parts = []
        for i, part in enumerate(parts):
            if i == 0:
                # First part - convert object reference
                if part.lower() == "parent":
                    converted_parts.append("widget")
                else:
                    converted_parts.append(self._convert_object_reference(part))
            else:
                # Method call or property
                if '(' in part:
                    # Method call
                    method_match = re.match(r'^(\w+)\s*\((.*)\)$', part)
                    if method_match:
                        method_name = self._to_camel_case(method_match.group(1))
                        params = method_match.group(2)
                        if params:
                            converted_params = self._convert_method_parameters(params)
                            converted_parts.append(f"{method_name}({converted_params})")
                        else:
                            converted_parts.append(f"{method_name}()")
                    else:
                        converted_parts.append(part)
                else:
                    # Property access
                    converted_parts.append(self._to_camel_case(part))
        
        return '.'.join(converted_parts)
    
    def _convert_array_access(self, expr: str) -> str:

    
        
    
        """Convert array/structure member access.
        
        Handles:
        - data_array[row_index][col_index].value
        - employee_data[current_emp].address.street
        - menu_items[GetCurrentIndex() + offset]
        """
        import re
        
        # Pattern to match array access
        array_pattern = r'(\w+)(\[.+?\])+(.*)$'
        match = re.match(array_pattern, expr)
        
        if match:
            var_name = self._to_camel_case(match.group(1))
            indices = match.group(2)
            remainder = match.group(3)
            
            # Convert indices
            converted_indices = self._convert_array_indices(indices)
            
            # Convert remainder (property access)
            if remainder:
                if remainder.startswith('.'):
                    remainder = remainder[1:]  # Remove leading dot
                    converted_remainder = self._convert_property_chain(remainder)
                    return f"{var_name}{converted_indices}.{converted_remainder}"
                else:
                    return f"{var_name}{converted_indices}{remainder}"
            else:
                return f"{var_name}{converted_indices}"
        
        return expr
    
    def _convert_array_indices(self, indices_str: str) -> str:

    
        
    
        """Convert array indices like [expr1][expr2] to [expr1][expr2]."""
        import re
        
        # Extract each index expression
        index_pattern = r'\[([^\[\]]+)\]'
        indices = re.findall(index_pattern, indices_str)
        
        converted_indices = []
        for index in indices:
            try:
                converted_index = self.expression_converter.convert_expression(index)
                converted_indices.append(f"[{converted_index}]")
            except Exception as e:
                converted_indices.append(f"[{index}]")
        
        return ''.join(converted_indices)
    
    def _convert_property_chain(self, chain: str) -> str:

    
        
    
        """Convert property chain like address.street.number."""
        parts = chain.split('.')
        converted_parts = [self._to_camel_case(part) for part in parts]
        return '.'.join(converted_parts)
    
    def _convert_type_cast(self, expr: str) -> str:

    
        
    
        """Convert PowerBuilder type casting to Dart.
        
        Handles:
        - Integer(String(decimal_value * 100))
        - Long(dw_1.GetItemString(row, "id"))
        - Dec(IsNull(raw_value, "0"))
        """
        import re
        
        # Type cast patterns
        cast_patterns = [
            (r'Integer\s*\((.+?)\)', lambda m: f"int.parse({self.expression_converter.convert_expression(m.group(1))}.toString())"),
            (r'Int\s*\((.+?)\)', lambda m: f"int.parse({self.expression_converter.convert_expression(m.group(1))}.toString())"),
            (r'Long\s*\((.+?)\)', lambda m: f"int.parse({self.expression_converter.convert_expression(m.group(1))}.toString())"),
            (r'Double\s*\((.+?)\)', lambda m: f"double.parse({self.expression_converter.convert_expression(m.group(1))}.toString())"),
            (r'Dec\s*\((.+?)\)', lambda m: f"double.parse({self.expression_converter.convert_expression(m.group(1))}.toString())"),
            (r'Decimal\s*\((.+?)\)', lambda m: f"double.parse({self.expression_converter.convert_expression(m.group(1))}.toString())"),
            (r'String\s*\((.+?)\)', lambda m: f"{self.expression_converter.convert_expression(m.group(1))}.toString()"),
            (r'Date\s*\((.+?)\)', lambda m: f"DateTime.parse({self.expression_converter.convert_expression(m.group(1))})"),
            (r'DateTime\s*\((.+?)\)', lambda m: f"DateTime.parse({self.expression_converter.convert_expression(m.group(1))})"),
            (r'Boolean\s*\((.+?)\)', lambda m: f"({self.expression_converter.convert_expression(m.group(1))} != 0)"),
            (r'Bool\s*\((.+?)\)', lambda m: f"({self.expression_converter.convert_expression(m.group(1))} != 0)")
        ]
        
        # Apply cast conversions
        converted = expr
        for pattern, replacement in cast_patterns:
            converted = re.sub(pattern, replacement, converted, flags=re.IGNORECASE)
        
        return converted
    
    def _convert_complex_assignment(self, statement: str) -> str:

    
        
    
        """Convert complex assignment expressions.
        
        Handles:
        - total += GetItemAmount(row) * (1 + GetTaxRate() / 100)
        - flags &= ~(READONLY_FLAG | SYSTEM_FLAG)
        - message += "Row " + String(row) + ": " + GetError()
        """
        import re
        
        # Handle special operators
        special_ops = [
            ('&=', lambda lhs, rhs: f"{lhs} = {lhs} & {rhs}"),
            ('|=', lambda lhs, rhs: f"{lhs} = {lhs} | {rhs}"),
            ('^=', lambda lhs, rhs: f"{lhs} = {lhs} ^ {rhs}"),
            ('<<=', lambda lhs, rhs: f"{lhs} = {lhs} << {rhs}"),
            ('>>=', lambda lhs, rhs: f"{lhs} = {lhs} >> {rhs}")
        ]
        
        # Check for special operators
        for op, converter in special_ops:
            if op in statement:
                parts = statement.split(op, 1)
                if len(parts) == 2:
                    lhs = parts[0].strip()
                    rhs = parts[1].strip()
                    
                    try:
                        converted_lhs = self._convert_lhs(lhs)
                        
                        # Handle bitwise NOT
                        rhs = re.sub(r'~\s*\(', 'not (', rhs)
                        
                        # Convert flags/constants
                        rhs = self._convert_constants(rhs)
                        
                        converted_rhs = self.expression_converter.convert_expression(rhs)
                        result = converter(converted_lhs, converted_rhs)
                        
                        if self._needs_set_state(lhs):
                            return f"setState(() {{ {result}; }});"
                        return f"{result};"
                    except Exception as e:
                        logger.debug("Exception caught: %s", e)
        
        # Handle string concatenation assignment
        if '+=' in statement and '"' in statement:
            parts = statement.split('+=', 1)
            if len(parts) == 2:
                lhs = parts[0].strip()
                rhs = parts[1].strip()
                
                # Convert string concatenation
                rhs = self._convert_string_concat(rhs)
                
                try:
                    converted_lhs = self._convert_lhs(lhs)
                    if self._needs_set_state(lhs):
                        return f"setState(() {{ {converted_lhs} += {rhs}; }});"
                    return f"{converted_lhs} += {rhs};"
                except Exception as e:
                    logger.debug("Exception caught: %s", e)
        
        # Fall back to standard assignment conversion
        return self._convert_assignment_statement(statement)
    
    def _convert_constants(self, expr: str) -> str:

    
        
    
        """Convert PowerBuilder constants to Dart equivalents."""
        # Common flag patterns
        constants = {
            'READONLY_FLAG': 'readOnlyFlag',
            'SYSTEM_FLAG': 'systemFlag',
            'HIDDEN_FLAG': 'hiddenFlag',
            'VISIBLE_FLAG': 'visibleFlag',
            'ENABLED_FLAG': 'enabledFlag',
            'MODIFIED_FLAG': 'modifiedFlag'
        }
        
        result = expr
        for pb_const, dart_const in constants.items():
            result = result.replace(pb_const, dart_const)
        
        return result
    
    def _convert_string_concat(self, expr: str) -> str:

    
        
    
        """Convert PowerBuilder string concatenation to Dart string interpolation."""
        import re
        
        # Pattern to match string concatenation with +
        parts = self._split_by_plus(expr)
        
        if len(parts) > 1:
            # Multiple parts - try to create interpolated string
            string_parts = []
            expressions = []
            
            for part in parts:
                part = part.strip()
                if (part.startswith('"') and part.endswith('"')) or (part.startswith("'") and part.endswith("'")):
                    # String literal
                    string_parts.append(part[1:-1])  # Remove quotes
                else:
                    # Expression
                    if part.lower().startswith('string('):
                        # String() function call
                        match = re.match(r'string\s*\((.+)\)', part, re.IGNORECASE)
                        if match:
                            inner_expr = match.group(1)
                            try:
                                converted = self.expression_converter.convert_expression(inner_expr)
                                string_parts.append(f"${{{converted}}}")
                            except Exception as e:
                                string_parts.append(f"${{{inner_expr}}}")
                        else:
                            string_parts.append(f"${{{part}}}")
                    else:
                        # Other expression
                        try:
                            converted = self.expression_converter.convert_expression(part)
                            string_parts.append(f"${{{converted}}}")
                        except Exception as e:
                            string_parts.append(f"${{{part}}}")
            
            # Combine into interpolated string
            return f"'{{''.join(string_parts)}}'"
        else:
            # Single expression
            try:
                return self.expression_converter.convert_expression(expr)
            except Exception as e:
                return expr
    
    def _split_by_plus(self, expr: str) -> list:

    
        
    
        """Split expression by + operator, respecting parentheses and quotes."""
        parts = []
        current = []
        paren_depth = 0
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(expr):
            char = expr[i]
            
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == '(' and not in_quotes:
                paren_depth += 1
            elif char == ')' and not in_quotes:
                paren_depth -= 1
            elif char == '+' and paren_depth == 0 and not in_quotes:
                # Check if it's part of += or ++
                if i + 1 < len(expr) and expr[i + 1] in ('=', '+'):
                    current.append(char)
                else:
                    parts.append(''.join(current))
                    current = []
                    i += 1
                    continue
            
            current.append(char)
            i += 1
        
        if current:
            parts.append(''.join(current))
        
        return parts
    
    def _convert_statement(self, statement: str) -> str:

    
        
    
        """Convert a single statement for use in ternary or single-line if."""
        statement = statement.strip()
        
        # Remove trailing semicolon if present
        if statement.endswith(';'):
            statement = statement[:-1]
        
        # Try to convert as expression first
        try:
            return self.expression_converter.convert_expression(statement)
        except Exception as e:
            # Try specific statement conversions
            if statement.lower().startswith('return'):
                return_val = statement[6:].strip()
                if return_val:
                    return return_val
                else:
                    return 'null'
            elif '=' in statement:
                # Assignment - extract right side
                parts = statement.split('=', 1)
                if len(parts) == 2:
                    try:
                        return self.expression_converter.convert_expression(parts[1].strip())
                    except Exception as e:
                        return parts[1].strip()
            
            # Default
            return statement