"""Code generation module for converting PowerBuilder models to modern code.

This module forms the final stage in the PowerBuilder reverse engineering pipeline,
generating modern web application code from the parsed and analyzed PowerBuilder models.
It transforms the internal representation into executable code for both backend and frontend.

Key components:
- CodeGenerator: Base class providing template rendering functionality
- ModelGenerator: Generates SQLModel models from PowerBuilder database schema
- ServiceGenerator: Converts PowerBuilder business logic into service layer classes
- FlutterGenerator: Transforms PowerBuilder UI into Flutter/Dart widgets and screens

The code generation relies on Jinja2 templates (stored in backend/templates and flutter/templates)
to produce consistent, well-formatted output across different target technologies:
- Backend: Litestar endpoints, SQLModel models, Pydantic schemas
- Frontend: Flutter/Dart widgets, screens, models, and state management

Each generator handles a specific aspect of the application and is orchestrated
through the main entry points: generate_models(), generate_services(), and generate_flutter().
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from model.utils.errors import GenerateError
from parse.sql_parser import SQLParser
from generate.converters.relationship_extractor import RelationshipExtractor

from .jinja_filters import register_filters
from .template_schemas import validate_template_context
from .template_validator import TemplateValidator

logger = logging.getLogger(__name__)


def extract_datawindow_from_ast(ast_data: dict) -> dict | None:
    """Extract DataWindow information from parsed AST.

    Args:
        ast_data: Parsed AST data from JSON

    Returns:
        Dictionary with columns, relationships, and SQL info
    """
    if not isinstance(ast_data, dict):
        return None

    # Look for DataWindow node in the AST
    if (
        ast_data.get("node_type") == "DataWindow"
        or ast_data.get("type") == "datawindow"
    ):
        columns = []
        relationships = []
        sql_info = {}
        primary_keys = []

        # Extract columns with foreign key information
        if "columns" in ast_data:
            for col in ast_data["columns"]:
                col_name = col.get("name", col.get("column_name", ""))
                col_type = col.get("column_type", col.get("type", "string"))
                
                column_info = {
                    "name": col_name,
                    "type": col_type,
                    "nullable": col.get("is_nullable", True),
                    "length": col.get("length"),
                    "precision": col.get("precision"),
                    "scale": col.get("scale"),
                }
                
                # Extract foreign key information if present
                if col.get("foreign_key"):
                    column_info["foreign_key"] = col["foreign_key"]
                    # Create a relationship entry
                    relationships.append({
                        "type": "foreign_key",
                        "source_column": column_info["name"],
                        "target_table": col.get("foreign_table"),
                        "target_column": col.get("foreign_column", "id"),
                    })
                
                # Check if this column is a primary key
                if col.get("is_primary_key") or col.get("primary_key"):
                    primary_keys.append(column_info["name"])
                    column_info["primary_key"] = True
                
                # Add blob metadata if this is a blob column
                if col_type.lower() == "blob":
                    # Determine blob usage based on column name
                    blob_usage = _determine_blob_usage(col_name)
                    column_info["blob_metadata"] = {
                        "usage": blob_usage,
                        "display_widget": f"{_to_pascal_case(col_name)}BlobDisplay",
                        "mime_type": _guess_mime_type(blob_usage, col_name),
                        "expected_size": col.get("blob_size", "medium")  # small, medium, large
                    }
                
                columns.append(column_info)

        # Extract SQL statements
        for sql_type in ["retrieve_sql", "update_sql", "insert_sql", "delete_sql"]:
            if ast_data.get(sql_type):
                sql_info[sql_type] = ast_data[sql_type]
        
        # Extract foreign keys from SQL
        if sql_info.get("retrieve_sql"):
            try:
                # Parse the SQL to get AST
                sql_parser = SQLParser()
                parsed_sql = sql_parser.parse(sql_info["retrieve_sql"])
                
                if parsed_sql and isinstance(parsed_sql, list) and len(parsed_sql) > 0:
                    sql_stmt = parsed_sql[0]
                    
                    # Use RelationshipExtractor to find relationships
                    rel_extractor = RelationshipExtractor()
                    sql_relationships = rel_extractor.extract_from_select(sql_stmt)
                    
                    # Convert relationships to our format
                    for rel in sql_relationships:
                        # Extract column mappings from the relationship
                        for mapping in rel.column_mappings:
                            # Check if we already have this relationship from explicit foreign keys
                            existing = False
                            for existing_rel in relationships:
                                if (existing_rel.get("source_column") == mapping.source_column and
                                    existing_rel.get("target_table") == mapping.target_table):
                                    existing = True
                                    break
                            
                            if not existing:
                                relationships.append({
                                    "type": "foreign_key",
                                    "source_table": mapping.source_table,
                                    "source_column": mapping.source_column,
                                    "target_table": mapping.target_table,
                                    "target_column": mapping.target_column,
                                    "join_type": rel.join_type.value,
                                    "inferred_from_sql": True
                                })
                    
                    logger.debug(f"Extracted {len(sql_relationships)} relationships from SQL")
                    
            except Exception as e:
                logger.warning(f"Failed to extract relationships from SQL: {e}")

        # Extract table information with primary keys
        table_info = ast_data.get("table", {})
        if isinstance(table_info, dict):
            # Use table name if available
            table_name = table_info.get("name", "")
            
            # Extract primary keys from table definition
            if "primary_key" in table_info:
                pk = table_info["primary_key"]
                if isinstance(pk, list):
                    primary_keys.extend(pk)
                elif isinstance(pk, str):
                    primary_keys.append(pk)
        else:
            # Try to parse from SQL
            table_name = extract_table_from_sql(sql_info.get("retrieve_sql", ""))
        
        # Extract nested DataWindow relationships
        if ast_data.get("datawindow_type") == "nested" or "nested_datawindow" in ast_data:
            nested_info = ast_data.get("nested_datawindow", {})
            if nested_info:
                relationships.append({
                    "type": "nested",
                    "parent_columns": nested_info.get("parent_columns", []),
                    "child_datawindow": nested_info.get("child_datawindow"),
                    "linkage_columns": nested_info.get("linkage_columns", []),
                })
        
        # Extract any explicit relationships in the AST
        if "relationships" in ast_data:
            for rel in ast_data["relationships"]:
                relationships.append({
                    "type": rel.get("type", "unknown"),
                    "source_table": rel.get("source_table", table_name),
                    "source_column": rel.get("source_column"),
                    "target_table": rel.get("target_table"),
                    "target_column": rel.get("target_column"),
                    "join_type": rel.get("join_type", "inner"),
                })

        return {
            "columns": columns,
            "relationships": relationships,  # Now includes extracted relationships
            "sql": sql_info,
            "table_name": table_name,
            "primary_keys": list(set(primary_keys)),  # Deduplicated primary keys
        }

    # Recursively search for DataWindow nodes
    for value in ast_data.values():
        if isinstance(value, dict):
            result = extract_datawindow_from_ast(value)
            if result:
                return result
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = extract_datawindow_from_ast(item)
                    if result:
                        return result

    return None


def extract_table_from_sql(sql: str) -> str:
    """Extract table name from SQL statement.

    Args:
        sql: SQL statement

    Returns:
        Table name or empty string
    """
    if not sql:
        return ""

    # Simple extraction - look for FROM clause
    sql_upper = sql.upper()
    from_idx = sql_upper.find("FROM")
    if from_idx != -1:
        # Extract text after FROM
        after_from = sql[from_idx + 4 :].strip()
        # Get first word (table name)
        parts = after_from.split()
        if parts:
            return parts[0].strip('"').strip("'").strip("`")

    return ""


def _determine_blob_usage(column_name: str) -> str:
    """Determine the usage type of a blob column based on name.
    
    Args:
        column_name: Name of the column
        
    Returns:
        Usage type: 'image', 'document', 'data'
    """
    name_lower = column_name.lower()
    
    # Check for image-related names
    image_keywords = ['photo', 'picture', 'image', 'icon', 'logo', 'avatar', 
                     'thumbnail', 'screenshot', 'jpg', 'jpeg', 'png', 'gif']
    if any(keyword in name_lower for keyword in image_keywords):
        return 'image'
    
    # Check for document-related names
    doc_keywords = ['document', 'doc', 'pdf', 'file', 'attachment', 'report',
                   'excel', 'word', 'spreadsheet', 'presentation']
    if any(keyword in name_lower for keyword in doc_keywords):
        return 'document'
    
    # Default to generic data
    return 'data'


def _to_pascal_case(name: str) -> str:
    """Convert name to PascalCase."""
    # Remove common prefixes
    if name.startswith("d_"):
        name = name[2:]
    if name.startswith("dw_"):
        name = name[3:]
    
    # Convert to PascalCase
    parts = name.split("_")
    return "".join(p.capitalize() for p in parts)


def _guess_mime_type(usage: str, column_name: str) -> str:
    """Guess MIME type based on usage and column name.
    
    Args:
        usage: Usage type ('image', 'document', 'data')
        column_name: Name of the column
        
    Returns:
        Guessed MIME type
    """
    name_lower = column_name.lower()
    
    if usage == 'image':
        if 'jpg' in name_lower or 'jpeg' in name_lower:
            return 'image/jpeg'
        elif 'png' in name_lower:
            return 'image/png'
        elif 'gif' in name_lower:
            return 'image/gif'
        elif 'bmp' in name_lower:
            return 'image/bmp'
        else:
            return 'image/jpeg'  # Default for images
    elif usage == 'document':
        if 'pdf' in name_lower:
            return 'application/pdf'
        elif 'excel' in name_lower or 'xls' in name_lower:
            return 'application/vnd.ms-excel'
        elif 'word' in name_lower or 'doc' in name_lower:
            return 'application/msword'
        else:
            return 'application/octet-stream'
    else:
        return 'application/octet-stream'


def extract_methods_from_ast(ast_data: dict) -> list[dict]:
    """Extract method information from parsed AST.

    Args:
        ast_data: Parsed AST data from JSON

    Returns:
        List of method dictionaries
    """
    methods = []

    if not isinstance(ast_data, dict):
        return methods

    # Look for function/event nodes
    if ast_data.get("node_type") in ["Function", "Event", "Method"] or ast_data.get(
        "type"
    ) in ["function", "event", "method"]:
        method_info = {
            "name": ast_data.get("name", ""),
            "return_type": ast_data.get("return_type", "void"),
            "visibility": ast_data.get("visibility", "public"),
            "parameters": [],
        }

        # Extract parameters
        if "arguments" in ast_data:
            args = ast_data["arguments"]
            if isinstance(args, dict) and "arguments" in args:
                args = args["arguments"]

            for arg in args if isinstance(args, list) else []:
                param = {
                    "name": arg.get("name", ""),
                    "type": arg.get("type", "any"),
                    "is_reference": arg.get("is_reference", False),
                    "is_readonly": arg.get("is_readonly", False),
                    "default_value": arg.get("default_value"),
                }
                method_info["parameters"].append(param)

        methods.append(method_info)

    # Recursively search for method nodes
    for value in ast_data.values():
        if isinstance(value, dict):
            methods.extend(extract_methods_from_ast(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    methods.extend(extract_methods_from_ast(item))

    return methods


def parse_decompiled_functions(fun_file: Path) -> dict[str, str]:
    """Parse decompiled function file to extract implementations.

    Args:
        fun_file: Path to .fun file

    Returns:
        Dictionary mapping function names to implementations
    """
    functions = {}

    try:
        with open(fun_file) as f:
            content = f.read()

        # Simple parsing - look for function boundaries
        lines = content.split("\n")
        current_function = None
        current_impl = []

        for line in lines:
            # Check for function start
            if line.strip().startswith("function ") or line.strip().startswith(
                "subroutine "
            ):
                # Save previous function
                if current_function:
                    functions[current_function] = "\n".join(current_impl)

                # Start new function
                parts = line.strip().split()
                if len(parts) >= 2:
                    current_function = parts[1].split("(")[0]
                    current_impl = [line]
            elif line.strip().startswith("end function") or line.strip().startswith(
                "end subroutine"
            ):
                # End current function
                if current_function:
                    current_impl.append(line)
                    functions[current_function] = "\n".join(current_impl)
                    current_function = None
                    current_impl = []
            elif current_function:
                # Add to current function
                current_impl.append(line)

        # Save last function if any
        if current_function:
            functions[current_function] = "\n".join(current_impl)

    except Exception as e:
        logger.warning(f"Failed to parse {fun_file}: {e}")

    return functions


def extract_window_from_ast(ast_data: dict) -> dict:
    """Extract window information from parsed AST.

    Args:
        ast_data: Parsed AST data from JSON

    Returns:
        Dictionary with window parameters, controllers, and services
    """
    window_info = {
        "params": {},
        "controllers": [],
        "services": [],
    }

    if not isinstance(ast_data, dict):
        return window_info

    # Look for window node
    if ast_data.get("node_type") == "Window" or ast_data.get("type") == "window":
        # Extract window parameters (instance variables)
        if "variables" in ast_data:
            for var in ast_data["variables"]:
                if var.get("visibility") == "public":
                    window_info["params"][var.get("name", "")] = {
                        "type": var.get("type", "any"),
                        "default": var.get("initial_value"),
                    }

        # Extract events that act as controllers
        if "events" in ast_data:
            for event in ast_data["events"]:
                window_info["controllers"].append(
                    {
                        "name": event.get("name", ""),
                        "type": "event",
                    }
                )

        # Extract referenced services (functions)
        methods = extract_methods_from_ast(ast_data)
        for method in methods:
            if method.get("visibility") == "public":
                window_info["services"].append(method["name"])

    # Recursively search
    for value in ast_data.values():
        if isinstance(value, dict):
            result = extract_window_from_ast(value)
            # Merge results
            window_info["params"].update(result["params"])
            window_info["controllers"].extend(result["controllers"])
            window_info["services"].extend(result["services"])
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = extract_window_from_ast(item)
                    window_info["params"].update(result["params"])
                    window_info["controllers"].extend(result["controllers"])
                    window_info["services"].extend(result["services"])

    # Remove duplicates
    window_info["controllers"] = list(
        {c["name"]: c for c in window_info["controllers"]}.values()
    )
    window_info["services"] = list(set(window_info["services"]))

    return window_info


def extract_widget_from_ast(ast_data: dict) -> dict:
    """Extract widget information from parsed AST.

    Args:
        ast_data: Parsed AST data from JSON

    Returns:
        Dictionary with widget properties, state, and children
    """
    widget_info = {
        "props": {},
        "is_stateful": False,
        "children": [],
    }

    if not isinstance(ast_data, dict):
        return widget_info

    # Look for user object node
    if (
        ast_data.get("node_type") == "UserObject"
        or ast_data.get("type") == "userobject"
    ):
        # Extract properties (public variables)
        if "variables" in ast_data:
            for var in ast_data["variables"]:
                if var.get("visibility") == "public":
                    widget_info["props"][var.get("name", "")] = {
                        "type": var.get("type", "any"),
                        "default": var.get("initial_value"),
                    }

        # Check if stateful (has instance variables or events)
        if "variables" in ast_data or "events" in ast_data:
            widget_info["is_stateful"] = True

        # Extract child controls
        if "controls" in ast_data:
            for control in ast_data["controls"]:
                widget_info["children"].append(
                    {
                        "type": control.get("type", "unknown"),
                        "name": control.get("name", ""),
                        "properties": control.get("properties", {}),
                    }
                )

    # Recursively search
    for value in ast_data.values():
        if isinstance(value, dict):
            result = extract_widget_from_ast(value)
            # Merge results
            widget_info["props"].update(result["props"])
            widget_info["is_stateful"] = (
                widget_info["is_stateful"] or result["is_stateful"]
            )
            widget_info["children"].extend(result["children"])
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = extract_widget_from_ast(item)
                    widget_info["props"].update(result["props"])
                    widget_info["is_stateful"] = (
                        widget_info["is_stateful"] or result["is_stateful"]
                    )
                    widget_info["children"].extend(result["children"])

    return widget_info


class CodeGenerator:
    """Base class for code generation."""

    def __init__(self, template_dir: str, output_dir: str, validate_templates: bool = True) -> None:
        """Initialize code generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
            validate_templates: Whether to validate templates before rendering
        """
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.validate_templates = validate_templates
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Register custom filters
        register_filters(self.env)
        
        # Initialize template validator if validation is enabled
        if self.validate_templates:
            self.validator = TemplateValidator(str(self.template_dir))

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with given context.

        Args:
            template_name: Name of template file
            context: Template context variables

        Returns:
            str: Rendered template

        Raises:
            GenerateError: If template rendering fails
        """
        # Validate context types using template schemas
        try:
            validated_context = validate_template_context(template_name, context)
            context = validated_context  # Use validated context
        except ValueError as e:
            logger.warning(f"Context type validation failed for {template_name}: {e}")
            # Continue with original context if schema validation fails
            # This allows templates without schemas to still work
            
        # Validate template before rendering if enabled
        if self.validate_templates:
            validation_result = self.validator.validate_template(
                template_name,
                sample_context=context,
                validate_output=True
            )
            
            if not validation_result['valid']:
                errors = validation_result.get('errors', [])
                msg = f"Template validation failed for {template_name}: {'; '.join(errors)}"
                raise GenerateError(
                    msg,
                    template=template_name,
                    context=context,
                    details=validation_result
                )
            
            # Log warnings if any
            warnings = validation_result.get('warnings', [])
            if warnings:
                logger.warning(f"Template {template_name} has warnings: {'; '.join(warnings)}")
        
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            msg = f"Failed to render template {template_name}"
            raise GenerateError(
                msg,
                template=template_name,
                context=context,
                details={"error": str(e)},
            )

    def validate_all_templates(self) -> dict[str, list[dict[str, Any]]]:
        """Validate all templates in the template directory.
        
        Returns:
            Dictionary with validation results
            
        Raises:
            GenerateError: If validation is not enabled
        """
        if not self.validate_templates:
            raise GenerateError(
                "Template validation is not enabled",
                details={"validate_templates": self.validate_templates}
            )
            
        return self.validator.validate_all_templates()
    
    def write_file(self, file_path: str, content: str) -> None:
        """Write content to file.

        Args:
            file_path: Path to output file
            content: File content to write

        Raises:
            GenerateError: If file writing fails
        """
        try:
            output_file = self.output_dir / file_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(content)
        except Exception as e:
            msg = f"Failed to write file {file_path}"
            raise GenerateError(
                msg,
                details={"error": str(e)},
            )


