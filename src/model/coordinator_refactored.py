"""Refactored Model coordinator using dependency injection and services.

This is a clean, focused coordinator that delegates to specialized services.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.contracts.models import (
    IEntityFactory, IEntityValidator, IRelationshipManager,
    IASTProcessor, IModelExtractor, IModelPersistence
)
from src.model.base.pb_entity import PBSourcedEntity

logger = logging.getLogger(__name__)


class ModelCoordinator:
    """Refactored coordinator for PowerBuilder object model management.
    
    This coordinator is focused on orchestration only, delegating all
    business logic to specialized services.
    """
    
    def __init__(
        self,
        entity_factory: IEntityFactory,
        entity_validator: IEntityValidator,
        relationship_manager: IRelationshipManager,
        ast_processor: IASTProcessor,
        model_extractor: IModelExtractor,
        model_persistence: IModelPersistence,
        input_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ):
        """Initialize the model coordinator with injected services.
        
        Args:
            entity_factory: Factory for creating entities
            entity_validator: Validator for entities
            relationship_manager: Manager for entity relationships
            ast_processor: Processor for AST files
            model_extractor: Extractor for models from AST
            model_persistence: Persistence service for models
            input_dir: Input directory for AST files
            output_dir: Output directory for model files
        """
        self.entity_factory = entity_factory
        self.entity_validator = entity_validator
        self.relationship_manager = relationship_manager
        self.ast_processor = ast_processor
        self.model_extractor = model_extractor
        self.model_persistence = model_persistence
        
        self.input_dir = Path(input_dir) if input_dir else None
        self.output_dir = Path(output_dir) if output_dir else None
        
        self._processed_files = 0
        self._failed_files = 0
    
    # Entity Management Methods (delegated to EntityFactory)
    
    def create_entity(self, entity_type: str, name: str, **kwargs) -> PBSourcedEntity:
        """Create a new PowerBuilder entity."""
        # Validate first
        entity = self.entity_factory.create_entity(entity_type, name, **kwargs)
        validation_errors = self.entity_validator.validate_entity(entity)
        
        if validation_errors:
            for error in validation_errors:
                logger.warning("Validation warning for %s %s: %s", entity_type, name, error)
        
        return entity
    
    def get_entity(self, entity_type: str, name: str) -> Optional[PBSourcedEntity]:
        """Get a cached entity by type and name."""
        return self.entity_factory.get_entity(entity_type, name)
    
    def create_library(self, name: str, **kwargs) -> Any:
        """Create a PowerBuilder library."""
        return self.entity_factory.create_library(name, **kwargs)
    
    def create_application(self, name: str, **kwargs) -> Any:
        """Create a PowerBuilder application."""
        return self.create_entity("application", name, **kwargs)
    
    def create_window(self, name: str, **kwargs) -> Any:
        """Create a PowerBuilder window."""
        return self.create_entity("window", name, **kwargs)
    
    def create_function(self, name: str, return_type: str = "void", **kwargs) -> Any:
        """Create a PowerBuilder function."""
        return self.create_entity("function", name, return_type=return_type, **kwargs)
    
    def create_datawindow(self, name: str, sql_statement: Optional[str] = None, **kwargs) -> Any:
        """Create a PowerBuilder DataWindow."""
        return self.create_entity("datawindow", name, sql_statement=sql_statement, **kwargs)
    
    def register_custom_type(self, type_name: str, type_class: type[PBSourcedEntity]) -> None:
        """Register a custom entity type."""
        self.entity_factory.register_custom_type(type_name, type_class)
    
    def clear_cache(self) -> None:
        """Clear the entity cache."""
        self.entity_factory.clear_cache()
    
    def get_all_entities(self) -> List[PBSourcedEntity]:
        """Get all cached entities."""
        return self.entity_factory.get_all_entities()
    
    # Relationship Management Methods (delegated to RelationshipManager)
    
    def add_relationship(self, from_entity: str, to_entity: str, relationship_type: str = "uses") -> None:
        """Add a relationship between entities."""
        self.relationship_manager.add_relationship(from_entity, to_entity, relationship_type)
    
    def get_entity_relationships(self, entity_key: str) -> List[Dict[str, Any]]:
        """Get all entities that this entity has relationships with."""
        return self.relationship_manager.get_entity_relationships(entity_key)
    
    def get_entity_dependencies(self, entity_key: str) -> List[str]:
        """Get all entities that depend on this entity."""
        return self.relationship_manager.get_entity_dependencies(entity_key)
    
    def validate_all_relationships(self) -> List[str]:
        """Validate all entity relationships."""
        return self.relationship_manager.validate_all_relationships()
    
    # Pipeline Stage Methods
    
    def process_ast_file(self, ast_file: Path) -> bool:
        """Process a single AST file and convert to model objects."""
        try:
            # Process AST file
            model_data = self.ast_processor.process_ast_file(ast_file)
            if not model_data:
                self._failed_files += 1
                return False
            
            # Extract model based on type
            object_type = model_data.get('type', 'unknown')
            object_name = model_data.get('name', ast_file.stem)
            ast = model_data.get('ast', {})
            
            # Set current object for extraction context
            self.model_extractor.set_current_object(object_name)
            
            # Extract model based on type
            if object_type == 'window':
                model = self.model_extractor.extract_window_model(ast)
            elif object_type == 'datawindow':
                model = self.model_extractor.extract_datawindow_model(ast)
            elif object_type == 'function':
                model = self.model_extractor.extract_function_model(ast)
            else:
                model = self.model_extractor.extract_generic_model(ast, object_type)
            
            # Update model data
            model_data['data'] = model
            
            # Save model to output
            if self.output_dir:
                output_path = self.model_persistence.save_model_by_type(
                    model_data, 
                    self.output_dir, 
                    object_type, 
                    object_name
                )
                logger.debug("Saved model to %s", output_path)
            
            self._processed_files += 1
            return True
            
        except Exception as e:
            logger.error("Failed to process AST file %s: %s", ast_file, e)
            self._failed_files += 1
            return False
    
    def convert_directory(self) -> Dict[str, Any]:
        """Convert all AST files in input directory to models."""
        if not self.input_dir or not self.output_dir:
            raise ValueError("Input and output directories must be set")
        
        results = {
            'processed': 0,
            'failed': 0,
            'models': []
        }
        
        # Process all AST files
        for ast_file in self.input_dir.rglob("*.ast.json"):
            if self.process_ast_file(ast_file):
                results['processed'] += 1
                results['models'].append(str(ast_file.name))
            else:
                results['failed'] += 1
        
        # Create summary
        summary = self.model_persistence.create_model_summary(self.output_dir)
        results['summary'] = summary
        
        return results
    
    def convert_file(self, ast_file: Path) -> Optional[Path]:
        """Convert a single AST file to model format."""
        if self.process_ast_file(ast_file):
            # Return path to generated model file
            object_type = self.ast_processor.extract_metadata({'file': str(ast_file)}).get('object_type', 'unknown')
            object_name = ast_file.stem.replace('.ast', '')
            
            if self.output_dir:
                return self.output_dir / object_type / f"{object_name}.model.json"
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            'processed_files': self._processed_files,
            'failed_files': self._failed_files,
            'ast_processor': self.ast_processor.get_statistics(),
            'persistence': self.model_persistence.get_statistics(),
            'entities': len(self.get_all_entities()),
            'relationships': len(self.relationship_manager.get_relationship_graph())
        }