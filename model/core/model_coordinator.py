"""Model coordinator for PowerBuilder object model management.

This module provides centralized coordination for the PowerBuilder object model,
managing the creation and relationships between various model components.
"""


import logging
from pathlib import Path
from typing import Any, Callable
import re

from model.base.pb_entity import PBSourcedEntity
from model.entities.pb_application import PBApplication
from model.entities.pb_event import PBEvent
from model.entities.function_entities import PBFunction, PBVariable
from model.core.library import Library as PBLibrary
from model.datawindow.datawindow import PBDataWindow
from model.transaction.transaction import PBTransaction
from model.ui import Menu, Window
from model.utils.errors import ValidationError

logger = logging.getLogger(__name__)


class ModelCoordinator:
    """Coordinates the creation and management of PowerBuilder model objects.

    This class provides a centralized interface for creating and managing
    PowerBuilder model objects, ensuring consistency and proper relationships
    between different model components.
    """

    def __init__(self) -> None:
        """Initialize the model coordinator."""
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

    def get_entity(self, entity_type: str, name: str) -> PBSourcedEntity | None:




        """Get a cached entity by type and name.

        Args:
            entity_type: Type of entity
            name: Name of the entity

        Returns:
            Cached entity instance or None if not found
        """
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
        self, name: str, sql_source: str | None = None, **kwargs,
    ) -> PBDataWindow:




        """Create a PowerBuilder DataWindow.

        Args:
            name: DataWindow name
            sql_source: SQL source for the DataWindow
            **kwargs: Additional DataWindow properties

        Returns:
            Created DataWindow instance
        """
        return self.create_entity("datawindow", name, sql_source=sql_source, **kwargs)

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
        self._entity_cache.clear()
        logger.debug("Cleared entity cache")

    def get_all_entities(self) -> list[PBSourcedEntity]:
        """Get all cached entities.

        Returns:
            List of all cached entities
        """
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
    name: str, sql_source: str | None = None, **kwargs,
) -> PBDataWindow:
    """Create a PowerBuilder DataWindow using the global coordinator."""
    return _coordinator.create_datawindow(name, sql_source, **kwargs)


def add_relationship(from_entity: str, to_entity: str, relationship_type: str = "uses") -> None:
    """Add a relationship between entities using the global coordinator."""
    return _coordinator.add_relationship(from_entity, to_entity, relationship_type)


def validate_all_relationships() -> list[str]:
    """Validate all entity relationships using the global coordinator."""
    return _coordinator.validate_all_relationships()
