"""Entity validation service for PowerBuilder entities."""
import logging
import re
from typing import Any, Callable, Dict, List

from src.model.utils.errors import ValidationError
from src.model.interfaces import IEntityValidator

logger = logging.getLogger(__name__)


class EntityValidator(IEntityValidator):
    """Validator for PowerBuilder entities."""
    
    def __init__(self):
        """Initialize the entity validator."""
        # Validation rules for each entity type
        self._validation_rules: Dict[str, List[Callable[[str, Dict[str, Any]], None]]] = {
        "application": [self._validate_application],
            "function": [self._validate_function],
            "event": [self._validate_event],
            "variable": [self._validate_variable],
            "window": [self._validate_window],
            "menu": [self._validate_menu],
            "datawindow": [self._validate_datawindow],
            "transaction": [self._validate_transaction],
        }
        
        # Track validated entities to prevent duplicates
        self._validated_entities: set[str] = set()
    
    def validate_entity(self, entity: Any) -> List[str]:
        """Validate an entity.
        
        Args:
            entity: Entity to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Get entity type and name
        entity_type = getattr(entity, '__class__.__name__', 'unknown').lower()
        entity_name = getattr(entity, 'name', '')
        
        try:
            # Validate name
            if not self.validate_name(entity_name, entity_type):
                errors.append(f"Invalid name for {entity_type}: {entity_name}")
            
            # Run type-specific validation
            kwargs = {
            'return_type': getattr(entity, 'return_type', None),
                'var_type': getattr(entity, 'var_type', None),
                'sql_statement': getattr(entity, 'sql_statement', None),
            }
            
            # Run validation rules
            if entity_type in self._validation_rules:
                for rule in self._validation_rules[entity_type]:
                    try:
                        rule(entity_name, kwargs)
                    except ValidationError as e:
                        errors.append(str(e))
                        
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            
        return errors
    
    def validate_name(self, name: str, entity_type: str) -> bool:
        """Validate entity name.
        
        Args:
            name: Entity name
            entity_type: Type of entity
            
        Returns:
            True if valid, False otherwise
        """
        # Common validation
        if not name or not isinstance(name, str):
            return False
        
        # PowerBuilder naming rules
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            return False
        
        # Check for duplicates
        cache_key = f"{entity_type}:{name}"
        if cache_key in self._validated_entities:
            logger.warning("%s with name '%s' already exists", entity_type, name)
            return False
        
        # Mark as validated
        self._validated_entities.add(cache_key)
        return True
    
    def _validate_application(self, name: str, kwargs: Dict[str, Any]) -> None:
        """Validate application creation."""
        # Application names typically end with _app
        if not name.endswith("_app") and "app" not in name.lower():
            logger.warning(
            "Application name '%s' does not follow naming convention (usually ends with _app)", 
                name
            )
    
    def _validate_function(self, name: str, kwargs: Dict[str, Any]) -> None:
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
            logger.warning(
            "Function name '%s' does not follow PowerBuilder naming conventions (of_, uf_, or f_ prefix)", 
                name
            )
    
    def _validate_event(self, name: str, kwargs: Dict[str, Any]) -> None:
        """Validate event creation."""
        # Event naming convention
        standard_events = [
        "clicked", "doubleclicked", "constructor", "destructor", 
            "open", "close", "activate", "deactivate", "resize",
            "rbuttondown", "lbuttondown", "mousedown", "mouseup",
            "keydown", "keyup", "getfocus", "losefocus"
        ]
        
        if not (name.startswith("ue_") or name in standard_events):
            logger.warning(
            "Event name '%s' does not follow naming convention (ue_ prefix for user events)", 
                name
            )
    
    def _validate_variable(self, name: str, kwargs: Dict[str, Any]) -> None:
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
            logger.warning(
            "Variable name '%s' does not follow PowerBuilder naming conventions (i/g/l/a prefix)", 
                name
            )
    
    def _validate_window(self, name: str, kwargs: Dict[str, Any]) -> None:
        """Validate window creation."""
        # Window naming convention
        if not name.startswith("w_"):
            logger.warning(
            "Window name '%s' does not follow naming convention (w_ prefix)", 
                name
            )
    
    def _validate_menu(self, name: str, kwargs: Dict[str, Any]) -> None:
        """Validate menu creation."""
        # Menu naming convention
        if not name.startswith("m_"):
            logger.warning(
            "Menu name '%s' does not follow naming convention (m_ prefix)", 
                name
            )
    
    def _validate_datawindow(self, name: str, kwargs: Dict[str, Any]) -> None:
        """Validate datawindow creation."""
        # DataWindow naming convention
        if not (name.startswith("d_") or name.startswith("dw_")):
            logger.warning(
            "DataWindow name '%s' does not follow naming convention (d_ or dw_ prefix)", 
                name
            )
    
    def _validate_transaction(self, name: str, kwargs: Dict[str, Any]) -> None:
        """Validate transaction creation."""
        # Transaction objects often have specific suffixes
        if not (name.endswith("_trans") or name == "sqlca"):
            logger.warning(
            "Transaction name '%s' does not follow naming convention (usually ends with _trans)", 
                name
            )
    
    def clear_validated(self) -> None:
        """Clear the validated entities set."""
        self._validated_entities.clear()
        logger.debug("Cleared validated entities set")