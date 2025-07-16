"""Interfaces for model services."""
from typing import Protocol, Optional, Any, Dict, List
from pathlib import Path
from abc import abstractmethod


class IEntityFactory(Protocol):
    """Interface for entity creation."""
    
    def create_application(self, name: str, **kwargs) -> Any:
        """Create application entity.
        
        Args:
            name: Application name
            **kwargs: Additional properties
            
        Returns:
            Application entity
        """
        ...
    
    def create_window(self, name: str, **kwargs) -> Any:
        """Create window entity.
        
        Args:
            name: Window name
            **kwargs: Additional properties
            
        Returns:
            Window entity
        """
        ...
    
    def create_function(self, name: str, **kwargs) -> Any:
        """Create function entity.
        
        Args:
            name: Function name
            **kwargs: Additional properties
            
        Returns:
            Function entity
        """
        ...
    
    def create_datawindow(self, name: str, **kwargs) -> Any:
        """Create datawindow entity.
        
        Args:
            name: DataWindow name
            **kwargs: Additional properties
            
        Returns:
            DataWindow entity
        """
        ...
    
    def create_library(self, name: str, **kwargs) -> Any:
        """Create library entity.
        
        Args:
            name: Library name
            **kwargs: Additional properties
            
        Returns:
            Library entity
        """
        ...


class IEntityValidator(Protocol):
    """Interface for entity validation."""
    
    def validate_entity(self, entity: Any) -> List[str]:
        """Validate an entity.
        
        Args:
            entity: Entity to validate
            
        Returns:
            List of validation errors
        """
        ...
    
    def validate_name(self, name: str, entity_type: str) -> bool:
        """Validate entity name.
        
        Args:
            name: Entity name
            entity_type: Type of entity
            
        Returns:
            True if valid, False otherwise
        """
        ...


class IRelationshipManager(Protocol):
    """Interface for relationship management."""
    
    def add_relationship(
        self, 
        from_entity: str, 
        to_entity: str, 
        relationship_type: str
    ) -> None:
        """Add relationship between entities.
        
        Args:
            from_entity: Source entity name
            to_entity: Target entity name
            relationship_type: Type of relationship
        """
        ...
    
    def get_entity_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        """Get all relationships for an entity.
        
        Args:
            entity_name: Entity name
            
        Returns:
            List of relationships
        """
        ...
    
    def get_entity_dependencies(self, entity_name: str) -> List[str]:
        """Get entity dependencies.
        
        Args:
            entity_name: Entity name
            
        Returns:
            List of dependency names
        """
        ...
    
    def validate_all_relationships(self) -> List[str]:
        """Validate all relationships.
        
        Returns:
            List of validation errors
        """
        ...


class IASTProcessor(Protocol):
    """Interface for AST processing."""
    
    def process_ast_file(self, file_path: Path) -> Dict[str, Any]:
        """Process an AST file.
        
        Args:
            file_path: Path to AST file
            
        Returns:
            Processed model
        """
        ...
    
    def extract_metadata(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            Extracted metadata
        """
        ...


class IModelExtractor(Protocol):
    """Interface for model extraction."""
    
    def extract_window_model(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract window model from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            Window model
        """
        ...
    
    def extract_datawindow_model(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract datawindow model from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            DataWindow model
        """
        ...
    
    def extract_function_model(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """Extract function model from AST.
        
        Args:
            ast: Abstract syntax tree
            
        Returns:
            Function model
        """
        ...


class IModelPersistence(Protocol):
    """Interface for model persistence."""
    
    def save_model(self, model: Dict[str, Any], file_path: Path) -> None:
        """Save model to file.
        
        Args:
            model: Model to save
            file_path: Output file path
        """
        ...
    
    def load_model(self, file_path: Path) -> Dict[str, Any]:
        """Load model from file.
        
        Args:
            file_path: Model file path
            
        Returns:
            Loaded model
        """
        ...


# Keep existing interfaces for compatibility
class IModelCoordinator(Protocol):
    """Interface for model coordinator."""

    @abstractmethod
    def process(self, input_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """Process model transformations."""
        ...

    @abstractmethod
    def analyze(self, ast: Any) -> Dict[str, Any]:
        """Analyze AST and extract metadata."""
        ...

    @abstractmethod
    def optimize(self, ast: Any) -> Any:
        """Optimize AST structure."""
        ...

    @abstractmethod
    def validate(self, ast: Any) -> List[str]:
        """Validate AST and return errors."""
        ...