class ModelGenerator(CodeGenerator):
    """Generate SQLModel models from PowerBuilder schema."""

    def __init__(self, template_dir: str, output_dir: str) -> None:
        """Initialize model generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
        """
        super().__init__(template_dir, output_dir)

    def generate_model(
        self,
        table_name: str,
        columns: list[dict[str, Any]],
        relationships: list[dict[str, Any]] | None = None,
    ) -> None:
        """Generate a SQLModel model for a table.

        Args:
            table_name: Name of the table
            columns: List of column definitions
            relationships: Optional list of relationship definitions
        """
        context = {
            "table_name": table_name,
            "columns": columns,
            "relationships": relationships or [],
        }
        content = self.render_template("sqlmodel_model.jinja2", context)
        self.write_file(f"models/{table_name.lower()}.py", content)


class ServiceGenerator(CodeGenerator):
    """Generate service layer from PowerBuilder business logic."""

    def __init__(self, template_dir: str, output_dir: str) -> None:
        """Initialize service generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
        """
        super().__init__(template_dir, output_dir)

    def generate_service(self, name: str, methods: list[dict[str, Any]]) -> None:
        """Generate a service class.

        Args:
            name: Service name
            methods: List of method definitions
        """
        context = {
            "service_name": name,
            "methods": methods,
        }
        content = self.render_template("service.jinja2", context)
        self.write_file(f"services/{name.lower()}_service.py", content)


