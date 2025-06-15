"""PowerBuilder to Flutter/Dart expression converter.

Converts PowerBuilder expressions, operators, and function calls
to Dart syntax.
"""

import re
import logging
from typing import Optional, Dict, Any
from .type_converter import TypeConverter

logger = logging.getLogger(__name__)


class ExpressionConverter:
    """Converts PowerBuilder expressions to Dart syntax."""
    
    def __init__(self, type_converter: Optional[TypeConverter] = None):
        """Initialize the expression converter.
        
        Args:
            type_converter: Type converter instance
        """
        self.type_converter = type_converter or TypeConverter()
        
        # PowerBuilder to Dart operator mappings
        self.operator_map = {
            "=": "==",
            "<>": "!=",
            "and": "&&",
            "or": "||",
            "not": "!",
            "mod": "%",
            "^": "pow",  # Requires dart:math import
        }
        
        # PowerBuilder to Dart function mappings
        self.function_map = {
            # String functions
            "len": "length",
            "lenw": "length",
            "trim": "trim()",
            "ltrim": "trimLeft()",
            "rtrim": "trimRight()",
            "upper": "toUpperCase()",
            "lower": "toLowerCase()",
            "mid": "_substring",  # Custom implementation needed
            "pos": "indexOf",
            "replace": "replaceAll",
            
            # Numeric functions
            "abs": "_abs",
            "ceiling": "ceil",
            "int": "toInt()",
            "round": "_round",
            "truncate": "truncate()",
            
            # Date/Time functions
            "today": "DateTime.now()",
            "now": "DateTime.now()",
            "year": "_year",
            "month": "_month",
            "day": "_day",
            
            # Type checking
            "isnull": "== null",
            "isvalid": "!= null",
            "isnumber": "_isNumber",
            "isdate": "_isDate",
        }
    
    def convert_expression(self, pb_expr: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Convert a PowerBuilder expression to Dart.
        
        Args:
            pb_expr: PowerBuilder expression
            context: Optional context with variable types
            
        Returns:
            Dart expression
        """
        if not pb_expr:
            return ""
        
        dart_expr = pb_expr
        
        # Convert operators
        dart_expr = self._convert_operators(dart_expr)
        
        # Convert function calls
        dart_expr = self._convert_functions(dart_expr)
        
        # Convert null handling
        dart_expr = self._convert_null_handling(dart_expr)
        
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
            else:
                # Direct replacement for symbols
                result = result.replace(pb_op, dart_op)
        
        return result
    
    def _convert_functions(self, expr: str) -> str:
        """Convert PowerBuilder function calls to Dart."""
        result = expr
        
        for pb_func, dart_func in self.function_map.items():
            # Match function calls with parentheses
            pattern = rf'\b{pb_func}\s*\('
            
            # Special handling for different function types
            if dart_func.startswith("_"):
                # Custom function implementation needed
                replacement = self._get_custom_function(pb_func, dart_func)
                result = re.sub(pattern, replacement + "(", result, flags=re.IGNORECASE)
            elif "()" in dart_func:
                # Property access without parameters
                pattern = rf'\b{pb_func}\s*\(\s*\)'
                result = re.sub(pattern, dart_func, result, flags=re.IGNORECASE)
            else:
                # Direct function name replacement
                result = re.sub(pattern, dart_func + "(", result, flags=re.IGNORECASE)
        
        return result
    
    def _get_custom_function(self, pb_func: str, dart_func: str) -> str:
        """Get custom function implementation for complex conversions."""
        custom_functions = {
            "_substring": "substring",  # mid(str, start, len) -> str.substring(start-1, start-1+len)
            "_abs": "abs",  # Requires dart:math
            "_round": "round",  # Different signature
            "_year": ".year",  # Property access
            "_month": ".month",
            "_day": ".day",
            "_isNumber": "double.tryParse",
            "_isDate": "DateTime.tryParse",
        }
        
        return custom_functions.get(dart_func, dart_func)
    
    def _convert_null_handling(self, expr: str) -> str:
        """Convert PowerBuilder null handling to Dart."""
        result = expr
        
        # Convert IsNull(var) to var == null
        result = re.sub(r'IsNull\s*\(\s*([^)]+)\s*\)', r'\1 == null', result, flags=re.IGNORECASE)
        
        # Convert IsValid(var) to var != null
        result = re.sub(r'IsValid\s*\(\s*([^)]+)\s*\)', r'\1 != null', result, flags=re.IGNORECASE)
        
        # Convert SetNull(var) to var = null
        result = re.sub(r'SetNull\s*\(\s*([^)]+)\s*\)', r'\1 = null', result, flags=re.IGNORECASE)
        
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
            ".text": ".text",
            ".enabled": ".enabled",
            ".visible": ".visible",
            ".checked": ".value",  # For checkboxes
            ".selected": ".value",  # For dropdowns
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
                return f"{var_name} = null;"
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
        if "Uint8List" in expr:
            imports.add("import 'dart:typed_data';")
        
        return list(imports)