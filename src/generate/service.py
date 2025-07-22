"""Service generator for creating service/business logic classes from PowerBuilder code."""

import logging
import re
from typing import Any

from .base import CodeGenerator

logger = logging.getLogger(__name__)


class ServiceGenerator(CodeGenerator):
    """Generate service classes from PowerBuilder business logic."""

    def __init__(
        self,
        template_dir: str,
        output_dir: str,
        target_language: str = "python",
        validate_templates: bool = True,
    ) -> None:
        """Initialize the service generator.

        Args:
            template_dir: Directory containing service templates
            output_dir: Directory for generated services
            target_language: Target language for services ('python', 'dart', 'typescript')
            validate_templates: Whether to validate templates before rendering
        """
        super().__init__(
            template_dir, output_dir, validate_templates=validate_templates
        )
        self.target_language = target_language

    def generate_service(
        self,
        name: str,
        methods: list[dict[str, Any]],
        dependencies: list[str] | None = None,
        datawindows: list[str] | None = None,
    ) -> None:
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
            logger.info("Generated service: %s", filename)
        except Exception as e:
            logger.error("Failed to generate service for %s: %s", name, e)
            # Fallback to simple service generation
            content = self._generate_simple_service(context)
            filename = f"services/{self._to_filename(context['service_name'])}.py"
            self.write_file(filename, content)
            logger.info("Generated fallback service: %s", filename)

    def _process_methods(self, methods: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

    def _process_parameters(
        self, parameters: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
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

    def _process_method_body(self, body: str) -> list[str]:
        """Process method body into lines of code."""
        if isinstance(body, str):
            return body.split("\n")
        if isinstance(body, list):
            return body
        return []

    def _requires_transaction(self, method: dict[str, Any]) -> bool:
        """Check if method requires database transaction."""
        # Check method body for database operations
        body = str(method.get("body", "")).lower()
        db_keywords = [
            "insert",
            "update",
            "delete",
            "commit",
            "rollback",
            "datastore",
            "datawindow",
        ]
        return any(keyword in body for keyword in db_keywords)

    def _get_required_imports(
        self,
        methods: list[dict[str, Any]],
        dependencies: list[str] | None,
        datawindows: list[str] | None,
    ) -> list[str]:
        """Get required imports based on methods and dependencies."""
        imports = []

        if self.target_language == "python":
            imports.append("import logging")

            # Check if we need typing imports
            needs_typing = False
            for method in methods:
                if method.get("return_type") == "any" or any(
                    p.get("type") == "any" for p in method.get("parameters", [])
                ):
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

        return sorted(set(imports))

    def _to_service_name(self, name: str) -> str:
        """Convert name to service class name."""
        # Remove common prefixes
        name = name.lower()
        for prefix in ["n_", "nvo_", "uo_"]:
            name = name.removeprefix(prefix)

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

        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _generate_simple_service(self, context: dict[str, Any]) -> str:
        """Generate a simple service class as fallback."""
        if self.target_language == "python":
            lines = ["import logging", ""]
            lines.append("logger = logging.getLogger(__name__)")
            lines.append("")
            lines.append(f"class {context['service_name']}:")
            lines.append('    """Service class for business logic."""')
            lines.append("    ")
            lines.append("    def __init__(self):")
            lines.append('        """Initialize the service."""')
            lines.append("        self.logger = logger")

            # Add dependencies
            for dep in context["dependencies"]:
                lines.append(f"        self.{self._to_property_name(dep)} = {dep}()")

            lines.append("    ")

            # Add methods
            for method in context["methods"]:
                # Method signature
                params = [f"{p['name']}: {p['type']}" for p in method["parameters"]]
                return_type = (
                    f" -> {method['return_type']}"
                    if method["return_type"] != "None"
                    else ""
                )
                lines.append(
                    f"    def {method['name']}(self{', ' + ', '.join(params) if params else ''}){return_type}:"
                )

                # Method documentation
                if method["documentation"]:
                    lines.append(f'        """{method["documentation"]}"""')
                else:
                    lines.append(f'        """Execute {method["name"]}."""')

                # Method body
                if method["body"]:
                    for line in method["body"]:
                        lines.append(f"        {line}")
                else:
                    lines.append("        # TODO: Implement method logic")
                    if method["return_type"] != "None":
                        lines.append(
                            f"        return None  # TODO: Return {method['return_type']}"
                        )
                    else:
                        lines.append("        pass")

                lines.append("    ")

            return "\n".join(lines)

        if self.target_language == "dart":
            lines = []
            if context["imports"]:
                lines.extend(context["imports"])
                lines.append("")

            lines.append(f"class {context['service_name']} {{")

            # Properties
            lines.append(
                "  final _logger = Logger('{}');".format(context["service_name"])
            )
            for dep in context["dependencies"]:
                lines.append(f"  final {self._to_property_name(dep)} = {dep}();")

            lines.append("")

            # Methods
            for method in context["methods"]:
                # Method signature
                params = [f"{p['type']} {p['name']}" for p in method["parameters"]]
                async_keyword = "Future<" if method["is_async"] else ""
                async_suffix = ">" if method["is_async"] else ""
                lines.append(
                    f"  {async_keyword}{method['return_type']}{async_suffix} {method['name']}({', '.join(params)}) {{"
                )

                # Method body
                if method["body"]:
                    for line in method["body"]:
                        lines.append(f"    {line}")
                else:
                    lines.append("    // TODO: Implement method logic")

                lines.append("  }")
                lines.append("")

            lines.append("}")

            return "\n".join(lines)

        return f"// Service generation not implemented for {self.target_language}"

    def _to_property_name(self, class_name: str) -> str:
        """Convert class name to property name."""
        # Remove Service suffix if present
        class_name = class_name.removesuffix("Service")

        # Convert to camelCase
        import re

        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", class_name)
        snake_case = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
        parts = snake_case.split("_")

        if len(parts) > 1:
            return parts[0] + "".join(p.capitalize() for p in parts[1:])
        return parts[0]

    def _generate_service_methods(
        self, model_name: str, model: dict[str, Any], target_language: str = "python"
    ) -> list[dict[str, Any]]:
        """Generate CRUD methods for a service based on model.

        Args:
            model_name: Name of the model/entity
            model: Model definition with properties
            target_language: Target language for service

        Returns:
            List of method definitions
        """
        methods = []

        # Determine primary key
        pk_field = self._find_primary_key(model) or "id"
        pk_type = self._get_field_type(model, pk_field)

        if target_language == "python":
            # Create method
            methods.append(
                {
                    "name": f"create_{self._to_snake_case(model_name)}",
                    "return_type": model_name,
                    "parameters": [
                        {
                            "name": "data",
                            "type": "dict[str, Any]",
                            "is_optional": False,
                        }
                    ],
                    "is_async": True,
                    "body": [
                        "try:",
                        f"    # Validate {model_name} data",
                        "    validated_data = self._validate_create_data(data)",
                        "    ",
                        "    # Create in database",
                        "    async with self.db.transaction() as tx:",
                        "        result = await tx.execute(",
                        f'            "INSERT INTO {self._to_table_name(model_name)} ({self._get_insert_columns(model)}) VALUES ({self._get_insert_placeholders(model)})",',
                        "            validated_data",
                        "        )",
                        "        new_id = result.lastrowid",
                        "        ",
                        "        # Fetch and return created object",
                        f"        return await self.get_{self._to_snake_case(model_name)}(new_id)",
                        "except Exception as e:",
                        f'    logger.error("Failed to create {model_name}: %s", e)',
                        "    raise",
                    ],
                    "documentation": f"Create a new {model_name} instance.",
                    "throws": ["ValidationError", "DatabaseError"],
                    "transaction_required": True,
                }
            )

            # Read method
            methods.append(
                {
                    "name": f"get_{self._to_snake_case(model_name)}",
                    "return_type": f"{model_name} | None",
                    "parameters": [
                        {
                            "name": pk_field,
                            "type": pk_type,
                            "is_optional": False,
                        }
                    ],
                    "is_async": True,
                    "body": [
                        "try:",
                        "    result = await self.db.fetch_one(",
                        f'        "SELECT * FROM {self._to_table_name(model_name)} WHERE {pk_field} = %s",',
                        f"        ({pk_field},)",
                        "    )",
                        "    ",
                        "    if result:",
                        f"        return {model_name}(**result)",
                        "    return None",
                        "except Exception as e:",
                        f'    logger.error("Failed to get {model_name}: %s", e)',
                        "    raise",
                    ],
                    "documentation": f"Get a {model_name} by {pk_field}.",
                    "throws": ["DatabaseError"],
                    "transaction_required": False,
                }
            )

            # Update method
            methods.append(
                {
                    "name": f"update_{self._to_snake_case(model_name)}",
                    "return_type": f"{model_name} | None",
                    "parameters": [
                        {
                            "name": pk_field,
                            "type": pk_type,
                            "is_optional": False,
                        },
                        {
                            "name": "data",
                            "type": "dict[str, Any]",
                            "is_optional": False,
                        },
                    ],
                    "is_async": True,
                    "body": [
                        "try:",
                        "    # Validate update data",
                        "    validated_data = self._validate_update_data(data)",
                        "    ",
                        "    async with self.db.transaction() as tx:",
                        "        # Build dynamic update query",
                        "        set_clause = ', '.join(f'{k} = %s' for k in validated_data.keys())",
                        "        values = list(validated_data.values()) + ["
                        + pk_field
                        + "]",
                        "        ",
                        "        result = await tx.execute(",
                        f'            f"UPDATE {self._to_table_name(model_name)} SET {{set_clause}} WHERE {pk_field} = %s",',
                        "            values",
                        "        )",
                        "        ",
                        "        if result.rowcount > 0:",
                        f"            return await self.get_{self._to_snake_case(model_name)}({pk_field})",
                        "        return None",
                        "except Exception as e:",
                        f'    logger.error("Failed to update {model_name}: %s", e)',
                        "    raise",
                    ],
                    "documentation": f"Update a {model_name}.",
                    "throws": ["ValidationError", "DatabaseError"],
                    "transaction_required": True,
                }
            )

            # Delete method
            methods.append(
                {
                    "name": f"delete_{self._to_snake_case(model_name)}",
                    "return_type": "bool",
                    "parameters": [
                        {
                            "name": pk_field,
                            "type": pk_type,
                            "is_optional": False,
                        }
                    ],
                    "is_async": True,
                    "body": [
                        "try:",
                        "    async with self.db.transaction() as tx:",
                        "        result = await tx.execute(",
                        f'            "DELETE FROM {self._to_table_name(model_name)} WHERE {pk_field} = %s",',
                        f"            ({pk_field},)",
                        "        )",
                        "        return result.rowcount > 0",
                        "except Exception as e:",
                        f'    logger.error("Failed to delete {model_name}: %s", e)',
                        "    raise",
                    ],
                    "documentation": f"Delete a {model_name}.",
                    "throws": ["DatabaseError"],
                    "transaction_required": True,
                }
            )

            # List method
            methods.append(
                {
                    "name": f"list_{self._to_snake_case(model_name)}s",
                    "return_type": f"list[{model_name}]",
                    "parameters": [
                        {
                            "name": "limit",
                            "type": "int",
                            "is_optional": True,
                            "default": 100,
                        },
                        {
                            "name": "offset",
                            "type": "int",
                            "is_optional": True,
                            "default": 0,
                        },
                        {
                            "name": "filters",
                            "type": "dict[str, Any]",
                            "is_optional": True,
                            "default": None,
                        },
                    ],
                    "is_async": True,
                    "body": [
                        "try:",
                        "    query = f'SELECT * FROM "
                        + self._to_table_name(model_name)
                        + "'",
                        "    params = []",
                        "    ",
                        "    # Apply filters",
                        "    if filters:",
                        "        where_clauses = []",
                        "        for key, value in filters.items():",
                        "            where_clauses.append(f'{key} = %s')",
                        "            params.append(value)",
                        "        query += ' WHERE ' + ' AND '.join(where_clauses)",
                        "    ",
                        "    # Add pagination",
                        "    query += ' LIMIT %s OFFSET %s'",
                        "    params.extend([limit, offset])",
                        "    ",
                        "    results = await self.db.fetch_all(query, params)",
                        f"    return [{model_name}(**row) for row in results]",
                        "except Exception as e:",
                        f'    logger.error("Failed to list {model_name}s: %s", e)',
                        "    raise",
                    ],
                    "documentation": f"List {model_name}s with optional filtering and pagination.",
                    "throws": ["DatabaseError"],
                    "transaction_required": False,
                }
            )

            # Add validation methods
            methods.append(
                {
                    "name": "_validate_create_data",
                    "return_type": "dict[str, Any]",
                    "parameters": [
                        {
                            "name": "data",
                            "type": "dict[str, Any]",
                            "is_optional": False,
                        }
                    ],
                    "is_private": True,
                    "body": [
                        "# TODO: Add field validation logic",
                        "validated = {}",
                        "required_fields = " + str(self._get_required_fields(model)),
                        "",
                        "for field in required_fields:",
                        "    if field not in data:",
                        "        raise ValidationError(f'Required field {field} is missing')",
                        "    validated[field] = data[field]",
                        "",
                        "# Copy optional fields",
                        "optional_fields = " + str(self._get_optional_fields(model)),
                        "for field in optional_fields:",
                        "    if field in data:",
                        "        validated[field] = data[field]",
                        "",
                        "return validated",
                    ],
                    "documentation": "Validate data for creation.",
                    "throws": ["ValidationError"],
                }
            )

            methods.append(
                {
                    "name": "_validate_update_data",
                    "return_type": "dict[str, Any]",
                    "parameters": [
                        {
                            "name": "data",
                            "type": "dict[str, Any]",
                            "is_optional": False,
                        }
                    ],
                    "is_private": True,
                    "body": [
                        "# TODO: Add field validation logic",
                        "validated = {}",
                        "updatable_fields = " + str(self._get_updatable_fields(model)),
                        "",
                        "for field, value in data.items():",
                        "    if field in updatable_fields:",
                        "        validated[field] = value",
                        "",
                        "if not validated:",
                        "    raise ValidationError('No valid fields to update')",
                        "",
                        "return validated",
                    ],
                    "documentation": "Validate data for updates.",
                    "throws": ["ValidationError"],
                }
            )

        elif target_language == "dart":
            # Dart/Flutter service methods
            methods.append(
                {
                    "name": f"create{model_name}",
                    "return_type": f"Future<{model_name}>",
                    "parameters": [
                        {
                            "name": "data",
                            "type": "Map<String, dynamic>",
                            "is_optional": False,
                        }
                    ],
                    "is_async": True,
                    "body": [
                        "try {",
                        "  final validated = _validateCreateData(data);",
                        f"  final response = await _api.post('/{self._to_snake_case(model_name)}s', validated);",
                        f"  return {model_name}.fromJson(response.data);",
                        "} catch (e) {",
                        f"  _logger.error('Failed to create {model_name}: $e');",
                        "  rethrow;",
                        "}",
                    ],
                    "documentation": f"Create a new {model_name}.",
                }
            )

        return methods

    def _find_primary_key(self, model: dict[str, Any]) -> str | None:
        """Find primary key field in model."""
        for field in model.get("fields", []):
            if field.get("is_primary_key") or field.get("primary_key"):
                return field.get("name")

        # Check for common primary key names
        field_names = [f.get("name", "").lower() for f in model.get("fields", [])]
        for pk_name in ["id", "uid", f"{model.get('name', '').lower()}_id"]:
            if pk_name in field_names:
                return pk_name

        return None

    def _get_field_type(self, model: dict[str, Any], field_name: str) -> str:
        """Get the type of a field in the model."""
        for field in model.get("fields", []):
            if field.get("name") == field_name:
                return self._convert_type(field.get("type", "any"))
        return "Any"

    def _to_table_name(self, model_name: str) -> str:
        """Convert model name to database table name."""
        # Convert to snake_case and pluralize
        snake = self._to_snake_case(model_name)
        if not snake.endswith("s"):
            snake += "s"
        return snake

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _get_insert_columns(self, model: dict[str, Any]) -> str:
        """Get comma-separated column names for INSERT."""
        fields = [
            f.get("name")
            for f in model.get("fields", [])
            if not f.get("is_generated") and f.get("name")
        ]
        return ", ".join(fields)

    def _get_insert_placeholders(self, model: dict[str, Any]) -> str:
        """Get placeholders for INSERT VALUES."""
        fields = [
            f
            for f in model.get("fields", [])
            if not f.get("is_generated") and f.get("name")
        ]
        return ", ".join(["%s"] * len(fields))

    def _get_required_fields(self, model: dict[str, Any]) -> list[str]:
        """Get list of required fields."""
        return [
            f.get("name")
            for f in model.get("fields", [])
            if f.get("required", False) and not f.get("is_generated")
        ]

    def _get_optional_fields(self, model: dict[str, Any]) -> list[str]:
        """Get list of optional fields."""
        return [
            f.get("name")
            for f in model.get("fields", [])
            if not f.get("required", False) and not f.get("is_generated")
        ]

    def _get_updatable_fields(self, model: dict[str, Any]) -> list[str]:
        """Get list of fields that can be updated."""
        return [
            f.get("name")
            for f in model.get("fields", [])
            if not f.get("is_generated") and not f.get("is_primary_key")
        ]
