"""Core model functionality for SIME Finch."""

from .analysis import CodeAnalyzer
from .attribute import Attribute, AttributeAccess
from .library import Library, LibraryManager
from .model_coordinator import ModelCoordinator
from .source import SourcePosition

__all__ = [
    "ModelCoordinator",
    "SourcePosition", 
    "Attribute",
    "AttributeAccess",
    "CodeAnalyzer",
    "Library",
    "LibraryManager",
]