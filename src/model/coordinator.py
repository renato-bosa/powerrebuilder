"""Model coordinator for PowerBuilder object model management.

This module provides centralized coordination for the PowerBuilder object model,
managing the creation and relationships between various model components.

It also serves as the Model stage coordinator for the pipeline, converting
parsed AST JSON files into structured model objects.

Pipeline Stage: Model (Stage 4)
Input: AST JSON files from Parse stage
Output: Model JSON files for Generate stage

This coordinator supports two usage patterns:
1. Simple constructor for backward compatibility (used by pipeline)
2. Dependency injection for testability and flexibility
"""


import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import re

from src.model.base.pb_entity import PBSourcedEntity
from src.model.entities.application import PBApplication
from src.model.entities.event import PBEvent
from src.model.entities.function import PBFunction, PBVariableNode as PBVariable
from src.model.entities.library import Library as PBLibrary
from src.model.transformers.ast_to_model import Window, Menu, DataWindow as PBDataWindow
from src.model.transaction.transaction import PBTransaction
from src.model.utils.errors import ValidationError

# Import interfaces for dependency injection
try:
    from src.contracts.models import (
        IEntityFactory, IEntityValidator, IRelationshipManager,
        IASTProcessor, IModelExtractor, IModelPersistence
    )
except ImportError:
    # Interfaces not available - running in simple mode
    IEntityFactory = None
    IEntityValidator = None
    IRelationshipManager = None
    IASTProcessor = None
    IModelExtractor = None
    IModelPersistence = None

logger = logging.getLogger(__name__)