class FlutterGenerator(CodeGenerator):
    """Generate Flutter widgets and screens from PowerBuilder UI."""

    def __init__(self, template_dir: str, output_dir: str) -> None:
        """Initialize Flutter generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
        """
        super().__init__(template_dir, output_dir)

    def generate_widget(
        self,
        name: str,
        props: list[dict[str, Any]],
        is_stateful: bool = False,
        children: list[dict[str, Any]] | None = None,
    ) -> None:
        """Generate a Flutter widget.

        Args:
            name: Widget name
            props: List of widget properties
            is_stateful: Whether the widget should be stateful
            children: Optional list of child widgets
        """
        context = {
            "widget_name": name,
            "properties": props,
            "is_stateful": is_stateful,
            "children": children or [],
        }
        content = self.render_template("widget.dart.jinja2", context)
        self.write_file(f"widgets/{name.lower()}.dart", content)

    def generate_screen(
        self,
        name: str,
        route_name: str,
        params: list[dict[str, Any]] | None = None,
        controllers: list[dict[str, Any]] | None = None,
        services: list[str] | None = None,
    ) -> None:
        """Generate a Flutter screen.

        Args:
            name: Screen name
            route_name: Route name for navigation
            params: Optional list of screen parameters
            controllers: Optional list of controllers (TextEditingController, etc.)
            services: Optional list of service dependencies
        """
        context = {
            "screen_name": name,
            "route_name": route_name,
            "parameters": params or [],
            "controllers": controllers or [],
            "services": services or [],
        }
        content = self.render_template("screen.dart.jinja2", context)
        self.write_file(f"screens/{name.lower()}_screen.dart", content)

    def generate_model(
        self,
        name: str,
        fields: list[dict[str, Any]],
        methods: list[dict[str, Any]] | None = None,
    ) -> None:
        """Generate a Flutter data model.

        Args:
            name: Model name
            fields: List of model fields
            methods: Optional list of model methods
        """
        context = {
            "model_name": name,
            "fields": fields,
            "methods": methods or [],
        }
        content = self.render_template("model.dart.jinja2", context)
        self.write_file(f"models/{name.lower()}.dart", content)

    def generate_datawindow_widget(
        self,
        name: str,
        columns: list[dict[str, Any]],
        data_source: str,
        presentation_style: str = "grid",
        row_type: str = "Map<String, dynamic>",
    ) -> None:
        """Generate a Flutter widget for PowerBuilder DataWindow.

        Args:
            name: Widget name
            columns: List of DataWindow columns
            data_source: Data source for the DataWindow
            presentation_style: DataWindow presentation style (grid, freeform, etc.)
            row_type: Dart type for row data
        """
        context = {
            "datawindow": {
                "name": name,
                "columns": columns,
                "presentation_style": presentation_style,
                "row_type": row_type,
                "imports": []
            },
            "widget_name": name,
            "columns": columns,
            "data_source": data_source,
        }
        content = self.render_template("datawindow_widget.dart.jinja2", context)
        self.write_file(f"widgets/{name.lower()}_datawindow.dart", content)


