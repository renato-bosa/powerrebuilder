"""Base code generator class.

This module contains the base CodeGenerator class used by all specific generators.
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from generate.jinja_filters import register_filters
from generate.template_schemas import validate_template_context
from generate.template_validator import TemplateValidator
from model.utils.errors import GenerateError

logger = logging.getLogger(__name__)


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
            loader=FileSystemLoader(str(self.template_dir)), trim_blocks=True, lstrip_blocks=True, )
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
            logger.warning("Context type validation failed for %s: %s", template_name, e)
            # Continue with original context if schema validation fails
            # This allows templates without schemas to still work

        # Validate template before rendering if enabled
        if self.validate_templates:
            validation_result = self.validator.validate_template(
                template_name, sample_context=context, validate_output=True,
            )

            if not validation_result["valid"]:
                errors = validation_result.get("errors", [])
                msg = f"Template validation failed for {template_name}: {" ".join(errors)}"
                raise GenerateError(
                    msg,
                    template=template_name,
                    context=context,
                    details=validation_result,
                )

            # Log warnings if any
            warnings = validation_result.get("warnings", [])
            if warnings:
                logger.warning("Template %s has warnings: %s", template_name, "; ".join(warnings))

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
                details={"validate_templates": self.validate_templates},
            )

        return self.validator.validate_all_templates()

    def write_file(self, relative_path: str, content: str) -> None:




        """Write generated content to a file.

        Args:
            relative_path: Path relative to output directory
            content: File content to write
        """
        file_path = self.output_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            f.write(content)

        logger.info("Generated: %s", file_path)
