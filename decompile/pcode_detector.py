"""P-code detection utilities for PowerBuilder objects.

This module provides utilities to detect and extract P-code sections
from PowerBuilder object data.
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class PCodeDetector:
    """Utilities for detecting P-code in PowerBuilder objects."""
    
    # Common headers/markers in PowerBuilder files
    PB_EXPORT_HEADER = b'HA$PBExportHeader$'
    PB_EXPORT_COMMENTS = b'$PBExportComments$'
    
    # P-code typically starts after these patterns
    PCODE_START_MARKERS = [
        b'\x04\x00\x00\x00',  # Common 4-byte length prefix
        b'\x08\x00\x00\x00',  # Another common prefix
        # Unicode markers
        b'\x00\x04\x00\x00\x00\x00',
        b'\x00\x08\x00\x00\x00\x00',
    ]
    
    @classmethod
    def find_pcode_section(cls, data: bytes) -> Tuple[int, int]:
        """Find the P-code section in PowerBuilder object data.
        
        Args:
            data: Raw object data
            
        Returns:
            Tuple of (offset, length) for P-code section, or (-1, 0) if not found
        """
        # Strategy 1: Look for export comments marker
        export_pos = data.find(cls.PB_EXPORT_COMMENTS)
        if export_pos >= 0:
            # Find end of export line (newline)
            newline_pos = data.find(b'\n', export_pos)
            if newline_pos >= 0:
                # P-code often starts after the newline
                pcode_start = newline_pos + 1
                
                # Try to find the P-code length
                # Look for structured data after the export comments
                if pcode_start + 4 <= len(data):
                    # Check if next few bytes look like P-code
                    test_bytes = data[pcode_start:pcode_start + 20]
                    
                    # Heuristic: P-code often has non-printable bytes
                    non_printable = sum(1 for b in test_bytes if b < 32 or b > 126)
                    
                    if non_printable > len(test_bytes) // 2:
                        # Likely P-code
                        pcode_length = len(data) - pcode_start
                        logger.debug(f"Found P-code after export comments at offset {pcode_start}")
                        return pcode_start, pcode_length
        
        # Strategy 2: Look for P-code start markers
        for marker in cls.PCODE_START_MARKERS:
            pos = data.find(marker)
            if pos >= 0:
                # Found a potential P-code start
                pcode_start = pos
                pcode_length = len(data) - pcode_start
                logger.debug(f"Found P-code by marker at offset {pcode_start}")
                return pcode_start, pcode_length
        
        # Strategy 3: Look for function/event markers in source
        # PowerBuilder source often has patterns like "function" or "event"
        # followed by P-code
        for keyword in [b'function ', b'event ', b'on ', b'subroutine ']:
            pos = data.find(keyword)
            if pos >= 0:
                # Find the end of the source section
                # Look for typical P-code patterns after source
                search_start = pos + len(keyword)
                
                # Skip to end of source (look for multiple newlines or binary data)
                i = search_start
                while i < len(data) - 4:
                    # Check for transition to binary data
                    if data[i:i+4] in cls.PCODE_START_MARKERS:
                        logger.debug(f"Found P-code after {keyword.decode()} at offset {i}")
                        return i, len(data) - i
                    
                    # Check for multiple control characters indicating binary data
                    if i + 10 < len(data):
                        test_window = data[i:i+10]
                        control_chars = sum(1 for b in test_window if b < 32 and b not in [9, 10, 13])
                        if control_chars >= 5:
                            logger.debug(f"Found P-code by control chars at offset {i}")
                            return i, len(data) - i
                    
                    i += 1
        
        # Strategy 4: Brute force - look for binary data sections
        # Scan for regions with high concentration of non-printable bytes
        window_size = 20
        threshold = 0.7  # 70% non-printable
        
        for i in range(0, len(data) - window_size, 4):  # 4-byte aligned
            window = data[i:i + window_size]
            non_printable = sum(1 for b in window if b < 32 or b > 126)
            
            if non_printable / window_size >= threshold:
                # Check if this looks like structured binary data
                # (not just random bytes or padding)
                if any(marker in data[i:i+8] for marker in cls.PCODE_START_MARKERS):
                    logger.debug(f"Found P-code by binary scan at offset {i}")
                    return i, len(data) - i
        
        logger.debug("No P-code section found")
        return -1, 0
    
    @classmethod
    def is_pcode_object(cls, object_name: str) -> bool:
        """Check if an object type typically contains P-code.
        
        Args:
            object_name: Name of the object (including extension)
            
        Returns:
            True if object type typically has P-code
        """
        name_lower = object_name.lower()
        
        # These object types typically contain P-code
        pcode_extensions = [
            '.fun',  # Functions
            '.win',  # Windows (event handlers)
            '.udo',  # User objects (methods/events)
            '.app',  # Application (events)
            '.men',  # Menus (event handlers)
            '.srf',  # Function objects
            '.srj',  # Project objects
        ]
        
        return any(name_lower.endswith(ext) for ext in pcode_extensions)
    
    @classmethod
    def extract_source_and_pcode(cls, data: bytes) -> Tuple[bytes, bytes]:
        """Extract source code and P-code sections separately.
        
        Args:
            data: Raw object data
            
        Returns:
            Tuple of (source_bytes, pcode_bytes)
        """
        # Find P-code section
        pcode_offset, pcode_length = cls.find_pcode_section(data)
        
        if pcode_offset > 0:
            # Split into source and P-code
            source_bytes = data[:pcode_offset]
            pcode_bytes = data[pcode_offset:pcode_offset + pcode_length]
            return source_bytes, pcode_bytes
        else:
            # No P-code found, it's all source
            return data, b''