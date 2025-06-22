"""Model coordinator for PowerBuilder object model management.

This module provides centralized coordination for the PowerBuilder object model,
managing the creation and relationships between various model components.
"""


import logging
from pathlib import Path

from .base.pb_entity import PBSourcedEntity
from .entities.pb_application import PBApplication
from .entities.pb_event import PBEvent
from .entities.pb_function import PBFunction
from .entities.pb_variable import PBVariable
from .library.library import PBLibrary
from .pb_datawindow.datawindow import PBDataWindow
from .pb_transaction.transaction import PBTransaction
from .ui.ui_elements import Menu, Window

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
            "application": PBApplication, "function": PBFunction, "event": PBEvent, "variable": PBVariable, "window": Window, "menu": Menu, "datawindow": PBDataWindow, "transaction": PBTransaction, }

    def create_entity(self, entity_type: str, name: str, **kwargs) -> PBSourcedEntity:


        

        """Create a new PowerBuilder entity.

        Args:
            entity_type: Type of entity to create (e.g., 'function', 'window')
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
        self, name: str, return_type: str = "void", **kwargs
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
        self, name: str, sql_source: str | None = None, **kwargs
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
        self, type_name: str, type_class: type[PBSourcedEntity]
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
    name: str, sql_source: str | None = None, **kwargs
) -> PBDataWindow:



    
    


    """Create a PowerBuilder DataWindow using the global coordinator."""
    return _coordinator.create_datawindow(name, sql_source, **kwargs)