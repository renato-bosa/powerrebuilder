"""PowerBuilder to target language type converter.

This module handles type conversions between PowerBuilder types and target languages
like Dart (Flutter), Python, etc.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TypeConverter:
    """Converts PowerBuilder types to target language types."""

    def __init__(self, target_language: str = "dart"):
        """Initialize the type converter.

        Args:
            target_language: Target language ('dart', 'python', etc.)
        """
        self.target_language = target_language

        # PowerBuilder to Dart type mappings
        self.dart_type_map = {
            # Basic types
            "integer": "int",
            "long": "int",
            "ulong": "int",
            "uint": "int",
            "decimal": "double",
            "real": "double",
            "double": "double",
            "string": "String",
            "char": "String",
            "boolean": "bool",
            "blob": "Uint8List",
            "byte": "int",
            "date": "DateTime",
            "time": "DateTime",
            "datetime": "DateTime",
            "timestamp": "DateTime",

            # Object types
            "any": "dynamic",
            "powerobject": "Object",
            "nonvisualobject": "Object",
            "structure": "Map<String, dynamic>",
            "datastore": "DataStore",
            "datawindow": "DataWindow",

            # Array suffix handling
            "[]": "List",
        }

        # PowerBuilder to Python type mappings
        self.python_type_map = {
            # Basic types
            "integer": "int",
            "long": "int",
            "ulong": "int",
            "uint": "int",
            "decimal": "float",
            "real": "float",
            "double": "float",
            "string": "str",
            "char": "str",
            "boolean": "bool",
            "blob": "bytes",
            "byte": "int",
            "date": "datetime.date",
            "time": "datetime.time",
            "datetime": "datetime.datetime",
            "timestamp": "datetime.datetime",

            # Object types
            "any": "Any",
            "powerobject": "object",
            "nonvisualobject": "object",
            "structure": "Dict[str, Any]",
            "datastore": "DataStore",
            "datawindow": "DataWindow",

            # Array suffix handling
            "[]": "List",
        }

        # Default values for types
        self.dart_defaults = {
            "int": "0",
            "double": "0.0",
            "String": "''",
            "bool": "false",
            "DateTime": "DateTime.now()",
            "List": "[]",
            "Map": "{}",
            "dynamic": "null",
        }

        self.python_defaults = {
            "int": "0",
            "float": "0.0",
            "str": "''",
            "bool": "False",
            "datetime": "datetime.now()",
            "List": "[]",
            "Dict": "{}",
            "Any": "None",
        }

    def convert_type(self, pb_type: str, nullable: bool = True) -> str:
        """Convert PowerBuilder type to target language type.

        Args:
            pb_type: PowerBuilder type name
            nullable: Whether the type should be nullable

        Returns:
            Converted type string
        """
        if not pb_type:
            return self._get_dynamic_type()

        # Normalize type
        pb_type = pb_type.lower().strip()

        # Handle array types
        is_array = pb_type.endswith("[]")
        if is_array:
            pb_type = pb_type[:-2]

        # Get base type
        if self.target_language == "dart":
            base_type = self._convert_to_dart(pb_type)
            if is_array:
                base_type = f"List<{base_type}>"
            if nullable and base_type != "dynamic":
                base_type = f"{base_type}?"
        elif self.target_language == "python":
            base_type = self._convert_to_python(pb_type)
            if is_array:
                base_type = f"List[{base_type}]"
            if nullable:
                base_type = f"Optional[{base_type}]"
        else:
            base_type = pb_type

        return base_type

    def _convert_to_dart(self, pb_type: str) -> str:
        """Convert PowerBuilder type to Dart type."""
        return self.dart_type_map.get(pb_type, "Object")

    def _convert_to_python(self, pb_type: str) -> str:
        """Convert PowerBuilder type to Python type."""
        return self.python_type_map.get(pb_type, "object")

    def _get_dynamic_type(self) -> str:
        """Get the dynamic/any type for the target language."""
        if self.target_language == "dart":
            return "dynamic"
        elif self.target_language == "python":
            return "Any"
        return "object"

    def get_default_value(self, type_str: str) -> str:
        """Get default value for a type.

        Args:
            type_str: Type string in target language

        Returns:
            Default value string
        """
        if self.target_language == "dart":
            # Handle nullable types
            if type_str.endswith("?"):
                return "null"
            # Handle generic types
            for dart_type, default in self.dart_defaults.items():
                if type_str.startswith(dart_type):
                    return default
            return "null"
        elif self.target_language == "python":
            # Handle Optional types
            if type_str.startswith("Optional"):
                return "None"
            # Handle generic types
            for py_type, default in self.python_defaults.items():
                if py_type in type_str:
                    return default
            return "None"
        return ""

    def is_numeric_type(self, pb_type: str) -> bool:
        """Check if a PowerBuilder type is numeric."""
        numeric_types = {
            "integer", "long", "ulong", "uint", 
            "decimal", "real", "double", "byte"
        }
        return pb_type.lower().strip() in numeric_types

    def is_string_type(self, pb_type: str) -> bool:
        """Check if a PowerBuilder type is string-based."""
        string_types = {"string", "char"}
        return pb_type.lower().strip() in string_types

    def is_date_type(self, pb_type: str) -> bool:
        """Check if a PowerBuilder type is date/time-based."""
        date_types = {"date", "time", "datetime", "timestamp"}
        return pb_type.lower().strip() in date_types

    def is_object_type(self, pb_type: str) -> bool:
        """Check if a PowerBuilder type is an object type."""
        object_types = {
            "powerobject", "nonvisualobject", "structure",
            "datastore", "datawindow", "any"
        }
        return pb_type.lower().strip() in object_types

    def get_import_for_type(self, type_str: str) -> Optional[str]:
        """Get import statement needed for a type.

        Args:
            type_str: Type string in target language

        Returns:
            Import statement or None if no import needed
        """
        if self.target_language == "dart":
            if "Uint8List" in type_str:
                return "import 'dart:typed_data';"
            elif "DateTime" in type_str:
                return None  # DateTime is built-in
            elif "DataStore" in type_str or "DataWindow" in type_str:
                return "import 'package:powerbuilder_core/powerbuilder_core.dart';"
        elif self.target_language == "python":
            if "datetime" in type_str:
                return "from datetime import datetime"
            elif "Optional" in type_str or "List" in type_str or "Dict" in type_str:
                return "from typing import Optional, List, Dict, Any"
        return None