def generate_models(parsed_dir: str = "output/parsed") -> None:
    """Generate all database models from parsed PowerBuilder files.

    Args:
        parsed_dir: Directory containing parsed AST files (default: output/parsed)
    """
    try:
        import json
        from pathlib import Path

        generator = ModelGenerator("templates", "output/backend")
        parsed_path = Path(parsed_dir)

        # Read parsed summary if available
        summary_file = parsed_path / "parsed_summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
                logger.info(f"Found parsed data from {summary['parsed_at']}")

        # Find all parsed DataWindow files (.srd)
        datawindow_files = list(parsed_path.rglob("*.srd.ast.json"))
        logger.info(f"Found {len(datawindow_files)} DataWindow files")

        # Extract table information from DataWindows
        tables = {}
        for dw_file in datawindow_files:
            try:
                with open(dw_file) as f:
                    ast_data = json.load(f)

                # Extract table schema from AST
                table_name = dw_file.stem.replace(".srd.ast", "")
                if table_name not in tables:
                    # Extract DataWindow information
                    dw_data = extract_datawindow_from_ast(ast_data)
                    if dw_data:
                        tables[table_name] = {
                            "name": table_name,
                            "columns": dw_data.get("columns", []),
                            "relationships": dw_data.get("relationships", []),
                            "sql": dw_data.get("sql", {}),
                        }
            except Exception as e:
                logger.warning(f"Failed to process {dw_file}: {e}")

        # Generate models for each table
        for table in tables.values():
            generator.generate_model(
                table["name"],
                table["columns"],
                table.get("relationships"),
            )

        logger.info(f"Generated {len(tables)} models")

    except Exception as e:
        logger.exception(f"Failed to generate models: {e}")
        raise


