"""Service generator for PowerBuilder business logic.

Converts PowerBuilder service classes and methods into modern Python services
using SQLModel and FastAPI.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from parse.pseudocode_parser import PowerBuilderPseudocodeParser


class ServiceGenerator:
    """Generate Python services from PowerBuilder business logic."""

    def __init__(self, template_dir: str, output_dir: str) -> None:
        """Initialize service generator.

        Args:
            template_dir: Directory containing templates
            output_dir: Directory for generated code
        """
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.parser = PowerBuilderPseudocodeParser()

        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def translate_method_body(self, body: str) -> list[str]:
        """Translate PowerBuilder method body to Python.

        Args:
            body: PowerBuilder pseudocode

        Returns:
            List of Python code lines

        Raises:
            ValueError: If translation fails
        """
        try:
            return self.parser.parse_and_transform(body)
        except Exception as e:
            raise ValueError(f"Failed to translate method body: {e}") from e

    def generate_service(self, service_class: dict[str, Any]) -> None:
        """Generate a service class.

        Args:
            service_class: Service class metadata

        Raises:
            ValueError: If generation fails
        """
        try:
            # Translate method bodies
            for method in service_class['methods']:
                if 'body' in method:
                    method['python_body'] = self.translate_method_body(method['body'])

            # Render template
            template = self.env.get_template('service.py.jinja2')
            rendered = template.render(
                classname=service_class['name'],
                methods=service_class['methods'],
            )

            # Write output file
            output_file = self.output_dir / f"{service_class['name']}Service.py"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(rendered)

        except Exception as e:
            raise ValueError(
                f"Failed to generate service {service_class['name']}: {e}",
            ) from e

    def generate_services(self, service_classes: list[dict[str, Any]]) -> None:
        """Generate all service classes.

        Args:
            service_classes: List of service class metadata

        Raises:
            ValueError: If generation fails
        """
        for service_class in service_classes:
            self.generate_service(service_class)
