"""Factory for creating GenerateCoordinator with all dependencies.

This factory handles the construction of the GenerateCoordinator and all its
dependencies, supporting both simple and advanced configurations.
"""

import logging
from pathlib import Path
from typing import Any

from src.contracts.generators import (
    ITemplateEngine,
    ITypeConverter,
)

from .converters.data.db_formatter import DatabaseOperationFormatter
from .converters.flutter.design_system import DesignSystemConverter
from .converters.utils.types import TypeConverter
from .coordinator import GenerateCoordinator
from .templates.engine import TemplateEngine, TemplateValidator

logger = logging.getLogger(__name__)


class GenerateCoordinatorFactory:
    """Factory for creating GenerateCoordinator instances."""

    @staticmethod
    def create_simple(
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        framework: str = "flutter",
        validate_templates: bool = True,
        enable_formatting: bool = True,
        **kwargs,
    ) -> GenerateCoordinator:
        """Create a simple GenerateCoordinator with default components.

        Args:
            input_dir: Input directory containing model files
            output_dir: Output directory for generated code
            framework: Target framework (flutter, python, etc.)
            validate_templates: Whether to validate templates
            enable_formatting: Whether to format generated code
            **kwargs: Additional configuration options

        Returns:
            Configured GenerateCoordinator instance
        """
        # Create all components with default configuration
        template_engine = TemplateEngine()
        type_converter = TypeConverter(target_language=framework)
        database_formatter = DatabaseOperationFormatter()
        design_system = DesignSystemConverter()
        template_validator = TemplateValidator() if validate_templates else None

        # Create coordinator - note that current implementation
        # doesn't support dependency injection yet
        coordinator = GenerateCoordinator(
            input_dir=input_dir, output_dir=output_dir, framework=framework
        )

        # Store components for future use when DI is implemented
        coordinator._template_engine = template_engine
        coordinator._type_converter = type_converter
        coordinator._database_formatter = database_formatter
        coordinator._design_system = design_system
        coordinator._template_validator = template_validator

        logger.info("Created simple GenerateCoordinator for %s", framework)

        return coordinator

    @staticmethod
    def create_advanced(
        components: dict[str, Any],
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        framework: str = "flutter",
    ) -> GenerateCoordinator:
        """Create a GenerateCoordinator with custom components.

        Args:
            components: Dictionary of custom components
            input_dir: Input directory containing model files
            output_dir: Output directory for generated code
            framework: Target framework

        Returns:
            Configured GenerateCoordinator instance
        """
        # Extract components from dictionary, using defaults for missing ones
        template_engine = components.get("template_engine") or TemplateEngine()
        type_converter = components.get("type_converter") or TypeConverter(
            target_language=framework
        )
        database_formatter = (
            components.get("database_formatter") or DatabaseOperationFormatter()
        )
        design_system = components.get("design_system") or DesignSystemConverter()
        template_validator = components.get("template_validator") or TemplateValidator()

        # Create coordinator
        coordinator = GenerateCoordinator(
            input_dir=input_dir, output_dir=output_dir, framework=framework
        )

        # Store components for future use
        coordinator._template_engine = template_engine
        coordinator._type_converter = type_converter
        coordinator._database_formatter = database_formatter
        coordinator._design_system = design_system
        coordinator._template_validator = template_validator

        logger.info(
            "Created advanced GenerateCoordinator with custom components for %s",
            framework,
        )

        return coordinator

    @staticmethod
    def create_for_testing(
        mock_components: dict[str, Any] | None = None, framework: str = "flutter"
    ) -> GenerateCoordinator:
        """Create a GenerateCoordinator suitable for testing.

        Args:
            mock_components: Optional dictionary of mock components
            framework: Target framework

        Returns:
            GenerateCoordinator configured for testing
        """
        # Use mock components if provided, otherwise create minimal real ones
        components = mock_components or {}

        # Create with test configuration
        coordinator = GenerateCoordinatorFactory.create_advanced(
            components=components,
            input_dir=Path("/tmp/test_input"),
            output_dir=Path("/tmp/test_output"),
            framework=framework,
        )

        logger.info("Created GenerateCoordinator for testing")

        return coordinator

    @staticmethod
    def create_from_config(config: dict[str, Any]) -> GenerateCoordinator:
        """Create a GenerateCoordinator from a configuration dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            Configured GenerateCoordinator instance
        """
        # Extract paths
        input_dir = config.get("input_dir")
        output_dir = config.get("output_dir")
        framework = config.get("framework", "flutter")

        # Extract options
        options = config.get("options", {})
        validate_templates = options.get("validate_templates", True)
        enable_formatting = options.get("enable_formatting", True)

        # Extract component configuration
        component_config = config.get("components", {})

        # Create components based on configuration
        components = {}

        # Template engine configuration
        if "template_engine" in component_config:
            engine_config = component_config["template_engine"]
            template_engine = TemplateEngine()
            if "template_path" in engine_config:
                template_engine.set_template_path(engine_config["template_path"])
            components["template_engine"] = template_engine

        # Type converter configuration
        if "type_converter" in component_config:
            converter_config = component_config["type_converter"]
            components["type_converter"] = TypeConverter(
                target_language=converter_config.get("target_language", framework)
            )

        # Add other component configurations as needed

        # Use simple or advanced creation based on component presence
        if components:
            return GenerateCoordinatorFactory.create_advanced(
                components=components,
                input_dir=input_dir,
                output_dir=output_dir,
                framework=framework,
            )
        return GenerateCoordinatorFactory.create_simple(
            input_dir=input_dir,
            output_dir=output_dir,
            framework=framework,
            validate_templates=validate_templates,
            enable_formatting=enable_formatting,
        )

    @staticmethod
    def create_with_di(container) -> callable:
        """Create a GenerateCoordinator factory using dependency injection.

        Note: Current GenerateCoordinator doesn't support full DI,
        so we return a factory function.

        Args:
            container: The DI container

        Returns:
            Factory function that creates GenerateCoordinator
        """
        # Get components from container
        template_engine = container.resolve(ITemplateEngine)
        type_converter = container.resolve(ITypeConverter)
        # database_formatter = container.resolve(IDatabaseFormatter)
        # design_system = container.resolve(IDesignSystemConverter)
        # template_validator = container.resolve(ITemplateValidator)

        # Use concrete classes for now
        database_formatter = DatabaseOperationFormatter()
        design_system = DesignSystemConverter()
        template_validator = None  # TemplateValidator()

        # Return factory function
        def factory(input_dir: str, output_dir: str, framework: str = "flutter"):
            coordinator = GenerateCoordinator(
                input_dir=input_dir, output_dir=output_dir, framework=framework
            )

            # Inject components
            coordinator._template_engine = template_engine
            coordinator._type_converter = type_converter
            coordinator._database_formatter = database_formatter
            coordinator._design_system = design_system
            coordinator._template_validator = template_validator

            return coordinator

        return factory


# Convenience function for backward compatibility


def create_generate_coordinator(
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    framework: str = "flutter",
    **kwargs,
) -> GenerateCoordinator:
    """Create a GenerateCoordinator with default configuration.

    This function provides backward compatibility with existing code.

    Args:
        input_dir: Input directory containing model files
        output_dir: Output directory for generated code
        framework: Target framework
        **kwargs: Additional configuration options

    Returns:
        Configured GenerateCoordinator instance
    """
    return GenerateCoordinatorFactory.create_simple(
        input_dir=input_dir, output_dir=output_dir, framework=framework, **kwargs
    )