def generate_services(
    parsed_dir: str = "output/parsed", decompiled_dir: str = "output/decompiled"
) -> None:
    """Generate all services from parsed PowerBuilder files.

    Args:
        parsed_dir: Directory containing parsed AST files
        decompiled_dir: Directory containing decompiled functions
    """
    try:
        import json
        from pathlib import Path

        generator = ServiceGenerator("templates", "output/backend")
        parsed_path = Path(parsed_dir)
        decompiled_path = Path(decompiled_dir)

        # Find all parsed user object files (.sru) - these often contain business logic
        user_object_files = list(parsed_path.rglob("*.sru.ast.json"))
        logger.info(f"Found {len(user_object_files)} user object files")

        # Extract service information
        services = {}
        for uo_file in user_object_files:
            try:
                with open(uo_file) as f:
                    ast_data = json.load(f)

                # Extract service name from filename
                service_name = uo_file.stem.replace(".sru.ast", "")

                # Skip if it looks like a UI component
                if any(
                    prefix in service_name.lower() for prefix in ["w_", "dw_", "uo_"]
                ):
                    continue

                # Create service definition
                if service_name not in services:
                    # Extract methods from AST
                    methods = extract_methods_from_ast(ast_data)

                    services[service_name] = {
                        "name": service_name,
                        "methods": methods,
                    }

                    # Check for corresponding decompiled functions
                    fun_file = decompiled_path / f"{service_name}.fun"
                    if fun_file.exists():
                        logger.debug(f"Found decompiled functions for {service_name}")
                        # Parse decompiled functions to get implementation details
                        decompiled_methods = parse_decompiled_functions(fun_file)
                        # Merge with AST methods
                        for method in services[service_name]["methods"]:
                            if method["name"] in decompiled_methods:
                                method["implementation"] = decompiled_methods[
                                    method["name"]
                                ]

            except Exception as e:
                logger.warning(f"Failed to process {uo_file}: {e}")

        # Generate services
        for service in services.values():
            generator.generate_service(
                service["name"],
                service["methods"],
            )

        logger.info(f"Generated {len(services)} services")

    except Exception as e:
        logger.exception(f"Failed to generate services: {e}")
        raise


