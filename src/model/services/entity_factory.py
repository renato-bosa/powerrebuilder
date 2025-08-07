"""Entity factory service for creating PowerBuilder entities."""
import logging
from typing import Optional

from src.model.types.base import PBNode as PBSourcedEntity
from src.model.entities.application import PBApplication
from src.model.entities.event import PBEvent
from src.model.entities.function import PBFunction, PBVariableNode as PBVariable
from src.model.entities.library import Library as PBLibrary
# Create stub classes for missing entity types
from dataclasses import dataclass
from typing import Any

class Window(PBSourcedEntity):
    """Stub Window class."""

    def __init__(self, name: str = ""):
        super().__init__()
        self.name = name  # Use inherited property

class Menu(PBSourcedEntity):
    """Stub Menu class."""

    def __init__(self, name: str = ""):
        super().__init__()
        self.name = name  # Use inherited property

class PBDataWindow(PBSourcedEntity):
    """Stub DataWindow class."""

    sql_statement: Optional[str] = None

    def __init__(self, name: str = "", sql_statement: Optional[str] = None):
        super().__init__()
        self.name = name  # Use inherited property
        self.sql_statement = sql_statement
from src.model.transaction.transaction import PBTransaction
from src.model.interfaces import IEntityFactory

logger = logging.getLogger(__name__)


class EntityFactory(IEntityFactory):
    """Factory for creating PowerBuilder entities."""
    
    def __init__(self):
        """Initialize the entity factory."""
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
        self._entity_cache: dict[str, PBSourcedEntity] = {}
    
    def create_entity(self, entity_type: str, name: str, **kwargs) -> PBSourcedEntity:
        """Create a new PowerBuilder entity.
        
        Args:
            entity_type: Type of entity to create
            name: Name of the entity
            **kwargs: Additional arguments for entity creation
            
        Returns:
            Created entity instance
            
        Raises:
            ValueError: If entity_type is not recognized
        """
        if entity_type not in self._type_registry:
            msg = f"Unknown entity type: {entity_type}"
            raise ValueError(msg)
        
        entity_class = self._type_registry[entity_type]
        entity = entity_class(name=name, **kwargs)
        
        # Cache the entity
        cache_key = f"{entity_type}:{name}"
        self._entity_cache[cache_key] = entity
        
        logger.debug("Created %s entity: %s", entity_type, name)
        return entity
    
    def create_application(self, name: str, **kwargs) -> PBApplication:
        """Create a PowerBuilder application.
        
        Args:
            name: Application name
            **kwargs: Additional application properties
            
        Returns:
            Created application instance
        """
        entity = self.create_entity("application", name, **kwargs)
        if not isinstance(entity, PBApplication):
            raise TypeError(f"Expected PBApplication, got {type(entity)}")
        return entity
    
    def create_window(self, name: str, **kwargs) -> Window:
        """Create a PowerBuilder window.
        
        Args:
            name: Window name
            **kwargs: Additional window properties
            
        Returns:
            Created window instance
        """
        entity = self.create_entity("window", name, **kwargs)
        if not isinstance(entity, Window):
            raise TypeError(f"Expected Window, got {type(entity)}")
        return entity
    
    def create_function(self, name: str, return_type: str = "void", **kwargs) -> PBFunction:
        """Create a PowerBuilder function.
        
        Args:
            name: Function name
            return_type: Function return type
            **kwargs: Additional function properties
            
        Returns:
            Created function instance
        """
        entity = self.create_entity("function", name, return_type=return_type, **kwargs)
        if not isinstance(entity, PBFunction):
            raise TypeError(f"Expected PBFunction, got {type(entity)}")
        return entity
    
    def create_datawindow(
        self, name: str, sql_statement: Optional[str] = None, **kwargs
    ) -> PBDataWindow:
        """Create a PowerBuilder DataWindow.
        
        Args:
            name: DataWindow name
            sql_statement: SQL statement for the DataWindow
            **kwargs: Additional DataWindow properties
            
        Returns:
            Created DataWindow instance
        """
        entity = self.create_entity("datawindow", name, sql_statement=sql_statement, **kwargs)
        if not isinstance(entity, PBDataWindow):
            raise TypeError(f"Expected PBDataWindow, got {type(entity)}")
        return entity
    
    def create_library(self, name: str, **kwargs) -> PBLibrary:
        """Create a PowerBuilder library.
        
        Args:
            name: Library name
            **kwargs: Additional library properties
            
        Returns:
            Created library instance
        """
        # Libraries are special - they don't go through the normal entity creation
        from pathlib import Path
        path = kwargs.get('path', Path(name))
        library = PBLibrary(name=name, path=path)
        logger.debug("Created library: %s at %s", name, path)
        return library
    
    def register_custom_type(self, type_name: str, type_class: type[PBSourcedEntity]) -> None:
        """Register a custom entity type.
        
        Args:
            type_name: Name for the entity type
            type_class: Class to use for creating entities of this type
        """
        self._type_registry[type_name] = type_class
        logger.debug("Registered custom type: %s", type_name)
    
    def get_entity(self, entity_type: str, name: str) -> Optional[PBSourcedEntity]:
        """Get a cached entity by type and name.
        
        Args:
            entity_type: Type of entity
            name: Name of the entity
            
        Returns:
            Cached entity instance or None if not found
        """
        cache_key = f"{entity_type}:{name}"
        return self._entity_cache.get(cache_key)
    
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