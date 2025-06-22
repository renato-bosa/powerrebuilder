"""PowerBuilder to Flutter/Dart expression converter.

Converts PowerBuilder expressions, operators, and function calls
to Dart syntax.
"""

import re
import logging
from typing import Any
from .type_converter import TypeConverter

logger = logging.getLogger(__name__)


class ExpressionConverter:
    """Converts PowerBuilder expressions to Dart syntax."""
    
    def __init__(self, type_converter: TypeConverter | None = None) -> None:

    
        """Initialize the expression converter.
        
        Args:
            type_converter: Type converter instance
        """
        self.type_converter = type_converter or TypeConverter()
        
        # PowerBuilder to Dart operator mappings
        self.operator_map = {
            "=": "==", "<>": "!=", "and": "&&", "or": "||", "not": "!", "mod": "%", "^": "pow", # Requires dart:math import
        }
        
        # PowerBuilder to Dart function mappings
        self.function_map = {
            # String functions
            "len": "_length", "lenw": "_length", "trim": "_trim", "ltrim": "_ltrim", "rtrim": "_rtrim", "upper": "_upper", "lower": "_lower", "mid": "_substring", # Custom implementation needed
            "pos": "_indexOf", "replace": "_replace", # Numeric functions
            "abs": "_abs", "ceiling": "ceil", "int": "toInt()", "round": "_round", "truncate": "truncate()", # Date/Time functions
            "today": "DateTime.now()", "now": "DateTime.now()", "year": "_year", "month": "_month", "day": "_day", # Type checking
            "isnull": "== null", "isvalid": "!= null", "isnumber": "_isNumber", "isdate": "_isDate", # Blob functions
            "blob": "_blob", "blobedit": "_blobEdit", "blobmid": "_blobMid", }
    
    def convert_expression(self, pb_expr: Any, context: dict[str, Any | None] = None) -> str:

    
        
    
        """Convert a PowerBuilder expression to Dart.
        
        Args:
            pb_expr: PowerBuilder expression (string or AST node)
            context: Optional context with variable types
            
        Returns:
            Dart expression
        """
        if not pb_expr:
            return ""
        
        # Handle AST nodes
        if hasattr(pb_expr, '__class__'):
            class_name = pb_expr.__class__.__name__
            
            # Handle different AST node types
            if class_name == 'IntegerLiteral':
                return str(pb_expr.value)
            elif class_name == 'StringLiteral':
                return f'"{pb_expr.value}"'
            elif class_name == 'BooleanLiteral':
                return 'true' if pb_expr.value else 'false'
            elif class_name == 'Variable':
                # Convert snake_case to camelCase for variables
                return self._to_camel_case(pb_expr.name)
            elif class_name == 'BinaryExpression':
                left = self.convert_expression(pb_expr.left, context)
                right = self.convert_expression(pb_expr.right, context)
                operator = self.operator_map.get(pb_expr.operator, pb_expr.operator)
                return f"{left} {operator} {right}"
            elif class_name == 'ArrayAccess':
                # Convert array name
                array_name = self._to_camel_case(pb_expr.array_name)
                # Convert indices
                indices = []
                for idx in pb_expr.indices:
                    if isinstance(idx, str):
                        indices.append(self._to_camel_case(idx))
                    else:
                        indices.append(str(idx))
                # Build array access expression
                result = array_name
                for idx in indices:
                    result += f"[{idx}]"
                return result
            # Add more AST node types as needed
        
        # Handle string expressions
        dart_expr = str(pb_expr)
        
        # Convert null handling FIRST (before function conversion)
        dart_expr = self._convert_null_handling(dart_expr)
        
        # Convert operators
        dart_expr = self._convert_operators(dart_expr)
        
        # Convert function calls
        dart_expr = self._convert_functions(dart_expr)
        
        # Convert string concatenation
        dart_expr = self._convert_string_concat(dart_expr)
        
        # Convert array access
        dart_expr = self._convert_array_access(dart_expr)
        
        # Convert property access
        dart_expr = self._convert_property_access(dart_expr)
        
        return dart_expr
    
    def _convert_operators(self, expr: str) -> str:

    
        
    
        """Convert PowerBuilder operators to Dart operators."""
        result = expr
        
        # Sort operators by length to avoid partial replacements
        sorted_ops = sorted(self.operator_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for pb_op, dart_op in sorted_ops:
            # Use word boundaries for logical operators
            if pb_op in ["and", "or", "not", "mod"]:
                pattern = rf'\b{pb_op}\b'
                result = re.sub(pattern, dart_op, result, flags=re.IGNORECASE)
            elif pb_op == "=":
                # Special handling for = to avoid converting == to ====
                # Only convert = to == when it's not already ==
                result = re.sub(r'(?<![=!<>])\s*=\s*(?!=)', ' == ', result)
            elif pb_op == "<>":
                # Convert <> to !=
                result = result.replace("<>", "!=")
            else:
                # Direct replacement for other symbols
                result = result.replace(pb_op, dart_op)
        
        return result
    
    def _convert_functions(self, expr: str) -> str:

    
        
    
        """Convert PowerBuilder function calls to Dart."""
        result = expr
        
        for pb_func, dart_func in self.function_map.items():
            # Special handling for different function types
            if dart_func.startswith("_"):
                # Custom function implementation needed
                custom_func = self._get_custom_function(pb_func, dart_func)
                
                # Handle method calls that should be invoked on the object
                if custom_func.startswith("."):
                    # Convert func(obj) to obj.method()
                    pattern = rf'\b{pb_func}\s*\(\s*([^)]+)\s*\)'
                    
                    def replace_method(match):
                        
                    
                        args = match.group(1).strip()
                        if ', ' in args:
                            # Multiple arguments - only some functions support this
                            parts = [arg.strip() for arg in args.split(', ', 1)]
                            if custom_func in ['.indexOf', '.replaceAll']:
                                return f"{parts[0]}{custom_func}({parts[1]})"
                            else:
                                # For functions that only take one argument
                                return f"{parts[0]}{custom_func}"
                        else:
                            # Single argument
                            return f"{args}{custom_func}"
                    
                    result = re.sub(pattern, replace_method, result, flags=re.IGNORECASE)
                else:
                    # Regular function replacement
                    pattern = rf'\b{pb_func}\s*\('
                    result = re.sub(pattern, custom_func + "(", result, flags=re.IGNORECASE)
            else:
                # Direct function name replacement
                pattern = rf'\b{pb_func}\s*\('
                result = re.sub(pattern, dart_func + "(", result, flags=re.IGNORECASE)
        
        return result
    
    def _get_custom_function(self, pb_func: str, dart_func: str) -> str:

    
        
    
        """Get custom function implementation for complex conversions."""
        custom_functions = {
            "_substring": "substring", # mid(str, start, len) -> str.substring(start-1, start-1+len)
            "_abs": "abs", # Requires dart:math
            "_round": "round", # Different signature
            "_year": ".year", # Property access
            "_month": ".month", "_day": ".day", "_isNumber": "double.tryParse", "_isDate": "DateTime.tryParse", "_blob": "Uint8List.fromList", # blob(string) -> Uint8List
            "_blobEdit": "_editBlob", # Custom helper function
            "_blobMid": ".sublist", # blob.sublist(start-1, start-1+len)
            "_length": ".length", # len(str) -> str.length
            "_trim": ".trim()", # trim(str) -> str.trim()
            "_ltrim": ".trimLeft()", # ltrim(str) -> str.trimLeft()
            "_rtrim": ".trimRight()", # rtrim(str) -> str.trimRight()
            "_upper": ".toUpperCase()", # upper(str) -> str.toUpperCase()
            "_lower": ".toLowerCase()", # lower(str) -> str.toLowerCase()
            "_indexOf": ".indexOf", # pos(str, substr) -> str.indexOf(substr)
            "_replace": ".replaceAll", # replace(str, old, new) -> str.replaceAll(old, new)
        }
        
        return custom_functions.get(dart_func, dart_func)
    
    def _convert_null_handling(self, expr: str) -> str:

    
        
    
        """Convert PowerBuilder null handling to Dart."""
        result = expr
        
        # Convert IsNull(var) to var == null
        result = re.sub(r'\bIsNull\s*\(\s*([^)]+)\s*\)', r'(\1 == null)', result, flags=re.IGNORECASE)
        
        # Convert IsValid(var) to var != null
        result = re.sub(r'\bIsValid\s*\(\s*([^)]+)\s*\)', r'(\1 != null)', result, flags=re.IGNORECASE)
        
        # Convert SetNull(var) to var = null
        result = re.sub(r'\bSetNull\s*\(\s*([^)]+)\s*\)', r'\1 = null', result, flags=re.IGNORECASE)
        
        return result
    
    def _convert_string_concat(self, expr: str) -> str:

    
        
    
        """Convert PowerBuilder string concatenation to Dart."""
        # PowerBuilder uses + for string concatenation
        # In Dart, we need to ensure proper string interpolation
        
        # This is a simplified implementation
        # A full implementation would need to parse the expression tree
        
        # Convert simple concatenations
        result = expr
        
        # Look for string literals being concatenated
        # "string1" + "string2" -> "string1" + "string2" (same in Dart)
        
        # For variables, we might want to use string interpolation
        # "Hello " + name -> "Hello $name" or "Hello ${name}"
        
        return result
    
    def _to_camel_case(self, snake_str: str) -> str:

    
        
    
        """Convert snake_case to camelCase."""
        if '.' in snake_str:
            # Handle property access like "this.width"
            parts = snake_str.split('.')
            return '.'.join(self._to_camel_case(part) if i > 0 else part for i, part in enumerate(parts))
        
        components = snake_str.split('_')
        # First component stays lowercase, rest are capitalized
        return components[0] + ''.join(x.capitalize() for x in components[1:])
    
    def _convert_array_access(self, expr: str) -> str:

    
        
    
        """Convert PowerBuilder array access to Dart."""
        result = expr
        
        # PowerBuilder uses 1-based arrays, Dart uses 0-based
        # array[1] -> array[0]
        
        # Find array access patterns
        pattern = r'(\w+)\[(\d+)\]'
        
        def adjust_index(match):
            
        
            var_name = match.group(1)
            index = int(match.group(2))
            # Convert 1-based to 0-based
            if index > 0:
                index -= 1
            return f"{var_name}[{index}]"
        
        result = re.sub(pattern, adjust_index, result)
        
        return result
    
    def _convert_property_access(self, expr: str) -> str:

    
        
    
        """Convert PowerBuilder property access to Dart."""
        result = expr
        
        # PowerBuilder uses both . and :: for member access
        # Convert :: to .
        result = result.replace("::", ".")
        
        # Convert common property patterns
        property_map = {
            ".text": ".text", ".enabled": ".enabled", ".visible": ".visible", ".checked": ".value", # For checkboxes
            ".selected": ".value", # For dropdowns
        }
        
        for pb_prop, dart_prop in property_map.items():
            result = result.replace(pb_prop, dart_prop)
        
        return result
    
    def convert_assignment(self, pb_assignment: str) -> str:

    
        
    
        """Convert a PowerBuilder assignment statement to Dart.
        
        Args:
            pb_assignment: PowerBuilder assignment statement
            
        Returns:
            Dart assignment statement
        """
        # Match assignment pattern
        match = re.match(r'^\s*(\w+)\s*=\s*(.+)$', pb_assignment)
        if match:
            var_name = match.group(1)
            value_expr = match.group(2)
            
            # Convert the value expression
            dart_value = self.convert_expression(value_expr)
            
            # Handle special cases
            if dart_value.lower() == "null":
                return f"{var_name} = null"
            elif dart_value.lower() == "true" or dart_value.lower() == "false":
                return f"{var_name} = {dart_value.lower()};"
            else:
                return f"{var_name} = {dart_value};"
        
        return pb_assignment
    
    def convert_conditional(self, pb_if: str) -> str:

    
        
    
        """Convert PowerBuilder IF statement to Dart.
        
        Args:
            pb_if: PowerBuilder IF statement
            
        Returns:
            Dart if statement
        """
        # Match IF pattern
        match = re.match(r'^\s*IF\s+(.+)\s+THEN\s*$', pb_if, re.IGNORECASE)
        if match:
            condition = match.group(1)
            dart_condition = self.convert_expression(condition)
            return f"if ({dart_condition}) {{"
        
        # Handle ELSEIF
        match = re.match(r'^\s*ELSEIF\s+(.+)\s+THEN\s*$', pb_if, re.IGNORECASE)
        if match:
            condition = match.group(1)
            dart_condition = self.convert_expression(condition)
            return f"}} else if ({dart_condition}) {{"
        
        # Handle ELSE
        if re.match(r'^\s*ELSE\s*$', pb_if, re.IGNORECASE):
            return "} else {"
        
        # Handle END IF
        if re.match(r'^\s*END\s+IF\s*$', pb_if, re.IGNORECASE):
            return "}"
        
        return pb_if
    
    def get_required_imports(self, expr: str) -> list[str]:

    
        
    
        """Get required imports for an expression.
        
        Args:
            expr: Dart expression
            
        Returns:
            List of import statements
        """
        imports = set()
        
        # Check for math functions
        math_functions = ["pow", "abs", "ceil", "round", "sqrt", "sin", "cos", "tan"]
        for func in math_functions:
            if func in expr:
                imports.add("import 'dart:math' as math;")
        
        # Check for async operations
        if "await" in expr or "Future" in expr:
            imports.add("import 'dart:async';")
        
        # Check for typed data
        if "Uint8List" in expr or "_blob" in expr.lower():
            imports.add("import 'dart:typed_data';")
        
        # Check for base64 encoding
        if "base64" in expr.lower():
            imports.add("import 'dart:convert';")
        
        return list(imports)
    
    def convert_blob_expression(self, pb_expr: str) -> str:

    
        
    
        """Convert PowerBuilder blob expressions to Dart.
        
        Args:
            pb_expr: PowerBuilder blob expression
            
        Returns:
            Dart blob expression
        """
        result = pb_expr
        
        # Convert Blob(string) -> Uint8List.fromList(string.codeUnits)
        result = re.sub(
            r'Blob\s*\(\s*([^)]+)\s*\)',
            r'Uint8List.fromList(\1.codeUnits)',
            result,
            flags=re.IGNORECASE
        )
        
        # Convert String(blob) -> String.fromCharCodes(blob)
        result = re.sub(
            r'String\s*\(\s*(.*?blob.*?)\s*\)',
            r'String.fromCharCodes(\1)',
            result,
            flags=re.IGNORECASE
        )
        
        # Convert String(blob, encoding) -> custom helper
        def convert_string_with_encoding(match):
            
            blob_var = match.group(1)
            encoding = match.group(2).strip().strip('"\'')
            
            if encoding.lower() in ['utf8', 'utf-8']:
                return f"utf8.decode({blob_var})"
            elif encoding.lower() in ['utf16', 'utf-16']:
                return f"_decodeUtf16({blob_var})"
            elif encoding.lower() == 'base64':
                return f"base64.encode({blob_var})"
            else:
                return f"String.fromCharCodes({blob_var})"
        
        result = re.sub(
            r'String\s*\(\s*([^,]+),\s*([^)]+)\s*\)',
            convert_string_with_encoding,
            result,
            flags=re.IGNORECASE
        )
        
        # Convert BlobMid(blob, start, len) -> blob.sublist(start-1, start-1+len)
        def convert_blobmid(match):
            
            blob_var = match.group(1)
            start = match.group(2)
            length = match.group(3) if match.group(3) else None
            
            if length:
                return f"{blob_var}.sublist({start} - 1, ({start} - 1) + {length})"
            else:
                return f"{blob_var}.sublist({start} - 1)"
        
        result = re.sub(
            r'BlobMid\s*\(\s*([^,]+),\s*([^,]+)(?:,\s*([^)]+))?\s*\)',
            convert_blobmid,
            result,
            flags=re.IGNORECASE
        )
        
        # Convert BlobEdit(blob, pos, value) -> custom helper
        def convert_blobedit(match):
            
            blob_var = match.group(1)
            pos = match.group(2)
            value = match.group(3)
            
            # Generate inline blob edit code
            return f"(() {{ var _temp = Uint8List.from({blob_var}); _temp[{pos} - 1] = {value}; return _temp; }})()"
        
        result = re.sub(
            r'BlobEdit\s*\(\s*([^,]+),\s*([^,]+),\s*([^)]+)\s*\)',
            convert_blobedit,
            result,
            flags=re.IGNORECASE
        )
        
        # Convert Len(blob) -> blob.length for Uint8List
        result = re.sub(
            r'Len\s*\(\s*(.*?(?:blob|Uint8List).*?)\s*\)',
            r'\1.length',
            result,
            flags=re.IGNORECASE
        )
        
        # Convert blob concatenation: blob1 + blob2 -> Uint8List.fromList([...blob1, ...blob2])
        result = re.sub(
            r'(\w+blob\w*|\w*Uint8List\w*)\s*\+\s*(\w+blob\w*|\w*Uint8List\w*)',
            r'Uint8List.fromList([...\1, ...\2])',
            result,
            flags=re.IGNORECASE
        )
        
        # Convert IsNull(blob) -> blob == null
        result = re.sub(
            r'IsNull\s*\(\s*(.*?blob.*?)\s*\)',
            r'(\1 == null)',
            result,
            flags=re.IGNORECASE
        )
        
        # Convert SetNull(blob) -> blob = null
        result = re.sub(
            r'SetNull\s*\(\s*(.*?blob.*?)\s*\)',
            r'\1 = null',
            result,
            flags=re.IGNORECASE
        )
        
        # Convert blob comparison: blob1 = blob2 -> listEquals(blob1, blob2)
        result = re.sub(
            r'(\w+blob\w*|\w*Uint8List\w*)\s*==\s*(\w+blob\w*|\w*Uint8List\w*)',
            r'listEquals(\1, \2)',
            result
        )
        
        return result
    
    def get_required_blob_helpers(self) -> list:

    
        
    
        """Get required helper functions for blob operations.
        
        Returns:
            List of helper function definitions
        """
        helpers = []
        
        # UTF-16 decoder helper
        helpers.append("""
String _decodeUtf16(Uint8List bytes) {
  // Decode UTF-16 bytes to string
  final buffer = StringBuffer();
  for (int i = 0; i < bytes.length - 1; i += 2) {
    final charCode = bytes[i] | (bytes[i + 1] << 8);
    buffer.writeCharCode(charCode);
  }
  return buffer.toString();
}""")
        
        # Blob comparison helper (if listEquals not imported)
        helpers.append("""
bool _blobEquals(Uint8List? a, Uint8List? b) {
  if (a == null || b == null) return a == b;
  if (a.length != b.length) return false;
  for (int i = 0; i < a.length; i++) {
    if (a[i] != b[i]) return false;
  }
  return true;
}""")
        
        return helpers