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


def generate_models(parsed_dir: str = "output/parsed") -> None:
    """Generate all database models from parsed PowerBuilder files.
    
    Args:
        parsed_dir: Directory containing parsed AST files (default: output/parsed)
    """
    try:
        from pathlib import Path
        import json
        
        generator = ModelGenerator("templates", "output/backend")
        parsed_path = Path(parsed_dir)
        
        # Read parsed summary if available
        summary_file = parsed_path / "parsed_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                summary = json.load(f)
                logger.info(f"Found parsed data from {summary['parsed_at']}")
        
        # Find all parsed DataWindow files (.srd)
        datawindow_files = list(parsed_path.rglob("*.srd.ast.json"))
        logger.info(f"Found {len(datawindow_files)} DataWindow files")
        
        # Extract table information from DataWindows
        tables = {}
        for dw_file in datawindow_files:
            try:
                with open(dw_file, 'r') as f:
                    ast_data = json.load(f)
                
                # TODO: Extract table schema from AST
                # For now, create a placeholder
                table_name = dw_file.stem.replace('.srd.ast', '')
                if table_name not in tables:
                    tables[table_name] = {
                        "name": table_name,
                        "columns": [],  # TODO: Extract from AST
                        "relationships": [],
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
        logger.error(f"Failed to generate models: {e}")
        raise


def generate_services(parsed_dir: str = "output/parsed", decompiled_dir: str = "output/decompiled") -> None:
    """Generate all services from parsed PowerBuilder files.
    
    Args:
        parsed_dir: Directory containing parsed AST files
        decompiled_dir: Directory containing decompiled functions
    """
    try:
        from pathlib import Path
        import json
        
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
                with open(uo_file, 'r') as f:
                    ast_data = json.load(f)
                
                # Extract service name from filename
                service_name = uo_file.stem.replace('.sru.ast', '')
                
                # Skip if it looks like a UI component
                if any(prefix in service_name.lower() for prefix in ['w_', 'dw_', 'uo_']):
                    continue
                
                # Create service definition
                if service_name not in services:
                    services[service_name] = {
                        "name": service_name,
                        "methods": [],  # TODO: Extract methods from AST
                    }
                    
                    # Check for corresponding decompiled functions
                    fun_file = decompiled_path / f"{service_name}.fun"
                    if fun_file.exists():
                        logger.debug(f"Found decompiled functions for {service_name}")
                        # TODO: Extract method signatures from decompiled code
                        
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
        logger.error(f"Failed to generate services: {e}")
        raise


def generate_flutter(parsed_dir: str = "output/parsed") -> None:
    """Generate all Flutter widgets and screens from parsed PowerBuilder files.
    
    Args:
        parsed_dir: Directory containing parsed AST files
    """
    try:
        from pathlib import Path
        import json
        
        generator = FlutterGenerator("flutter/templates", "output/flutter")
        parsed_path = Path(parsed_dir)
        
        # Find all parsed window files (.srw)
        window_files = list(parsed_path.rglob("*.srw.ast.json"))
        logger.info(f"Found {len(window_files)} window files")
        
        # Generate screens from PowerBuilder windows
        for window_file in window_files:
            try:
                with open(window_file, 'r') as f:
                    ast_data = json.load(f)
                
                window_name = window_file.stem.replace('.srw.ast', '')
                
                # Create screen definition
                generator.generate_screen(
                    name=window_name,
                    route_name=f"/{window_name.lower()}",
                    params=None,  # TODO: Extract params from AST
                    controllers=None,  # TODO: Extract controllers
                    services=None,  # TODO: Extract services
                )
                
            except Exception as e:
                logger.warning(f"Failed to process window {window_file}: {e}")
        
        # Find all parsed user object files (.sru)
        user_object_files = list(parsed_path.rglob("*.sru.ast.json"))
        
        # Generate widgets from PowerBuilder user objects
        for uo_file in user_object_files:
            try:
                with open(uo_file, 'r') as f:
                    ast_data = json.load(f)
                
                widget_name = uo_file.stem.replace('.sru.ast', '')
                
                # Skip non-UI objects
                if not any(prefix in widget_name.lower() for prefix in ['uo_', 'u_']):
                    continue
                
                generator.generate_widget(
                    name=widget_name,
                    props={},  # TODO: Extract props from AST
                    is_stateful=True,
                    children=None,
                )
                
            except Exception as e:
                logger.warning(f"Failed to process user object {uo_file}: {e}")
        
        # Find all parsed DataWindow files (.srd)
        datawindow_files = list(parsed_path.rglob("*.srd.ast.json"))
        logger.info(f"Found {len(datawindow_files)} DataWindow files")
        
        # Generate DataWindow widgets
        for dw_file in datawindow_files:
            try:
                with open(dw_file, 'r') as f:
                    ast_data = json.load(f)
                
                dw_name = dw_file.stem.replace('.srd.ast', '')
                
                generator.generate_datawindow_widget(
                    name=dw_name,
                    columns=[],  # TODO: Extract columns from AST
                    data_source=f"api/{dw_name}",
                )
                
            except Exception as e:
                logger.warning(f"Failed to process DataWindow {dw_file}: {e}")
        
        logger.info(f"Generated Flutter code for {len(window_files)} screens and {len(datawindow_files)} DataWindows")
            
    except Exception as e:
        logger.error(f"Failed to generate Flutter code: {e}")
        raise
