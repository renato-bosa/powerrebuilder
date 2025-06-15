"""PowerBuilder to Flutter/Dart type converter.

Converts PowerBuilder data types to appropriate Dart types based on
the mapping specification.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class TypeConverter:
    """Converts PowerBuilder types to Dart types."""
    
    def __init__(self, mapping_file: Optional[Path] = None):
        """Initialize the type converter with mapping rules.
        
        Args:
            mapping_file: Path to the JSON mapping file
        """
        if mapping_file is None:
            mapping_file = Path(__file__).parent.parent / "flutter" / "powerbuilder_flutter_mapping.json"
        
        self.mappings = self._load_mappings(mapping_file)
        self._type_cache: Dict[str, str] = {}
    
    def _load_mappings(self, mapping_file: Path) -> Dict:
        """Load type mappings from JSON file."""
        try:
            with open(mapping_file, 'r') as f:
                data = json.load(f)
                return data.get("type_mappings", {})
        except Exception as e:
            logger.warning(f"Failed to load type mappings: {e}. Using defaults.")
            return self._get_default_mappings()
    
    def _get_default_mappings(self) -> Dict:
        """Get default type mappings if file is not available."""
        return {
            "basic_types": {
                "integer": {"dart_type": "int", "nullable_syntax": "int?", "default_value": "0"},
                "long": {"dart_type": "int", "nullable_syntax": "int?", "default_value": "0"},
                "decimal": {"dart_type": "double", "nullable_syntax": "double?", "default_value": "0.0"},
                "real": {"dart_type": "double", "nullable_syntax": "double?", "default_value": "0.0"},
                "double": {"dart_type": "double", "nullable_syntax": "double?", "default_value": "0.0"},
                "string": {"dart_type": "String", "nullable_syntax": "String?", "default_value": "''"},
                "char": {"dart_type": "String", "nullable_syntax": "String?", "default_value": "''"},
                "boolean": {"dart_type": "bool", "nullable_syntax": "bool?", "default_value": "false"},
                "date": {"dart_type": "DateTime", "nullable_syntax": "DateTime?", "default_value": "DateTime.now()"},
                "time": {"dart_type": "DateTime", "nullable_syntax": "DateTime?", "default_value": "DateTime.now()"},
                "datetime": {"dart_type": "DateTime", "nullable_syntax": "DateTime?", "default_value": "DateTime.now()"},
                "blob": {"dart_type": "Uint8List", "nullable_syntax": "Uint8List?", "default_value": "Uint8List(0)"},
                "any": {"dart_type": "dynamic", "nullable_syntax": "dynamic", "default_value": "null"},
            },
            "complex_types": {
                "array": {"dart_type": "List<{element_type}>", "nullable_syntax": "List<{element_type}>?", "default_value": "[]"},
                "structure": {"dart_type": "class", "pattern": "freezed", "nullable_syntax": "{class_name}?", "default_value": "null"},
                "datastore": {"dart_type": "Repository", "pattern": "repository", "nullable_syntax": "{repository_name}?", "default_value": "null"},
            }
        }
    
    def convert_type(self, pb_type: str, nullable: bool = False) -> str:
        """Convert a PowerBuilder type to Dart type.
        
        Args:
            pb_type: PowerBuilder type name
            nullable: Whether the type should be nullable
            
        Returns:
            Dart type string
        """
        # Check cache first
        cache_key = f"{pb_type}:{nullable}"
        if cache_key in self._type_cache:
            return self._type_cache[cache_key]
        
        # Normalize the PowerBuilder type
        pb_type_lower = pb_type.lower().strip()
        
        # Handle array types
        if pb_type_lower.endswith("[]"):
            element_type = pb_type_lower[:-2]
            dart_element_type = self.convert_type(element_type, False)
            dart_type = f"List<{dart_element_type}>"
            if nullable:
                dart_type += "?"
            self._type_cache[cache_key] = dart_type
            return dart_type
        
        # Look up in basic types
        basic_types = self.mappings.get("basic_types", {})
        if pb_type_lower in basic_types:
            type_info = basic_types[pb_type_lower]
            dart_type = type_info["nullable_syntax"] if nullable else type_info["dart_type"]
            self._type_cache[cache_key] = dart_type
            return dart_type
        
        # Check if it's a decimal with precision
        if pb_type_lower.startswith("decimal("):
            dart_type = "double" + ("?" if nullable else "")
            self._type_cache[cache_key] = dart_type
            return dart_type
        
        # Check if it's a char with length
        if pb_type_lower.startswith("char("):
            dart_type = "String" + ("?" if nullable else "")
            self._type_cache[cache_key] = dart_type
            return dart_type
        
        # Default to treating unknown types as custom classes
        dart_type = pb_type + ("?" if nullable else "")
        self._type_cache[cache_key] = dart_type
        return dart_type
    
    def get_default_value(self, pb_type: str) -> str:
        """Get the default value for a PowerBuilder type in Dart.
        
        Args:
            pb_type: PowerBuilder type name
            
        Returns:
            Default value string for Dart
        """
        pb_type_lower = pb_type.lower().strip()
        
        # Handle array types
        if pb_type_lower.endswith("[]"):
            return "[]"
        
        # Look up in basic types
        basic_types = self.mappings.get("basic_types", {})
        if pb_type_lower in basic_types:
            return basic_types[pb_type_lower].get("default_value", "null")
        
        # Special cases
        if pb_type_lower.startswith("decimal("):
            return "0.0"
        if pb_type_lower.startswith("char("):
            return "''"
        
        # Default
        return "null"
    
    def get_imports_for_type(self, pb_type: str) -> list[str]:
        """Get required imports for a PowerBuilder type.
        
        Args:
            pb_type: PowerBuilder type name
            
        Returns:
            List of import statements needed
        """
        imports = []
        pb_type_lower = pb_type.lower().strip()
        
        # Check basic types for imports
        basic_types = self.mappings.get("basic_types", {})
        if pb_type_lower in basic_types:
            type_info = basic_types[pb_type_lower]
            if "import" in type_info:
                imports.append(f"import '{type_info['import']}';")
        
        # Special cases
        if pb_type_lower == "blob" or "uint8list" in pb_type_lower:
            imports.append("import 'dart:typed_data';")
            # Additional imports for blob handling
            imports.append("import 'dart:convert';")  # For base64
            if self._requires_file_storage(pb_type_lower):
                imports.append("import 'dart:io';")
                imports.append("import 'package:path_provider/path_provider';")
        
        return imports
    
    def is_primitive_type(self, pb_type: str) -> bool:
        """Check if a PowerBuilder type is a primitive type.
        
        Args:
            pb_type: PowerBuilder type name
            
        Returns:
            True if primitive type
        """
        pb_type_lower = pb_type.lower().strip()
        primitives = {
            "integer", "long", "decimal", "real", "double",
            "string", "char", "boolean", "date", "time", "datetime"
        }
        
        # Remove array notation
        if pb_type_lower.endswith("[]"):
            pb_type_lower = pb_type_lower[:-2]
        
        # Remove precision notation
        if "(" in pb_type_lower:
            pb_type_lower = pb_type_lower[:pb_type_lower.index("(")]
        
        return pb_type_lower in primitives
    
    def convert_method_signature(self, pb_signature: str) -> Tuple[str, str]:
        """Convert a PowerBuilder method signature to Dart.
        
        Args:
            pb_signature: PowerBuilder method signature
            
        Returns:
            Tuple of (return_type, parameter_list)
        """
        # This is a simplified implementation
        # In a real implementation, you would parse the signature properly
        
        # Default return type
        return_type = "void"
        
        # Default empty parameter list
        param_list = ""
        
        # Parse return type if present
        if " function " in pb_signature.lower():
            parts = pb_signature.split(" function ")
            if len(parts) > 0:
                pb_return_type = parts[0].strip()
                return_type = self.convert_type(pb_return_type)
        
        # Parameter parsing would be implemented here if needed
        
        return return_type, param_list
    
    def _requires_file_storage(self, pb_type: str) -> bool:
        """Check if a blob type requires file storage based on context.
        
        Args:
            pb_type: PowerBuilder type name
            
        Returns:
            True if file storage is recommended
        """
        # This is a simplified check - in practice, you'd check the actual data size
        # or have metadata about expected blob sizes
        return "large" in pb_type or "file" in pb_type
    
    def convert_blob_type(self, pb_type: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Convert blob type with context-aware handling.
        
        Args:
            pb_type: PowerBuilder blob type
            context: Context information (size hints, usage, etc.)
            
        Returns:
            Dictionary with dart_type and handling strategy
        """
        pb_type_lower = pb_type.lower().strip()
        
        if pb_type_lower != "blob":
            return {"dart_type": self.convert_type(pb_type), "strategy": "default"}
        
        # Check context for size hints
        expected_size = context.get("expected_size", 0)
        usage = context.get("usage", "data")  # data, image, document, etc.
        
        # Determine strategy based on context
        if usage == "image":
            return {
                "dart_type": "ImageProvider",
                "strategy": "image",
                "implementation": "MemoryImage"
            }
        elif expected_size > 1024 * 1024:  # > 1MB
            return {
                "dart_type": "File",
                "strategy": "file",
                "implementation": "FileStorage"
            }
        elif expected_size > 10 * 1024:  # > 10KB
            return {
                "dart_type": "Uint8List",
                "strategy": "memory",
                "implementation": "InMemory"
            }
        else:
            return {
                "dart_type": "String",
                "strategy": "base64",
                "implementation": "Base64Encoded"
            }