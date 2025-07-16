"""Interfaces for generation services."""
from typing import Protocol, Optional, Any, Dict, List
from pathlib import Path
from abc import abstractmethod


class IASTExtractor(Protocol):
    """Interface for AST extraction."""
    
    def extract_datawindow_from_ast(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract DataWindow from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            DataWindow structure
        """
        ...
    
    def extract_methods_from_ast(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract methods from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            List of methods
        """
        ...
    
    def extract_window_from_ast(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract window from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            Window structure
        """
        ...


class IGeneratorFactory(Protocol):
    """Interface for generator factory."""
    
    def create_model_generator(self, config: Dict[str, Any]) -> Any:
        """Create model generator.
        
        Args:
            config: Generator configuration
            
        Returns:
            Model generator instance
        """
        ...
    
    def create_service_generator(self, config: Dict[str, Any]) -> Any:
        """Create service generator.
        
        Args:
            config: Generator configuration
            
        Returns:
            Service generator instance
        """
        ...
    
    def create_ui_generator(self, framework: str, config: Dict[str, Any]) -> Any:
        """Create UI generator.
        
        Args:
            framework: Target UI framework
            config: Generator configuration
            
        Returns:
            UI generator instance
        """
        ...


class ITypeConverter(Protocol):
    """Interface for type conversion."""
    
    def convert_type(self, pb_type: str, target_language: str) -> str:
        """Convert PowerBuilder type to target language.
        
        Args:
            pb_type: PowerBuilder type
            target_language: Target language
            
        Returns:
            Converted type
        """
        ...
    
    def get_initial_value(self, pb_type: str, target_language: str) -> str:
        """Get initial value for type.
        
        Args:
            pb_type: PowerBuilder type
            target_language: Target language
            
        Returns:
            Initial value string
        """
        ...


class IUIProcessor(Protocol):
    """Interface for UI processing."""
    
    def process_controls(self, controls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process UI controls.
        
        Args:
            controls: List of controls
            
        Returns:
            Processed controls
        """
        ...
    
    def generate_layout(self, controls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate layout from controls.
        
        Args:
            controls: List of controls
            
        Returns:
            Layout structure
        """
        ...
    
    def extract_menus(self, window: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract menus from window.
        
        Args:
            window: Window structure
            
        Returns:
            List of menus
        """
        ...


class IEventProcessor(Protocol):
    """Interface for event processing."""
    
    def process_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process event definitions.
        
        Args:
            events: List of event definitions
            
        Returns:
            Processed events with handlers and metadata
        """
        ...
    
    def extract_event_handlers(self, ast: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract event handlers from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            Dictionary mapping control names to their event handlers
        """
        ...
    
    def wire_events(self, controls: List[Dict[str, Any]], event_handlers: Dict[str, List[str]]) -> Dict[str, Any]:
        """Wire events to controls.
        
        Args:
            controls: List of controls
            event_handlers: Event handlers by control name
            
        Returns:
            Event wiring configuration
        """
        ...


class IProjectScaffolder(Protocol):
    """Interface for project scaffolding."""
    
    def create_project_structure(self, project_name: str, framework: str, output_dir: Path) -> Dict[str, Any]:
        """Create project directory structure.
        
        Args:
            project_name: Name of the project
            framework: Target framework
            output_dir: Output directory path
            
        Returns:
            Dictionary with created paths and metadata
        """
        ...
    
    def generate_config_files(self, project_root: Path, config: Dict[str, Any]) -> List[str]:
        """Generate configuration files.
        
        Args:
            project_root: Project root directory
            config: Configuration options
            
        Returns:
            List of generated file paths
        """
        ...
    
    def create_boilerplate_files(self, project_root: Path, modules: List[str]) -> Dict[str, str]:
        """Create boilerplate code files.
        
        Args:
            project_root: Project root directory
            modules: List of module names
            
        Returns:
            Dictionary mapping file paths to their content
        """
        ...


class ITemplateEngine(Protocol):
    """Interface for template engine."""
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render template with context.
        
        Args:
            template_name: Template name
            context: Template context
            
        Returns:
            Rendered content
        """
        ...
    
    def register_filter(self, name: str, filter_func: callable) -> None:
        """Register template filter.
        
        Args:
            name: Filter name
            filter_func: Filter function
        """
        ...


# Keep existing interfaces for compatibility
class IGenerator(Protocol):
    """Interface for all generators."""

    @abstractmethod
    def generate(self, ast: Any, output_dir: Path) -> Dict[str, Any]:
        """Generate output from AST."""
        ...

    @abstractmethod
    def supports(self, target: str) -> bool:
        """Check if this generator supports the given target."""
        ...

    @abstractmethod
    def get_target_name(self) -> str:
        """Get the target name for this generator."""
        ...


class IGeneratorCoordinator(Protocol):
    """Interface for generate coordinator."""

    @abstractmethod
    def generate(self, input_dir: Path, output_dir: Path, target: str = "flutter") -> Dict[str, Any]:
        """Coordinate generation process."""
        ...

    @abstractmethod
    def register_generator(self, generator: IGenerator) -> None:
        """Register a new generator."""
        ...

    @abstractmethod
    def get_generators(self) -> List[IGenerator]:
        """Get all registered generators."""
        ...

    @abstractmethod
    def get_generator(self, target: str) -> Optional[IGenerator]:
        """Get a specific generator by target."""
        ...