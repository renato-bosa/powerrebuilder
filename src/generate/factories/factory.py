"""Generator factory service for creating code generators."""

from pathlib import Path
from typing import Any

from src.base import CodeGenerator
from src.interfaces import IGeneratorFactory
from src.models import ModelGenerator
from src.python_ui import PythonUIGenerator
from src.service import ServiceGenerator
import logging

logger = logging.getLogger(__name__)



class GeneratorFactory(IGeneratorFactory):
    """Factory for creating code generators."""

    def __init__(self, template_dir: Path | None = None) -> None:
        """Initialize the generator factory.

        Args:
            template_dir: Base directory for templates
        """
        self.template_dir = template_dir or Path(__file__).parent.parent / "templates"
        self._generator_cache: dict[str, Any] = {}

    def create_model_generator(self, config: dict[str, Any]) -> ModelGenerator:
        """Create model generator.

        Args:
            config: Generator configuration

        Returns:
        Model generator instance
        """
        cache_key = "model_generator"

        if cache_key in self._generator_cache:
            return self._generator_cache[cache_key]

        # Extract configuration
        output_dir = config.get("output_dir", ".")
        validate_templates = config.get("validate_templates", True)

        generator = ModelGenerator(
            template_dir=str(self.template_dir),
            output_dir=str(output_dir),
            validate_templates=validate_templates,
        )

        self._generator_cache[cache_key] = generator
        logger.debug("Created model generator with output dir: %s", output_dir)

        return generator

    def create_service_generator(self, config: dict[str, Any]) -> ServiceGenerator:
        """Create service generator.

        Args:
            config: Generator configuration

        Returns:
            Service generator instance
        """
        cache_key = "service_generator"

        if cache_key in self._generator_cache:
            return self._generator_cache[cache_key]

        # Extract configuration
        output_dir = config.get("output_dir", ".")
        validate_templates = config.get("validate_templates", True)

        generator = ServiceGenerator(
            template_dir=str(self.template_dir),
            output_dir=str(output_dir),
            validate_templates=validate_templates,
        )

        self._generator_cache[cache_key] = generator
        logger.debug("Created service generator with output dir: %s", output_dir)

        return generator

    def create_ui_generator(self, framework: str, config: dict[str, Any]) -> Any:
        """Create UI generator.

        Args:
            framework: Target UI framework
            config: Generator configuration

        Returns:
            UI generator instance
        """
        cache_key = f"ui_generator_{framework}"

        if cache_key in self._generator_cache:
            return self._generator_cache[cache_key]

        # Extract configuration
        output_dir = config.get("output_dir", ".")
        validate_templates = config.get("validate_templates", True)

        if framework.lower() == "python":
            generator = PythonUIGenerator(
                template_dir=str(self.template_dir),
                output_dir=str(output_dir),
                validate_templates=validate_templates,
            )
        elif framework.lower() == "flutter":
            # Import Flutter generator when available
            from src.generate.flutter import FlutterGenerator

            generator = FlutterGenerator(
                template_dir=str(self.template_dir),
                output_dir=str(output_dir),
                validate_templates=validate_templates,
            )
        else:
            raise ValueError(f"Unsupported UI framework: {framework}")

        self._generator_cache[cache_key] = generator
        logger.debug(
            "Created %s UI generator with output dir: %s", framework, output_dir
        )

        return generator

    def create_generic_generator(
        self, generator_type: str, config: dict[str, Any]
    ) -> CodeGenerator:
        """Create a generic code generator.

        Args:
            generator_type: Type of generator
            config: Generator configuration

        Returns:
            Code generator instance
        """
        cache_key = f"generic_{generator_type}"

        if cache_key in self._generator_cache:
            return self._generator_cache[cache_key]

        # Extract configuration
        output_dir = config.get("output_dir", ".")
        validate_templates = config.get("validate_templates", True)

        # Create base generator
        generator = CodeGenerator(
            template_dir=str(self.template_dir),
            output_dir=str(output_dir),
            validate_templates=validate_templates,
        )

        self._generator_cache[cache_key] = generator
        logger.debug("Created generic %s generator", generator_type)

        return generator

    def clear_cache(self) -> None:
        """Clear the generator cache."""
        self._generator_cache.clear()
        logger.debug("Cleared generator cache")

    def get_available_generators(self) -> dict[str, str]:
        """Get available generator types.

        Returns:
            Dictionary mapping generator names to descriptions
        """
        return {
            "model": "SQLModel/Pydantic model generator",
            "service": "Python service/API generator",
            "python_ui": "Python UI generator (Tkinter/PyQt)",
            "flutter": "Flutter/Dart UI generator",
        }

    def configure_generator(self, generator: Any, config: dict[str, Any]) -> None:
        """Apply additional configuration to a generator.

        Args:
            generator: Generator instance
            config: Configuration to apply
        """
        # Apply common configuration
        if hasattr(generator, "set_output_dir") and "output_dir" in config:
            generator.set_output_dir(config["output_dir"])

        if (
            hasattr(generator, "set_validate_templates")
            and "validate_templates" in config
        ):
            generator.set_validate_templates(config["validate_templates"])

        # Apply template overrides
        if hasattr(generator, "add_template_path") and "additional_templates" in config:
            for template_path in config["additional_templates"]:
                generator.add_template_path(template_path)

        # Apply filters
        if hasattr(generator, "register_filter") and "custom_filters" in config:
            for name, filter_func in config["custom_filters"].items():
                generator.register_filter(name, filter_func)

        logger.debug("Configured generator with custom settings")
