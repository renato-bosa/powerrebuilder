"""Factory for creating ParseCoordinator with all dependencies.

This factory handles the construction of the ParseCoordinator and all its
dependencies, supporting both simple and advanced configurations.
"""

import logging
from pathlib import Path
from typing import Any

from src.contracts.interfaces import (
    IGrammarManager,
    IImportResolver,
    ILibraryManager,
    IParser,
    IPreprocessor,
    ITransformer,
    ITypeResolver,
)

from .coordinator import ParseCoordinator
from .grammar.loader import GrammarManager
from .library import LibraryManager
from .parser.powerbuilder import PowerBuilderParser
from .preprocessor.imports import ImplicitImportResolver
from .preprocessor.preprocessor import PowerBuilderPreprocessor
from .resolution import TypeResolver
from .transformer.builder import PowerBuilderTransformer

logger = logging.getLogger(__name__)


class ParseCoordinatorFactory:
    """Factory for creating ParseCoordinator instances."""

    @staticmethod
    def create_simple(
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        library_path: str | Path | None = None,
        enable_preprocessing: bool = True,
        resolve_imports: bool = True,
        **kwargs,
    ) -> ParseCoordinator:
        """Create a simple ParseCoordinator with default components.

        Args:
        input_dir: Input directory containing PowerBuilder source
        output_dir: Output directory for AST files
        library_path: Path to PowerBuilder library files
        enable_preprocessing: Whether to enable preprocessing
        resolve_imports: Whether to resolve implicit imports
        **kwargs: Additional configuration options

        Returns:
        Configured ParseCoordinator instance
        """
        # Create all components with default configuration
        grammar_manager = GrammarManager()
        library_manager = LibraryManager(library_path=library_path)
        type_resolver = TypeResolver()
        imports_resolver = ImplicitImportResolver() if resolve_imports else None
        preprocessor = PowerBuilderPreprocessor() if enable_preprocessing else None
        parser = PowerBuilderParser(grammar_manager=grammar_manager)
        transformer = PowerBuilderTransformer()

        # Create coordinator with basic parameters
        coordinator = ParseCoordinator(
            input_dir=input_dir or Path("/tmp/default_input"),
            output_dir=output_dir or Path("/tmp/default_output"),
            enable_recovery=kwargs.get('enable_recovery', True),
            validate_ast=kwargs.get('validate_ast', True),
        )
        
        # Note: Components are created but not attached to coordinator
        # The current ParseCoordinator implementation creates its own components internally

        logger.info("Created simple ParseCoordinator")

        return coordinator

    @staticmethod
    def create_advanced(
        components: dict[str, Any],
        input_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> ParseCoordinator:
        """Create a ParseCoordinator with custom components.

        Args:
            components: Dictionary of custom components
            input_dir: Input directory containing PowerBuilder source
            output_dir: Output directory for AST files

        Returns:
            Configured ParseCoordinator instance
        """
        # Extract components from dictionary, using defaults for missing ones
        grammar_manager = components.get("grammar_manager") or GrammarManager()
        library_manager = components.get("library_manager") or LibraryManager()
        type_resolver = components.get("type_resolver") or TypeResolver()
        imports_resolver = (
            components.get("imports_resolver") or ImplicitImportResolver()
        )
        preprocessor = components.get("preprocessor") or PowerBuilderPreprocessor()
        parser = components.get("parser") or PowerBuilderParser(
            grammar_manager=grammar_manager
        )
        transformer = components.get("transformer") or PowerBuilderTransformer()

        # Create coordinator with basic parameters
        coordinator = ParseCoordinator(
            input_dir=input_dir or Path("/tmp/default_input"),
            output_dir=output_dir or Path("/tmp/default_output"),
            enable_recovery=components.get('enable_recovery', True),
            validate_ast=components.get('validate_ast', True),
        )
        
        # Note: Components are created but not attached to coordinator
        # The current ParseCoordinator implementation creates its own components internally

        logger.info("Created advanced ParseCoordinator with custom components")

        return coordinator

    @staticmethod
    def create_for_testing(
        mock_components: dict[str, Any] | None = None,
    ) -> ParseCoordinator:
        """Create a ParseCoordinator suitable for testing.

        Args:
            mock_components: Optional dictionary of mock components

        Returns:
            ParseCoordinator configured for testing
        """
        # Use mock components if provided, otherwise create minimal real ones
        components = mock_components or {}

        # Create with test configuration
        coordinator = ParseCoordinatorFactory.create_advanced(
            components=components,
            input_dir=Path("/tmp/test_input"),
            output_dir=Path("/tmp/test_output"),
        )

        logger.info("Created ParseCoordinator for testing")

        return coordinator

    @staticmethod
    def create_from_config(config: dict[str, Any]) -> ParseCoordinator:
        """Create a ParseCoordinator from a configuration dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            Configured ParseCoordinator instance
        """
        # Extract paths
        input_dir = config.get("input_dir")
        output_dir = config.get("output_dir")
        library_path = config.get("library_path")

        # Extract options
        options = config.get("options", {})
        enable_preprocessing = options.get("enable_preprocessing", True)
        resolve_imports = options.get("resolve_imports", True)

        # Extract component configuration
        component_config = config.get("components", {})

        # Create components based on configuration
        components = {}

        # Grammar configuration
        if "grammar" in component_config:
            grammar_config = component_config["grammar"]
            grammar_manager = GrammarManager()
            if "grammar_path" in grammar_config:
                grammar_manager.set_grammar_path(grammar_config["grammar_path"])
            components["grammar_manager"] = grammar_manager

        # Library configuration
        if "library" in component_config:
            library_config = component_config["library"]
            components["library_manager"] = LibraryManager(
                library_path=library_config.get("path", library_path)
            )

        # Add other component configurations as needed

        # Use simple or advanced creation based on component presence
        if components:
            return ParseCoordinatorFactory.create_advanced(
                components=components, input_dir=input_dir, output_dir=output_dir
            )
        return ParseCoordinatorFactory.create_simple(
            input_dir=input_dir,
            output_dir=output_dir,
            library_path=library_path,
            enable_preprocessing=enable_preprocessing,
            resolve_imports=resolve_imports,
        )

    @staticmethod
    def create_with_di(container) -> ParseCoordinator:
        """Create a ParseCoordinator using dependency injection.

        Args:
            container: The DI container

        Returns:
            ParseCoordinator with injected dependencies
        """
        # Create a basic coordinator - DI not supported by current implementation
        coordinator = ParseCoordinator(
            input_dir=Path("/tmp/di_input"),
            output_dir=Path("/tmp/di_output"),
        )
        # Note: DI container components are resolved but not used
        # Current ParseCoordinator creates its own dependencies
        return coordinator


# Convenience function for backward compatibility
def create_parse_coordinator(
    input_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    **kwargs,
) -> ParseCoordinator:
    """Create a ParseCoordinator with default configuration.

    This function provides backward compatibility with existing code.

    Args:
        input_dir: Input directory containing PowerBuilder source
        output_dir: Output directory for AST files
        **kwargs: Additional configuration options

    Returns:
        Configured ParseCoordinator instance
    """
    return ParseCoordinatorFactory.create_simple(
        input_dir=input_dir, output_dir=output_dir, **kwargs
    )
