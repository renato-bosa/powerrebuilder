"""Code generation module for converting PowerBuilder models to modern code.

This module forms the final stage in the PowerBuilder reverse engineering pipeline,
generating modern web application code from the parsed and analyzed PowerBuilder models.
It transforms the internal representation into executable code for both backend and frontend.

Key components:
- CodeGenerator: Base class providing template rendering functionality
- ModelGenerator: Generates SQLAlchemy models from PowerBuilder database schema
- ServiceGenerator: Converts PowerBuilder business logic into service layer classes
- FrontendGenerator: Transforms PowerBuilder UI into React or Astro components

The code generation relies on Jinja2 templates (stored in backend/templates and frontend/templates)
to produce consistent, well-formatted output across different target technologies:
- Backend: FastAPI endpoints, SQLAlchemy models, Pydantic schemas
- Frontend: React/TypeScript or Astro components, hooks, and form validation

Each generator handles a specific aspect of the application and is orchestrated
through the main entry points: generate_models(), generate_services(), and generate_frontend().
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from model.utils.errors import GenerateError

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
    """Generate SQLAlchemy models from PowerBuilder schema."""

    def __init__(self, template_dir: str, output_dir: str) -> None:
        """Initialize model generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
        """
        super().__init__(template_dir, output_dir)

    def generate_model(self, table_name: str, columns: list[dict[str, Any]],
                      relationships: list[dict[str, Any]] | None = None) -> None:
        """Generate a SQLAlchemy model for a table.

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
        content = self.render_template("sqlalchemy_model.jinja2", context)
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


class FrontendGenerator(CodeGenerator):
    """Generate frontend components from PowerBuilder UI."""

    def __init__(self, template_dir: str, output_dir: str, framework: str = "react") -> None:
        """Initialize frontend generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
            framework: Frontend framework to use
        """
        super().__init__(template_dir, output_dir)
        self.framework = framework

    def generate_component(self, name: str, props: list[dict[str, Any]],
                         children: list[dict[str, Any]] | None = None) -> None:
        """Generate a frontend component.

        Args:
            name: Component name
            props: List of component props
            children: Optional list of child components
        """
        context = {
            "component_name": name,
            "props": props,
            "children": children or [],
        }
        template = f"{self.framework}_component.jinja2"
        content = self.render_template(template, context)
        extension = "tsx" if self.framework == "react" else "astro"
        self.write_file(f"components/{name.lower()}.{extension}", content)


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


def generate_frontend() -> None:
    """Generate all frontend components."""
    try:
        generator = FrontendGenerator("templates", "output/frontend")
        # TODO: Get component definitions from parsed PowerBuilder files
        components = []  # Load components from parsed files
        for component in components:
            generator.generate_component(
                component["name"],
                component["props"],
                component.get("children"),
            )
    except Exception as e:
        logger.error(f"Failed to generate frontend: {e}")
        raise