def generate_flutter(parsed_dir: str = "output/parsed") -> None:
    """Generate all Flutter widgets and screens from parsed PowerBuilder files.

    Args:
        parsed_dir: Directory containing parsed AST files
    """
    try:
        import json
        from pathlib import Path

        generator = FlutterGenerator("flutter/templates", "output/flutter")
        parsed_path = Path(parsed_dir)

        # Find all parsed window files (.srw)
        window_files = list(parsed_path.rglob("*.srw.ast.json"))
        logger.info(f"Found {len(window_files)} window files")

        # Generate screens from PowerBuilder windows
        for window_file in window_files:
            try:
                with open(window_file) as f:
                    ast_data = json.load(f)

                window_name = window_file.stem.replace(".srw.ast", "")

                # Extract window information from AST
                window_info = extract_window_from_ast(ast_data)

                # Create screen definition
                generator.generate_screen(
                    name=window_name,
                    route_name=f"/{window_name.lower()}",
                    params=window_info.get("params", {}),
                    controllers=window_info.get("controllers", []),
                    services=window_info.get("services", []),
                )

            except Exception as e:
                logger.warning(f"Failed to process window {window_file}: {e}")

        # Find all parsed user object files (.sru)
        user_object_files = list(parsed_path.rglob("*.sru.ast.json"))

        # Generate widgets from PowerBuilder user objects
        for uo_file in user_object_files:
            try:
                with open(uo_file) as f:
                    ast_data = json.load(f)

                widget_name = uo_file.stem.replace(".sru.ast", "")

                # Skip non-UI objects
                if not any(prefix in widget_name.lower() for prefix in ["uo_", "u_"]):
                    continue

                # Extract widget information from AST
                widget_info = extract_widget_from_ast(ast_data)

                generator.generate_widget(
                    name=widget_name,
                    props=widget_info.get("props", {}),
                    is_stateful=widget_info.get("is_stateful", True),
                    children=widget_info.get("children", []),
                )

            except Exception as e:
                logger.warning(f"Failed to process user object {uo_file}: {e}")

        # Find all parsed DataWindow files (.srd)
        datawindow_files = list(parsed_path.rglob("*.srd.ast.json"))
        logger.info(f"Found {len(datawindow_files)} DataWindow files")

        # Generate DataWindow widgets
        for dw_file in datawindow_files:
            try:
                with open(dw_file) as f:
                    ast_data = json.load(f)

                dw_name = dw_file.stem.replace(".srd.ast", "")

                # Extract DataWindow information (reuse existing function)
                dw_info = extract_datawindow_from_ast(ast_data)

                generator.generate_datawindow_widget(
                    name=dw_name,
                    columns=dw_info.get("columns", []) if dw_info else [],
                    data_source=f"api/{dw_name}",
                )

            except Exception as e:
                logger.warning(f"Failed to process DataWindow {dw_file}: {e}")

        logger.info(
            f"Generated Flutter code for {len(window_files)} screens and {len(datawindow_files)} DataWindows"
        )

    except Exception as e:
        logger.exception(f"Failed to generate Flutter code: {e}")
        raise
