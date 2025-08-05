"""Simple template engine wrapper for Jinja2."""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Simple wrapper around Jinja2 for template rendering."""

    def __init__(self, template_dir: Path | None = None) -> None:
        """Initialize the template engine.

        Args:
            template_dir: Directory containing templates
        """
        if template_dir is None:
            # Default to the templates directory
            template_dir = Path(__file__).parent

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file
            context: Context dictionary for rendering

        Returns:
            Rendered template string
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error("Failed to render template %s: %s", template_name, e)
            raise

    def render_string(self, template_string: str, context: dict[str, Any]) -> str:
        """Render a template string with the given context.

        Args:
            template_string: Template string
            context: Context dictionary for rendering

        Returns:
            Rendered template string
        """
        try:
            template = Template(template_string)
            return template.render(**context)
        except Exception as e:
            logger.error("Failed to render template string: %s", e)
            raise

    def add_filter(self, name: str, func: Any) -> None:
        """Add a custom filter to the template engine.

        Args:
            name: Filter name
            func: Filter function
        """
        self.env.filters[name] = func

    def add_global(self, name: str, value: Any) -> None:
        """Add a global variable to the template engine.

        Args:
            name: Variable name
            value: Variable value
        """
        self.env.globals[name] = value


class TemplateValidator:
    """Validator for template files and rendering."""
    
    def __init__(self, template_dir: Path | None = None) -> None:
        """Initialize the template validator.
        
        Args:
            template_dir: Directory containing templates
        """
        self.template_dir = template_dir or Path(__file__).parent
        
    def validate_template(self, template_name: str) -> bool:
        """Validate that a template exists and is readable.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            True if template is valid
        """
        template_path = self.template_dir / template_name
        return template_path.exists() and template_path.is_file()
        
    def validate_context(self, context: dict[str, Any], required_keys: list[str] | None = None) -> bool:
        """Validate that the context has required keys.
        
        Args:
            context: Context dictionary
            required_keys: List of required keys
            
        Returns:
            True if context is valid
        """
        if not required_keys:
            return True
            
        return all(key in context for key in required_keys)
