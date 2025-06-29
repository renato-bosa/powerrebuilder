"""Base unified extractor for PowerBuilder objects."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type

from .datawindow import DataWindowExtractor
from .schema import DatabaseSchemaExtractor

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Abstract base class for all extractors."""
    
    @abstractmethod
    def extract(self, data: bytes, object_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract content from binary data.
        
        Args:
            data: Raw binary data
            object_info: Optional metadata about the object
            
        Returns:
            Dictionary with extracted content
        """
        pass
        
    @abstractmethod
    def can_extract(self, data: bytes, object_info: Optional[Dict[str, Any]] = None) -> bool:
        """Check if this extractor can handle the given data.
        
        Args:
            data: Raw binary data
            object_info: Optional metadata about the object
            
        Returns:
            True if this extractor can handle the data
        """
        pass


class UnifiedExtractor:
    """Unified extractor that delegates to appropriate specialized extractors."""
    
    def __init__(self):
        """Initialize unified extractor with all available extractors."""
        self.extractors: List[BaseExtractor] = [
            DataWindowExtractor(),
            DatabaseSchemaExtractor(),
        ]
        
        # Type-specific extractor mapping
        self.type_extractors: Dict[str, BaseExtractor] = {
            'datawindow': DataWindowExtractor(),
            'dwo': DataWindowExtractor(),
            'schema': DatabaseSchemaExtractor(),
            'database': DatabaseSchemaExtractor(),
        }
        
    def extract(self, data: bytes, object_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract content using appropriate extractor.
        
        Args:
            data: Raw binary data
            object_info: Optional metadata including 'type' field
            
        Returns:
            Dictionary with extracted content
        """
        result = {
            'success': False,
            'extractor': None,
            'content': None,
            'error': None
        }
        
        # Try type-specific extractor first
        if object_info and 'type' in object_info:
            obj_type = object_info['type'].lower()
            if obj_type in self.type_extractors:
                extractor = self.type_extractors[obj_type]
                try:
                    content = extractor.extract(data, object_info)
                    if content:
                        result['success'] = True
                        result['extractor'] = extractor.__class__.__name__
                        result['content'] = content
                        return result
                except Exception as e:
                    logger.debug(f"Type-specific extraction failed: {e}")
                    
        # Try all extractors to find one that can handle the data
        for extractor in self.extractors:
            try:
                if extractor.can_extract(data, object_info):
                    content = extractor.extract(data, object_info)
                    if content:
                        result['success'] = True
                        result['extractor'] = extractor.__class__.__name__
                        result['content'] = content
                        return result
            except Exception as e:
                logger.debug(f"Extraction with {extractor.__class__.__name__} failed: {e}")
                result['error'] = str(e)
                
        return result
        
    def register_extractor(self, extractor: BaseExtractor, types: Optional[List[str]] = None):
        """Register a new extractor.
        
        Args:
            extractor: Extractor instance to register
            types: Optional list of object types this extractor handles
        """
        if extractor not in self.extractors:
            self.extractors.append(extractor)
            
        if types:
            for obj_type in types:
                self.type_extractors[obj_type.lower()] = extractor
                
    def extract_all(self, data: bytes, object_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Try all applicable extractors and return combined results.
        
        Args:
            data: Raw binary data
            object_info: Optional metadata
            
        Returns:
            Dictionary with results from all applicable extractors
        """
        results = {}
        
        for extractor in self.extractors:
            try:
                if extractor.can_extract(data, object_info):
                    content = extractor.extract(data, object_info)
                    if content:
                        extractor_name = extractor.__class__.__name__
                        results[extractor_name] = content
            except Exception as e:
                logger.debug(f"Extraction with {extractor.__class__.__name__} failed: {e}")
                
        return results


# Make extractors compatible with BaseExtractor
class DataWindowExtractorAdapter(BaseExtractor):
    """Adapter to make DataWindowExtractor compatible with BaseExtractor."""
    
    def __init__(self):
        self.extractor = DataWindowExtractor()
        
    def extract(self, data: bytes, object_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.extractor.extract(data, object_info)
        
    def can_extract(self, data: bytes, object_info: Optional[Dict[str, Any]] = None) -> bool:
        # Check for DataWindow markers
        markers = [
            b"P\x00B\x00S\x00E\x00L\x00E\x00C\x00T\x00",
            b"r\x00e\x00l\x00e\x00a\x00s\x00e\x00",
            b"d\x00a\x00t\x00a\x00w\x00i\x00n\x00d\x00o\x00w\x00",
        ]
        return any(marker in data for marker in markers)


class DatabaseSchemaExtractorAdapter(BaseExtractor):
    """Adapter to make DatabaseSchemaExtractor compatible with BaseExtractor."""
    
    def __init__(self):
        self.extractor = DatabaseSchemaExtractor()
        
    def extract(self, data: bytes, object_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # DatabaseSchemaExtractor has different interface - adapt it
        schema = self.extractor.extract_schema(data)
        return {
            'schema': schema,
            'tables': schema.get('tables', []) if schema else []
        }
        
    def can_extract(self, data: bytes, object_info: Optional[Dict[str, Any]] = None) -> bool:
        # Check for schema markers
        markers = [
            b"CREATE TABLE",
            b"CREATE INDEX",
            b"PRIMARY KEY",
        ]
        data_str = data.decode('utf-8', errors='ignore').upper()
        return any(marker.decode() in data_str for marker in markers)


# Convenience function
def extract_powerbuilder_object(data: bytes, object_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract content from PowerBuilder object data.
    
    Args:
        data: Raw binary data
        object_info: Optional metadata about the object
        
    Returns:
        Dictionary with extracted content
    """
    extractor = UnifiedExtractor()
    return extractor.extract(data, object_info)