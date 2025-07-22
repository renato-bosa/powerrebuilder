"""Factory for creating DecompileCoordinator with all dependencies.

This factory handles the construction of the DecompileCoordinator and all its
dependencies, supporting both simple and advanced configurations.
"""

import logging
from pathlib import Path
from typing import Any

from src.decompile.analysis.control import ControlFlowAnalyzer
from src.decompile.coordinator import DecompileCoordinator
from src.decompile.core.output import OutputFormatter
from src.decompile.core.validator import OutputValidator
from src.decompile.pcode.decoder import PCodeDecoderV2
from src.decompile.reconstruction.expression import ExpressionReconstructor
from src.decompile.utils.version import VersionDetector
from src.extract.pbd.type_detection import ObjectTypeDetector

logger = logging.getLogger(__name__)


class DecompileCoordinatorFactory:
    """Factory for creating DecompileCoordinator instances."""

    @staticmethod
    def create_simple(
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        validate_output: bool = True,
        format_output: bool = True,
        **kwargs,
    ) -> DecompileCoordinator:
        """Create a simple DecompileCoordinator with default components.

        Args:
            input_dir: Input directory containing P-code files
            output_dir: Output directory for decompiled source
            validate_output: Whether to validate decompiled output
            format_output: Whether to format decompiled output
            **kwargs: Additional configuration options

        Returns:
            Configured DecompileCoordinator instance
        """
        # Create all components with default configuration
        decoder = PCodeDecoderV2()
        type_detector = ObjectTypeDetector()
        version_detector = VersionDetector()
        analyzer = ControlFlowAnalyzer()
        reconstructor = ExpressionReconstructor()
        formatter = OutputFormatter() if format_output else None
        validator = OutputValidator() if validate_output else None

        # Create coordinator
        coordinator = DecompileCoordinator(
            input_dir=input_dir,
            output_dir=output_dir,
            decoder=decoder,
            type_detector=type_detector,
            version_detector=version_detector,
            analyzer=analyzer,
            reconstructor=reconstructor,
            formatter=formatter,
            validator=validator,
        )

        logger.info("Created simple DecompileCoordinator")

        return coordinator

    @staticmethod
    def create_advanced(
        components: dict[str, Any],
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> DecompileCoordinator:
        """Create a DecompileCoordinator with custom components.

        Args:
            components: Dictionary of custom components
            input_dir: Input directory containing P-code files
            output_dir: Output directory for decompiled source

        Returns:
            Configured DecompileCoordinator instance
        """
        # Extract components from dictionary, using defaults for missing ones
        decoder = components.get("decoder") or PCodeDecoderV2()
        type_detector = components.get("type_detector") or ObjectTypeDetector()
        version_detector = components.get("version_detector") or VersionDetector()
        analyzer = components.get("analyzer") or ControlFlowAnalyzer()
        reconstructor = components.get("reconstructor") or ExpressionReconstructor()
        formatter = components.get("formatter") or OutputFormatter()
        validator = components.get("validator") or OutputValidator()

        # Create coordinator
        coordinator = DecompileCoordinator(
            input_dir=input_dir,
            output_dir=output_dir,
            decoder=decoder,
            type_detector=type_detector,
            version_detector=version_detector,
            analyzer=analyzer,
            reconstructor=reconstructor,
            formatter=formatter,
            validator=validator,
        )

        logger.info("Created advanced DecompileCoordinator with custom components")

        return coordinator

    @staticmethod
    def create_for_testing(
        mock_components: dict[str, Any] | None = None,
    ) -> DecompileCoordinator:
        """Create a DecompileCoordinator suitable for testing.

        Args:
            mock_components: Optional dictionary of mock components

        Returns:
            DecompileCoordinator configured for testing
        """
        # Use mock components if provided, otherwise create minimal real ones
        components = mock_components or {}

        # Create with test configuration
        coordinator = DecompileCoordinatorFactory.create_advanced(
            components=components,
            input_dir=Path("/tmp/test_input"),
            output_dir=Path("/tmp/test_output"),
        )

        logger.info("Created DecompileCoordinator for testing")

        return coordinator

    @staticmethod
    def create_from_config(config: dict[str, Any]) -> DecompileCoordinator:
        """Create a DecompileCoordinator from a configuration dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            Configured DecompileCoordinator instance
        """
        # Extract paths
        input_dir = config.get("input_dir")
        output_dir = config.get("output_dir")

        # Extract options
        options = config.get("options", {})
        validate_output = options.get("validate_output", True)
        format_output = options.get("format_output", True)

        # Extract component configuration
        component_config = config.get("components", {})

        # Create components based on configuration
        components = {}

        # Decoder configuration
        if "decoder" in component_config:
            # Configure decoder based on settings
            components["decoder"] = PCodeDecoderV2()

        # Add other component configurations as needed

        # Use simple or advanced creation based on component presence
        if components:
            return DecompileCoordinatorFactory.create_advanced(
                components=components, input_dir=input_dir, output_dir=output_dir
            )
        return DecompileCoordinatorFactory.create_simple(
            input_dir=input_dir,
            output_dir=output_dir,
            validate_output=validate_output,
            format_output=format_output,
        )

    @staticmethod
    def create_with_di(container) -> DecompileCoordinator:
        """Create a DecompileCoordinator using dependency injection.

        Args:
            container: The DI container

        Returns:
            DecompileCoordinator with injected dependencies
        """
        return DecompileCoordinator(
            decoder=container.resolve(IPCodeDecoder),
            type_detector=container.resolve(IObjectTypeDetector),
            version_detector=container.resolve(IVersionDetector),
            analyzer=container.resolve(IControlFlowAnalyzer),
            reconstructor=container.resolve(IExpressionReconstructor),
            formatter=container.resolve(IOutputFormatter),
            validator=container.resolve(IOutputValidator),
        )


# Convenience function for backward compatibility
def create_decompile_coordinator(
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    **kwargs,
) -> DecompileCoordinator:
    """Create a DecompileCoordinator with default configuration.

    This function provides backward compatibility with existing code.

    Args:
        input_dir: Input directory containing P-code files
        output_dir: Output directory for decompiled source
        **kwargs: Additional configuration options

    Returns:
        Configured DecompileCoordinator instance
    """
    return DecompileCoordinatorFactory.create_simple(
        input_dir=input_dir, output_dir=output_dir, **kwargs
    )
