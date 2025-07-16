"""Model generator for creating data model classes from PowerBuilder definitions."""

import logging
from typing import Any, Dict, List, Optional

from src.generate.base_generator import CodeGenerator

logger = logging.getLogger(__name__)


class ModelGenerator(CodeGenerator):
    """Generate model classes from DataWindow definitions."""

    def __init__(self, template_dir: str, output_dir: str, target_language: str = "python"):
        """Initialize the model generator.

        Args:
            template_dir: Directory containing model templates
            output_dir: Directory for generated models
            target_language: Target language for models ('python', 'dart', 'typescript')
        """
        super().__init__(template_dir, output_dir)
        self.target_language = target_language
        self.type_mapping = self._get_type_mapping()

    def _get_type_mapping(self) -> Dict[str, str]:
        """Get PowerBuilder to target language type mappings."""
        if self.target_language == "python":
            return {
                "char": "str",
                "varchar": "str",
                "string": "str",
                "integer": "int",
                "long": "int",
                "decimal": "float",
                "real": "float",
                "double": "float",
                "boolean": "bool",
                "date": "datetime.date",
                "datetime": "datetime.datetime",
                "time": "datetime.time",
                "blob": "bytes",
            }
        elif self.target_language == "dart":
            return {
                "char": "String",
                "varchar": "String",
                "string": "String",
                "integer": "int",
                "long": "int",
                "decimal": "double",
                "real": "double",
                "double": "double",
                "boolean": "bool",
                "date": "DateTime",
                "datetime": "DateTime",
                "time": "DateTime",
                "blob": "Uint8List",
            }
        elif self.target_language == "typescript":
            return {
                "char": "string",
                "varchar": "string",
                "string": "string",
                "integer": "number",
                "long": "number",
                "decimal": "number",
                "real": "number",
                "double": "number",
                "boolean": "boolean",
                "date": "Date",
                "datetime": "Date",
                "time": "Date",
                "blob": "Uint8Array",
            }
        else:
            return {}

    def generate_model(self, name: str, columns: List[Dict[str, Any]], 
                      relationships: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate a model class.

        Args:
            name: Model class name
            columns: List of column definitions with 'name', 'type', 'nullable', etc.
            relationships: Optional list of relationships with other models

        Returns:
            Generated model class code
        """
        # Prepare context for template
        context = {
            "model_name": self._to_pascal_case(name),
            "table_name": name.lower(),
            "columns": self._process_columns(columns),
            "relationships": relationships or [],
            "has_relationships": bool(relationships),
            "imports": self._get_required_imports(columns, relationships),
            "target_language": self.target_language,
        }

        # Select template based on target language
        template_name = f"model_{self.target_language}.jinja2"

        try:
            return self.render_template(template_name, context)
        except Exception as e:
            logger.error(f"Failed to generate model for {name}: {e}")
            # Fallback to simple class generation
            return self._generate_simple_model(context)

    def _process_columns(self, columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process column definitions for template."""
        processed = []
        for col in columns:
            processed_col = {
                "name": col.get("name", ""),
                "type": col.get("type", "string"),
                "target_type": self.type_mapping.get(col.get("type", "string").lower(), "string"),
                "nullable": col.get("nullable", True),
                "primary_key": col.get("primary_key", False),
                "default": col.get("default"),
                "length": col.get("length"),
                "precision": col.get("precision"),
                "scale": col.get("scale"),
            }
            processed.append(processed_col)
        return processed

    def _get_required_imports(self, columns: List[Dict[str, Any]], 
                            relationships: Optional[List[Dict[str, Any]]]) -> List[str]:
        """Get required imports based on column types."""
        imports = set()

        if self.target_language == "python":
            # Check if we need datetime imports
            for col in columns:
                col_type = col.get("type", "").lower()
                if col_type in ("date", "datetime", "time"):
                    imports.add("from datetime import datetime, date, time")
                    break

            # Add typing imports if needed
            if any(col.get("nullable", True) for col in columns):
                imports.add("from typing import Optional")

            if relationships:
                imports.add("from typing import List")

        elif self.target_language == "dart":
            # Check if we need typed_data import for blob
            for col in columns:
                if col.get("type", "").lower() == "blob":
                    imports.add("import 'dart:typed_data';")
                    break

        return sorted(list(imports))

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase."""
        parts = name.replace("-", "_").split("_")
        return "".join(part.capitalize() for part in parts if part)

    def _generate_simple_model(self, context: Dict[str, Any]) -> str:
        """Generate a simple model class as fallback."""
        if self.target_language == "python":
            lines = ["from dataclasses import dataclass"]
            if context["imports"]:
                lines.extend(context["imports"])
            lines.append("")
            lines.append("@dataclass")
            lines.append(f"class {context['model_name']}:")
            lines.append(f'    """Model for {context["table_name"]} table."""')

            for col in context["columns"]:
                type_str = col["target_type"]
                if col["nullable"]:
                    type_str = f"Optional[{type_str}]"
                default = " = None" if col["nullable"] else ""
                lines.append(f"    {col['name']}: {type_str}{default}")

            return "\n".join(lines)

        elif self.target_language == "dart":
            lines = []
            if context["imports"]:
                lines.extend(context["imports"])
                lines.append("")

            lines.append(f"class {context['model_name']} {{")

            # Properties
            for col in context["columns"]:
                nullable = "?" if col["nullable"] else ""
                lines.append(f"  final {col['target_type']}{nullable} {col['name']};")

            # Constructor
            lines.append("")
            lines.append(f"  {context['model_name']}({{")
            for i, col in enumerate(context["columns"]):
                required = "required " if not col["nullable"] else ""
                comma = "," if i < len(context["columns"]) - 1 else ""
                lines.append(f"    {required}this.{col['name']}{comma}")
            lines.append("  });")
            lines.append("}")

            return "\n".join(lines)

        else:
            return f"// Model generation not implemented for {self.target_language}"