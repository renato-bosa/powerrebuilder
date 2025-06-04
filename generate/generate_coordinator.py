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

from .jinja_filters import register_filters

logger = logging.getLogger(__name__)


class CodeGenerator:
    """Base class for code generation."""

    def __init__(self, template_dir: str, output_dir: str) -> None:
        """Initialize code generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
        """
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Register custom filters
        register_filters(self.env)

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
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            raise GenerateError(
                f"Failed to render template {template_name}",
                template=template_name,
                context=context,
                details={"error": str(e)},
            )

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
            raise GenerateError(
                f"Failed to write file {file_path}",
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
    ) -> None:
        """Generate a Flutter widget for PowerBuilder DataWindow.

        Args:
            name: Widget name
            columns: List of DataWindow columns
            data_source: Data source for the DataWindow
        """
        context = {
            "widget_name": name,
            "columns": columns,
            "data_source": data_source,
        }
        content = self.render_template("datawindow_widget.dart.jinja2", context)
        self.write_file(f"widgets/{name.lower()}_datawindow.dart", content)


def generate_models() -> None:
    """Generate all database models."""
    try:
        generator = ModelGenerator("templates", "output/backend")
        # TODO: Get schema from parsed PowerBuilder files
        tables = []  # Load tables from schema
        for table in tables:
            generator.generate_model(
                table["name"],
                table["columns"],
                table.get("relationships"),
            )
    except Exception as e:
        logger.error(f"Failed to generate models: {e}")
        raise


def generate_services() -> None:
    """Generate all services."""
    try:
        generator = ServiceGenerator("templates", "output/backend")
        # TODO: Get service definitions from parsed PowerBuilder files
        services = []  # Load services from parsed files
        for service in services:
            generator.generate_service(
                service["name"],
                service["methods"],
            )
    except Exception as e:
        logger.error(f"Failed to generate services: {e}")
        raise


def generate_flutter() -> None:
    """Generate all Flutter widgets and screens."""
    try:
        generator = FlutterGenerator("flutter/templates", "output/flutter")
        # TODO: Get UI definitions from parsed PowerBuilder files
        
        # Generate screens from PowerBuilder windows
        screens = []  # Load screens from parsed files
        for screen in screens:
            generator.generate_screen(
                screen["name"],
                screen["route_name"],
                screen.get("params"),
                screen.get("controllers"),
                screen.get("services"),
            )
        
        # Generate widgets from PowerBuilder user objects
        widgets = []  # Load widgets from parsed files
        for widget in widgets:
            generator.generate_widget(
                widget["name"],
                widget["props"],
                widget.get("is_stateful", False),
                widget.get("children"),
            )
        
        # Generate DataWindow widgets
        datawindows = []  # Load DataWindows from parsed files
        for dw in datawindows:
            generator.generate_datawindow_widget(
                dw["name"],
                dw["columns"],
                dw["data_source"],
            )
        
        # Generate models
        models = []  # Load models from parsed files
        for model in models:
            generator.generate_model(
                model["name"],
                model["fields"],
                model.get("methods"),
            )
            
    except Exception as e:
        logger.error(f"Failed to generate Flutter code: {e}")
        raise
