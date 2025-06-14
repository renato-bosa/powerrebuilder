"""PowerBuilder object type detection and classification.

This module provides utilities to identify PowerBuilder object types and determine
whether they contain P-code (executable code) or are data-only objects.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class ObjectType:
    """PowerBuilder object types enumeration based on internal type codes."""
    
    FUNCTION = 0        # .fun - Contains P-code
    STRUCTURE = 1       # .str - Data only (type definitions)
    WINDOW = 13         # .win - Contains P-code
    USER_OBJECT = 8     # .udo - Contains P-code  
    DATAWINDOW = 18     # .dwo - Data only (SQL and layout)
    MENU = 55           # .men - Contains P-code
    APPLICATION = 9     # .apl - Contains P-code
    QUERY = 77          # .srq - Data only (SQL definitions)
    PIPELINE = 33       # .pip - Data only (pipeline definitions)
    PROJECT = 36        # .srj - Data only (project configuration)
    PROXY = 44          # .prx - Data only (proxy definitions)
    
    # Object types that contain P-code (executable code)
    PCODE_TYPES = {FUNCTION, WINDOW, USER_OBJECT, MENU, APPLICATION}
    
    # Object types that are data-only (no P-code)
    DATA_ONLY_TYPES = {STRUCTURE, DATAWINDOW, QUERY, PIPELINE, PROJECT, PROXY}


class ObjectTypeDetector:
    """Detects PowerBuilder object types and their characteristics."""
    
    # File extension to object type mapping
    EXTENSION_MAP = {
        '.fun': ObjectType.FUNCTION,
        '.str': ObjectType.STRUCTURE,
        '.win': ObjectType.WINDOW,
        '.udo': ObjectType.USER_OBJECT,
        '.sru': ObjectType.USER_OBJECT,  # Source format
        '.dwo': ObjectType.DATAWINDOW,
        '.srd': ObjectType.DATAWINDOW,   # Source format
        '.men': ObjectType.MENU,
        '.srm': ObjectType.MENU,         # Source format
        '.apl': ObjectType.APPLICATION,
        '.sra': ObjectType.APPLICATION,  # Source format
        '.srq': ObjectType.QUERY,
        '.pip': ObjectType.PIPELINE,
        '.srp': ObjectType.PIPELINE,     # Source format
        '.srj': ObjectType.PROJECT,
        '.prx': ObjectType.PROXY,
        '.mef': ObjectType.MENU,         # Menu compiled format
        '.apf': ObjectType.APPLICATION,  # Application compiled format
    }
    
    # Object name patterns (for objects without clear extensions)
    NAME_PATTERNS = {
        'w_': ObjectType.WINDOW,         # Window naming convention
        'u_': ObjectType.USER_OBJECT,    # User object naming convention
        'd_': ObjectType.DATAWINDOW,     # DataWindow naming convention
        'm_': ObjectType.MENU,           # Menu naming convention
        'n_': ObjectType.USER_OBJECT,    # Non-visual object convention
        'f_': ObjectType.FUNCTION,       # Function naming convention
        'of_': ObjectType.FUNCTION,      # Object function convention
    }
    
    @classmethod
    def detect_type(cls, filename: str, type_code: Optional[int] = None) -> Optional[int]:
        """Detect object type from filename or type code.
        
        Args:
            filename: The object filename (e.g., "d_customer.dwo")
            type_code: Optional PowerBuilder internal type code
            
        Returns:
            Object type constant or None if unknown
        """
        if type_code is not None:
            # Map from PBD internal type codes
            # Based on reference/decompilers/powerbuilder-decompile/pbd/definitions.py
            type_offset = type_code - 0x4077
            
            type_map = {
                0: ObjectType.FUNCTION,
                1: ObjectType.STRUCTURE,
                8: ObjectType.USER_OBJECT,
                9: ObjectType.APPLICATION,
                13: ObjectType.WINDOW,
                18: ObjectType.DATAWINDOW,
                55: ObjectType.MENU,
            }
            
            return type_map.get(type_offset)
        
        # Detect from filename
        path = Path(filename)
        ext = path.suffix.lower()
        
        # Check extension first
        if ext in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[ext]
        
        # Check name patterns
        name = path.stem.lower()
        for prefix, obj_type in cls.NAME_PATTERNS.items():
            if name.startswith(prefix):
                return obj_type
        
        # Check for specific patterns in name
        if '_w_' in name:
            return ObjectType.WINDOW
        elif '_u_' in name:
            return ObjectType.USER_OBJECT
        elif '_d_' in name:
            return ObjectType.DATAWINDOW
        elif '_m_' in name:
            return ObjectType.MENU
        elif '_f_' in name:
            return ObjectType.FUNCTION
        
        return None
    
    @classmethod
    def contains_pcode(cls, filename: str, type_code: Optional[int] = None) -> bool:
        """Check if an object type contains P-code.
        
        Args:
            filename: The object filename
            type_code: Optional PowerBuilder internal type code
            
        Returns:
            True if the object contains P-code, False otherwise
        """
        obj_type = cls.detect_type(filename, type_code)
        if obj_type is None:
            # Unknown type - assume it might contain P-code to be safe
            logger.warning(f"Unknown object type for {filename}, assuming P-code")
            return True
        
        return obj_type in ObjectType.PCODE_TYPES
    
    @classmethod
    def is_datawindow(cls, filename: str, type_code: Optional[int] = None) -> bool:
        """Check if an object is a DataWindow.
        
        Args:
            filename: The object filename
            type_code: Optional PowerBuilder internal type code
            
        Returns:
            True if the object is a DataWindow
        """
        obj_type = cls.detect_type(filename, type_code)
        return obj_type == ObjectType.DATAWINDOW
    
    @classmethod
    def is_structure(cls, filename: str, type_code: Optional[int] = None) -> bool:
        """Check if an object is a Structure.
        
        Args:
            filename: The object filename
            type_code: Optional PowerBuilder internal type code
            
        Returns:
            True if the object is a Structure
        """
        obj_type = cls.detect_type(filename, type_code)
        return obj_type == ObjectType.STRUCTURE
    
    @classmethod
    def get_object_info(cls, filename: str, type_code: Optional[int] = None) -> Tuple[str, bool]:
        """Get object type name and P-code status.
        
        Args:
            filename: The object filename
            type_code: Optional PowerBuilder internal type code
            
        Returns:
            Tuple of (type_name, contains_pcode)
        """
        obj_type = cls.detect_type(filename, type_code)
        
        type_names = {
            ObjectType.FUNCTION: "Function",
            ObjectType.STRUCTURE: "Structure",
            ObjectType.WINDOW: "Window",
            ObjectType.USER_OBJECT: "UserObject",
            ObjectType.DATAWINDOW: "DataWindow",
            ObjectType.MENU: "Menu",
            ObjectType.APPLICATION: "Application",
            ObjectType.QUERY: "Query",
            ObjectType.PIPELINE: "Pipeline",
            ObjectType.PROJECT: "Project",
            ObjectType.PROXY: "Proxy",
        }
        
        if obj_type is None:
            return "Unknown", True  # Assume P-code for safety
        
        type_name = type_names.get(obj_type, "Unknown")
        has_pcode = obj_type in ObjectType.PCODE_TYPES
        
        return type_name, has_pcode
    
    @classmethod
    def should_decompile(cls, filename: str) -> bool:
        """Check if a file should be sent to the decompiler.
        
        Args:
            filename: The object filename
            
        Returns:
            True if the file should be decompiled
        """
        # Only decompile files with specific P-code extensions
        path = Path(filename)
        ext = path.suffix.lower()
        
        # These are the compiled formats that contain P-code
        decompilable_extensions = {'.fun', '.win', '.udo', '.men', '.mef', '.apl', '.apf'}
        
        return ext in decompilable_extensions