"""Service generator for creating service/business logic classes from PowerBuilder code."""

import logging
from typing import Any, Dict, List, Optional

from src.generate.base_generator import CodeGenerator

logger = logging.getLogger(__name__)


class ServiceGenerator(CodeGenerator):
    """Generate service classes from PowerBuilder business logic."""

    def __init__(self, template_dir: str, output_dir: str, target_language: str = "python"):
        """Initialize the service generator.

        Args:
            template_dir: Directory containing service templates
            output_dir: Directory for generated services
            target_language: Target language for services ('python', 'dart', 'typescript')
        """
        super().__init__(template_dir, output_dir)
        self.target_language = target_language

    def generate_service(self, name: str, methods: List[Dict[str, Any]], 
                        dependencies: Optional[List[str]] = None,
                        datawindows: Optional[List[str]] = None) -> None:
        """Generate a service class and write to file.

        Args:
            name: Service class name
            methods: List of method definitions with signatures and logic
            dependencies: Optional list of service dependencies
            datawindows: Optional list of DataWindow names used by the service
        """
        # Prepare context for template
        context = {
            "service_name": self._to_service_name(name),
            "methods": self._process_methods(methods),
            "dependencies": dependencies or [],
            "datawindows": datawindows or [],
            "has_dependencies": bool(dependencies),
            "has_datawindows": bool(datawindows),
            "imports": self._get_required_imports(methods, dependencies, datawindows),
            "target_language": self.target_language,
        }

        # Select template based on target language
        # For now, use the single service.jinja2 template for all languages
        template_name = "service.jinja2"

        try:
            content = self.render_template(template_name, context)
            # Write to file
            filename = f"services/{self._to_filename(context['service_name'])}.py"
            self.write_file(filename, content)
            logger.info(f"Generated service: {filename}")
        except Exception as e:
            logger.error(f"Failed to generate service for {name}: {e}")
            # Fallback to simple service generation
            content = self._generate_simple_service(context)
            filename = f"services/{self._to_filename(context['service_name'])}.py"
            self.write_file(filename, content)
            logger.info(f"Generated fallback service: {filename}")

    def _process_methods(self, methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process method definitions for template."""
        processed = []
        for method in methods:
            processed_method = {
                "name": method.get("name", ""),
                "return_type": self._convert_type(method.get("return_type", "void")),
                "parameters": self._process_parameters(method.get("parameters", [])),
                "body": self._process_method_body(method.get("body", "")),
                "is_async": method.get("is_async", False),
                "is_static": method.get("is_static", False),
                "is_private": method.get("is_private", False),
                "documentation": method.get("documentation", ""),
                "throws": method.get("throws", []),
                "transaction_required": self._requires_transaction(method),
            }
            processed.append(processed_method)
        return processed

    def _process_parameters(self, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process method parameters."""
        processed = []
        for param in parameters:
            processed_param = {
                "name": param.get("name", ""),
                "type": self._convert_type(param.get("type", "any")),
                "default": param.get("default"),
                "is_optional": param.get("is_optional", False),
                "pass_by": param.get("pass_by", "value"),  # value, reference
            }
            processed.append(processed_param)
        return processed

    def _convert_type(self, pb_type: str) -> str:
        """Convert PowerBuilder type to target language type."""
        if self.target_language == "python":
            type_map = {
                "integer": "int",
                "long": "int",
                "string": "str",
                "boolean": "bool",
                "real": "float",
                "double": "float",
                "any": "Any",
                "void": "None",
                "datastore": "DataStore",
                "transaction": "Transaction",
            }
        elif self.target_language == "dart":
            type_map = {
                "integer": "int",
                "long": "int",
                "string": "String",
                "boolean": "bool",
                "real": "double",
                "double": "double",
                "any": "dynamic",
                "void": "void",
                "datastore": "DataStore",
                "transaction": "Transaction",
            }
        elif self.target_language == "typescript":
            type_map = {
                "integer": "number",
                "long": "number",
                "string": "string",
                "boolean": "boolean",
                "real": "number",
                "double": "number",
                "any": "any",
                "void": "void",
                "datastore": "DataStore",
                "transaction": "Transaction",
            }
        else:
            type_map = {}

        return type_map.get(pb_type.lower(), pb_type)

    def _process_method_body(self, body: str) -> List[str]:
        """Process method body into lines of code."""
        if isinstance(body, str):
            return body.split('\n')
        elif isinstance(body, list):
            return body
        else:
            return []

    def _requires_transaction(self, method: Dict[str, Any]) -> bool:
        """Check if method requires database transaction."""
        # Check method body for database operations
        body = str(method.get("body", "")).lower()
        db_keywords = ["insert", "update", "delete", "commit", "rollback", "datastore", "datawindow"]
        return any(keyword in body for keyword in db_keywords)

    def _get_required_imports(self, methods: List[Dict[str, Any]], 
                            dependencies: Optional[List[str]],
                            datawindows: Optional[List[str]]) -> List[str]:
        """Get required imports based on methods and dependencies."""
        imports = []

        if self.target_language == "python":
            imports.append("import logging")

            # Check if we need typing imports
            needs_typing = False
            for method in methods:
                if method.get("return_type") == "any" or any(p.get("type") == "any" for p in method.get("parameters", [])):
                    needs_typing = True
                    break

            if needs_typing:
                imports.append("from typing import Any, Optional")

            # Add dependency imports
            if dependencies:
                for dep in dependencies:
                    imports.append(f"from services import {dep}")

            # Add DataWindow imports if needed
            if datawindows:
                imports.append("from powerbuilder.datawindow import DataWindow")

            # Add transaction imports if needed
            if any(self._requires_transaction(m) for m in methods):
                imports.append("from powerbuilder.transaction import Transaction")

        elif self.target_language == "dart":
            if dependencies:
                for dep in dependencies:
                    imports.append(f"import '{self._to_filename(dep)}.dart';")

            if datawindows:
                imports.append("import 'package:powerbuilder/datawindow.dart';")

        return sorted(list(set(imports)))

    def _to_service_name(self, name: str) -> str:
        """Convert name to service class name."""
        # Remove common prefixes
        name = name.lower()
        for prefix in ["n_", "nvo_", "uo_"]:
            if name.startswith(prefix):
                name = name[len(prefix):]

        # Convert to PascalCase and add Service suffix
        parts = name.replace("-", "_").split("_")
        base_name = "".join(part.capitalize() for part in parts if part)

        if not base_name.endswith("Service"):
            base_name += "Service"

        return base_name

    def _to_filename(self, name: str) -> str:
        """Convert class name to filename."""
        # Convert from PascalCase to snake_case
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _generate_simple_service(self, context: Dict[str, Any]) -> str:
        """Generate a simple service class as fallback."""
        if self.target_language == "python":
            lines = ["import logging", ""]
            lines.append("logger = logging.getLogger(__name__)")
            lines.append("")
            lines.append(f"class {context['service_name']}:")
            lines.append(f'    """Service class for business logic."""')
            lines.append("    ")
            lines.append("    def __init__(self):")
            lines.append('        """Initialize the service."""')
            lines.append("        self.logger = logger")

            # Add dependencies
            for dep in context['dependencies']:
                lines.append(f"        self.{self._to_property_name(dep)} = {dep}()")

            lines.append("    ")

            # Add methods
            for method in context['methods']:
                # Method signature
                params = [f"{p['name']}: {p['type']}" for p in method['parameters']]
                return_type = f" -> {method['return_type']}" if method['return_type'] != "None" else ""
                lines.append(f"    def {method['name']}(self{', ' + ', '.join(params) if params else ''}){return_type}:")

                # Method documentation
                if method['documentation']:
                    lines.append(f'        """{method["documentation"]}"""')
                else:
                    lines.append(f'        """Execute {method["name"]}."""')

                # Method body
                if method['body']:
                    for line in method['body']:
                        lines.append(f"        {line}")
                else:
                    lines.append("        # TODO: Implement method logic")
                    if method['return_type'] != "None":
                        lines.append(f"        return None  # TODO: Return {method['return_type']}")
                    else:
                        lines.append("        pass")

                lines.append("    ")

            return "\n".join(lines)

        elif self.target_language == "dart":
            lines = []
            if context['imports']:
                lines.extend(context['imports'])
                lines.append("")

            lines.append(f"class {context['service_name']} {{")

            # Properties
            lines.append("  final _logger = Logger('{}');".format(context['service_name']))
            for dep in context['dependencies']:
                lines.append(f"  final {self._to_property_name(dep)} = {dep}();")

            lines.append("")

            # Methods
            for method in context['methods']:
                # Method signature
                params = [f"{p['type']} {p['name']}" for p in method['parameters']]
                async_keyword = "Future<" if method['is_async'] else ""
                async_suffix = ">" if method['is_async'] else ""
                lines.append(f"  {async_keyword}{method['return_type']}{async_suffix} {method['name']}({', '.join(params)}) {{")

                # Method body
                if method['body']:
                    for line in method['body']:
                        lines.append(f"    {line}")
                else:
                    lines.append("    // TODO: Implement method logic")

                lines.append("  }")
                lines.append("")

            lines.append("}")

            return "\n".join(lines)

        else:
            return f"// Service generation not implemented for {self.target_language}"

    def _to_property_name(self, class_name: str) -> str:
        """Convert class name to property name."""
        # Remove Service suffix if present
        if class_name.endswith("Service"):
            class_name = class_name[:-7]

        # Convert to camelCase
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', class_name)
        snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        parts = snake_case.split('_')

        if len(parts) > 1:
            return parts[0] + ''.join(p.capitalize() for p in parts[1:])
        return parts[0]