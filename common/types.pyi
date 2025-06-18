"""Type definitions for PowerBuilder type system."""

from typing import Any, Dict, Optional, List, Union
from enum import Enum

class TypeCategory(Enum):
    BASIC: str = "basic"
    ARRAY: str = "array"
    CUSTOM: str = "custom"
    STRUCTURE: str = "structure"
    ENUM: str = "enum"

class BasicType:
    name: str
    category: TypeCategory
    
    def __init__(self, name: str, category: TypeCategory = TypeCategory.BASIC) -> None: ...

class ArrayType:
    name: str
    element_type: BasicType
    dimensions: List[int]
    
    def __init__(self, name: str, element_type: BasicType, dimensions: Optional[List[int]] = None) -> None: ...

class CustomType:
    name: str
    base_type: Optional[str]
    
    def __init__(self, name: str, base_type: Optional[str] = None) -> None: ...

class TypeRegistry:
    @staticmethod
    def register(name: str, type_info: Dict[str, Any]) -> None: ...
    
    @staticmethod
    def get(name: str) -> Optional[Dict[str, Any]]: ...
    
    @staticmethod
    def is_registered(name: str) -> bool: ...