class ModelCoordinator:
    """Coordinates the creation and management of PowerBuilder model objects.

    This class provides a centralized interface for creating and managing
    PowerBuilder model objects, ensuring consistency and proper relationships
    between different model components.
    """

    def __init__(
        self,
        input_dir: Union[str, Path, IEntityFactory, None] = None,
        output_dir: Union[str, Path, IEntityValidator, None] = None,
        relationship_manager: Optional[IRelationshipManager] = None,
        ast_processor: Optional[IASTProcessor] = None,
        model_extractor: Optional[IModelExtractor] = None,
        model_persistence: Optional[IModelPersistence] = None,
    ) -> None:
        """Initialize the model coordinator.

        Supports two usage patterns:
        1. Simple: ModelCoordinator(input_dir, output_dir)
        2. DI: ModelCoordinator(entity_factory, entity_validator, relationship_manager, ...)

        Args:
            input_dir: Input directory (simple) or IEntityFactory (DI)
            output_dir: Output directory (simple) or IEntityValidator (DI)
            relationship_manager: Relationship manager service (DI only)
            ast_processor: AST processor service (DI only)
            model_extractor: Model extractor service (DI only)
            model_persistence: Model persistence service (DI only)
        """
        # Detect which constructor pattern is being used
        if relationship_manager is not None:
            # Dependency injection pattern
            self._init_with_services(
                entity_factory=input_dir,  # type: ignore
                entity_validator=output_dir,  # type: ignore
                relationship_manager=relationship_manager,
                ast_processor=ast_processor,
                model_extractor=model_extractor,
                model_persistence=model_persistence
            )
        else:
            # Simple pattern for backward compatibility
            self._init_simple(input_dir, output_dir)  # type: ignore
    
    def _init_simple(self, input_dir: Union[str, Path, None], output_dir: Union[str, Path, None]) -> None:
        """Initialize with simple constructor pattern."""
        # Services will be None in simple mode
        self.entity_factory = None
        self.entity_validator = None
        self.relationship_manager = None
        self.ast_processor = None
        self.model_extractor = None
        self.model_persistence = None
        self._entity_cache: dict[str, PBSourcedEntity] = {}
        self._type_registry: dict[str, type[PBSourcedEntity]] = {
            "application": PBApplication, 
            "function": PBFunction, 
            "event": PBEvent, 
            "variable": PBVariable, 
            "window": Window, 
            "menu": Menu, 
            "datawindow": PBDataWindow, 
            "transaction": PBTransaction,
        }
        # Entity relationships tracking
        self._entity_relationships: dict[str, set[str]] = {}
        # Entity dependencies
        self._entity_dependencies: dict[str, set[str]] = {}
        # Validation rules
        self._validation_rules: dict[str, list[Callable[[str, dict[str, Any]], None]]] = {
            "application": [self._validate_application],
            "function": [self._validate_function],
            "event": [self._validate_event],
            "variable": [self._validate_variable],
            "window": [self._validate_window],
            "menu": [self._validate_menu],
            "datawindow": [self._validate_datawindow],
            "transaction": [self._validate_transaction],
        }

        # Pipeline mode attributes
        self.input_dir = Path(input_dir) if input_dir else None
        self.output_dir = Path(output_dir) if output_dir else None
        self._processed_files = 0
        self._failed_files = 0
    
    def _init_with_services(
        self,
        entity_factory: IEntityFactory,
        entity_validator: IEntityValidator,
        relationship_manager: IRelationshipManager,
        ast_processor: Optional[IASTProcessor],
        model_extractor: Optional[IModelExtractor],
        model_persistence: Optional[IModelPersistence],
        input_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ) -> None:
        """Initialize with dependency injection pattern."""
        self.entity_factory = entity_factory
        self.entity_validator = entity_validator
        self.relationship_manager = relationship_manager
        self.ast_processor = ast_processor
        self.model_extractor = model_extractor
        self.model_persistence = model_persistence
        
        # Initialize internal state for compatibility
        self._entity_cache = {}
        self._type_registry = {}
        self._entity_relationships = {}
        self._entity_dependencies = {}
        self._validation_rules = {}
        
        self.input_dir = Path(input_dir) if input_dir else None
        self.output_dir = Path(output_dir) if output_dir else None
        self._processed_files = 0
        self._failed_files = 0

    def create_entity(self, entity_type: str, name: str, **kwargs) -> PBSourcedEntity:
        """Create a new PowerBuilder entity.

        Args:
            entity_type: Type of entity to create (e.g., "function", "window")
            name: Name of the entity
            **kwargs: Additional arguments for entity creation

        Returns:
            Created entity instance

        Raises:
            ValueError: If entity_type is not recognized
            ValidationError: If entity validation fails
        """
        if self.entity_factory:
            # Use injected service
            entity = self.entity_factory.create_entity(entity_type, name, **kwargs)
            if self.entity_validator:
                validation_errors = self.entity_validator.validate_entity(entity)
                if validation_errors:
                    for error in validation_errors:
                        logger.warning("Validation warning for %s %s: %s", entity_type, name, error)
            return entity
        else:
            # Use built-in implementation
            if entity_type not in self._type_registry:
                msg = f"Unknown entity type: {entity_type}"
                raise ValueError(msg)

            # Validate entity before creation
            self._validate_entity(entity_type, name, kwargs)

            entity_class = self._type_registry[entity_type]
            entity = entity_class(name=name, **kwargs)

            # Cache the entity
            cache_key = f"{entity_type}:{name}"
            self._entity_cache[cache_key] = entity

            # Initialize relationship tracking
            self._entity_relationships[cache_key] = set()
            self._entity_dependencies[cache_key] = set()

            logger.debug("Created %s entity: %s", entity_type, name)
            return entity

    def get_entity(self, entity_type: str, name: str) -> Optional[PBSourcedEntity]:
        """Get a cached entity by type and name.

        Args:
            entity_type: Type of entity
            name: Name of the entity

        Returns:
            Cached entity instance or None if not found
        """
        if self.entity_factory and hasattr(self.entity_factory, 'get_entity'):
            return self.entity_factory.get_entity(entity_type, name)
        
        cache_key = f"{entity_type}:{name}"
        return self._entity_cache.get(cache_key)

    def create_library(self, name: str, path: Path) -> PBLibrary:




        """Create a PowerBuilder library.

        Args:
            name: Library name
            path: Path to library file

        Returns:
            Created library instance
        """
        library = PBLibrary(name=name, path=path)
        logger.debug("Created library: %s at %s", name, path)
        return library

    def create_application(self, name: str, **kwargs) -> PBApplication:




        """Create a PowerBuilder application.

        Args:
            name: Application name
            **kwargs: Additional application properties

        Returns:
            Created application instance
        """
        return self.create_entity("application", name, **kwargs)

    def create_window(self, name: str, **kwargs) -> Window:




        """Create a PowerBuilder window.

        Args:
            name: Window name
            **kwargs: Additional window properties

        Returns:
            Created window instance
        """
        return self.create_entity("window", name, **kwargs)

    def create_function(
        self, name: str, return_type: str = "void", **kwargs,
    ) -> PBFunction:




        """Create a PowerBuilder function.

        Args:
            name: Function name
            return_type: Function return type
            **kwargs: Additional function properties

        Returns:
            Created function instance
        """
        return self.create_entity("function", name, return_type=return_type, **kwargs)

    def create_datawindow(
        self, name: str, sql_statement: str | None = None, **kwargs,
    ) -> PBDataWindow:




        """Create a PowerBuilder DataWindow.

        Args:
            name: DataWindow name
            sql_statement: SQL statement for the DataWindow
            **kwargs: Additional DataWindow properties

        Returns:
            Created DataWindow instance
        """
        return self.create_entity("datawindow", name, sql_statement=sql_statement, **kwargs)

    def register_custom_type(
        self, type_name: str, type_class: type[PBSourcedEntity],
    ) -> None:




        """Register a custom entity type.

        Args:
            type_name: Name for the entity type
            type_class: Class to use for creating entities of this type
        """
        self._type_registry[type_name] = type_class
        logger.debug("Registered custom type: %s", type_name)

    def clear_cache(self) -> None:
        """Clear the entity cache."""
        if self.entity_factory and hasattr(self.entity_factory, 'clear_cache'):
            self.entity_factory.clear_cache()
        else:
            self._entity_cache.clear()
        logger.debug("Cleared entity cache")

    def get_all_entities(self) -> List[PBSourcedEntity]:
        """Get all cached entities.

        Returns:
            List of all cached entities
        """
        if self.entity_factory and hasattr(self.entity_factory, 'get_all_entities'):
            return self.entity_factory.get_all_entities()
        return list(self._entity_cache.values())

    def _validate_entity(self, entity_type: str, name: str, kwargs: dict[str, Any]) -> None:
        """Validate entity creation parameters.

        Args:
            entity_type: Type of entity
            name: Entity name
            kwargs: Additional parameters

        Raises:
            ValidationError: If validation fails
        """
        # Common validation
        if not name or not isinstance(name, str):
            raise ValidationError("Entity name must be a non-empty string")

        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            raise ValidationError(f"Invalid entity name: {name}. Must start with letter/underscore and contain only alphanumeric/underscore")

        # Check for duplicate names within type
        cache_key = f"{entity_type}:{name}"
        if cache_key in self._entity_cache:
            raise ValidationError(f"{entity_type} with name '{name}' already exists")

        # Run type-specific validation rules
        if entity_type in self._validation_rules:
            for rule in self._validation_rules[entity_type]:
                rule(name, kwargs)

    def _validate_application(self, name: str, kwargs: dict[str, Any]) -> None:
        """Validate application creation."""
        # Application names typically end with _app
        if not name.endswith("_app") and "app" not in name.lower():
            logger.warning("Application name '%s' does not follow naming convention (usually ends with _app)", name)

    def _validate_function(self, name: str, kwargs: dict[str, Any]) -> None:
        """Validate function creation."""
        # Check return type
        return_type = kwargs.get("return_type", "void")
        if not return_type:
            raise ValidationError("Function must have a return type")

        # Function naming conventions
        if name.startswith("of_") or name.startswith("uf_"):
            # Object/User functions - good
            pass
        elif name.startswith("f_"):
            # Global function - good
            pass
        else:
            logger.warning("Function name '%s' does not follow PowerBuilder naming conventions (of_, uf_, or f_ prefix)", name)

    def _validate_event(self, name: str, kwargs: dict[str, Any]) -> None:
        """Validate event creation."""
        # Event naming convention
        if not (name.startswith("ue_") or name in ["clicked", "doubleclicked", "constructor", "destructor", "open", "close"]):
            logger.warning("Event name '%s' does not follow naming convention (ue_ prefix for user events)", name)

    def _validate_variable(self, name: str, kwargs: dict[str, Any]) -> None:
        """Validate variable creation."""
        # Check variable type
        var_type = kwargs.get("var_type")
        if not var_type:
            raise ValidationError("Variable must have a type")

        # Variable naming conventions
        if name.startswith("i"):
            # Instance variable - good
            pass
        elif name.startswith("g"):
            # Global variable - good
            pass
        elif name.startswith("l"):
            # Local variable - good
            pass
        elif name.startswith("a"):
            # Argument - good
            pass
        else:
            logger.warning("Variable name '%s' does not follow PowerBuilder naming conventions (i/g/l/a prefix)", name)

    def _validate_window(self, name: str, kwargs: dict[str, Any]) -> None:
        """Validate window creation."""
        # Window naming convention
        if not name.startswith("w_"):
            logger.warning("Window name '%s' does not follow naming convention (w_ prefix)", name)

    def _validate_menu(self, name: str, kwargs: dict[str, Any]) -> None:
        """Validate menu creation."""
        # Menu naming convention
        if not name.startswith("m_"):
            logger.warning("Menu name '%s' does not follow naming convention (m_ prefix)", name)

    def _validate_datawindow(self, name: str, kwargs: dict[str, Any]) -> None:
        """Validate datawindow creation."""
        # DataWindow naming convention
        if not (name.startswith("d_") or name.startswith("dw_")):
            logger.warning("DataWindow name '%s' does not follow naming convention (d_ or dw_ prefix)", name)

    def _validate_transaction(self, name: str, kwargs: dict[str, Any]) -> None:
        """Validate transaction creation."""
        # Transaction objects often have specific suffixes
        if not (name.endswith("_trans") or name == "sqlca"):
            logger.warning("Transaction name '%s' does not follow naming convention (usually ends with _trans)", name)

    def add_relationship(self, from_entity: str, to_entity: str, relationship_type: str = "uses") -> None:
        """Add a relationship between entities.

        Args:
            from_entity: Source entity (format: "type:name")
            to_entity: Target entity (format: "type:name")
            relationship_type: Type of relationship
        """
        if self.relationship_manager:
            self.relationship_manager.add_relationship(from_entity, to_entity, relationship_type)
        else:
            if from_entity not in self._entity_cache:
                raise ValueError(f"Source entity {from_entity} not found")
            if to_entity not in self._entity_cache:
                raise ValueError(f"Target entity {to_entity} not found")

            self._entity_relationships[from_entity].add(to_entity)
            self._entity_dependencies[to_entity].add(from_entity)

            logger.debug("Added relationship: %s %s %s", from_entity, relationship_type, to_entity)

    def get_entity_relationships(self, entity_key: str) -> set[str]:
        """Get all entities that this entity has relationships with.

        Args:
            entity_key: Entity key (format: "type:name")

        Returns:
            Set of related entity keys
        """
        return self._entity_relationships.get(entity_key, set())

    def get_entity_dependencies(self, entity_key: str) -> set[str]:
        """Get all entities that depend on this entity.

        Args:
            entity_key: Entity key (format: "type:name")

        Returns:
            Set of dependent entity keys
        """
        return self._entity_dependencies.get(entity_key, set())

    def find_entities(self, entity_type: str | None = None, name_pattern: str | None = None) -> list[tuple[str, PBSourcedEntity]]:
        """Find entities matching criteria.

        Args:
            entity_type: Filter by entity type
            name_pattern: Regex pattern for name matching

        Returns:
            List of (key, entity) tuples
        """
        results = []

        for key, entity in self._entity_cache.items():
            type_part, name_part = key.split(":", 1)

            # Filter by type
            if entity_type and type_part != entity_type:
                continue

            # Filter by name pattern
            if name_pattern and not re.match(name_pattern, name_part):
                continue

            results.append((key, entity))

        return results

    def validate_all_relationships(self) -> list[str]:
        """Validate all entity relationships.

        Returns:
            List of validation errors
        """
        errors = []

        # Check for circular dependencies
        for entity_key in self._entity_cache:
            visited = set()
            stack = set()

            def has_cycle(node: str) -> bool:
                if node in stack:
                    return True
                if node in visited:
                    return False

                visited.add(node)
                stack.add(node)

                for related in self._entity_relationships.get(node, set()):
                    if has_cycle(related):
                        return True

                stack.remove(node)
                return False

            if has_cycle(entity_key):
                errors.append(f"Circular dependency detected involving {entity_key}")

        # Check for orphaned relationships
        for entity_key, relationships in self._entity_relationships.items():
            for related in relationships:
                if related not in self._entity_cache:
                    errors.append(f"Entity {entity_key} has relationship to non-existent entity {related}")

        return errors

    # Pipeline Stage Methods

    def process_ast_file(self, ast_file: Union[str, Path]) -> bool:
        """Process a single AST file and convert to model objects.

        This is the main entry point for pipeline processing.

        Args:
            ast_file: Path to AST JSON file

        Returns:
            True if successful, False otherwise
        """
        if self.ast_processor and self.model_extractor and self.model_persistence:
            # Use injected services
            try:
                # Process AST file
                model_data = self.ast_processor.process_ast_file(Path(ast_file))
                if not model_data:
                    self._failed_files += 1
                    return False
                
                # Extract model based on type
                object_type = model_data.get('type', 'unknown')
                object_name = model_data.get('name', Path(ast_file).stem)
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
        else:
            # Use built-in implementation
            ast_path = Path(ast_file)
            if not ast_path.exists():
                logger.error("AST file not found: %s", ast_path)
                return False

            try:
                # Load AST data
                with open(ast_path, 'r', encoding='utf-8') as f:
                    ast_data = json.load(f)

                # Process based on format
                if 'ast' in ast_data:
                    # New format with metadata
                    return self._process_structured_ast(ast_path, ast_data)
                else:
                    # Legacy format - just the AST
                    return self._process_legacy_ast(ast_path, ast_data)

            except Exception as e:
                logger.error("Failed to process AST file %s: %s", ast_path, e)
                self._failed_files += 1
                return False

    def _process_structured_ast(self, ast_path: Path, ast_data: dict) -> bool:
        """Process AST data in structured format.

        Args:
            ast_path: Path to the AST file
            ast_data: Loaded AST data with metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract metadata
            file_path = ast_data.get('file', str(ast_path))
            object_type = ast_data.get('object_type', 'unknown')
            object_name = ast_data.get('object_name', ast_path.stem)

            # Get the AST
            ast_content = ast_data.get('ast')
            if not ast_content:
                logger.error("No AST content in %s", ast_path)
                return False

            # Handle different AST formats
            if isinstance(ast_content, dict):
                # Already a dictionary - could be serialized Tree or model
                ast = ast_content
            elif isinstance(ast_content, str):
                # Pretty-printed string format (legacy)
                ast = {'type': 'legacy_ast', 'content': ast_content}
            else:
                logger.error("Unknown AST format in %s", ast_path)
                return False

            # Extract object type and name from AST if not provided
            if object_type == 'unknown' and 'children' in ast and ast['children']:
                extracted_type, extracted_name = self._extract_type_from_ast(ast)
                if extracted_type:
                    object_type = extracted_type
                if extracted_name:
                    object_name = extracted_name

            # Create model based on object type
            model = self._create_model_from_ast(object_type, object_name, ast)
            if not model:
                return False

            # Save model to output
            if self.output_dir:
                self._save_model(model, object_type, object_name)

            self._processed_files += 1
            return True

        except Exception as e:
            logger.error("Error processing structured AST %s: %s", ast_path, e)
            return False

    def _process_legacy_ast(self, ast_path: Path, ast_data: dict) -> bool:
        """Process AST data in legacy format.

        Args:
            ast_path: Path to the AST file
            ast_data: Raw AST data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Infer object type from filename
            object_type = self._infer_object_type(ast_path.name)
            object_name = ast_path.stem.replace('.ast', '')

            # Create model
            model = self._create_model_from_ast(object_type, object_name, ast_data)
            if not model:
                return False

            # Save model
            if self.output_dir:
                self._save_model(model, object_type, object_name)

            self._processed_files += 1
            return True

        except Exception as e:
            logger.error("Error processing legacy AST %s: %s", ast_path, e)
            return False

    def _infer_object_type(self, filename: str) -> str:
        """Infer object type from filename.

        Args:
            filename: Name of the file

        Returns:
            Inferred object type
        """
        name_lower = filename.lower()

        if '.srw' in name_lower or name_lower.startswith('w_'):
            return 'window'
        elif '.srd' in name_lower or '.dwo' in name_lower or name_lower.startswith('d_'):
            return 'datawindow'
        elif '.sru' in name_lower or name_lower.startswith('u_') or name_lower.startswith('uo_'):
            return 'userobject'
        elif '.srf' in name_lower or name_lower.startswith('f_'):
            return 'function'
        elif '.srs' in name_lower:
            return 'structure'
        elif '.srm' in name_lower or name_lower.startswith('m_'):
            return 'menu'
        elif '.sra' in name_lower:
            return 'application'
        elif '.sql' in name_lower:
            return 'query'
        else:
            return 'unknown'

    def _create_model_from_ast(self, object_type: str, object_name: str, ast: dict) -> dict | None:
        """Create a model object from AST data.

        Args:
            object_type: Type of PowerBuilder object
            object_name: Name of the object
            ast: AST data

        Returns:
            Model dictionary or None if failed
        """
        try:
            # Store current object name for visitor context
            self.current_object_name = object_name
            
            # Create base model structure
            model = {
                'type': object_type,
                'name': object_name,
                'timestamp': Path(ast.get('file', '')).stat().st_mtime if 'file' in ast and Path(ast['file']).exists() else None,
                'data': {}
            }

            # Extract information based on object type
            if object_type == 'window':
                model['data'] = self._extract_window_model(ast)
            elif object_type == 'datawindow':
                model['data'] = self._extract_datawindow_model(ast)
            elif object_type == 'function':
                model['data'] = self._extract_function_model(ast)
            elif object_type == 'userobject':
                model['data'] = self._extract_userobject_model(ast)
            elif object_type == 'menu':
                model['data'] = self._extract_menu_model(ast)
            elif object_type == 'application':
                model['data'] = self._extract_application_model(ast)
            else:
                # Generic extraction
                model['data'] = self._extract_generic_model(ast)

            return model

        except Exception as e:
            logger.error("Failed to create model for %s: %s", object_name, e)
            return None

    def _extract_window_model(self, ast: dict) -> dict:
        """Extract window model from AST."""
        # Use visitor pattern for extraction
        try:
            from src.model.visitors import WindowModelExtractor
            
            visitor = WindowModelExtractor()
            object_name = getattr(self, 'current_object_name', '')
            return visitor.extract_model(ast, 'window', object_name)
        except ImportError:
            # Fallback to legacy regex-based extraction if visitor not available
            return self._extract_window_model_legacy(ast)
        except Exception as e:
            logger.warning("Visitor extraction failed, using legacy method: %s", e)
            return self._extract_window_model_legacy(ast)
    
    def _extract_window_model_legacy(self, ast: dict) -> dict:
        """Legacy regex-based window model extraction."""
        # Parse AST to extract window information
        events = []
        methods = []
        controls = []

        try:
            if 'children' in ast and ast['children']:
                ast_str = str(ast['children'][0].get('value', ''))

                # Extract event handlers
                import re
                event_matches = re.findall(r"Tree\(Token\('RULE', 'event_handler'\).*?Token\('IDENTIFIER', '(\w+)'\)", ast_str)
                for event_name in event_matches:
                    events.append({
                        'name': event_name,
                        'type': 'event',
                        'parameters': [],
                        'return_type': 'any'
                    })

                # Extract create/destroy handlers
                if "'on_block'" in ast_str:
                    if "'CREATE'" in ast_str:
                        events.append({'name': 'create', 'type': 'system_event'})
                    if "'DESTROY'" in ast_str:
                        events.append({'name': 'destroy', 'type': 'system_event'})
        except Exception as e:
            logger.debug("Error extracting window model: %s", e)

        return {
            'title': '',
            'controls': controls,
            'events': events,
            'methods': methods,
            'variables': [],
            'properties': {}
        }

    def _extract_datawindow_model(self, ast: dict) -> dict:
        """Extract datawindow model from AST."""
        # Use visitor pattern for extraction
        try:
            from src.model.visitors import ModelExtractorVisitor
            
            visitor = ModelExtractorVisitor()
            object_name = getattr(self, 'current_object_name', '')
            model = visitor.extract_model(ast, 'datawindow', object_name)
            
            # Add datawindow-specific defaults
            model.setdefault('columns', [])
            model.setdefault('sql', '')
            model.setdefault('presentation_style', 'grid')
            
            return model
        except Exception as e:
            logger.warning("Visitor extraction failed, using defaults: %s", e)
            return {
                'columns': ast.get('columns', []),
                'sql': ast.get('sql', ''),
                'presentation_style': ast.get('presentation_style', 'grid'),
                'properties': ast.get('properties', {})
            }

    def _extract_function_model(self, ast: dict) -> dict:
        """Extract function model from AST."""
        # Use visitor pattern for extraction
        try:
            from src.model.visitors import ModelExtractorVisitor
            
            visitor = ModelExtractorVisitor()
            object_name = getattr(self, 'current_object_name', '')
            model = visitor.extract_model(ast, 'function', object_name)
            
            # Add function-specific defaults
            model.setdefault('return_type', 'void')
            model.setdefault('parameters', [])
            model.setdefault('body', '')
            model.setdefault('visibility', 'public')
            
            return model
        except Exception as e:
            logger.warning("Visitor extraction failed, using defaults: %s", e)
            return {
                'return_type': ast.get('return_type', 'void'),
                'parameters': ast.get('parameters', []),
                'body': ast.get('body', ''),
                'visibility': ast.get('visibility', 'public')
            }

    def _extract_userobject_model(self, ast: dict) -> dict:
        """Extract user object model from AST."""
        # Use visitor pattern for extraction
        try:
            from src.model.visitors import UserObjectModelExtractor
            
            visitor = UserObjectModelExtractor()
            object_name = getattr(self, 'current_object_name', '')
            return visitor.extract_model(ast, 'userobject', object_name)
        except ImportError:
            # Fallback to legacy regex-based extraction if visitor not available
            return self._extract_userobject_model_legacy(ast)
        except Exception as e:
            logger.warning("Visitor extraction failed, using legacy method: %s", e)
            return self._extract_userobject_model_legacy(ast)
    
    def _extract_userobject_model_legacy(self, ast: dict) -> dict:
        """Legacy regex-based user object model extraction."""
        events = []
        methods = []

        try:
            if 'children' in ast and ast['children']:
                ast_str = str(ast['children'][0].get('value', ''))

                # Extract functions
                import re
                func_matches = re.findall(r"Tree\(Token\('RULE', 'function_decl'\).*?Token\('TYPE_NAME', '(\w+)'\).*?Token\('IDENTIFIER', '(\w+)'\)", ast_str)
                for return_type, func_name in func_matches:
                    methods.append({
                        'name': func_name,
                        'type': 'function',
                        'return_type': return_type,
                        'parameters': [],
                        'visibility': 'public'
                    })

                # Extract create/destroy handlers
                if "'on_block'" in ast_str:
                    if "'CREATE'" in ast_str:
                        events.append({'name': 'create', 'type': 'system_event'})
                    if "'DESTROY'" in ast_str:
                        events.append({'name': 'destroy', 'type': 'system_event'})
        except Exception as e:
            logger.debug("Error extracting userobject model: %s", e)

        return {
            'visual': False,
            'controls': [],
            'methods': methods,
            'events': events,
            'variables': [],
            'properties': {}
        }

    def _extract_menu_model(self, ast: dict) -> dict:
        """Extract menu model from AST."""
        # Use visitor pattern for extraction
        try:
            from src.model.visitors import ModelExtractorVisitor
            
            visitor = ModelExtractorVisitor()
            object_name = getattr(self, 'current_object_name', '')
            model = visitor.extract_model(ast, 'menu', object_name)
            
            # Add menu-specific defaults
            model.setdefault('items', [])
            
            return model
        except Exception as e:
            logger.warning("Visitor extraction failed, using defaults: %s", e)
            return {
                'items': ast.get('items', []),
                'events': ast.get('events', []),
                'properties': ast.get('properties', {})
            }

    def _extract_application_model(self, ast: dict) -> dict:
        """Extract application model from AST."""
        # Use visitor pattern for extraction
        try:
            from src.model.visitors import ModelExtractorVisitor
            
            visitor = ModelExtractorVisitor()
            object_name = getattr(self, 'current_object_name', '')
            model = visitor.extract_model(ast, 'application', object_name)
            
            # Add application-specific defaults
            model.setdefault('open_window', '')
            
            return model
        except Exception as e:
            logger.warning("Visitor extraction failed, using defaults: %s", e)
            return {
                'open_window': ast.get('open_window', ''),
                'variables': ast.get('variables', []),
                'events': ast.get('events', []),
                'properties': ast.get('properties', {})
            }

    def _extract_generic_model(self, ast: dict) -> dict:
        """Extract generic model from AST."""
        # Use visitor pattern for extraction
        try:
            from src.model.visitors import ModelExtractorVisitor
            
            visitor = ModelExtractorVisitor()
            object_name = getattr(self, 'current_object_name', '')
            model = visitor.extract_model(ast, 'unknown', object_name)
            
            # If visitor didn't extract much, include raw AST
            if not model.get('events') and not model.get('methods') and not model.get('variables'):
                model['raw_ast'] = ast
            
            return model
        except Exception as e:
            logger.warning("Visitor extraction failed, returning raw AST: %s", e)
            return ast

    def _extract_type_from_ast(self, ast: dict) -> tuple[str | None, str | None]:
        """Extract object type and name from AST structure.

        Args:
            ast: AST dictionary

        Returns:
            Tuple of (object_type, object_name)
        """
        # Try visitor-based extraction first
        try:
            from src.model.visitors.ast_walker import ASTWalker
            
            # Look for type declaration nodes
            type_nodes = ASTWalker.find_by_type(ast, 'type_declaration')
            if not type_nodes:
                type_nodes = ASTWalker.find_by_type(ast, 'global_type')
            
            if type_nodes:
                # Extract identifiers from the first type node
                identifiers = ASTWalker.extract_identifiers(type_nodes[0])
                if len(identifiers) >= 2:
                    name = identifiers[0]
                    parent_type = identifiers[1].lower()
                    
                    # Map parent type to object type
                    type_map = {
                        'window': 'window',
                        'userobject': 'userobject',
                        'menu': 'menu',
                        'datawindow': 'datawindow',
                        'application': 'application'
                    }
                    
                    object_type = type_map.get(parent_type, 'unknown')
                    return object_type, name
            
            return None, None
        except ImportError:
            # Fallback to legacy method
            return self._extract_type_from_ast_legacy(ast)
        except Exception as e:
            logger.warning("Visitor extraction failed, using legacy method: %s", e)
            return self._extract_type_from_ast_legacy(ast)
    
    def _extract_type_from_ast_legacy(self, ast: dict) -> tuple[str | None, str | None]:
        """Legacy regex-based type extraction from AST."""
        try:
            if 'children' in ast and ast['children']:
                # Look for the AST string representation
                first_child = ast['children'][0]
                if isinstance(first_child, dict) and 'value' in first_child:
                    ast_str = str(first_child['value'])

                    # Extract type from "global type X from Y" pattern
                    import re
                    type_match = re.search(r"Token\('IDENTIFIER', '(\w+)'\), Token\('FROM', 'from'\), Token\('IDENTIFIER', '(\w+)'\)", ast_str)
                    if type_match:
                        name = type_match.group(1)
                        parent_type = type_match.group(2)

                        # Map parent type to object type
                        type_map = {
                            'window': 'window',
                            'userobject': 'userobject',
                            'menu': 'menu',
                            'datawindow': 'datawindow',
                            'application': 'application'
                        }

                        object_type = type_map.get(parent_type, 'unknown')
                        return object_type, name

            return None, None
        except Exception as e:
            logger.debug("Could not extract type from AST: %s", e)
            return None, None

    def _save_model(self, model: dict, object_type: str, object_name: str) -> None:
        """Save model to output directory.

        Args:
            model: Model dictionary
            object_type: Type of object
            object_name: Name of object
        """
        if not self.output_dir:
            return

        # Create output path
        output_file = self.output_dir / f"{object_name}.model.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Add metadata
        model_with_meta = {
            'model_version': '1.0',
            'source_type': 'powerbuilder',
            'models': [model]
        }

        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(model_with_meta, f, indent=2)

        logger.debug("Saved model for %s to %s", object_name, output_file)

    def convert_directory(self, input_dir: Union[str, Path, None] = None, output_dir: Union[str, Path, None] = None) -> Dict[str, Any]:
        """Convert all AST files in a directory to models.

        Args:
            input_dir: Directory containing AST files (uses self.input_dir if None)
            output_dir: Directory for model files (uses self.output_dir if None)

        Returns:
            Dictionary with conversion statistics
        """
        input_path = Path(input_dir) if input_dir else self.input_dir
        output_path = Path(output_dir) if output_dir else self.output_dir

        if not input_path:
            raise ValueError("No input directory specified")
        if not output_path:
            raise ValueError("No output directory specified")

        # Reset counters
        self._processed_files = 0
        self._failed_files = 0

        # Find all AST files
        ast_files = list(input_path.rglob("*.ast.json"))
        logger.info("Found %d AST files to convert", len(ast_files))

        # Update paths for processing
        self.input_dir = input_path
        self.output_dir = output_path

        # Process each file
        for ast_file in ast_files:
            logger.debug("Processing %s", ast_file)
            self.process_ast_file(ast_file)

        # Return statistics
        return {
            'total_files': len(ast_files),
            'processed': self._processed_files,
            'failed': self._failed_files,
            'success_rate': self._processed_files / len(ast_files) if ast_files else 0
        }

    def convert_file(self, ast_file: Union[str, Path], output_dir: Union[str, Path, None] = None) -> Union[bool, Optional[Path]]:
        """Convert a single AST file to model.

        Args:
            ast_file: Path to AST file
            output_dir: Output directory (uses self.output_dir if None)

        Returns:
            True if successful, False otherwise
        """
        # Update output directory if provided
        if output_dir:
            self.output_dir = Path(output_dir)

        result = self.process_ast_file(ast_file)
        
        # For DI mode compatibility, return path if successful
        if result and self.ast_processor:
            object_type = 'unknown'
            object_name = Path(ast_file).stem.replace('.ast', '')
            
            # Try to extract metadata
            if hasattr(self.ast_processor, 'extract_metadata'):
                metadata = self.ast_processor.extract_metadata({'file': str(ast_file)})
                object_type = metadata.get('object_type', 'unknown')
            
            if self.output_dir:
                return self.output_dir / object_type / f"{object_name}.model.json"
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics.
        
        Returns:
            Dictionary with statistics about processing
        """
        stats = {
            'processed_files': self._processed_files,
            'failed_files': self._failed_files,
            'entities': len(self.get_all_entities()),
        }
        
        # Add service-specific stats if available
        if self.ast_processor and hasattr(self.ast_processor, 'get_statistics'):
            stats['ast_processor'] = self.ast_processor.get_statistics()
        
        if self.model_persistence and hasattr(self.model_persistence, 'get_statistics'):
            stats['persistence'] = self.model_persistence.get_statistics()
        
        if self.relationship_manager:
            if hasattr(self.relationship_manager, 'get_relationship_graph'):
                stats['relationships'] = len(self.relationship_manager.get_relationship_graph())
            elif hasattr(self.relationship_manager, 'get_all_relationships'):
                stats['relationships'] = len(self.relationship_manager.get_all_relationships())
        else:
            # Count relationships from internal tracking
            total_relationships = sum(len(rels) for rels in self._entity_relationships.values())
            stats['relationships'] = total_relationships
        
        return stats


# Global coordinator instance
_coordinator = ModelCoordinator()


def get_model_coordinator() -> ModelCoordinator:








    """Get the global model coordinator instance.

    Returns:
        The global ModelCoordinator instance
    """
    return _coordinator


# Convenience functions
def create_entity(entity_type: str, name: str, **kwargs) -> PBSourcedEntity:




    """Create a new PowerBuilder entity using the global coordinator.

    Args:
        entity_type: Type of entity to create
        name: Name of the entity
        **kwargs: Additional arguments for entity creation

    Returns:
        Created entity instance
    """
    return _coordinator.create_entity(entity_type, name, **kwargs)


def create_application(name: str, **kwargs) -> PBApplication:








    """Create a PowerBuilder application using the global coordinator."""
    return _coordinator.create_application(name, **kwargs)


def create_window(name: str, **kwargs) -> Window:








    """Create a PowerBuilder window using the global coordinator."""
    return _coordinator.create_window(name, **kwargs)


def create_function(name: str, return_type: str = "void", **kwargs) -> PBFunction:








    """Create a PowerBuilder function using the global coordinator."""
    return _coordinator.create_function(name, return_type, **kwargs)


def create_datawindow(
    name: str, sql_statement: str | None = None, **kwargs,
) -> PBDataWindow:
    """Create a PowerBuilder DataWindow using the global coordinator."""
    return _coordinator.create_datawindow(name, sql_statement, **kwargs)


def add_relationship(from_entity: str, to_entity: str, relationship_type: str = "uses") -> None:
    """Add a relationship between entities using the global coordinator."""
    return _coordinator.add_relationship(from_entity, to_entity, relationship_type)


def validate_all_relationships() -> list[str]:
    """Validate all entity relationships using the global coordinator."""
    return _coordinator.validate_all_relationships()
